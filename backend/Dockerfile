# backend/Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.9-slim as builder

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install system dependencies required by some Python packages (if any)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev

# 4. Install Poetry
RUN pip install poetry==1.7.1 # Pinning poetry version for consistency

# 5. Set the working directory in the container
WORKDIR /app

# 6. Copy only poetry.lock and pyproject.toml to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# 7. Install project dependencies using Poetry
# --no-root: Do not install the project itself as editable, install dependencies only
# --no-dev: Skip development dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-dev --compile

# Create a new stage for the final image from a clean base
FROM python:3.9-slim

WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the prestart script and make it executable
COPY ./prestart.sh /app/prestart.sh
RUN chmod +x /app/prestart.sh

# Copy the application code
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./alembic.ini /app/alembic.ini

# Expose port 8000 to the outside world
EXPOSE 8000

# Command to run when the container launches
# The prestart.sh script will run migrations
# Then uvicorn will start the FastAPI application
# Using CMD to allow overriding from docker-compose
CMD ["sh", "-c", "/app/prestart.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"] 