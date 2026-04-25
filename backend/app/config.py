from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_DATABASE = f"sqlite:///{(_BACKEND_DIR / 'algotrade.db').as_posix()}"


class Settings(BaseSettings):
    APP_NAME: str = "AlgoTrade Sentinel"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = _DEFAULT_DATABASE
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    SECRET_KEY: str = "change-me-in-production"

    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_STATUS_TIMEOUT_SECONDS: float = 3.0
    PREFECT_API_URL: str = "http://localhost:4200/api"

    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_APSCHEDULER: bool | None = None
    RATE_LIMIT_DEFAULT: str = "120/minute"
    LOG_LEVEL: str = "INFO"

    INGEST_CRON: str = "15 22 * * 1-5"
    FEATURE_CRON: str = "30 22 * * 1-5"
    INFERENCE_CRON: str = "45 22 * * 1-5"
    MONITORING_CRON: str = "0 23 * * 1-5"

    model_config = {"env_file": str(_BACKEND_DIR / ".env"), "case_sensitive": True}

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def normalize_environment(cls, value: Any) -> str:
        if not isinstance(value, str):
            return "development"
        normalized = value.strip().lower()
        aliases = {
            "dev": "development",
            "development": "development",
            "local": "development",
            "staging": "staging",
            "stage": "staging",
            "prod": "production",
            "production": "production",
            "release": "production",
        }
        return aliases.get(normalized, normalized)

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return bool(value)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: Any) -> str:
        if isinstance(value, str) and value.startswith("sqlite:///./"):
            rel = value[len("sqlite:///./"):]
            return f"sqlite:///{(_BACKEND_DIR / rel).as_posix()}"
        return str(value)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("[") and raw.endswith("]"):
                import json

                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in raw.split(",") if item.strip()]
        return []

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, value: Any) -> str:
        return str(value).upper().strip() if value is not None else "INFO"

    @field_validator("ENABLE_REQUEST_LOGGING", mode="before")
    @classmethod
    def parse_request_logging(cls, value: Any) -> bool:
        if value is None:
            return True
        return cls.parse_debug(value)

    @field_validator("ENABLE_APSCHEDULER", mode="before")
    @classmethod
    def parse_optional_bool(cls, value: Any) -> bool | None:
        if value is None or value == "":
            return None
        return cls.parse_debug(value)

    @model_validator(mode="after")
    def finalize(self) -> "Settings":
        if not self.CORS_ORIGINS:
            self.CORS_ORIGINS = [self.FRONTEND_URL]

        if self.ENVIRONMENT == "production":
            if self.FRONTEND_URL.startswith("http://localhost") or self.FRONTEND_URL.startswith("http://127.0.0.1"):
                raise ValueError("FRONTEND_URL must be set to the production frontend domain")
            if self.SECRET_KEY == "change-me-in-production":
                raise ValueError("SECRET_KEY must be set for production")
            if self.DATABASE_URL == _DEFAULT_DATABASE:
                raise ValueError("DATABASE_URL must be set for production")

            self.CORS_ORIGINS = [origin for origin in self.CORS_ORIGINS if origin]
            if self.FRONTEND_URL not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(self.FRONTEND_URL)

        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def apscheduler_enabled(self) -> bool:
        if self.ENABLE_APSCHEDULER is not None:
            return self.ENABLE_APSCHEDULER
        return not self.DEBUG and self.ENVIRONMENT != "development"


settings = Settings()
