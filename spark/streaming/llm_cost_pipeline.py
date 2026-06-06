"""
Spark Structured Streaming Pipeline — Medallion Architecture
Bronze → Silver → Gold

Ingests LLM cost events from Kafka and processes into Delta Lake layers.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, to_timestamp, year, month, dayofmonth,
    sum as _sum, count, avg, window, current_timestamp,
    when, lit, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, LongType, BooleanType
)
import logging

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
DELTA_BASE_PATH = "s3://ai-cost-platform-data/delta"
CHECKPOINT_BASE = "s3://ai-cost-platform-data/checkpoints"


def create_spark_session(app_name: str = "AIcostPlatform") -> SparkSession:
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.optimizeWrite.enabled", "true")
        .config("spark.databricks.delta.autoCompact.enabled", "true")
        .config("spark.sql.streaming.stateStore.providerClass",
                "org.apache.spark.sql.execution.streaming.state.RocksDBStateStoreProvider")
        .getOrCreate()
    )


# ── SCHEMA ────────────────────────────────────────────────────────
LLM_COST_SCHEMA = StructType([
    StructField("event_id", StringType(), True),
    StructField("organization_id", StringType(), False),
    StructField("team_id", StringType(), True),
    StructField("project_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("provider", StringType(), False),
    StructField("model", StringType(), False),
    StructField("prompt_tokens", IntegerType(), True),
    StructField("completion_tokens", IntegerType(), True),
    StructField("total_tokens", IntegerType(), True),
    StructField("prompt_cost_usd_micro", LongType(), True),
    StructField("completion_cost_usd_micro", LongType(), True),
    StructField("total_cost_usd_micro", LongType(), True),
    StructField("latency_ms", IntegerType(), True),
    StructField("status", StringType(), True),
    StructField("environment", StringType(), True),
    StructField("request_id", StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("timestamp", StringType(), False),
])


def bronze_layer(spark: SparkSession):
    """
    BRONZE: Raw events from Kafka — no transformation, just persistence.
    Append-only, partition by ingestion date.
    """
    df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", "llm_costs,llm_requests")
        .option("startingOffsets", "latest")
        .option("maxOffsetsPerTrigger", 100000)
        .option("kafka.security.protocol", "PLAINTEXT")
        .load()
    )

    parsed = df.select(
        col("topic"),
        col("partition"),
        col("offset"),
        col("timestamp").alias("kafka_timestamp"),
        from_json(col("value").cast("string"), LLM_COST_SCHEMA).alias("data"),
    ).select("topic", "partition", "offset", "kafka_timestamp", "data.*")

    # Add ingestion metadata
    enriched = parsed.withColumn("ingest_date", col("kafka_timestamp").cast("date"))

    query = (
        enriched.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/bronze")
        .option("mergeSchema", "true")
        .partitionBy("ingest_date", "provider")
        .trigger(processingTime="30 seconds")
        .start(f"{DELTA_BASE_PATH}/bronze/llm_events")
    )
    return query


def silver_layer(spark: SparkSession):
    """
    SILVER: Cleaned, validated, deduplicated events.
    Enriched with computed cost in USD, filtered bad records.
    """
    df = (
        spark.readStream
        .format("delta")
        .option("readChangeFeed", "true")
        .option("startingVersion", "latest")
        .load(f"{DELTA_BASE_PATH}/bronze/llm_events")
    )

    cleaned = (
        df
        .where(col("event_id").isNotNull())
        .where(col("organization_id").isNotNull())
        .where(col("model").isNotNull())
        .where(col("status") == "success")
        .withColumn("event_ts", to_timestamp(col("timestamp")))
        .withColumn("event_year", year("event_ts"))
        .withColumn("event_month", month("event_ts"))
        .withColumn("event_day", dayofmonth("event_ts"))
        .withColumn(
            "total_cost_usd",
            (col("total_cost_usd_micro") / lit(1_000_000)).cast("double")
        )
        .withColumn(
            "provider_normalized",
            when(col("provider") == "openai", "OpenAI")
            .when(col("provider") == "anthropic", "Anthropic")
            .when(col("provider") == "gemini", "Google Gemini")
            .when(col("provider") == "bedrock", "AWS Bedrock")
            .otherwise(col("provider"))
        )
        .dropDuplicates(["event_id"])
    )

    query = (
        cleaned.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/silver")
        .partitionBy("event_year", "event_month", "provider")
        .trigger(processingTime="60 seconds")
        .start(f"{DELTA_BASE_PATH}/silver/llm_events_clean")
    )
    return query


def gold_layer_daily_aggregates(spark: SparkSession):
    """
    GOLD: Business-ready daily aggregates per org/team/model.
    Used directly by API for dashboard queries.
    """
    df = (
        spark.readStream
        .format("delta")
        .option("readChangeFeed", "true")
        .load(f"{DELTA_BASE_PATH}/silver/llm_events_clean")
    )

    aggregated = (
        df
        .withWatermark("event_ts", "1 hour")
        .groupBy(
            window("event_ts", "1 day"),
            "organization_id",
            "team_id",
            "project_id",
            "model",
            "provider",
            "event_year",
            "event_month",
            "event_day",
        )
        .agg(
            _sum("total_cost_usd").alias("daily_cost_usd"),
            _sum("total_tokens").alias("daily_tokens"),
            count("event_id").alias("daily_requests"),
            avg("latency_ms").alias("avg_latency_ms"),
            _sum("prompt_tokens").alias("daily_prompt_tokens"),
            _sum("completion_tokens").alias("daily_completion_tokens"),
        )
        .select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            "*"
        )
        .drop("window")
    )

    query = (
        aggregated.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", f"{CHECKPOINT_BASE}/gold_daily")
        .partitionBy("event_year", "event_month", "organization_id")
        .trigger(processingTime="5 minutes")
        .start(f"{DELTA_BASE_PATH}/gold/daily_cost_aggregates")
    )
    return query


def run_pipeline():
    spark = create_spark_session()
    logger.info("Starting Medallion Architecture Pipeline")

    q1 = bronze_layer(spark)
    q2 = silver_layer(spark)
    q3 = gold_layer_daily_aggregates(spark)

    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    run_pipeline()
