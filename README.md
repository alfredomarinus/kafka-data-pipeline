# Real-Time Streaming Data Pipeline

A production-like streaming data pipeline with:

- Kafka for event streaming
- Spark Structured Streaming for processing
- PostgreSQL as sink
- Airflow (CeleryExecutor) for orchestration
- Superset for dashboards

## Stack

- Kafka + Zookeeper
- Spark Structured Streaming
- PostgreSQL
- Apache Airflow + CeleryExecutor + Redis + Flower
- Apache Superset

## How to Run

```bash
docker-compose build --no-cache
docker-compose up --d
