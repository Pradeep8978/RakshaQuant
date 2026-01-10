"""
Application settings and configuration management.

Uses pydantic-settings for environment variable loading with validation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===========================================
    # LLM Provider - Groq
    # ===========================================
    groq_api_key: SecretStr = Field(..., description="Groq API key for LLM access")
    groq_model_primary: str = Field(
        default="llama-3.3-70b-versatile",
        description="Primary Groq model for agent reasoning",
    )
    groq_model_fallback: str = Field(
        default="llama-3.1-8b-instant",
        description="Fallback Groq model for rate limit scenarios",
    )
    groq_temperature: float = Field(
        default=0.1,
        description="Temperature for LLM responses (low for consistency)",
    )
    groq_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens per LLM response",
    )

    # ===========================================
    # Broker API - DhanHQ
    # ===========================================
    dhan_client_id: str = Field(..., description="DhanHQ client ID")
    dhan_access_token: SecretStr = Field(..., description="DhanHQ access token")
    dhan_base_url: str = Field(
        default="https://api.dhan.co/v2",
        description="DhanHQ API base URL (use sandbox.dhan.co for testing)",
    )

    # ===========================================
    # Observability - LangSmith
    # ===========================================
    langsmith_api_key: SecretStr = Field(..., description="LangSmith API key")
    langsmith_project: str = Field(
        default="trading-agent",
        description="LangSmith project name for tracing",
    )
    langsmith_tracing_v2: bool = Field(
        default=True,
        description="Enable LangSmith tracing v2",
    )

    # ===========================================
    # Database - PostgreSQL
    # ===========================================
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/trading_agent",
        description="PostgreSQL connection URL",
    )

    # ===========================================
    # Optional: Redis (not required for basic functionality)
    # ===========================================
    redis_url: str | None = Field(
        default=None,
        description="Optional Redis URL for market data caching",
    )

    # ===========================================
    # Trading Configuration
    # ===========================================
    trading_mode: Literal["paper", "live"] = Field(
        default="paper",
        description="Trading mode - paper for simulation, live for real trading",
    )
    max_daily_trades: int = Field(
        default=50,
        description="Maximum number of trades allowed per day",
    )
    max_position_size: float = Field(
        default=100000.0,
        description="Maximum position size in INR",
    )
    daily_loss_limit: float = Field(
        default=10000.0,
        description="Maximum daily loss limit in INR (kill switch trigger)",
    )

    # ===========================================
    # Agent Memory Configuration
    # ===========================================
    memory_top_n_lessons: int = Field(
        default=5,
        description="Number of top lessons to inject into agent context",
    )
    memory_decay_days: int = Field(
        default=30,
        description="Days after which lesson relevance starts decaying",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
