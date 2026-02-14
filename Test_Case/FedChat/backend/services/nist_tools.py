"""
NIST-specific tools for LangGraph agent integration
Allows agents to automatically search NIST standards during task execution
"""
from langchain_core.tools import tool
from backend.services.nist_rag_service import nist_rag_service


@tool("search_nist_standards")
async def search_nist_standards(query: str) -> str:
    """
    Search NIST cybersecurity standards and frameworks (596 publications, 530K+ examples).
    Use this for questions about:
    - NIST SP 800 series (Security Controls, Risk Management, CUI protection)
    - NIST Cybersecurity Framework 2.0
    - Zero Trust Architecture (SP 800-207)
    - Post-Quantum Cryptography guidance
    - FIPS standards
    - Any NIST cybersecurity guidance
    
    Args:
        query: Search query about NIST standards
    
    Returns:
        Relevant NIST document excerpts with citations and URLs
    """
    try:
        results = await nist_rag_service.search(query, top_k=3)
        
        if not results:
            return "No relevant NIST documents found for this query."
        
        response = "## NIST Standards Information\n\n"
        for idx, result in enumerate(results, 1):
            # Truncate content for readability
            content = result['content'][:600] + "..." if len(result['content']) > 600 else result['content']
            
            response += f"### Result {idx} (Similarity: {result.get('similarity_score', 0):.2f})\n"
            response += f"{content}\n\n"
            response += f"**Source:** {result['source']}\n"
            
            if result.get('control_id'):
                response += f"**Control:** {result['control_id']}\n"
            if result.get('section'):
                response += f"**Section:** {result['section']}\n"
            if result.get('url'):
                response += f"**URL:** {result['url']}\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error searching NIST standards: {str(e)}"


@tool("get_nist_control")
async def get_nist_control(control_id: str) -> str:
    """
    Get detailed information about a specific NIST SP 800-53 control.
    
    Args:
        control_id: NIST control identifier (e.g., AC-2, IR-4, SC-7, AU-2, IA-5)
    
    Returns:
        Control description, requirements, and implementation guidance with sources
    """
    try:
        # Clean up control ID
        control_id = control_id.strip().upper()
        
        results = await nist_rag_service.search_by_control(control_id, top_k=2)
        
        if not results:
            return f"Control {control_id} not found in NIST database. Please verify the control ID format (e.g., AC-2, IR-4)."
        
        response = f"## NIST Control {control_id}\n\n"
        
        for idx, result in enumerate(results, 1):
            response += f"### Information Source {idx}\n"
            response += f"{result['content']}\n\n"
            response += f"**Source:** {result['source']}\n"
            
            if result.get('section'):
                response += f"**Section:** {result['section']}\n"
            if result.get('url'):
                response += f"**URL:** {result['url']}\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error retrieving control {control_id}: {str(e)}"


@tool("search_nist_csf")
async def search_nist_csf(query: str) -> str:
    """
    Search NIST Cybersecurity Framework 2.0 specifically.
    Use this for questions about:
    - CSF functions (Govern, Identify, Protect, Detect, Respond, Recover)
    - CSF implementation guidance
    - Framework profiles and tiers
    
    Args:
        query: Search query about NIST CSF 2.0
    
    Returns:
        Relevant CSF 2.0 content with sources
    """
    try:
        results = await nist_rag_service.search_csf(query, top_k=3)
        
        if not results:
            return "No relevant NIST Cybersecurity Framework 2.0 information found."
        
        response = "## NIST Cybersecurity Framework 2.0\n\n"
        
        for idx, result in enumerate(results, 1):
            content = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
            
            response += f"### {idx}. {result.get('section', 'CSF Information')}\n"
            response += f"{content}\n\n"
            response += f"**Source:** {result['source']}\n"
            if result.get('url'):
                response += f"**URL:** {result['url']}\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error searching NIST CSF: {str(e)}"


@tool("search_zero_trust")
async def search_zero_trust(query: str) -> str:
    """
    Search NIST Zero Trust Architecture guidance (SP 800-207).
    Use this for questions about:
    - Zero Trust principles and core components
    - Zero Trust deployment models
    - Zero Trust implementation strategies
    
    Args:
        query: Search query about Zero Trust Architecture
    
    Returns:
        Relevant Zero Trust guidance from NIST SP 800-207
    """
    try:
        results = await nist_rag_service.search_zero_trust(query, top_k=3)
        
        if not results:
            return "No relevant Zero Trust Architecture information found."
        
        response = "## NIST SP 800-207: Zero Trust Architecture\n\n"
        
        for idx, result in enumerate(results, 1):
            content = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
            
            response += f"### {idx}. {result.get('section', 'Zero Trust Information')}\n"
            response += f"{content}\n\n"
            response += f"**Source:** {result['source']}\n"
            if result.get('url'):
                response += f"**URL:** {result['url']}\n"
            response += "\n"
        
        return response
        
    except Exception as e:
        return f"Error searching Zero Trust guidance: {str(e)}"


# Export all NIST tools for agent integration
NIST_TOOLS = [
    search_nist_standards,
    get_nist_control,
    search_nist_csf,
    search_zero_trust
]
