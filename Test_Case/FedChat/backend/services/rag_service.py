"""
RAG Service - Document processing and retrieval
"""

from typing import List, Dict, Any, Optional
import structlog
from pathlib import Path
from datetime import datetime
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_community.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

from core.config import settings
from models import Document, DocumentChunk

logger = structlog.get_logger()


class RAGService:
    """Service for RAG document processing and retrieval"""
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        
        # Initialize embeddings model
        self.embeddings = OllamaEmbeddings(
            base_url=settings.LOCAL_LLM_BASE_URL,
            model=settings.LOCAL_EMBEDDING_MODEL,
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        
        logger.info("rag_service_initialized", chunk_size=settings.RAG_CHUNK_SIZE)
    
    async def process_document(
        self,
        file_path: str,
        filename: str,
        user_id: uuid.UUID,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> uuid.UUID:
        """
        Process and embed a document
        
        Args:
            file_path: Path to document file
            filename: Original filename
            user_id: User who uploaded the document
            metadata: Optional metadata dict
        
        Returns:
            Document UUID
        """
        if not self.db:
            raise ValueError("Database session required for document processing")
        
        try:
            # Load document based on file type
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == ".pdf":
                loader = PyPDFLoader(file_path)
            elif file_ext in [".docx", ".doc"]:
                loader = Docx2txtLoader(file_path)
            elif file_ext == ".md":
                loader = UnstructuredMarkdownLoader(file_path)
            elif file_ext == ".txt":
                loader = TextLoader(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # Load and split document
            raw_documents = loader.load()
            chunks = self.text_splitter.split_documents(raw_documents)
            
            # Create document record
            document = Document(
                filename=filename,
                file_type=file_ext,
                file_size=Path(file_path).stat().st_size,
                uploaded_by=user_id,
                chunk_count=len(chunks),
                metadata_=metadata or {}
            )
            
            self.db.add(document)
            await self.db.flush()  # Get document ID
            
            # Generate embeddings and create chunks
            for idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding_vector = await self._generate_embedding(chunk.page_content)
                
                # Create chunk record
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    content=chunk.page_content,
                    embedding=embedding_vector,
                    metadata_={
                        "source": filename,
                        "file_type": file_ext,
                        "page": chunk.metadata.get("page", 0),
                        **(metadata or {})
                    }
                )
                self.db.add(doc_chunk)
            
            await self.db.commit()
            await self.db.refresh(document)
            
            logger.info(
                "document_processed",
                document_id=str(document.id),
                filename=filename,
                chunks=len(chunks),
                file_type=file_ext,
            )
            
            return document.id
            
        except Exception as e:
            await self.db.rollback()
            logger.error("document_processing_error", error=str(e), filename=filename)
            raise
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error("embedding_generation_error", error=str(e))
            # Fallback to sync method if async fails
            return self.embeddings.embed_query(text)
    
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
        
        Returns:
            List of search results with content and metadata
        """
        if not self.db:
            raise ValueError("Database session required for search")
        
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Perform vector similarity search using pgvector
            # Note: This uses PostgreSQL's <-> operator for cosine distance
            from sqlalchemy import text
            
            sql = text("""
                SELECT 
                    dc.id,
                    dc.content,
                    dc.metadata_,
                    dc.chunk_index,
                    d.filename,
                    d.file_type,
                    (dc.embedding <-> :query_embedding::vector) as distance
                FROM document_chunks dc
                JOIN documents d ON dc.document_id = d.id
                WHERE d.is_active = true
                ORDER BY distance
                LIMIT :limit
            """)
            
            result = await self.db.execute(
                sql,
                {
                    "query_embedding": str(query_embedding),
                    "limit": top_k
                }
            )
            
            # Format results
            results = []
            for row in result:
                # Convert distance to similarity score (0-1, higher is better)
                similarity_score = 1 / (1 + row.distance)
                
                if similarity_score >= settings.RAG_SIMILARITY_THRESHOLD:
                    results.append({
                        "chunk_id": str(row.id),
                        "content": row.content,
                        "metadata": row.metadata_,
                        "chunk_index": row.chunk_index,
                        "source": row.filename,
                        "file_type": row.file_type,
                        "score": float(similarity_score),
                        "distance": float(row.distance),
                    })
            
            logger.info(
                "rag_search_complete",
                query=query[:100],
                results_count=len(results),
            )
            
            return results
            
        except Exception as e:
            logger.error("rag_search_error", error=str(e), query=query[:100])
            raise
    
    async def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get document by ID"""
        if not self.db:
            raise ValueError("Database session required")
        
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()
    
    async def list_documents(
        self,
        user_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List documents"""
        if not self.db:
            raise ValueError("Database session required")
        
        query = select(Document).where(Document.is_active == True)
        
        if user_id:
            query = query.where(Document.uploaded_by == user_id)
        
        query = query.order_by(Document.uploaded_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """
        Delete a document and its embeddings
        
        Args:
            document_id: Document UUID
        
        Returns:
            Success boolean
        """
        if not self.db:
            raise ValueError("Database session required")
        
        try:
            # Soft delete - mark as inactive
            result = await self.db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                return False
            
            document.is_active = False
            await self.db.commit()
            
            logger.info("document_deleted", document_id=str(document_id))
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("document_deletion_error", error=str(e))
            raise
    
    async def hard_delete_document(self, document_id: uuid.UUID) -> bool:
        """
        Permanently delete a document and all its chunks
        
        Args:
            document_id: Document UUID
        
        Returns:
            Success boolean
        """
        if not self.db:
            raise ValueError("Database session required")
        
        try:
            # Delete all chunks (cascade delete should handle this, but being explicit)
            await self.db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            
            # Delete document
            await self.db.execute(
                delete(Document).where(Document.id == document_id)
            )
            
            await self.db.commit()
            
            logger.info("document_hard_deleted", document_id=str(document_id))
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error("document_hard_deletion_error", error=str(e))
            raise
