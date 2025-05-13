#!/bin/bash

echo "Waiting for Kafka broker to be available at kafka:9092..."

# Retry loop
RETRIES=20
until kafka-topics --bootstrap-server kafka:9092 --list >/dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "Kafka is not ready yet... waiting..."
  sleep 5
  RETRIES=$((RETRIES-1))
done

if [ $RETRIES -eq 0 ]; then
  echo "Kafka did not become ready in time. Exiting."
  exit 1
fi

echo "Kafka is ready. Creating topic..."

kafka-topics --create --if-not-exists \
  --topic my_stream_topic \
  --bootstrap-server kafka:9092 \
  --replication-factor 1 \
  --partitions 1

echo "Topic creation done."