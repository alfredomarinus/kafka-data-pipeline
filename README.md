# Real-Time Streaming Data Pipeline

A production-like streaming data pipeline with:

- Kafka for event streaming
- Spark Structured Streaming for processing
- PostgreSQL as sink
- Airflow (CeleryExecutor) for orchestration

## Stack

- Kafka + Zookeeper
- Spark Structured Streaming
- PostgreSQL
- Apache Airflow + CeleryExecutor + Redis + Flower

## How to Run

```bash
docker-compose up --build -d
