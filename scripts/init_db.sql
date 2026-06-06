-- =====================================================
-- AI Cost Intelligence Platform — PostgreSQL Schema
-- =====================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ── ORGANIZATIONS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organizations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) UNIQUE NOT NULL,
    domain              VARCHAR(255),
    logo_url            TEXT,
    is_active           BOOLEAN DEFAULT TRUE,
    monthly_budget_usd  INTEGER DEFAULT 0,
    plan                VARCHAR(50) DEFAULT 'free',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ
);
CREATE INDEX idx_org_slug ON organizations(slug);

-- ── TEAMS ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id     UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) NOT NULL,
    description         VARCHAR(500),
    monthly_budget_usd  INTEGER DEFAULT 0,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ,
    UNIQUE(organization_id, slug)
);
CREATE INDEX idx_teams_org ON teams(organization_id);

-- ── USERS ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id     UUID REFERENCES organizations(id),
    team_id             UUID REFERENCES teams(id),
    email               VARCHAR(255) UNIQUE NOT NULL,
    full_name           VARCHAR(255) NOT NULL,
    hashed_password     VARCHAR(255),
    role                VARCHAR(50) DEFAULT 'developer',
    avatar_url          VARCHAR(500),
    is_active           BOOLEAN DEFAULT TRUE,
    is_verified         BOOLEAN DEFAULT FALSE,
    last_login_at       TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(organization_id);

-- ── PROJECTS ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id     UUID NOT NULL REFERENCES organizations(id),
    team_id             UUID REFERENCES teams(id),
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(100) NOT NULL,
    description         TEXT,
    api_key             VARCHAR(64) UNIQUE NOT NULL,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ
);
CREATE INDEX idx_projects_org ON projects(organization_id);
CREATE INDEX idx_projects_api_key ON projects(api_key);

-- ── COST EVENTS (partitioned by month) ────────────────────────────
CREATE TABLE IF NOT EXISTS cost_events (
    id                          UUID NOT NULL DEFAULT uuid_generate_v4(),
    organization_id             UUID NOT NULL,
    team_id                     UUID,
    project_id                  UUID,
    user_id                     UUID,
    provider                    VARCHAR(50) NOT NULL,
    model                       VARCHAR(100) NOT NULL,
    model_version               VARCHAR(50),
    prompt_tokens               INTEGER DEFAULT 0,
    completion_tokens           INTEGER DEFAULT 0,
    total_tokens                INTEGER DEFAULT 0,
    prompt_cost_usd_micro       BIGINT DEFAULT 0,
    completion_cost_usd_micro   BIGINT DEFAULT 0,
    total_cost_usd_micro        BIGINT DEFAULT 0,
    latency_ms                  INTEGER DEFAULT 0,
    first_token_latency_ms      INTEGER,
    is_streaming                SMALLINT DEFAULT 0,
    request_id                  VARCHAR(128),
    session_id                  VARCHAR(128),
    environment                 VARCHAR(50) DEFAULT 'production',
    endpoint                    VARCHAR(255),
    tags                        JSONB,
    status                      VARCHAR(50) DEFAULT 'success',
    error_code                  VARCHAR(100),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create monthly partitions (2024-2026)
DO $$
DECLARE
    start_date DATE := '2024-01-01';
    partition_date DATE;
    partition_name TEXT;
BEGIN
    FOR i IN 0..23 LOOP
        partition_date := start_date + (i || ' months')::INTERVAL;
        partition_name := 'cost_events_' || TO_CHAR(partition_date, 'YYYY_MM');
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS %I PARTITION OF cost_events
             FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            partition_date,
            partition_date + INTERVAL '1 month'
        );
    END LOOP;
END $$;

CREATE INDEX idx_cost_events_org_time ON cost_events(organization_id, created_at DESC);
CREATE INDEX idx_cost_events_model ON cost_events(model, created_at DESC);
CREATE INDEX idx_cost_events_team ON cost_events(team_id, created_at DESC);
CREATE INDEX idx_cost_events_provider ON cost_events(provider, created_at DESC);

