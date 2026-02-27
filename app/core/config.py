"""Core configuration settings.

Centralized configuration using Pydantic Settings for environment
variable management with sensible defaults.
"""

from functools import lru_cache

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
    azure_tenant_id: str | None = None
    azure_client_id: str | None = None
    azure_client_secret: str | None = None

    # Key Vault (for multi-tenant credentials)
    key_vault_url: str | None = None

    # Multi-tenant configuration
    # Comma-separated list of tenant IDs to manage
    managed_tenant_ids: list[str] = Field(default_factory=list)

    # Sync Configuration
    cost_sync_interval_hours: int = 24
    compliance_sync_interval_hours: int = 4
    resource_sync_interval_hours: int = 1
    identity_sync_interval_hours: int = 24

    # Alerting
    teams_webhook_url: str | None = None
    cost_anomaly_threshold_percent: float = 20.0
    compliance_alert_threshold_percent: float = 5.0

    # Notifications
    notification_enabled: bool = False
    notification_min_severity: str = "warning"  # info, warning, error, critical
    notification_cooldown_minutes: int = 30

    # CORS (for development)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Caching Configuration
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    cache_ttl_cost_summary: int = Field(default=3600, alias="CACHE_TTL_COST_SUMMARY")  # 1 hour
    cache_ttl_compliance_summary: int = Field(default=1800, alias="CACHE_TTL_COMPLIANCE_SUMMARY")  # 30 min
    cache_ttl_resource_inventory: int = Field(default=900, alias="CACHE_TTL_RESOURCE_INVENTORY")  # 15 min
    cache_ttl_identity_summary: int = Field(default=3600, alias="CACHE_TTL_IDENTITY_SUMMARY")  # 1 hour
    cache_ttl_riverside_summary: int = Field(default=900, alias="CACHE_TTL_RIVERSIDE_SUMMARY")  # 15 min

    # Database Configuration
    database_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    slow_query_threshold_ms: float = Field(default=500.0, alias="SLOW_QUERY_THRESHOLD_MS")
    enable_query_logging: bool = Field(default=False, alias="ENABLE_QUERY_LOGGING")

    # Performance & Bulk Operations
    bulk_batch_size: int = Field(default=1000, alias="BULK_BATCH_SIZE")
    sync_chunk_size: int = Field(default=1000, alias="SYNC_CHUNK_SIZE")
    enable_parallel_sync: bool = Field(default=True, alias="ENABLE_PARALLEL_SYNC")
    max_parallel_tenants: int = Field(default=5, alias="MAX_PARALLEL_TENANTS")

    @property
    def is_configured(self) -> bool:
        """Check if minimum Azure configuration is present."""
        return all([
            self.azure_tenant_id,
            self.azure_client_id,
            self.azure_client_secret,
        ])

    def get_cache_ttl(self, data_type: str) -> int:
        """Get TTL for a specific data type."""
        ttl_map = {
            "cost_summary": self.cache_ttl_cost_summary,
            "compliance_summary": self.cache_ttl_compliance_summary,
            "resource_inventory": self.cache_ttl_resource_inventory,
            "identity_summary": self.cache_ttl_identity_summary,
            "riverside_summary": self.cache_ttl_riverside_summary,
        }
        return ttl_map.get(data_type, 300)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
