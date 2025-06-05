#!/usr/bin/env bash

echo "--- Running prestart.sh ---"

echo "--- Database Environment Variables ---"
echo "POSTGRES_SERVER: ${POSTGRES_SERVER}"
echo "POSTGRES_USER: ${POSTGRES_USER}"
echo "POSTGRES_PASSWORD: <hidden>" # Avoid printing password
echo "POSTGRES_DB: ${POSTGRES_DB}"
echo "POSTGRES_PORT: ${POSTGRES_PORT}"
echo "DATABASE_URL (from env, if set): ${DATABASE_URL}"
echo "------------------------------------"

# Run Alembic migrations
echo "Attempting to apply Alembic migrations..."

if command -v alembic &> /dev/null
then
    echo "Using 'alembic upgrade head'..."
    alembic upgrade head
else
    echo "'alembic' command not found, attempting 'python -m alembic upgrade head'..."
    python -m alembic upgrade head
fi

if [ $? -eq 0 ]; then
  echo "Alembic migrations applied successfully (or no new migrations)."
else
  echo "!!! Alembic migrations FAILED. Check logs. !!!"
  # Optionally, exit here if migrations are critical for startup
  # exit 1 
fi

echo "--- prestart.sh finished ---" 