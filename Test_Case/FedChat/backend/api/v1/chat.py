"""
Chat API Endpoints - Main conversation interface
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
from fastapi.responses import StreamingResponse

from core.database import get_db
from core.config import settings
from services.llm_service import LLMService
from services.guardrails_service import GuardrailsService

router = APIRouter()
logger = structlog.get_logger()


class Message(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is FISMA compliance?"
            }
        }


class ChatRequest(BaseModel):
    """Chat request with message history"""
    messages: List[Message] = Field(..., description="Conversation history")
    stream: bool = Field(default=False, description="Enable streaming responses")
    max_tokens: Optional[int] = Field(default=2048, description="Maximum response tokens")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    use_rag: bool = Field(default=False, description="Enable RAG for this request")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Explain FISMA moderate controls"}
                ],
                "stream": False,
                "use_rag": False
            }
        }


class ChatResponse(BaseModel):
    """Chat response model"""
    message: Message
    model: str
    usage: Optional[dict] = None
    guardrails_applied: bool = False
    rag_sources: Optional[List[str]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a chat message and get a response
    
    This endpoint applies guardrails, optional RAG, and LLM processing.
    """
    try:
        # Initialize services
        llm_service = LLMService()
        guardrails_service = GuardrailsService() if settings.ENABLE_GUARDRAILS else None
        
        # Get last user message
        user_message = request.messages[-1].content
        
        # Apply input guardrails
        guardrails_applied = False
        if guardrails_service:
            validated_message = await guardrails_service.validate_input(user_message)
            if validated_message != user_message:
                guardrails_applied = True
                logger.info("guardrails_applied", original_length=len(user_message), 
                          validated_length=len(validated_message))
                user_message = validated_message
        
        # Prepare context (RAG or direct)
        rag_sources = None
        if request.use_rag and settings.ENABLE_RAG:
            # TODO: Implement RAG retrieval
            rag_sources = []
            logger.info("rag_enabled", query=user_message[:100])
        
        # Get LLM response
        response_text = await llm_service.chat(
            messages=[m.dict() for m in request.messages],
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )
        
        # Apply output guardrails
        if guardrails_service:
            response_text = await guardrails_service.validate_output(response_text)
        
        # Build response
        response = ChatResponse(
            message=Message(role="assistant", content=response_text),
            model=settings.LOCAL_LLM_MODEL,
            guardrails_applied=guardrails_applied,
            rag_sources=rag_sources,
        )
        
        return response
        
    except Exception as e:
        logger.error("chat_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Streaming chat endpoint for real-time responses
    """
    async def generate_response() -> AsyncGenerator[str, None]:
        try:
            llm_service = LLMService()
            
            async for chunk in llm_service.chat_stream(
                messages=[m.dict() for m in request.messages],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            ):
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error("chat_stream_error", error=str(e))
            yield "data: {\"error\": \"An internal error occurred. Please try again.\"}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream"
    )
