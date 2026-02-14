"""
NIST-specific RAG endpoints
Provides access to 596 NIST publications with 530K+ examples
"""
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from backend.services.nist_rag_service import nist_rag_service
from backend.api.dependencies import get_current_user
from backend.models import User
from backend.middleware.audit import log_audit

router = APIRouter(prefix="/nist", tags=["NIST RAG"])


class NistSearchRequest(BaseModel):
    """Request model for NIST search"""
    query: str = Field(..., description="Search query", min_length=3)
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    document_id: Optional[str] = Field(None, description="Filter by NIST document (e.g., SP-800-53)")
    control_id: Optional[str] = Field(None, description="Filter by control ID (e.g., AC-2)")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class NistSearchResult(BaseModel):
    """Individual search result"""
    content: str
    source: str
    document_id: str
    control_id: Optional[str] = None
    section: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    similarity_score: float


class NistSearchResponse(BaseModel):
    """Response model for NIST search"""
    results: List[NistSearchResult]
    query: str
    total_results: int


@router.post("/search", response_model=NistSearchResponse)
async def search_nist_standards(
    request: NistSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search NIST cybersecurity standards using RAG
    
    Access 596 NIST publications with 530K+ examples:
    - **SP 800 Series**: Security Controls (800-53), Risk Management (800-37), CUI (800-171)
    - **FIPS**: Federal Information Processing Standards
    - **CSWP**: Cybersecurity White Papers (CSF 2.0, Zero Trust, etc.)
    - **SP 1800 Series**: NIST Practice Guides
    - **IR Series**: Interagency/Internal Reports
    
    Examples:
    - "What are the requirements for access control?"
    - "Explain Zero Trust Architecture principles"
    - "What's new in NIST CSF 2.0?"
    """
    try:
        await log_audit(
            user_id=current_user.id,
            action="nist_search",
            details={"query": request.query[:100]}
        )
        
        # Build filter dict
        filter_dict = {}
        if request.document_id:
            filter_dict["document_id"] = request.document_id
        if request.control_id:
            filter_dict["control_id"] = request.control_id.upper()
        
        # Perform search
        results = await nist_rag_service.search(
            query=request.query,
            top_k=request.top_k,
            filter_dict=filter_dict if filter_dict else None,
            similarity_threshold=request.similarity_threshold
        )
        
        return NistSearchResponse(
            results=[NistSearchResult(**r) for r in results],
            query=request.query,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NIST search failed: {str(e)}")


@router.get("/control/{control_id}")
async def get_control_details(
    control_id: str,
    top_k: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    Get details for a specific NIST SP 800-53 control
    
    Examples:
    - AC-2: Account Management
    - IR-4: Incident Handling
    - SC-7: Boundary Protection
    - AU-2: Audit Events
    """
    try:
        await log_audit(
            user_id=current_user.id,
            action="nist_control_lookup",
            details={"control_id": control_id.upper()}
        )
        
        results = await nist_rag_service.search_by_control(
            control_id=control_id.upper(),
            top_k=top_k
        )
        
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Control {control_id.upper()} not found in NIST database"
            )
        
        return {
            "control_id": control_id.upper(),
            "results": [NistSearchResult(**r) for r in results]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{document_id}")
async def search_document(
    document_id: str,
    query: str = Field(..., min_length=3),
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Search within a specific NIST document
    
    Common document IDs:
    - SP-800-53: Security and Privacy Controls
    - SP-800-171: CUI Protection
    - SP-800-37: Risk Management Framework
    - SP-800-207: Zero Trust Architecture
    - CSF-2.0: Cybersecurity Framework 2.0
    """
    try:
        await log_audit(
            user_id=current_user.id,
            action="nist_document_search",
            details={"document_id": document_id, "query": query[:100]}
        )
        
        results = await nist_rag_service.search_by_document(
            document_id=document_id,
            query=query,
            top_k=top_k
        )
        
        return {
            "document_id": document_id,
            "query": query,
            "results": [NistSearchResult(**r) for r in results]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/csf")
async def search_csf(
    query: str = Field(..., min_length=3),
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Search NIST Cybersecurity Framework 2.0
    
    Topics include:
    - Govern function (new in 2.0)
    - Identify, Protect, Detect, Respond, Recover
    - Implementation guidance
    """
    try:
        results = await nist_rag_service.search_csf(query=query, top_k=top_k)
        
        return {
            "framework": "NIST Cybersecurity Framework 2.0",
            "query": query,
            "results": [NistSearchResult(**r) for r in results]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/zero-trust")
async def search_zero_trust(
    query: str = Field(..., min_length=3),
    top_k: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Search NIST Zero Trust Architecture (SP 800-207)
    
    Topics include:
    - Core principles
    - Logical components
    - Deployment models
    - Implementation guidance
    """
    try:
        results = await nist_rag_service.search_zero_trust(query=query, top_k=top_k)
        
        return {
            "document": "NIST SP 800-207 (Zero Trust Architecture)",
            "query": query,
            "results": [NistSearchResult(**r) for r in results]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_nist_rag_stats(
    current_user: User = Depends(get_current_user)
):
    """Get NIST RAG system statistics and coverage information"""
    return nist_rag_service.get_stats()


@router.post("/initialize")
async def initialize_nist_rag(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Initialize NIST RAG system (downloads dataset if not cached)
    
    **Warning**: This can take 10-20 minutes on first run
    - Downloads ~7GB HuggingFace dataset
    - Creates FAISS index with 530K+ vectors
    - Subsequent runs use cached index (<30 seconds)
    
    Admin only endpoint.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Check if already initialized
        stats = nist_rag_service.get_stats()
        if stats.get("initialized"):
            return {
                "status": "already_initialized",
                "message": "NIST RAG system is already initialized",
                "stats": stats
            }
        
        # Initialize in background
        background_tasks.add_task(nist_rag_service.initialize)
        
        return {
            "status": "initializing",
            "message": "NIST RAG initialization started in background. This may take 10-20 minutes on first run.",
            "note": "Check /api/v1/nist/stats to monitor progress"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Initialization failed: {str(e)}"
        )


@router.get("/health")
async def nist_health_check():
    """Check NIST RAG service health (no authentication required)"""
    stats = nist_rag_service.get_stats()
    
    return {
        "service": "NIST RAG",
        "status": "healthy" if stats.get("initialized") else "not_initialized",
        "initialized": stats.get("initialized", False),
        "total_vectors": stats.get("total_vectors", 0)
    }
