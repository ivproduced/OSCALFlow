"""
Policy RAG Agent Tools

LangChain tools for agent integration with organizational policies:
- Search policy documents
- Get policy by category
- Retrieve specific policy sections
"""

from typing import Optional
from langchain.tools import tool

from backend.services.policy_rag_service import get_policy_rag_service
from backend.core.logging import get_logger

logger = get_logger(__name__)


@tool
async def search_policies(query: str, category: Optional[str] = None) -> str:
    """
    Search organizational security policies for information on procedures, requirements, and guidelines.
    
    Use this tool to find:
    - Security policy requirements
    - Incident response procedures
    - Access control policies
    - Data handling requirements
    - Vulnerability remediation timelines
    - Business continuity procedures
    
    Args:
        query: Search query (e.g., "password requirements", "incident escalation")
        category: Optional category filter (incident_response, vulnerability_management, etc.)
    
    Returns:
        Relevant policy excerpts
    """
    try:
        policy_service = get_policy_rag_service()
        results = await policy_service.search(query=query, top_k=3, category=category)
        
        if not results:
            return f"No policy information found for query: {query}"
        
        # Format results
        response = f"Policy Information for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. From {result['source']} ({result['category']}):\n"
            response += f"{result['content']}\n\n"
        
        return response
        
    except Exception as e:
        logger.error("policy_tool_search_error", error=str(e))
        return f"Error searching policies: {str(e)}"


@tool
async def get_incident_response_policy() -> str:
    """
    Get incident response procedures and escalation guidelines.
    
    Use this tool when questions involve:
    - Incident reporting
    - Incident classification
    - Escalation procedures
    - Containment and eradication
    - Post-incident activities
    
    Returns:
        Incident response policy details
    """
    try:
        policy_service = get_policy_rag_service()
        results = await policy_service.search_by_category(
            category="incident_response",
            top_k=5
        )
        
        if not results:
            return "Incident response policy not found"
        
        response = "Incident Response Policy:\n\n"
        for result in results:
            response += f"{result['content']}\n\n"
        
        return response
        
    except Exception as e:
        logger.error("policy_tool_ir_error", error=str(e))
        return f"Error retrieving incident response policy: {str(e)}"


@tool
async def get_vulnerability_policy() -> str:
    """
    Get vulnerability management and remediation requirements.
    
    Use this tool for questions about:
    - Vulnerability scanning requirements
    - Patch management timelines
    - Risk classification
    - Remediation procedures
    
    Returns:
        Vulnerability management policy details
    """
    try:
        policy_service = get_policy_rag_service()
        results = await policy_service.search_by_category(
            category="vulnerability_management",
            top_k=5
        )
        
        if not results:
            return "Vulnerability management policy not found"
        
        response = "Vulnerability Management Policy:\n\n"
        for result in results:
            response += f"{result['content']}\n\n"
        
        return response
        
    except Exception as e:
        logger.error("policy_tool_vuln_error", error=str(e))
        return f"Error retrieving vulnerability policy: {str(e)}"


@tool
async def get_access_control_policy() -> str:
    """
    Get access control and authentication requirements.
    
    Use this tool for questions about:
    - Password/credential requirements
    - Multi-factor authentication
    - Least privilege access
    - Account management
    - Service account requirements
    
    Returns:
        Access control policy details
    """
    try:
        policy_service = get_policy_rag_service()
        results = await policy_service.search(
            query="access control authentication credentials",
            top_k=5
        )
        
        if not results:
            return "Access control policy not found"
        
        response = "Access Control Policy:\n\n"
        for result in results:
            response += f"{result['content']}\n\n"
        
        return response
        
    except Exception as e:
        logger.error("policy_tool_access_error", error=str(e))
        return f"Error retrieving access control policy: {str(e)}"


# Export tools for agent integration
POLICY_TOOLS = [
    search_policies,
    get_incident_response_policy,
    get_vulnerability_policy,
    get_access_control_policy
]
