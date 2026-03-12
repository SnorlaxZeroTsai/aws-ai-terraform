"""
FastAPI application for AI Agent Platform.
Provides unified API entry point for all agent services.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from shared.config.settings import settings
from shared.middleware.logging import LoggingMiddleware
from shared.middleware.errors import ErrorHandlerMiddleware
from shared.middleware.tracing import TracingMiddleware
from platform.api.routes import api_router
from platform.orchestrator.agent_orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    logger.info("Starting AI Agent Platform...")

    # Initialize agent orchestrator
    orchestrator = AgentOrchestrator(settings=settings)
    await orchestrator.initialize()

    # Store in app state
    app.state.orchestrator = orchestrator

    logger.info("AI Agent Platform started successfully")
    yield

    # Cleanup
    logger.info("Shutting down AI Agent Platform...")
    await orchestrator.shutdown()
    logger.info("AI Agent Platform stopped")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
if settings.enable_xray:
    app.add_middleware(TracingMiddleware)


# Include routers
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "AI Agent Platform",
        "version": settings.api_version,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "platform": settings.platform_name,
        "environment": settings.environment,
        "version": settings.api_version
    }


# List available agents
@app.get("/agents", tags=["Agents"])
async def list_agents(request: Request) -> dict:
    """List available agents."""
    orchestrator = request.app.state.orchestrator
    agents = await orchestrator.list_agents()

    return {
        "agents": agents,
        "count": len(agents)
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.log_level == "DEBUG" else "An error occurred"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"AWS Region: {settings.aws_region}")
    logger.info(f"Platform: {settings.platform_name}")
    logger.info(f"Orchestration pattern: {settings.orchestration_pattern}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "platform.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
