"""Core configuration settings.

Centralized configuration using Pydantic Settings for environment
variable management with sensible defaults.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Azure Governance Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    database_url: str = "sqlite:///./data/governance.db"

    # Azure Authentication
    azure_tenant_id: Optional[str] = None
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None

    # Key Vault (for multi-tenant credentials)
    key_vault_url: Optional[str] = None

    # Multi-tenant configuration
    # Comma-separated list of tenant IDs to manage
    managed_tenant_ids: List[str] = Field(default_factory=list)

    # Sync Configuration
    cost_sync_interval_hours: int = 24
    compliance_sync_interval_hours: int = 4
    resource_sync_interval_hours: int = 1
    identity_sync_interval_hours: int = 24

    # Alerting
    teams_webhook_url: Optional[str] = None
    cost_anomaly_threshold_percent: float = 20.0
    compliance_alert_threshold_percent: float = 5.0

    # CORS (for development)
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @property
    def is_configured(self) -> bool:
        """Check if minimum Azure configuration is present."""
        return all([
            self.azure_tenant_id,
            self.azure_client_id,
            self.azure_client_secret,
        ])


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
