# Bill Digitizer API

A FastAPI service for digitizing bills and receipts using Google's Gemini AI.

## Project Structure

```
backend/
├── alembic/                  # Alembic migration scripts and environment
├── alembic.ini               # Alembic configuration
├── app/                      # Main application code
│   ├── api/                  # API routers and endpoints
│   ├── core/                 # Core components (e.g., config)
│   ├── crud/                 # CRUD operations for database interaction
│   ├── db/                   # Database models, session management, base class
│   ├── schemas/              # Pydantic schemas (API data shapes)
│   ├── services/             # Business logic (e.g., BillAnalyzer)
│   └── main.py               # FastAPI application entry point
├── Dockerfile                # Docker configuration for the backend
├── poetry.lock
├── pyproject.toml            # Poetry dependency management
├── prestart.sh               # Script to run before app start (e.g., migrations)
├── README.md                 # This file
└── .env.example              # Example environment variables
```

(Note: `docker-compose.yml` is at the project root, outside the `backend` directory)

## Local Setup (Without Docker - for IDE integration & local Alembic commands)

1.  **Navigate to the backend directory:**

    ```bash
    cd backend
    ```

2.  **Install Poetry (if not already installed):**

    ```bash
    curl -sSL https://install.python-poetry.org | python3 -
    # Or: pip install poetry
    ```

3.  **Install dependencies:**

    ```bash
    poetry install
    ```

4.  **Set up Environment Variables:**
    Copy `backend/.env.example` to `backend/.env` and fill in your details:

    ```bash
    cp .env.example .env
    ```

    -   Add your `GEMINI_API_KEY`.
    -   For local development **without Docker and a locally running PostgreSQL instance**, set `POSTGRES_SERVER=localhost` and ensure your local PostgreSQL matches other `POSTGRES_*` variables.

5.  **Activate the virtual environment (optional, if your IDE doesn't do it automatically):**
    ```bash
    poetry shell
    ```

## Database Migrations (Alembic)

This project uses Alembic to manage database schema changes.

### Initial Migration (Manual Step Required First Time)

Due to potential issues running `alembic init` through automated tools, some manual setup for Alembic was performed. The initial migration script template was generated at:
`backend/alembic/versions/xxxxxxxxxxxx_create_initial_bill_tables.py`

**You MUST:**

1.  **Rename this file**: Replace `xxxxxxxxxxxx` with a unique revision ID (e.g., 12 characters like `0a1b2c3d4e5f`. You can generate one with `python -c "import uuid; print(uuid.uuid4().hex[:12])"`).
2.  **Edit the renamed file**:
    -   Update the `revision: str = 'xxxxxxxxxxxx'` line to use your new unique ID.
    -   Update the `Create Date:` in the docstring at the top of the file.

### Generating New Migrations (Locally)

After making changes to your SQLAlchemy models in `backend/app/db/models/`, you can generate a new migration script (ensure you have a local DB running or correct `DATABASE_URL` in `.env` for Alembic to connect and compare):

```bash
# Ensure you are in the backend/ directory and your .env is configured for local DB access
poetry run alembic revision -m "short_description_of_changes" --autogenerate
```

Review the generated script in `backend/alembic/versions/` before applying.

### Applying Migrations

-   **With Docker Compose (Recommended for Development & Production):** Migrations are applied automatically when the `backend` container starts, thanks to the `prestart.sh` script.
-   **Locally:** To apply migrations to your local database:
    ```bash
    # Ensure you are in the backend/ directory
    poetry run alembic upgrade head
    ```

## Running the Service with Docker Compose (Recommended)

This is the preferred way to run the application for development and production-like environments.

1.  **Ensure Docker and Docker Compose are installed.**

2.  **Set up Environment Variables for Docker:**

    -   Make sure you have `backend/.env` created from `backend/.env.example`.
    -   **Crucially, in `backend/.env`, set `POSTGRES_SERVER=db`**. This tells the backend app (running in Docker) to connect to the PostgreSQL container named `db`.
    -   Fill in your `GEMINI_API_KEY`.
    -   The `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` in `.env` will be used to initialize the PostgreSQL container.

3.  **Build and Run the Services:**
    From the **project root directory** (where `docker-compose.yml` is located):

    ```bash
    docker-compose up --build
    ```

    -   `--build` forces a rebuild of the images if anything in `backend/Dockerfile` or the source code it copies has changed.
    -   To run in detached mode: `docker-compose up --build -d`

4.  **The API will be available at `http://localhost:8000`**

    -   Swagger UI (API Docs): `http://localhost:8000/docs`
    -   ReDoc: `http://localhost:8000/redoc`

5.  **To stop the services:**
    ```bash
    docker-compose down
    ```
    To stop and remove volumes (like the database data, use with caution):
    ```bash
    docker-compose down -v
    ```

## API Endpoints

### POST /api/v1/analyze

Analyze a bill/receipt image, extract structured data, and save it to the database.

**Request:**

-   `file`: Image file (multipart/form-data)
-   `downsize`: Boolean (optional, default: `false`) - Whether to downsize the image before processing

**Response (Example):**

```json
{
    "document_type": "Receipt",
    "merchant_company_name": "ABC Store",
    "address": "123 Main St",
    "phone_number": "555-0123",
    "date": "2024-02-14",
    "time": "02:30 PM",
    "transaction_id": "12345",
    "subtotal": 4.99,
    "tax": 0.5,
    "discount_savings": 0.0,
    "total_amount": 5.49,
    "payment_method": "Credit Card",
    "card_last_four": "1234",
    "approval_code": "ABC123",
    "currency": "USD",
    "other_info": null,
    "id": 1, // Database ID
    "items_services_purchased": [
        {
            "description": "Coffee",
            "quantity": 1,
            "unit_price": 4.99,
            "total_price_per_item": 4.99,
            "id": 1, // Database ID
            "bill_id": 1 // Database ID
        }
    ]
}
```

### GET /api/v1/bills

Retrieve a list of processed bills.

**Query Parameters:**

-   `skip`: int (default: 0)
-   `limit`: int (default: 100)

### GET /api/v1/bills/{bill_id}

Retrieve a specific bill by its ID.

## Development (Inside Docker)

With the Docker Compose setup using volumes (`./backend:/app`), changes you make to your backend code will be reflected live in the running container (Uvicorn's `--reload` will restart the server).

### Running Tests (To be configured)

```bash
# Example: To run pytest inside the backend container
# docker-compose exec backend poetry run pytest
```

### Code Formatting & Linting (Locally)

```bash
# In backend/ directory
poetry run black .
poetry run isort .
poetry run flake8
```
