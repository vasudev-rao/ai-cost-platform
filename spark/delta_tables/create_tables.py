"""
Delta Lake Table DDL — Create all tables with proper partitioning and properties
"""

BRONZE_LLM_EVENTS = """
CREATE TABLE IF NOT EXISTS bronze.llm_events (
    event_id        STRING NOT NULL,
    organization_id STRING NOT NULL,
    team_id         STRING,
    project_id      STRING,
    user_id         STRING,
    provider        STRING NOT NULL,
    model           STRING NOT NULL,
    prompt_tokens   INT,
    completion_tokens INT,
    total_tokens    INT,
    total_cost_usd_micro BIGINT,
    latency_ms      INT,
    status          STRING,
    environment     STRING,
    request_id      STRING,
    timestamp       STRING NOT NULL,
    ingest_date     DATE NOT NULL,
    kafka_offset    BIGINT,
    kafka_partition INT
)
USING DELTA
PARTITIONED BY (ingest_date, provider)
LOCATION 's3://ai-cost-platform-data/delta/bronze/llm_events'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.logRetentionDuration' = 'interval 30 days',
    'delta.deletedFileRetentionDuration' = 'interval 7 days'
);
"""

SILVER_LLM_EVENTS_CLEAN = """
CREATE TABLE IF NOT EXISTS silver.llm_events_clean (
    event_id            STRING NOT NULL,
    organization_id     STRING NOT NULL,
    team_id             STRING,
    project_id          STRING,
    user_id             STRING,
    provider            STRING NOT NULL,
    provider_normalized STRING,
    model               STRING NOT NULL,
    prompt_tokens       INT,
    completion_tokens   INT,
    total_tokens        INT,
    total_cost_usd      DOUBLE,
    total_cost_usd_micro BIGINT,
    latency_ms          INT,
    status              STRING,
    environment         STRING,
    event_ts            TIMESTAMP NOT NULL,
    event_year          INT NOT NULL,
    event_month         INT NOT NULL,
    event_day           INT NOT NULL
)
USING DELTA
PARTITIONED BY (event_year, event_month, provider)
LOCATION 's3://ai-cost-platform-data/delta/silver/llm_events_clean'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.enableChangeDataFeed' = 'true'
);
"""

GOLD_DAILY_AGGREGATES = """
CREATE TABLE IF NOT EXISTS gold.daily_cost_aggregates (
    window_start        TIMESTAMP NOT NULL,
    window_end          TIMESTAMP NOT NULL,
    organization_id     STRING NOT NULL,
    team_id             STRING,
    project_id          STRING,
    model               STRING NOT NULL,
    provider            STRING NOT NULL,
    daily_cost_usd      DOUBLE,
    daily_tokens        BIGINT,
    daily_requests      BIGINT,
    avg_latency_ms      DOUBLE,
    daily_prompt_tokens BIGINT,
    daily_completion_tokens BIGINT,
    event_year          INT NOT NULL,
    event_month         INT NOT NULL,
    event_day           INT NOT NULL
)
USING DELTA
PARTITIONED BY (event_year, event_month, organization_id)
LOCATION 's3://ai-cost-platform-data/delta/gold/daily_cost_aggregates'
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableChangeDataFeed' = 'true'
);
"""
