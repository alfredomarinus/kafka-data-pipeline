#!/bin/bash

echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U "$POSTGRES_USER"; do
  sleep 2;
done

echo "Initializing Airflow DB..."
airflow db migrate

echo "Creating Airflow user..."
airflow users create \
  --username admin \
  --password admin \
  --firstname Airflow \
  --lastname Admin \
  --role Admin \
  --email admin@example.com || true

echo "Starting webserver..."
exec airflow webserver