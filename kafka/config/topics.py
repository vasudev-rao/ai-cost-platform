"""Kafka topic configuration for AI Cost Intelligence Platform"""

TOPICS = {
    "llm_requests": {
        "partitions": 12,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(7 * 24 * 60 * 60 * 1000),  # 7 days
            "compression.type": "lz4",
            "cleanup.policy": "delete",
        },
    },
    "llm_costs": {
        "partitions": 12,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(30 * 24 * 60 * 60 * 1000),  # 30 days
            "compression.type": "lz4",
        },
    },
    "llm_errors": {
        "partitions": 6,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(14 * 24 * 60 * 60 * 1000),  # 14 days
        },
    },
    "llm_latency": {
        "partitions": 12,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(7 * 24 * 60 * 60 * 1000),
        },
    },
    "llm_forecasts": {
        "partitions": 3,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(90 * 24 * 60 * 60 * 1000),  # 90 days
        },
    },
    "llm_dlq": {
        "partitions": 3,
        "replication_factor": 3,
        "config": {
            "retention.ms": str(30 * 24 * 60 * 60 * 1000),
        },
    },
}

CONSUMER_GROUPS = {
    "cost-aggregator": ["llm_costs"],
    "anomaly-detector": ["llm_costs"],
    "alert-processor": ["llm_costs", "llm_errors"],
    "forecast-trigger": ["llm_costs"],
    "spark-ingestion": ["llm_requests", "llm_costs"],
}
