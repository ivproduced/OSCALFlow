"""
NIST RAG Service - Specialized RAG for NIST cybersecurity standards
Integrates HuggingFace dataset (596 publications, 530K+ examples) with FedChat
Based on: https://github.com/euCann/nist-rag-agent
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import logging

from datasets import load_dataset
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from backend.core.config import settings

logger = logging.getLogger(__name__)


class NistRagService:
    """
    Service for querying NIST cybersecurity standards using RAG
    
    Features:
    - 596 NIST publications (SP 800, FIPS, CSWP, SP 1800, IR series)
    - 530K+ training examples from HuggingFace
    - FAISS vector search with caching
    - CSF 2.0, Zero Trust Architecture, Post-Quantum Cryptography
    """
    
    def __init__(
        self,
        cache_dir: str = None,
        use_huggingface: bool = True,
        embedding_model: str = None
    ):
        self.cache_dir = Path(cache_dir or settings.NIST_RAG_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_huggingface = use_huggingface and settings.NIST_USE_HUGGINGFACE
        self.embedding_model = embedding_model or settings.NIST_EMBEDDING_MODEL
        self.vectorstore = None
        
        # Initialize on first use
        self._initialized = False
        
        logger.info(f"NIST RAG Service configured: cache_dir={self.cache_dir}, use_hf={self.use_huggingface}")
    
    async def initialize(self):
        """Initialize NIST RAG system (lazy loading)"""
        if self._initialized:
            return
            
        logger.info("Initializing NIST RAG Service...")
        
        try:
            # Check for cached FAISS index
            index_path = self.cache_dir / "faiss_index"
            
            if index_path.exists():
                logger.info("Loading cached NIST FAISS index...")
                embeddings = OpenAIEmbeddings(
                    model=self.embedding_model,
                    openai_api_key=settings.OPENAI_API_KEY
                )
                self.vectorstore = FAISS.load_local(
                    str(index_path),
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"Cached index loaded successfully ({self.vectorstore.index.ntotal} vectors)")
            else:
                logger.info("No cached index found. Building from HuggingFace dataset...")
                await self._build_index()
            
            self._initialized = True
            logger.info("NIST RAG Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NIST RAG Service: {e}", exc_info=True)
            raise
    
    async def _build_index(self):
        """Build FAISS index from HuggingFace dataset"""
        logger.info("Downloading NIST dataset from HuggingFace...")
        logger.info("This may take 10-20 minutes on first run (downloading ~7GB dataset)")
        
        # Load dataset
        dataset = load_dataset(
            "ethanolivertroy/nist-cybersecurity-training",
            split="train",  # 424K examples
            cache_dir=str(self.cache_dir / "huggingface")
        )
        
        logger.info(f"Dataset loaded: {len(dataset)} examples")
        
        # Convert to LangChain documents
        documents = []
        for idx, item in enumerate(dataset):
            if idx % 10000 == 0:
                logger.info(f"Processing document {idx}/{len(dataset)}")
            
            # Extract text content
            text = item.get("text", "")
            if not text or len(text.strip()) < 50:
                continue
            
            doc = Document(
                page_content=text,
                metadata={
                    "source": item.get("source", ""),
                    "document_id": item.get("document_id", ""),
                    "section": item.get("section", ""),
                    "control_id": item.get("control_id", ""),
                    "type": item.get("type", ""),
                    "url": item.get("url", ""),
                }
            )
            documents.append(doc)
        
        logger.info(f"Creating FAISS index from {len(documents)} documents...")
        
        # Create embeddings and FAISS index
        embeddings = OpenAIEmbeddings(
            model=self.embedding_model,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Build index in batches to avoid memory issues
        batch_size = 1000
        self.vectorstore = None
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(documents)//batch_size) + 1}")
            
            if self.vectorstore is None:
                self.vectorstore = await FAISS.afrom_documents(batch, embeddings)
            else:
                batch_store = await FAISS.afrom_documents(batch, embeddings)
                self.vectorstore.merge_from(batch_store)
        
        # Save index for future use
        index_path = self.cache_dir / "faiss_index"
        self.vectorstore.save_local(str(index_path))
        
        logger.info(f"FAISS index created and cached successfully ({self.vectorstore.index.ntotal} vectors)")
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search NIST documents using semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filters (e.g., {"control_id": "AC-2"})
            similarity_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of search results with content and metadata
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Perform similarity search with scores
            results_with_scores = await self.vectorstore.asimilarity_search_with_score(
                query,
                k=top_k * 2,  # Get extra to filter by threshold
                filter=filter_dict
            )
            
            # Filter by similarity threshold and format results
            formatted_results = []
            for doc, score in results_with_scores:
                # Convert distance to similarity (FAISS returns L2 distance)
                similarity = 1 / (1 + score)
                
                if similarity >= similarity_threshold:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": doc.metadata.get("source", ""),
                        "document_id": doc.metadata.get("document_id", ""),
                        "control_id": doc.metadata.get("control_id", ""),
                        "section": doc.metadata.get("section", ""),
                        "type": doc.metadata.get("type", ""),
                        "url": doc.metadata.get("url", ""),
                        "similarity_score": float(similarity)
                    })
                
                if len(formatted_results) >= top_k:
                    break
            
            logger.info(f"NIST search for '{query[:50]}...' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"NIST RAG search failed: {e}", exc_info=True)
            return []
    
    async def search_by_control(
        self,
        control_id: str,
        top_k: int = 3
    ) -> List[Dict]:
        """Search for specific NIST control (e.g., AC-2, IR-4, SC-7)"""
        logger.info(f"Searching for NIST control: {control_id}")
        return await self.search(
            query=f"NIST control {control_id} requirements implementation",
            top_k=top_k,
            filter_dict={"control_id": control_id.upper()}
        )
    
    async def search_by_document(
        self,
        document_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """Search within a specific NIST document (e.g., SP 800-53, SP 800-171)"""
        logger.info(f"Searching in document {document_id}: {query[:50]}")
        return await self.search(
            query=query,
            top_k=top_k,
            filter_dict={"document_id": document_id}
        )
    
    async def search_csf(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """Search NIST Cybersecurity Framework 2.0"""
        return await self.search(
            query=f"NIST Cybersecurity Framework {query}",
            top_k=top_k,
            filter_dict={"document_id": "CSF-2.0"}
        )
    
    async def search_zero_trust(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """Search NIST Zero Trust Architecture (SP 800-207)"""
        return await self.search(
            query=f"Zero Trust Architecture {query}",
            top_k=top_k,
            filter_dict={"document_id": "SP-800-207"}
        )
    
    def get_stats(self) -> Dict:
        """Get statistics about the NIST RAG system"""
        if not self._initialized or not self.vectorstore:
            return {
                "initialized": False,
                "total_documents": 0,
                "cache_dir": str(self.cache_dir),
                "embedding_model": self.embedding_model
            }
        
        return {
            "initialized": True,
            "total_vectors": self.vectorstore.index.ntotal,
            "embedding_model": self.embedding_model,
            "cache_dir": str(self.cache_dir),
            "dataset": "ethanolivertroy/nist-cybersecurity-training",
            "publications": 596,
            "examples": "530K+",
            "coverage": [
                "SP 800 Series (Security Controls, Risk Management, etc.)",
                "FIPS (Federal Information Processing Standards)",
                "CSWP (CSF 2.0, Zero Trust, Post-Quantum Crypto)",
                "SP 1800 Series (Practice Guides)",
                "IR Series (Interagency Reports)"
            ]
        }


# Global instance
nist_rag_service = NistRagService()
