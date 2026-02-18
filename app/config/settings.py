"""Application settings and configuration management."""
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8000, description="API port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database Configuration
    db_host: str = Field(..., description="Database host")
    db_port: int = Field(default=4000, description="Database port")
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")
    db_name: str = Field(..., description="Database name")
    db_pool_size: int = Field(default=10, description="Connection pool size")
    db_max_overflow: int = Field(default=20, description="Max pool overflow")
    db_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    
    # CORS Configuration
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard Python logging levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper
    
    @property
    def database_url(self) -> str:
        """Construct database URL for SQLAlchemy."""
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def model_dump(self, **kwargs) -> dict:
        """Override to mask sensitive fields in output."""
        data = super().model_dump(**kwargs)
        if "db_password" in data:
            data["db_password"] = "***MASKED***"
        return data
    
    def __repr__(self) -> str:
        """Override to mask sensitive fields in string representation."""
        return f"Settings(api_host={self.api_host}, db_host={self.db_host}, db_user={self.db_user})"


# Global settings instance
settings = Settings()
