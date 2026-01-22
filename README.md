### Note: sync migrations, async runtime

We intentionally use two different DB engines:

- **Migrations (sync)**: Alembic runs with a synchronous SQLAlchemy engine. This is configured in `alembic.ini`:

```ini
sqlalchemy.url = sqlite:///./app.db
```

- **Application (async)**: FastAPI uses the async SQLAlchemy engine for non-blocking I/O during requests, configured in `app/database.py`:

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
```

This separation is best practice: migrations run synchronously and predictably, while the app benefits from async performance at runtime.

### Run the app

Use the following command:

```bash
uv run hypercorn main:app --reload
```

### Database migrations

Create a new migration file by hand:

```bash
uv run alembic revision -m "create users table"
```

Apply all pending migrations:

```bash
uv run alembic upgrade head
```

Reset the whole DB with a fresh migration (alternative to Laravel's `php artisan migrate:fresh`):

```bash
uv run alembic downgrade base
uv run alembic upgrade head
```

### View the SQLite database (sqlite-web)

Launch a lightweight web UI to browse the local SQLite file:

```bash
uv run sqlite_web app.db
```
