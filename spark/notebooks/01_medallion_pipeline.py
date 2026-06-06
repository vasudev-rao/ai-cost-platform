# Databricks notebook source
# MAGIC %md
# MAGIC # AI Cost Intelligence Platform — Medallion Architecture Pipeline
# MAGIC
# MAGIC This notebook implements the full Bronze → Silver → Gold pipeline
# MAGIC for processing LLM cost events from Kafka into Delta Lake.
# MAGIC
# MAGIC **Architecture:**
# MAGIC - Bronze: Raw Kafka events, append-only, 30-day retention
# MAGIC - Silver: Cleaned, deduplicated, enriched events
# MAGIC - Gold: Daily aggregates by org/team/model for dashboard queries

# COMMAND ----------
# MAGIC %md ## 1. Configuration

# COMMAND ----------
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from delta.tables import DeltaTable

KAFKA_SERVERS   = spark.conf.get("pipeline.kafka_servers", "kafka:9092")
S3_BASE         = spark.conf.get("pipeline.s3_base",       "s3://ai-cost-platform-data/delta")
CHECKPOINT_BASE = spark.conf.get("pipeline.checkpoint",    "s3://ai-cost-platform-data/checkpoints")

dbutils.widgets.text("env", "prod", "Environment")
ENV = dbutils.widgets.get("env")

print(f"Environment: {ENV}")
print(f"Kafka: {KAFKA_SERVERS}")
print(f"Delta base: {S3_BASE}")

# COMMAND ----------
# MAGIC %md ## 2. Create Delta Databases

# COMMAND ----------
spark.sql(f"CREATE DATABASE IF NOT EXISTS bronze LOCATION '{S3_BASE}/bronze'")
spark.sql(f"CREATE DATABASE IF NOT EXISTS silver LOCATION '{S3_BASE}/silver'")
spark.sql(f"CREATE DATABASE IF NOT EXISTS gold   LOCATION '{S3_BASE}/gold'")

# COMMAND ----------
# MAGIC %md ## 3. Schema Definition

# COMMAND ----------
LLM_SCHEMA = StructType([
    StructField("event_id",                 StringType(),  False),
    StructField("organization_id",          StringType(),  False),
    StructField("team_id",                  StringType(),  True),
    StructField("project_id",               StringType(),  True),
    StructField("user_id",                  StringType(),  True),
    StructField("provider",                 StringType(),  False),
    StructField("model",                    StringType(),  False),
    StructField("prompt_tokens",            IntegerType(), True),
    StructField("completion_tokens",        IntegerType(), True),
    StructField("total_tokens",             IntegerType(), True),
    StructField("prompt_cost_usd_micro",    LongType(),    True),
    StructField("completion_cost_usd_micro",LongType(),    True),
    StructField("total_cost_usd_micro",     LongType(),    True),
    StructField("latency_ms",               IntegerType(), True),
    StructField("status",                   StringType(),  True),
    StructField("environment",              StringType(),  True),
    StructField("request_id",               StringType(),  True),
    StructField("timestamp",                StringType(),  False),
])

# COMMAND ----------
# MAGIC %md ## 4. Bronze Layer — Raw Kafka Ingestion

# COMMAND ----------
def start_bronze_stream():
    kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_SERVERS)
        .option("subscribe", "llm_costs")
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 50000)
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed = (
        kafka_df
        .select(
            col("timestamp").alias("kafka_ts"),
            col("partition").alias("kafka_partition"),
            col("offset").alias("kafka_offset"),
            from_json(col("value").cast("string"), LLM_SCHEMA).alias("d")
        )
        .select("kafka_ts", "kafka_partition", "kafka_offset", "d.*")
        .withColumn("ingest_date", col("kafka_ts").cast("date"))
        .withColumn("ingest_hour", hour("kafka_ts"))
    )

    return (
        parsed.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/bronze_{ENV}")
        .option("mergeSchema", "true")
        .partitionBy("ingest_date", "provider")
        .trigger(processingTime="30 seconds")
        .toTable("bronze.llm_events")
    )

bronze_query = start_bronze_stream()
print(f"Bronze stream started: {bronze_query.id}")

# COMMAND ----------
# MAGIC %md ## 5. Silver Layer — Clean & Enrich

