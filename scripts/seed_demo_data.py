#!/usr/bin/env python3
"""
Seed script — generates realistic demo cost data for the platform.
Run after database init to populate the dashboard with sample data.
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta
import asyncpg

DB_URL = "postgresql://postgres:postgres@localhost:5432/ai_cost_platform"

ORG_ID    = "00000000-0000-0000-0000-000000000001"
TEAM1_ID  = "00000000-0000-0000-0000-000000000010"
TEAM2_ID  = "00000000-0000-0000-0000-000000000011"

MODELS = [
    ("openai",    "gpt-4o",                     5,  15),
    ("openai",    "gpt-4o-mini",                0.15, 0.6),
    ("openai",    "gpt-4-turbo",                10, 30),
    ("anthropic", "claude-3-opus-20240229",     15, 75),
    ("anthropic", "claude-3-sonnet-20240229",    3, 15),
    ("anthropic", "claude-3-haiku-20240307",    0.25, 1.25),
    ("gemini",    "gemini-1.5-pro",             3.5, 10.5),
    ("gemini",    "gemini-1.5-flash",           0.35, 1.05),
]

def calc_cost(provider, model, prompt_tokens, completion_tokens):
    for p, m, input_price, output_price in MODELS:
        if p == provider and m == model:
            prompt_cost  = int((prompt_tokens  / 1_000_000) * input_price  * 1_000_000)
            comp_cost    = int((completion_tokens / 1_000_000) * output_price * 1_000_000)
            return prompt_cost, comp_cost, prompt_cost + comp_cost
    return 0, 0, 0

async def seed(days=60, events_per_day=200):
    conn = await asyncpg.connect(DB_URL)
    print(f"Seeding {days} days × ~{events_per_day} events/day = ~{days * events_per_day} total events...")

    events = []
    base_date = datetime.utcnow() - timedelta(days=days)

    for day in range(days):
        current_date = base_date + timedelta(days=day)
        # Weekday adjustment — less traffic on weekends
        daily_volume = events_per_day if current_date.weekday() < 5 else int(events_per_day * 0.3)
        # Gradual growth trend
        growth_factor = 1 + (day / days) * 0.8
        daily_volume = int(daily_volume * growth_factor)

        for _ in range(daily_volume):
            provider, model, inp, outp = random.choices(MODELS, weights=[20,35,5,3,15,20,4,8])[0]
            prompt_tokens     = random.randint(100, 3000)
            completion_tokens = random.randint(50, 1500)
            pc, cc, tc        = calc_cost(provider, model, prompt_tokens, completion_tokens)
            team_id = random.choice([TEAM1_ID, TEAM2_ID])
            hour    = random.randint(8, 22)
            ts      = current_date.replace(hour=hour, minute=random.randint(0,59))

            events.append((
                str(uuid.uuid4()), ORG_ID, team_id,
                provider, model,
                prompt_tokens, completion_tokens, prompt_tokens + completion_tokens,
                pc, cc, tc,
                random.randint(150, 4000),
                "success", "production", ts
            ))

    await conn.executemany("""
        INSERT INTO cost_events (
            id, organization_id, team_id,
            provider, model,
            prompt_tokens, completion_tokens, total_tokens,
            prompt_cost_usd_micro, completion_cost_usd_micro, total_cost_usd_micro,
            latency_ms, status, environment, created_at
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
        ON CONFLICT DO NOTHING
    """, events)

    print(f"✅ Seeded {len(events)} cost events")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed())
