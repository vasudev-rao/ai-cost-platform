#!/bin/bash
# Create Kafka topics for AI Cost Intelligence Platform
BOOTSTRAP="localhost:9092"

topics=(
  "llm_requests:12:1:7"
  "llm_costs:12:1:30"
  "llm_errors:6:1:14"
  "llm_latency:12:1:7"
  "llm_forecasts:3:1:90"
  "llm_dlq:3:1:30"
)

for topic_config in "${topics[@]}"; do
  IFS=':' read -r topic partitions replication retention <<< "$topic_config"
  retention_ms=$((retention * 24 * 3600 * 1000))
  echo "Creating topic: $topic (partitions=$partitions, replication=$replication, retention=${retention}d)"
  kafka-topics.sh --create \
    --bootstrap-server "$BOOTSTRAP" \
    --topic "$topic" \
    --partitions "$partitions" \
    --replication-factor "$replication" \
    --config "retention.ms=$retention_ms" \
    --config "compression.type=lz4" \
    --if-not-exists
  echo "✅ $topic created"
done

echo "All topics created. Listing:"
kafka-topics.sh --list --bootstrap-server "$BOOTSTRAP"
