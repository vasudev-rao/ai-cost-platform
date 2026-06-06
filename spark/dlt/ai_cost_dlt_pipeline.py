"""
Delta Live Tables Pipeline Definition
Declarative version of the Bronze → Silver → Gold pipeline
Deploy via Databricks DLT UI or API
"""
import dlt
from pyspark.sql.functions import *
from pyspark.sql.types import *

KAFKA_SERVERS = spark.conf.get("pipelines.kafka_servers", "kafka:9092")

LLM_SCHEMA = StructType([
    StructField("event_id",              StringType(), False),
    StructField("organization_id",       StringType(), False),
    StructField("team_id",               StringType(), True),
    StructField("provider",              StringType(), False),
    StructField("model",                 StringType(), False),
    StructField("prompt_tokens",         IntegerType(), True),
    StructField("completion_tokens",     IntegerType(), True),
    StructField("total_cost_usd_micro",  LongType(), True),
    StructField("latency_ms",            IntegerType(), True),
    StructField("status",                StringType(), True),
    StructField("timestamp",             StringType(), False),
])


@dlt.table(
    name="bronze_llm_events",
    comment="Raw LLM events from Kafka — no transformations",
    table_properties={
        "quality": "bronze",
        "delta.autoOptimize.optimizeWrite": "true",
    },
    partition_cols=["ingest_date", "provider"],
)
def bronze_llm_events():
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_SERVERS)
        .option("subscribe", "llm_costs")
        .option("startingOffsets", "latest")
        .load()
        .select(
            col("timestamp").alias("kafka_ts"),
            from_json(col("value").cast("string"), LLM_SCHEMA).alias("d"),
        )
        .select("kafka_ts", "d.*")
        .withColumn("ingest_date", col("kafka_ts").cast("date"))
    )


@dlt.table(
    name="silver_llm_events",
    comment="Cleaned, validated, deduplicated LLM events with cost in USD",
    table_properties={
        "quality": "silver",
        "delta.enableChangeDataFeed": "true",
    },
    partition_cols=["event_year", "event_month", "provider"],
)
@dlt.expect_all({
    "valid_event_id": "event_id IS NOT NULL",
    "valid_org": "organization_id IS NOT NULL",
    "valid_model": "model IS NOT NULL",
    "positive_tokens": "total_cost_usd_micro >= 0",
})
def silver_llm_events():
    return (
        dlt.read_stream("bronze_llm_events")
        .where(col("status") == "success")
        .withColumn("event_ts", to_timestamp("timestamp"))
        .withColumn("event_year", year("event_ts"))
        .withColumn("event_month", month("event_ts"))
        .withColumn("event_day", dayofmonth("event_ts"))
        .withColumn("total_cost_usd", (col("total_cost_usd_micro") / lit(1_000_000)).cast("double"))
        .dropDuplicates(["event_id"])
    )


@dlt.table(
    name="gold_daily_cost_aggregates",
    comment="Daily cost aggregates by org/team/model — used by API dashboards",
    table_properties={
        "quality": "gold",
        "delta.autoOptimize.autoCompact": "true",
    },
    partition_cols=["event_year", "event_month", "organization_id"],
)
def gold_daily_cost_aggregates():
    return (
        dlt.read_stream("silver_llm_events")
        .withWatermark("event_ts", "2 hours")
        .groupBy(
            window("event_ts", "1 day"),
            "organization_id", "team_id",
            "model", "provider",
            "event_year", "event_month", "event_day",
        )
        .agg(
            sum("total_cost_usd").alias("daily_cost_usd"),
            sum("total_tokens").alias("daily_tokens"),
            count("event_id").alias("daily_requests"),
            avg("latency_ms").alias("avg_latency_ms"),
        )
    )