# COMMAND ----------
def start_silver_stream():
    bronze_df = (
        spark.readStream
        .format("delta")
        .option("readChangeFeed", "true")
        .option("startingVersion", "latest")
        .table("bronze.llm_events")
    )

    enriched = (
        bronze_df
        .where(col("event_id").isNotNull() & col("organization_id").isNotNull())
        .where(col("status") == "success")
        .withColumn("event_ts",   to_timestamp("timestamp"))
        .withColumn("event_year",  year("event_ts"))
        .withColumn("event_month", month("event_ts"))
        .withColumn("event_day",   dayofmonth("event_ts"))
        .withColumn("total_cost_usd", (col("total_cost_usd_micro") / lit(1_000_000)).cast("double"))
        .withColumn("provider_display",
            when(col("provider") == "openai",       "OpenAI")
            .when(col("provider") == "anthropic",   "Anthropic")
            .when(col("provider") == "gemini",      "Google Gemini")
            .when(col("provider") == "bedrock",     "AWS Bedrock")
            .when(col("provider") == "azure_openai","Azure OpenAI")
            .otherwise(col("provider"))
        )
        .withColumn("cost_tier",
            when(col("total_cost_usd") > 0.10, "high")
            .when(col("total_cost_usd") > 0.01, "medium")
            .otherwise("low")
        )
        .dropDuplicates(["event_id"])
        .drop("kafka_ts", "kafka_partition", "kafka_offset", "ingest_date", "ingest_hour")
    )

    return (
        enriched.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/silver_{ENV}")
        .partitionBy("event_year", "event_month", "provider")
        .trigger(processingTime="60 seconds")
        .toTable("silver.llm_events_clean")
    )

silver_query = start_silver_stream()
print(f"Silver stream started: {silver_query.id}")

# COMMAND ----------
# MAGIC %md ## 6. Gold Layer — Daily Aggregates

# COMMAND ----------
def start_gold_daily_stream():
    silver_df = (
        spark.readStream
        .format("delta")
        .option("readChangeFeed", "true")
        .table("silver.llm_events_clean")
    )

    agg = (
        silver_df
        .withWatermark("event_ts", "2 hours")
        .groupBy(
            window("event_ts", "1 day"),
            "organization_id", "team_id", "project_id",
            "model", "provider", "provider_display",
            "event_year", "event_month", "event_day",
        )
        .agg(
            sum("total_cost_usd").alias("daily_cost_usd"),
            sum("total_tokens").alias("daily_tokens"),
            count("event_id").alias("daily_requests"),
            avg("latency_ms").alias("avg_latency_ms"),
            sum("prompt_tokens").alias("daily_prompt_tokens"),
            sum("completion_tokens").alias("daily_completion_tokens"),
            sum("total_cost_usd_micro").alias("daily_cost_usd_micro"),
        )
        .select(
            col("window.start").alias("day_start"),
            col("window.end").alias("day_end"),
            "*"
        )
        .drop("window")
    )

    return (
        agg.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/gold_daily_{ENV}")
        .partitionBy("event_year", "event_month", "organization_id")
        .trigger(processingTime="5 minutes")
        .toTable("gold.daily_cost_aggregates")
    )

gold_query = start_gold_daily_stream()
print(f"Gold stream started: {gold_query.id}")

# COMMAND ----------
# MAGIC %md ## 7. Delta Lake Optimization Jobs

# COMMAND ----------
def optimize_delta_tables():
    """Run OPTIMIZE and VACUUM on all Delta tables"""
    tables = [
        ("bronze.llm_events",           ["ingest_date", "provider"]),
        ("silver.llm_events_clean",      ["event_year", "event_month"]),
        ("gold.daily_cost_aggregates",   ["event_year", "event_month"]),
    ]
    for table, zorder_cols in tables:
        print(f"Optimizing {table}...")
        zorder_str = ", ".join(zorder_cols)
        spark.sql(f"OPTIMIZE {table} ZORDER BY ({zorder_str})")
        spark.sql(f"VACUUM {table} RETAIN 168 HOURS")
        print(f"✅ {table} optimized")

# Run if triggered manually
# optimize_delta_tables()

# COMMAND ----------
# MAGIC %md ## 8. Sample Gold Layer Query

# COMMAND ----------
display(
    spark.sql("""
        SELECT
            organization_id,
            provider_display AS provider,
            model,
            event_year,
            event_month,
            SUM(daily_cost_usd)      AS total_cost_usd,
            SUM(daily_tokens)        AS total_tokens,
            SUM(daily_requests)      AS total_requests,
            AVG(avg_latency_ms)      AS avg_latency_ms
        FROM gold.daily_cost_aggregates
        WHERE event_year = year(current_date())
          AND event_month = month(current_date())
        GROUP BY 1,2,3,4,5
        ORDER BY total_cost_usd DESC
        LIMIT 50
    """)
)
