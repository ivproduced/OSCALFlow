"""
LLM Service - Interface to language models
"""

from typing import List, Dict, Any, AsyncGenerator, Optional
import structlog
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
import tiktoken

from core.config import settings

logger = structlog.get_logger()


class LLMService:
    """Service for interacting with LLMs"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LOCAL_LLM_MODEL
        
        # Initialize LLM based on provider
        if self.provider == "local":
            self.llm = Ollama(
                base_url=settings.LOCAL_LLM_BASE_URL,
                model=self.model,
                temperature=0.7,
            )
        elif self.provider == "azure":
            self.llm = ChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                openai_api_version=settings.AZURE_OPENAI_API_VERSION,
                deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
                temperature=0.7,
            )
        elif self.provider == "aws":
            # AWS Bedrock implementation
            from langchain_community.chat_models import BedrockChat
            self.llm = BedrockChat(
                model_id=settings.AWS_BEDROCK_MODEL,
                region_name=settings.AWS_REGION,
                credentials_profile_name=None,  # Uses environment variables
                model_kwargs={"temperature": 0.7},
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
        
        logger.info("llm_service_initialized", provider=self.provider, model=self.model)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """ount input tokens
            input_tokens = self._count_tokens(messages)
            
            # Create chat prompt
            if self.provider == "local":
                # For Ollama, just use the last message
                response = await self.llm.ainvoke(
                    lc_messages[-1].content if lc_messages else ""
                )
            else:
                # For OpenAI-compatible APIs, use full message history
                response = await self.llm.ainvoke(lc_messages)
                if hasattr(response, "content"):
                    response = response.content
            
            output_tokens = self._count_tokens([{"role": "assistant", "content": response}])
            
            logger.info(
                "llm_chat_complete",
                model=self.model,
                message_count=len(messages),
                input_tokens=input_tokens,
                output_tokens=output_tokens
            # Convert messages to LangChain format
            lc_messages = self._convert_messages(messages)
            
            # Create chain with parser
            chain = self.llm | StrOutputParser()
            
            # Get response
            response = await chain.ainvoke(
                lc_messages[-1].content if lc_messages else "",
            )
            
            logger.info(
                "llm_chat_complete",
                model=self.model,
                message_count=len(messages),
                response_length=len(response),
            )
            
            return response
            
        except Exception as e:
            logger.error("llm_chat_error", error=str(e), error_type=type(e).__name__)
            raise
    
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response
        
        Yields response chunks as they're generated
        """
        try:
            lc_messages = self._convert_messages(messages)
            
    
    def _count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Count tokens in messages"""
        try:
            # Use tiktoken for OpenAI-compatible models
            encoding = tiktoken.get_encoding("cl100k_base")
            total_tokens = 0
            
            for msg in messages:
                content = msg.get("content", "")
                total_tokens += len(encoding.encode(content))
            
            return total_tokens
        except Exception:
            # Fallback: rough estimate (1 token ~= 4 chars)
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return total_chars // 4
    
    async def generate_title(self, messages: List[Dict[str, str]]) -> str:
        """Generate a conversation title from messages"""
        try:
            # Get first user message
            first_message = next(
                (msg["content"] for msg in messages if msg["role"] == "user"),
                "New Conversation"
            )
            
            # Truncate and create title
            if len(first_message) > 100:
                title = first_message[:97] + "..."
            else:
                title = first_message
            
            return title
        except Exception as e:
            logger.error("generate_title_error", error=str(e))
            return "New Conversation"
            # Stream response
            async for chunk in self.llm.astream(
                lc_messages[-1].content if lc_messages else ""
            ):
                yield chunk
            
        except Exception as e:
            logger.error("llm_stream_error", error=str(e))
            raise
    
    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """Convert message dicts to LangChain message objects"""
        lc_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
        
        return lc_messages
