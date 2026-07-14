"""SentinelAI application configuration.

Uses pydantic-settings to load from environment variables and .env files.
All configuration is centralized here — no magic strings elsewhere.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "SentinelAI"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # ── API Server ───────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ── Database ─────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/sentinelai.db"

    # ── ChromaDB ─────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma"

    # ── Google AI (Gemini) ───────────────────────────────────
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_fallback_model: str = "gemini-2.0-flash-lite"

    # ── JWT Authentication ───────────────────────────────────
    jwt_secret_key: str = "change-this-to-a-secure-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 480

    # ── Rate Limiting ────────────────────────────────────────
    rate_limit_per_minute: int = 60

    # ── Data Paths ───────────────────────────────────────────
    data_dir: str = "../challenge-3-kyc-autonomous-auditor/data"
    risk_policy_path: str = "./risk_policy.yaml"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: Any) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).resolve()


class RiskPolicy:
    """Runtime-reloadable risk policy loaded from YAML.

    Encapsulates all deterministic scoring parameters.
    The LLM never computes risk — it only explains scores
    computed using values from this policy.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload policy from disk. Called on startup and via admin endpoint."""
        with open(self._path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)

    @property
    def event_weights(self) -> dict[str, float]:
        return self._data["scoring"]["event_weights"]

    @property
    def severity_multipliers(self) -> dict[str, float]:
        return self._data["scoring"]["severity_multipliers"]

    @property
    def jurisdiction_tiers(self) -> dict[str, Any]:
        return self._data["scoring"]["jurisdiction_tiers"]

    @property
    def bands(self) -> dict[str, dict[str, int]]:
        return self._data["scoring"]["bands"]

    @property
    def velocity_config(self) -> dict[str, Any]:
        return self._data["scoring"]["velocity"]

    @property
    def decay_config(self) -> dict[str, Any]:
        return self._data["scoring"]["decay"]

    @property
    def resolution_confidence(self) -> dict[str, Any]:
        return self._data["alerts"]["resolution_confidence"]

    @property
    def fuzzy_threshold(self) -> int:
        return self._data["screening"]["fuzzy_threshold"]

    @property
    def max_candidates(self) -> int:
        return self._data["screening"]["max_candidates"]

    @property
    def ingestion_config(self) -> dict[str, Any]:
        return self._data["ingestion"]

    def get_jurisdiction_multiplier(self, country_code: str) -> float:
        """Get the risk multiplier for a given ISO country code."""
        code = country_code.upper()
        for tier_data in self.jurisdiction_tiers.values():
            if code in tier_data.get("countries", []):
                return tier_data["multiplier"]
        return self.jurisdiction_tiers.get("tier_3", {}).get("multiplier", 1.0)

    def get_risk_band(self, score: float) -> str:
        """Classify a numeric score into a risk band."""
        for band_name, bounds in self.bands.items():
            if bounds["min"] <= score <= bounds["max"]:
                return band_name
        return "critical" if score > 100 else "low"

    def compute_score_delta(
        self,
        event_type: str,
        severity: str,
        country_code: str = "",
    ) -> float:
        """Deterministic risk score delta computation.

        Formula: delta = event_weight × severity_multiplier × jurisdiction_multiplier
        This is the ONLY place risk math happens. Never in an LLM.
        """
        weight = self.event_weights.get(event_type, 0.3)
        sev_mult = self.severity_multipliers.get(severity, 1.0)
        jur_mult = self.get_jurisdiction_multiplier(country_code) if country_code else 1.0
        return round(weight * sev_mult * jur_mult * 100, 2)


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
