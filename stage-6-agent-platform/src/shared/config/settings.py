"""
Configuration settings for the AI Agent Platform.
Uses pydantic-settings for environment-based configuration.
"""
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Platform Configuration
    platform_name: str = Field(default="ai-agent-platform", description="Platform name")
    environment: str = Field(default="prod", description="Environment name")
    aws_region: str = Field(default="us-east-1", description="AWS region")

    # API Configuration
    api_title: str = Field(default="AI Agent Platform API", description="API title")
    api_version: str = Field(default="1.0.0", description="API version")
    api_description: str = Field(
        default="Unified API for AI Agent Platform with multi-agent collaboration",
        description="API description"
    )

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    reload: bool = Field(default=False, description="Enable auto-reload")

    # Container Configuration
    container_port: int = Field(default=8000, description="Container port")

    # Authentication
    auth_type: str = Field(default="jwt", description="Authentication type (jwt, api_key, cognito)")
    jwt_secret: str = Field(default="change-me-in-production", description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration: int = Field(default=3600, description="JWT expiration in seconds")

    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_allow_methods: List[str] = Field(
        default=["*"],
        description="CORS allowed methods"
    )
    cors_allow_headers: List[str] = Field(
        default=["*"],
        description="CORS allowed headers"
    )

    # Agent Configuration
    enable_chatbot_agent: bool = Field(default=True, description="Enable chatbot agent")
    enable_rag_agent: bool = Field(default=True, description="Enable RAG agent")
    enable_autonomous_agent: bool = Field(default=True, description="Enable autonomous agent")
    enable_document_agent: bool = Field(default=True, description="Enable document agent")

    # Agent Timeout (seconds)
    agent_timeout: int = Field(default=30, description="Agent request timeout")

    # Orchestration Pattern
    orchestration_pattern: str = Field(
        default="hierarchical",
        description="Orchestration pattern (hierarchical, network, pipeline)"
    )

    # X-Ray Configuration
    enable_xray: bool = Field(default=True, description="Enable X-Ray tracing")
    xray_context_missing: str = Field(default="LOG_ERROR", description="X-Ray context missing strategy")

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(default="json", description="Log format (json, text)")

    # Metrics Configuration
    enable_prometheus: bool = Field(default=True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(default=9090, description="Prometheus metrics port")

    # Stage 2 Integration (Chatbot)
    stage2_chatbot_lambda_arn: Optional[str] = Field(
        default=None,
        description="Stage 2 chatbot Lambda ARN"
    )
    stage2_api_gateway_url: Optional[str] = Field(
        default=None,
        description="Stage 2 API Gateway URL"
    )

    # Stage 3 Integration (Document Analysis)
    stage3_sqs_queue_url: Optional[str] = Field(
        default=None,
        description="Stage 3 SQS queue URL"
    )
    stage3_s3_bucket_name: Optional[str] = Field(
        default=None,
        description="Stage 3 S3 bucket name"
    )

    # Stage 4 Integration (RAG)
    stage4_opensearch_endpoint: Optional[str] = Field(
        default=None,
        description="Stage 4 OpenSearch endpoint"
    )
    stage4_search_lambda_arn: Optional[str] = Field(
        default=None,
        description="Stage 4 search Lambda ARN"
    )

    # Stage 5 Integration (Autonomous Agent)
    stage5_step_function_arn: Optional[str] = Field(
        default=None,
        description="Stage 5 Step Function ARN"
    )
    stage5_agent_core_lambda_arn: Optional[str] = Field(
        default=None,
        description="Stage 5 agent core Lambda ARN"
    )

    # Caching Configuration
    enable_cache: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")

    # Rate Limiting
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per minute")
    rate_limit_burst: int = Field(default=20, description="Rate limit burst")

    # Health Check
    health_check_interval: int = Field(default=30, description="Health check interval")


# Global settings instance
settings = Settings()
