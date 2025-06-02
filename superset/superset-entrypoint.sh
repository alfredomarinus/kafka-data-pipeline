#!/bin/bash
set -e

# Run DB migrations
superset db upgrade

# Create admin user (idempotent)
superset fab create-admin \
    --username "admin" \
    --firstname Superset \
    --lastname Admin \
    --email "admin@example.com" \
    --password "admin" || true

# Initialize Superset
superset init