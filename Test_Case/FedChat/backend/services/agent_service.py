"""
Agent Service - LangGraph agent execution
"""

from typing import List, Dict, Any, Optional
import structlog
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage

from services.llm_service import LLMService
from services.mcp_service import MCPService
from services.rag_service import RAGService
from core.config import settings

logger = structlog.get_logger()


class AgentState(Dict):
    """State for agent execution"""
    task: str
    messages: List[Any]
    iterations: int
    max_iterations: int
    result: Optional[str]
    tools_used: List[str]
    error: Optional[str]


class AgentService:
    """Service for executing LangGraph agents"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.mcp_service = MCPService() if settings.ENABLE_MCP else None
        self.rag_service = RAGService() if settings.ENABLE_RAG else None
        
        # Add NIST RAG tools if enabled
        self.nist_tools = []
        if settings.ENABLE_NIST_RAG:
            from backend.services.nist_tools import NIST_TOOLS
            self.nist_tools = NIST_TOOLS
            logger.info("nist_rag_tools_loaded", tool_count=len(NIST_TOOLS))
        
        logger.info("agent_service_initialized")
    
    async def execute_agent(
        self,
        task: str,
        agent_type: str = "general",
        max_iterations: int = 10,
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute an agent task
        
        Args:
            task: Task description
            agent_type: Type of agent (general, research, code)
            max_iterations: Maximum iterations
            tools: Specific tools to use
        
        Returns:
            Agent execution result
        """
        try:
            logger.info("agent_execution_start", task=task[:100], agent_type=agent_type)
            
            # Initialize state
            initial_state = AgentState(
                task=task,
                messages=[HumanMessage(content=task)],
                iterations=0,
                max_iterations=max_iterations,
                result=None,
                tools_used=[],
                error=None
            )
            
            # Create agent graph
            graph = self._create_agent_graph(agent_type, tools)
            
            # Execute agent
            final_state = await graph.ainvoke(initial_state)
            
            logger.info(
                "agent_execution_complete",
                iterations=final_state.get("iterations", 0),
                tools_used=final_state.get("tools_used", [])
            )
            
            return {
                "success": final_state.get("error") is None,
                "result": final_state.get("result", ""),
                "iterations": final_state.get("iterations", 0),
                "tools_used": final_state.get("tools_used", []),
                "error": final_state.get("error"),
            }
            
        except Exception as e:
            logger.error("agent_execution_error", error=str(e))
            return {
                "success": False,
                "result": "",
                "iterations": 0,
                "tools_used": [],
                "error": str(e),
            }
    
    def _create_agent_graph(
        self,
        agent_type: str,
        tools: Optional[List[str]] = None
    ) -> StateGraph:
        """Create LangGraph agent"""
        
        # Define agent workflow
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("reflect", self._reflect_node)
        
        # Define edges
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "execute")
        workflow.add_conditional_edges(
            "execute",
            self._should_continue,
            {
                "continue": "reflect",
                "end": END
            }
        )
        workflow.add_edge("reflect", "plan")
        
        return workflow.compile()
    
    async def _plan_node(self, state: AgentState) -> AgentState:
        """Planning node - decide what to do next"""
        task = state["task"]
        iterations = state["iterations"]
        
        # Create planning prompt
        planning_messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Plan the next step to complete the task."},
            {"role": "user", "content": f"Task: {task}\n\nIteration: {iterations + 1}\n\nWhat should I do next?"}
        ]
        
        # Get plan from LLM
        plan = await self.llm_service.chat(planning_messages)
        
        state["messages"].append(AIMessage(content=plan))
        return state
    
    async def _execute_node(self, state: AgentState) -> AgentState:
        """Execution node - perform actions"""
        try:
            # Get last message (the plan)
            last_message = state["messages"][-1].content
            
            # Check if policy-related query
            policy_keywords = ["policy", "procedure", "requirement", "incident response", "vulnerability management", "access control", "password", "acceptable use"]
            if any(keyword in last_message.lower() for keyword in policy_keywords) and self.policy_tools:
                # Use Policy RAG tools
                from backend.services.policy_tools import search_policies
                try:
                    result = await search_policies(state["task"])
                    state["tools_used"].append("policy_rag")
                    state["messages"].append(AIMessage(content=f"Policy Information:\n{result}"))
                except Exception as e:
                    logger.error("policy_tool_error", error=str(e))
            
            # Check if NIST-related query
            elif any(keyword in last_message.lower() for keyword in ["nist", "control", "sp 800", "cybersecurity framework", "csf", "zero trust", "800-53", "800-171"]) and self.nist_tools:
                # Use NIST RAG tools
                from backend.services.nist_tools import search_nist_standards
                try:
                    result = await search_nist_standards(state["task"])
                    state["tools_used"].append("nist_rag")
                    state["messages"].append(AIMessage(content=f"NIST Information:\n{result}"))
                except Exception as e:
                    logger.error("nist_tool_error", error=str(e))
            
            # Check if we need to use RAG
            elif "search" in last_message.lower() and self.rag_service:
                # Use RAG
                results = await self.rag_service.search(state["task"], top_k=3)
                state["tools_used"].append("rag_search")
                
                # Add results to context
                context = "\n\n".join([r["content"] for r in results])
                state["messages"].append(AIMessage(content=f"RAG Results:\n{context}"))
            
            elif "query" in last_message.lower() and self.mcp_service:
                # Use MCP database tool
                try:
                    result = await self.mcp_service.execute_tool(
                        "query_database",
                        {"query": "SELECT COUNT(*) FROM documents"}
                    )
                    state["tools_used"].append("database_query")
                    state["messages"].append(AIMessage(content=f"Database result: {result}"))
                except Exception as e:
                    logger.error("mcp_tool_error", error=str(e))
            
            # Generate response
            response_messages = [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": state["task"]},
                {"role": "assistant", "content": "\n".join([m.content for m in state["messages"][-3:]])}
            ]
            
            response = await self.llm_service.chat(response_messages)
            state["result"] = response
            state["iterations"] += 1
            
        except Exception as e:
            state["error"] = str(e)
            logger.error("execute_node_error", error=str(e))
        
        return state
    
    async def _reflect_node(self, state: AgentState) -> AgentState:
        """Reflection node - evaluate progress"""
        # Simple reflection: check if we have a good answer
        if state.get("result"):
            result_quality = await self._evaluate_result(state["result"], state["task"])
            
            if result_quality > 0.7:  # Good enough
                logger.info("agent_reflection_satisfied")
            else:
                logger.info("agent_reflection_needs_improvement")
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Decide whether to continue or end"""
        if state.get("error"):
            return "end"
        
        if state["iterations"] >= state["max_iterations"]:
            return "end"
        
        if state.get("result"):
            # Simple heuristic: end if we have a substantive result
            if len(state["result"]) > 100:
                return "end"
        
        # Continue for a few iterations
        if state["iterations"] < 3:
            return "continue"
        
        return "end"
    
    async def _evaluate_result(self, result: str, task: str) -> float:
        """Evaluate result quality (0-1)"""
        # Simple heuristic: length and relevance
        if len(result) < 50:
            return 0.3
        
        # Check if task keywords appear in result
        task_words = set(task.lower().split())
        result_words = set(result.lower().split())
        overlap = len(task_words & result_words) / len(task_words) if task_words else 0
        
        return min(0.5 + overlap, 1.0)
    
    async def list_available_agents(self) -> List[Dict[str, Any]]:
        """List available agent types"""
        agents = [
            {
                "type": "general",
                "description": "General-purpose assistant for various tasks",
                "capabilities": ["question_answering", "analysis", "summarization"]
            },
            {
                "type": "research",
                "description": "Research agent with RAG and web search",
                "capabilities": ["document_search", "information_retrieval", "synthesis"]
            },
            {
                "type": "code",
                "description": "Code analysis and generation agent",
                "capabilities": ["code_review", "debugging", "generation"]
            }
        ]
        
        return agents
