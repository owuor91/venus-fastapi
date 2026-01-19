#!/bin/bash
set -e

# Wait for database to be ready
# Use host.docker.internal to connect to host's PostgreSQL
echo "Waiting for database to be ready..."
DB_HOST=${DB_HOST:-host.docker.internal}
DB_USER=${DATABASE_USER:-owuor}
DB_NAME=${POSTGRES_DB:-venus_fastapi}

while ! pg_isready -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} > /dev/null 2>&1; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec "$@"