-- ── BUDGETS ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budgets (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id         UUID NOT NULL REFERENCES organizations(id),
    team_id                 UUID REFERENCES teams(id),
    project_id              UUID REFERENCES projects(id),
    name                    VARCHAR(255) NOT NULL,
    amount_usd_micro        BIGINT NOT NULL,
    period                  VARCHAR(20) DEFAULT 'monthly',
    alert_threshold_pct     INTEGER DEFAULT 80,
    hard_limit              BOOLEAN DEFAULT FALSE,
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ── ALERTS ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id         UUID NOT NULL REFERENCES organizations(id),
    team_id                 UUID REFERENCES teams(id),
    alert_type              VARCHAR(50) NOT NULL,
    severity                VARCHAR(20) DEFAULT 'warning',
    title                   VARCHAR(255) NOT NULL,
    message                 VARCHAR(1000) NOT NULL,
    metadata                JSONB,
    is_resolved             BOOLEAN DEFAULT FALSE,
    resolved_at             TIMESTAMPTZ,
    notification_channels   JSONB DEFAULT '["email"]',
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_alerts_org_resolved ON alerts(organization_id, is_resolved, created_at DESC);

-- ── FORECASTS ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forecasts (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id             UUID NOT NULL REFERENCES organizations(id),
    team_id                     UUID REFERENCES teams(id),
    horizon                     VARCHAR(10) NOT NULL,
    model_used                  VARCHAR(50) DEFAULT 'prophet',
    forecast_data               JSONB NOT NULL,
    total_predicted_usd_micro   BIGINT DEFAULT 0,
    confidence_score            FLOAT DEFAULT 0.0,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_forecasts_org ON forecasts(organization_id, created_at DESC);

-- ── RECOMMENDATIONS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    id                              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id                 UUID NOT NULL REFERENCES organizations(id),
    team_id                         UUID REFERENCES teams(id),
    title                           VARCHAR(255) NOT NULL,
    description                     TEXT NOT NULL,
    rec_type                        VARCHAR(50) NOT NULL,
    current_model                   VARCHAR(100),
    recommended_model               VARCHAR(100),
    estimated_savings_usd_micro     BIGINT DEFAULT 0,
    estimated_savings_pct           FLOAT DEFAULT 0.0,
    confidence                      FLOAT DEFAULT 0.0,
    evidence                        JSONB,
    is_applied                      BOOLEAN DEFAULT FALSE,
    applied_at                      TIMESTAMPTZ,
    created_at                      TIMESTAMPTZ DEFAULT NOW()
);

-- ── AUDIT LOGS ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100) NOT NULL,
    resource_id     VARCHAR(100),
    changes         JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);

CREATE TABLE IF NOT EXISTS audit_logs_2025 PARTITION OF audit_logs
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS audit_logs_2026 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- ── SUBSCRIPTIONS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subscriptions (
    id                          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id             UUID NOT NULL REFERENCES organizations(id),
    plan                        VARCHAR(50) DEFAULT 'free',
    stripe_customer_id          VARCHAR(255),
    stripe_subscription_id      VARCHAR(255),
    is_active                   BOOLEAN DEFAULT TRUE,
    trial_ends_at               TIMESTAMPTZ,
    current_period_start        TIMESTAMPTZ,
    current_period_end          TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ DEFAULT NOW()
);

-- ── SEED DATA ─────────────────────────────────────────────────────
INSERT INTO organizations (id, name, slug, plan) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Demo Organization', 'demo-org', 'growth')
ON CONFLICT DO NOTHING;

INSERT INTO teams (id, organization_id, name, slug) VALUES
    ('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000001', 'Platform Team', 'platform'),
    ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', 'AI Products Team', 'ai-products')
ON CONFLICT DO NOTHING;
