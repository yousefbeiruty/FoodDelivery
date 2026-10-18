# FreshBite API

Modular FastAPI backend for restaurant discovery, menu browsing, JWT authentication, checkout, order history, and live order tracking.

## Local setup

Requires Python 3.10 or later. The project-local `.venv` in this checkout was created with Python 3.9, which is too old for the type syntax used by the API. Recreate it with a supported Python version before launching the server.

```bash
deactivate 2>/dev/null || true
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Set a unique `SECRET_KEY` in `.env`. The default database is a local SQLite file (`freshbite.db`); for PostgreSQL set, for example, `DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/freshbite`.

Start the development server:

```bash
python -m uvicorn main:app --reload
```

Using `python -m uvicorn` ensures Uvicorn runs under the active virtual environment's Python interpreter.

Swagger UI: <http://127.0.0.1:8000/docs>  
ReDoc: <http://127.0.0.1:8000/redoc>

## Run with Docker

Install Docker Desktop or Docker Engine with the Compose plugin. Create a local `.env` file and set a strong `SECRET_KEY` (the file is excluded from the image):

```bash
cp .env.example .env
```

Then start the API:

```bash
docker compose up --build -d
```

The API is available at <http://localhost:8000>; Swagger UI is at <http://localhost:8000/docs>. SQLite data is stored in the persistent `freshbite_data` Docker volume. To add the sample restaurants and menu items, run:

```bash
docker compose exec api python -m app.seed
```

Stop the service with `docker compose down`. The named database volume remains in place; remove it with `docker compose down --volumes` only when you intend to delete the stored data.

## API outline

- `POST /api/auth/register` creates a user.
- `POST /api/auth/token` accepts OAuth2 form fields `username` (email) and `password` and returns a JWT.
- Send `Authorization: Bearer <token>` to protected routes.
- `GET /api/restaurants?search=...&category=...` browses restaurants; `GET /api/restaurants/{id}` returns menu details.
- `POST /api/orders/quote` calculates a price. `FRESH10` applies a 10% subtotal discount.
- `POST /api/orders/` places an order. Order item prices and totals are recalculated server-side; items must belong to one restaurant.
- `GET /api/orders/` and `GET /api/orders/{id}` return the signed-in user's orders.
- `PATCH /api/orders/{id}/status` simulates a driver/admin update for an order owned by the signed-in user.
- `WS /api/orders/{id}/ws?token=<JWT>` streams the current order state and later updates. Connect using a secure WebSocket (`wss://`) when deployed.

## Sample restaurant data

Run `python -m app.seed` once to add 50 recognizable restaurant brands with four illustrative menu items each (200 items total). The menus, ratings, and JOD-like sample prices are demo content, not current official brand menus or prices. The seed command is safe to rerun and only adds missing records. It also creates original, locally served SVG category illustrations at `/static/menu/`; these are generic food illustrations, not restaurant product photos or logos.

The status simulation endpoint currently uses customer authentication and ownership as its access rule. Add staff roles/authorization before exposing driver or admin operations in a multi-user production deployment. For schema changes in production, use migrations (for example Alembic) and set `AUTO_CREATE_TABLES=false`.

## Run tests

Install development dependencies and run the API suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Tests use a fresh in-memory SQLite database per test and do not modify `freshbite.db`.
