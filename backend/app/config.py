"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = "AeroOps AI"
    app_version: str = "0.1.0-day1"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./aeroops.db")
    frontend_origins_raw: str = os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173"
    )

    @property
    def frontend_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_origins_raw.split(",")
            if origin.strip()
        ]


settings = Settings()

