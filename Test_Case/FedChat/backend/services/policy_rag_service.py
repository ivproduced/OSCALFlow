"""
Policy RAG Service - Organizational Policy Grounding

Provides semantic search over organizational security policies using:
- GitHub repository cloning (0xdefendA/policies as demo)
- Markdown document processing
- FAISS vector indexing with OpenAI embeddings
- Category-based policy retrieval

Policies include:
- Information Security Policy
- Incident Response Program
- Vulnerability Management Program
- And custom organizational policies
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from backend.core.config import settings

logger = logging.getLogger(__name__)


class PolicyRagService:
    """Service for policy document RAG with GitHub integration"""
    
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.documents = []
        self.initialized = False
        
        # Policy repository configuration
        self.policy_repo_url = settings.POLICY_REPO_URL
        self.policy_cache_dir = Path(settings.POLICY_RAG_CACHE_DIR)
        self.policy_repo_path = self.policy_cache_dir / "repo"
        self.faiss_index_path = self.policy_cache_dir / "faiss_index"
        
    async def initialize(self):
        """Initialize policy RAG system (lazy loading)"""
        if self.initialized:
            return
            
        try:
            logger.info("policy_rag_init", action="starting")
            
            # Create cache directories
            self.policy_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize embeddings
            if settings.OPENAI_API_KEY:
                self.embeddings = OpenAIEmbeddings(
                    model=settings.POLICY_EMBEDDING_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY
                )
            else:
                logger.error("policy_rag_init", error="OPENAI_API_KEY not configured")
                raise ValueError("OPENAI_API_KEY required for policy embeddings")
            
            # Clone or update policy repository
            await self._sync_policy_repo()
            
            # Load or build FAISS index
            if self.faiss_index_path.exists():
                logger.info("policy_rag_init", action="loading_cached_index")
                self.vectorstore = FAISS.load_local(
                    str(self.faiss_index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                logger.info("policy_rag_init", action="building_index")
                await self._build_index()
            
            self.initialized = True
            logger.info("policy_rag_init", status="success")
            
        except Exception as e:
            logger.error("policy_rag_init", error=str(e))
            raise
    
    async def _sync_policy_repo(self):
        """Clone or update policy repository from GitHub"""
        try:
            import git
            
            if self.policy_repo_path.exists():
                # Pull latest changes
                logger.info("policy_repo_sync", action="pulling_updates")
                repo = git.Repo(self.policy_repo_path)
                origin = repo.remotes.origin
                origin.pull()
            else:
                # Clone repository
                logger.info("policy_repo_sync", action="cloning", url=self.policy_repo_url)
                git.Repo.clone_from(self.policy_repo_url, self.policy_repo_path)
            
            logger.info("policy_repo_sync", status="success")
            
        except Exception as e:
            logger.error("policy_repo_sync", error=str(e))
            raise
    
    async def _build_index(self):
        """Build FAISS index from policy documents"""
        try:
            # Load markdown documents from repository
            policy_files = list(self.policy_repo_path.glob("*.md"))
            
            # Exclude README and LICENSE
            policy_files = [
                f for f in policy_files 
                if f.name.lower() not in ["readme.md", "license.md"]
            ]
            
            logger.info("policy_index_build", file_count=len(policy_files))
            
            documents = []
            for policy_file in policy_files:
                try:
                    with open(policy_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract policy metadata from filename and content
                    policy_name = policy_file.stem
                    policy_category = self._categorize_policy(policy_name, content)
                    
                    # Split into chunks
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=settings.POLICY_CHUNK_SIZE,
                        chunk_overlap=settings.POLICY_CHUNK_OVERLAP,
                        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
                    )
                    
                    chunks = text_splitter.split_text(content)
                    
                    # Create documents with metadata
                    for i, chunk in enumerate(chunks):
                        documents.append({
                            "content": chunk,
                            "metadata": {
                                "source": policy_name,
                                "category": policy_category,
                                "chunk_id": i,
                                "file_path": str(policy_file.relative_to(self.policy_repo_path))
                            }
                        })
                    
                    logger.info(
                        "policy_file_processed", 
                        file=policy_name, 
                        chunks=len(chunks)
                    )
                    
                except Exception as e:
                    logger.error("policy_file_error", file=str(policy_file), error=str(e))
            
            if not documents:
                logger.error("policy_index_build", error="No policy documents found")
                raise ValueError("No policy documents found in repository")
            
            self.documents = documents
            
            # Create FAISS vectorstore
            texts = [doc["content"] for doc in documents]
            metadatas = [doc["metadata"] for doc in documents]
            
            logger.info("policy_index_build", action="creating_embeddings", count=len(texts))
            self.vectorstore = FAISS.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas
            )
            
            # Save index
            self.vectorstore.save_local(str(self.faiss_index_path))
            logger.info("policy_index_build", status="success", chunks=len(documents))
            
        except Exception as e:
            logger.error("policy_index_build", error=str(e))
            raise
    
    def _categorize_policy(self, filename: str, content: str) -> str:
        """Categorize policy document based on filename and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Category mapping
        if "incident" in filename_lower or "incident response" in content_lower:
            return "incident_response"
        elif "vulnerability" in filename_lower or "vulnerability management" in content_lower:
            return "vulnerability_management"
        elif "information security" in filename_lower or "infosec" in filename_lower:
            return "information_security"
        elif "data" in filename_lower and ("classification" in filename_lower or "security" in content_lower):
            return "data_security"
        elif "access" in content_lower and "control" in content_lower:
            return "access_control"
        elif "business continuity" in content_lower or "disaster recovery" in content_lower:
            return "business_continuity"
        elif "acceptable use" in content_lower or "aup" in filename_lower:
            return "acceptable_use"
        else:
            return "general"
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search policy documents by query
        
        Args:
            query: Search query
            top_k: Number of results to return
            category: Optional policy category filter
            
        Returns:
            List of matching policy excerpts with metadata
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Build filter if category specified
            filter_dict = {"category": category} if category else None
            
            # Perform similarity search
            docs = self.vectorstore.similarity_search_with_score(
                query, 
                k=top_k * 2 if category else top_k,  # Get more if filtering
                filter=filter_dict
            )
            
            # Format results
            results = []
            for doc, score in docs[:top_k]:
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "category": doc.metadata.get("category", "general"),
                    "file_path": doc.metadata.get("file_path", ""),
                    "similarity_score": float(1 - score),  # Convert distance to similarity
                })
            
            logger.info("policy_search", query=query[:50], results=len(results))
            return results
            
        except Exception as e:
            logger.error("policy_search", error=str(e))
            raise
    
    async def search_by_category(
        self, 
        category: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get policy documents by category
        
        Args:
            category: Policy category (incident_response, vulnerability_management, etc.)
            top_k: Number of results to return
            
        Returns:
            List of policy documents in category
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get all documents in category
            filtered_docs = [
                doc for doc in self.documents 
                if doc["metadata"].get("category") == category
            ]
            
            # Return top_k
            results = []
            for doc in filtered_docs[:top_k]:
                results.append({
                    "content": doc["content"],
                    "source": doc["metadata"].get("source", "unknown"),
                    "category": doc["metadata"].get("category", "general"),
                    "file_path": doc["metadata"].get("file_path", ""),
                })
            
            logger.info("policy_category_search", category=category, results=len(results))
            return results
            
        except Exception as e:
            logger.error("policy_category_search", error=str(e))
            raise
    
    async def get_policy_document(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """
        Get full policy document by name
        
        Args:
            policy_name: Policy document name (without .md extension)
            
        Returns:
            Policy document with metadata
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Find policy file
            policy_file = self.policy_repo_path / f"{policy_name}.md"
            
            if not policy_file.exists():
                logger.warning("policy_get_document", policy=policy_name, status="not_found")
                return None
            
            # Read full content
            with open(policy_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            category = self._categorize_policy(policy_name, content)
            
            return {
                "name": policy_name,
                "content": content,
                "category": category,
                "file_path": str(policy_file.relative_to(self.policy_repo_path))
            }
            
        except Exception as e:
            logger.error("policy_get_document", error=str(e))
            raise
    
    async def list_categories(self) -> List[Dict[str, Any]]:
        """
        List all policy categories with document counts
        
        Returns:
            List of categories with counts
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Count documents by category
            category_counts = {}
            for doc in self.documents:
                category = doc["metadata"].get("category", "general")
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Format results
            categories = [
                {"category": cat, "document_count": count}
                for cat, count in category_counts.items()
            ]
            
            return sorted(categories, key=lambda x: x["category"])
            
        except Exception as e:
            logger.error("policy_list_categories", error=str(e))
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get policy RAG statistics"""
        if not self.initialized:
            await self.initialize()
        
        return {
            "status": "ready" if self.initialized else "not_initialized",
            "document_count": len(self.documents),
            "indexed": self.vectorstore is not None,
            "repository": self.policy_repo_url,
            "cache_dir": str(self.policy_cache_dir)
        }


# Global service instance
_policy_rag_service = None


def get_policy_rag_service() -> PolicyRagService:
    """Get or create policy RAG service singleton"""
    global _policy_rag_service
    if _policy_rag_service is None:
        _policy_rag_service = PolicyRagService()
    return _policy_rag_service
