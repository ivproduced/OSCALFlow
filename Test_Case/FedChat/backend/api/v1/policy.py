"""
Policy RAG API Endpoints

Provides REST API access to organizational policy documents:
- Semantic search across all policies
- Category-based policy retrieval
- Full document access
- Policy statistics
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from backend.services.policy_rag_service import get_policy_rag_service
from backend.api.dependencies import get_current_user
from backend.models import User
from backend.core.logging import get_logger
from backend.middleware.audit import audit_log

logger = get_logger(__name__)
router = APIRouter(prefix="/policy", tags=["policy"])


# Request/Response Models
class PolicySearchRequest(BaseModel):
    """Policy search request"""
    query: str = Field(..., description="Search query", min_length=1, max_length=500)
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)
    category: Optional[str] = Field(None, description="Filter by policy category")


class PolicySearchResult(BaseModel):
    """Single policy search result"""
    content: str = Field(..., description="Policy excerpt")
    source: str = Field(..., description="Source policy document")
    category: str = Field(..., description="Policy category")
    file_path: str = Field(..., description="File path in repository")
    similarity_score: float = Field(..., description="Relevance score (0-1)")


class PolicySearchResponse(BaseModel):
    """Policy search response"""
    query: str
    results: List[PolicySearchResult]
    total_results: int


class PolicyDocument(BaseModel):
    """Full policy document"""
    name: str = Field(..., description="Policy document name")
    content: str = Field(..., description="Full policy content")
    category: str = Field(..., description="Policy category")
    file_path: str = Field(..., description="File path in repository")


class PolicyCategory(BaseModel):
    """Policy category with count"""
    category: str = Field(..., description="Category name")
    document_count: int = Field(..., description="Number of chunks in category")


class PolicyStats(BaseModel):
    """Policy RAG system statistics"""
    status: str = Field(..., description="System status")
    document_count: int = Field(..., description="Total document chunks")
    indexed: bool = Field(..., description="Whether index is built")
    repository: str = Field(..., description="Policy repository URL")
    cache_dir: str = Field(..., description="Local cache directory")


# Endpoints
@router.post("/search", response_model=PolicySearchResponse)
@audit_log("policy_search")
async def search_policies(
    request: PolicySearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search organizational policies
    
    Performs semantic search across all policy documents. Optionally filter by category.
    
    Example queries:
    - "password requirements"
    - "incident response procedures"
    - "data classification levels"
    - "vulnerability remediation timelines"
    """
    try:
        policy_service = get_policy_rag_service()
        
        results = await policy_service.search(
            query=request.query,
            top_k=request.top_k,
            category=request.category
        )
        
        return PolicySearchResponse(
            query=request.query,
            results=[PolicySearchResult(**r) for r in results],
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error("policy_search_error", error=str(e), query=request.query)
        raise HTTPException(status_code=500, detail=f"Policy search failed: {str(e)}")


@router.get("/document/{policy_name}", response_model=PolicyDocument)
@audit_log("policy_get_document")
async def get_policy_document(
    policy_name: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get full policy document by name
    
    Available policies:
    - Information Security Policy
    - Incident Response Program
    - Vulnerability Management Program
    """
    try:
        policy_service = get_policy_rag_service()
        
        document = await policy_service.get_policy_document(policy_name)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Policy document '{policy_name}' not found"
            )
        
        return PolicyDocument(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("policy_get_document_error", error=str(e), policy=policy_name)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve policy: {str(e)}")


@router.get("/category/{category}", response_model=PolicySearchResponse)
@audit_log("policy_get_category")
async def get_policies_by_category(
    category: str,
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Get policies by category
    
    Categories:
    - incident_response
    - vulnerability_management
    - information_security
    - data_security
    - access_control
    - business_continuity
    - acceptable_use
    - general
    """
    try:
        policy_service = get_policy_rag_service()
        
        results = await policy_service.search_by_category(
            category=category,
            top_k=top_k
        )
        
        return PolicySearchResponse(
            query=f"category:{category}",
            results=[PolicySearchResult(**{**r, "similarity_score": 1.0}) for r in results],
            total_results=len(results)
        )
        
    except Exception as e:
        logger.error("policy_category_error", error=str(e), category=category)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve category: {str(e)}")


@router.get("/categories", response_model=List[PolicyCategory])
@audit_log("policy_list_categories")
async def list_policy_categories(
    current_user: User = Depends(get_current_user)
):
    """
    List all policy categories with document counts
    """
    try:
        policy_service = get_policy_rag_service()
        
        categories = await policy_service.list_categories()
        
        return [PolicyCategory(**cat) for cat in categories]
        
    except Exception as e:
        logger.error("policy_list_categories_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list categories: {str(e)}")


@router.get("/stats", response_model=PolicyStats)
async def get_policy_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get policy RAG system statistics
    """
    try:
        policy_service = get_policy_rag_service()
        
        stats = await policy_service.get_stats()
        
        return PolicyStats(**stats)
        
    except Exception as e:
        logger.error("policy_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/initialize")
@audit_log("policy_initialize")
async def initialize_policy_rag(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Initialize or refresh policy RAG system
    
    This endpoint triggers:
    - Policy repository clone/update
    - Document processing
    - FAISS index building
    
    Process runs in background and may take 2-5 minutes.
    """
    try:
        policy_service = get_policy_rag_service()
        
        # Run initialization in background
        background_tasks.add_task(policy_service.initialize)
        
        return {
            "status": "initializing",
            "message": "Policy RAG initialization started in background"
        }
        
    except Exception as e:
        logger.error("policy_initialize_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to initialize: {str(e)}")
