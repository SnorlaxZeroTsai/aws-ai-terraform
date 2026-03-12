"""
API routes for the AI Agent Platform.
Defines all endpoints for agent interactions.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

from platform.orchestrator.agent_orchestrator import AgentOrchestrator
from shared.config.settings import settings

logger = logging.getLogger(__name__)

# Create router
api_router = APIRouter()


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message", min_length=1)
    session_id: Optional[str] = Field(None, description="Session ID for context")
    model: Optional[str] = Field(None, description="Model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Temperature")
    max_tokens: Optional[int] = Field(1000, ge=1, description="Max tokens to generate")


class RAGRequest(BaseModel):
    """RAG query request model."""
    query: str = Field(..., description="Query text", min_length=1)
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results")
    min_score: Optional[float] = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    include_sources: Optional[bool] = Field(True, description="Include source documents")


class AgentRequest(BaseModel):
    """Autonomous agent request model."""
    task: str = Field(..., description="Task description", min_length=1)
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    tools: Optional[list[str]] = Field(None, description="Specific tools to use")
    max_iterations: Optional[int] = Field(10, ge=1, le=50, description="Max iterations")


class DocumentRequest(BaseModel):
    """Document analysis request model."""
    document_key: str = Field(..., description="S3 object key")
    analysis_type: Optional[str] = Field("full", description="Analysis type")
    extract_tables: Optional[bool] = Field(True, description="Extract tables")
    extract_forms: Optional[bool] = Field(True, description="Extract forms")


class JobStatusResponse(BaseModel):
    """Job status response model."""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


class AgentResponse(BaseModel):
    """Generic agent response model."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Helper function to get orchestrator
def get_orchestrator(request: Request) -> AgentOrchestrator:
    """Get orchestrator from app state."""
    return request.app.state.orchestrator


# Chat endpoint
@api_router.post("/chat", response_model=AgentResponse, tags=["Chatbot"])
async def chat_endpoint(
    request: ChatRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> AgentResponse:
    """
    Chat with the AI chatbot.

    - **message**: User message to process
    - **session_id**: Optional session ID for conversation context
    - **temperature**: Response randomness (0.0 - 1.0)
    - **max_tokens**: Maximum tokens in response
    """
    try:
        if not settings.enable_chatbot_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chatbot agent is disabled"
            )

        logger.info(f"Chat request: {request.message[:100]}...")

        # Route to chatbot agent
        result = await orchestrator.route_to_agent(
            agent_type="chatbot",
            request_data=request.dict()
        )

        return AgentResponse(
            success=True,
            data=result,
            metadata={"agent": "chatbot", "session_id": request.session_id}
        )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# RAG endpoint
@api_router.post("/rag", response_model=AgentResponse, tags=["RAG"])
async def rag_query_endpoint(
    request: RAGRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> AgentResponse:
    """
    Query the RAG knowledge base.

    - **query**: Query text
    - **top_k**: Number of results to return
    - **min_score**: Minimum similarity score
    - **include_sources**: Include source documents in response
    """
    try:
        if not settings.enable_rag_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG agent is disabled"
            )

        logger.info(f"RAG query: {request.query[:100]}...")

        # Route to RAG agent
        result = await orchestrator.route_to_agent(
            agent_type="rag",
            request_data=request.dict()
        )

        return AgentResponse(
            success=True,
            data=result,
            metadata={"agent": "rag", "top_k": request.top_k}
        )

    except Exception as e:
        logger.error(f"RAG endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Autonomous agent endpoint
@api_router.post("/agent", response_model=AgentResponse, tags=["Autonomous Agent"])
async def autonomous_agent_endpoint(
    request: AgentRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> AgentResponse:
    """
    Execute a task using the autonomous agent.

    - **task**: Task description
    - **context**: Additional context for the task
    - **tools**: Specific tools to use (optional)
    - **max_iterations**: Maximum reasoning iterations
    """
    try:
        if not settings.enable_autonomous_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Autonomous agent is disabled"
            )

        logger.info(f"Autonomous agent task: {request.task[:100]}...")

        # Route to autonomous agent
        result = await orchestrator.route_to_agent(
            agent_type="autonomous",
            request_data=request.dict()
        )

        # Extract job ID if async execution
        job_id = result.get("job_id") if result else None

        return AgentResponse(
            success=True,
            data=result,
            metadata={"agent": "autonomous", "job_id": job_id}
        )

    except Exception as e:
        logger.error(f"Autonomous agent endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Document analysis endpoint
@api_router.post("/document", response_model=AgentResponse, tags=["Document Analysis"])
async def document_analysis_endpoint(
    request: DocumentRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> AgentResponse:
    """
    Analyze a document using AI.

    - **document_key**: S3 object key of the document
    - **analysis_type**: Type of analysis (full, text, tables, forms)
    - **extract_tables**: Extract tables from document
    - **extract_forms**: Extract forms from document
    """
    try:
        if not settings.enable_document_agent:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document agent is disabled"
            )

        logger.info(f"Document analysis request: {request.document_key}")

        # Route to document agent
        result = await orchestrator.route_to_agent(
            agent_type="document",
            request_data=request.dict()
        )

        return AgentResponse(
            success=True,
            data=result,
            metadata={"agent": "document", "document_key": request.document_key}
        )

    except Exception as e:
        logger.error(f"Document analysis endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Job status endpoint
@api_router.get("/status/{job_id}", response_model=JobStatusResponse, tags=["Jobs"])
async def job_status_endpoint(
    job_id: str,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> JobStatusResponse:
    """
    Get the status of an asynchronous job.

    - **job_id**: Job identifier
    """
    try:
        status_data = await orchestrator.get_job_status(job_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        return JobStatusResponse(**status_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job status endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Multi-agent collaboration endpoint
@api_router.post("/collaborate", response_model=AgentResponse, tags=["Multi-Agent"])
async def collaborate_endpoint(
    agents: list[str],
    task: str,
    context: Optional[Dict[str, Any]] = None,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> AgentResponse:
    """
    Collaborate multiple agents on a task.

    - **agents**: List of agent types to involve
    - **task**: Task description
    - **context**: Additional context
    """
    try:
        logger.info(f"Multi-agent collaboration: {agents} on task: {task[:100]}...")

        result = await orchestrator.collaborate(
            agents=agents,
            task=task,
            context=context or {}
        )

        return AgentResponse(
            success=True,
            data=result,
            metadata={"agents": agents, "collaboration_mode": settings.orchestration_pattern}
        )

    except Exception as e:
        logger.error(f"Collaboration endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
