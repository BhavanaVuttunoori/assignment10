import os


class Settings:
    # Database connection (can be overridden via environment variables or .env)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fastapi_db"
    )

    # JWT / security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-to-a-secure-random-string")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # Postgres defaults (used by docker-compose and local dev). Can be overridden.
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "fastapi_db")


settings = Settings()