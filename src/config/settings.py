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
    # Broker API - DhanHQ (Optional for free tier)
    # ===========================================
    dhan_client_id: str | None = Field(
        default=None,
        description="DhanHQ client ID (optional for local paper trading)",
    )
    dhan_access_token: SecretStr | None = Field(
        default=None,
        description="DhanHQ access token (optional for local paper trading)",
    )
    dhan_base_url: str = Field(
        default="https://api.dhan.co/v2",
        description="DhanHQ API base URL (use https://api.dhan.co/v2 for live)",
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

    # ===========================================
    # Free Tier Configuration
    # ===========================================
    market_data_source: Literal["yfinance", "dhan"] = Field(
        default="yfinance",
        description="Market data source: yfinance (free) or dhan (requires account)",
    )
    execution_mode: Literal["local_paper", "dhan_paper", "live"] = Field(
        default="local_paper",
        description="Execution mode: local_paper (free), dhan_paper (sandbox), or live",
    )
    enable_news_analysis: bool = Field(
        default=True,
        description="Enable AI-powered news sentiment analysis",
    )
    paper_wallet_balance: float = Field(
        default=1000000.0,
        description="Starting balance for local paper trading (INR)",
    )

    # ===========================================
    # Telegram Notifications
    # ===========================================
    telegram_bot_token: str | None = Field(
        default=None,
        description="Telegram bot token from @BotFather",
    )
    telegram_chat_id: str | None = Field(
        default=None,
        description="Your Telegram chat ID from @userinfobot",
    )
    telegram_enabled: bool = Field(
        default=True,
        description="Enable Telegram notifications",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
