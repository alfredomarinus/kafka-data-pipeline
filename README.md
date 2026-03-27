# Kafka + Airflow Pipeline

A production-like data pipeline combining **Kafka** for event streaming with **Apache Airflow (CeleryExecutor)** for orchestration, including PostgreSQL as metadata and sink database.

## Architecture

| Service | Description |
|---------|-------------|
| **airflow-api-server** | Web UI and REST API (port `8080`) |
| **airflow-scheduler** | Schedules DAG runs |
| **airflow-dag-processor** | Parses DAG files |
| **airflow-worker** | Celery worker that executes tasks |
| **airflow-triggerer** | Handles deferrable operators |
| **flower** | Celery task monitoring dashboard (port `5555`) |
| **postgres** | Metadata and sink database (port `5432`) |
| **redis** | Celery message broker (port `6379`) |
| **kafka** | Distributed event streaming broker (ports `9092`, `29092`) |
| **kafka-ui** | Web-based Kafka cluster browser (port `8085`) |

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24.0
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.20
- At least **8 GB RAM** allocated to Docker

## Quick Start

```bash
# 1. Clone the repository and navigate to it
git clone <repo-url> && cd kafka-data-pipeline

# 2. Copy the example env file
cp .env.example .env

# 3. Generate required Airflow secret keys (required for security)
# Generate fernet key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" | xargs -I {} sed -i '' 's/AIRFLOW__CORE__FERNET_KEY=CHANGE_ME/AIRFLOW__CORE__FERNET_KEY={}/' .env

# 4. Build and start all services
make build && make up

# 5. Check the logs to ensure everything started properly
make logs
```

> **Note:** On first run, the `airflow-init` container will initialize the database and create directories. This may take 1-2 minutes. Wait for all services to show `healthy` status.

## Common Operations

```bash
make up              # Start all services
make down            # Stop all running services
make restart         # Restart all running services
make logs            # Follow all service logs (Ctrl+C to exit)
make reset           # Stop everything, remove volumes, and restart fresh
make status          # Show running containers
make shell           # Open a bash shell in the Airflow container
make build           # Rebuild images (after Dockerfile changes)
make clean           # Remove cache files and logs
```

## Project Structure

```
kafka-data-pipeline/
├── .env              # Environment variables (create from .env.example)
├── .env.example      # Environment variables template
├── docker-compose.yml
├── Makefile
├── README.md
├── config/
│   └── airflow.cfg   # Airflow configuration
├── dags/             # Airflow DAG definitions (workflows)
├── kafka/
│   ├── init-topics.sh     # Kafka topic initialization script
│   └── producer.py        # Sample Kafka producer
├── plugins/          # Custom Airflow plugins
└── logs/             # Container and application logs
```

## Service URLs

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **Airflow UI** | http://localhost:8080 | `airflow` / `airflow` |
| **Kafka UI** | http://localhost:8085 | — |
| **Flower (Celery)** | http://localhost:5555 | — |
| **PostgreSQL** | `localhost:5432` | user: `airflow` / `airflow` |

## Workflow

1. **Events** → Kafka producers send data to Kafka topics
2. **Airflow** → DAGs orchestrate data processing workflows
3. **Processing** → Airflow tasks can consume Kafka messages, process data
4. **Output** → Results stored in PostgreSQL or other sinks

## Working with Airflow

### Creating a DAG

Add a new Python file to the `dags/` directory:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def kafka_consumer_task():
    # Consume from Kafka and process
    pass

dag = DAG(
    'kafka_data_pipeline',
    default_args={'retries': 2, 'retry_delay': timedelta(minutes=5)},
    description='Process Kafka events',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

task = PythonOperator(
    task_id='process_kafka_events',
    python_callable=kafka_consumer_task,
    dag=dag,
)
```

DAGs are automatically discovered within 1-2 minutes.

### Accessing Logs

```bash
# View logs for a specific service
docker compose logs airflow-scheduler -f
docker compose logs airflow-worker -f

# View all logs
make logs
```

## Troubleshooting

**Services not starting?**
- Check `.env` file is created and all `CHANGE_ME` values are set
- Run `make reset` to perform a clean restart
- Check `docker compose logs` for detailed error messages

**Out of memory?**
- The `airflow-init` container requires 4GB+ RAM
- Reduce resource limits for development, or allocate more Docker resources

**DAGs not appearing?**
- Check `dags/` folder for Python files
- Verify DAGs have valid Python syntax: `python -m py_compile dags/your_dag.py`
- Wait 1-2 minutes for scheduler to pick up changes

**Permission denied errors?**
- The `AIRFLOW_UID` environment variable should match your user ID
- Run `id -u` and update `.env` if needed |
