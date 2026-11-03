"""RAG service managing ChromaDB vector store, semantic search, and grounded Gemini answers."""

import logging
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.services.embedding_service import embedding_service
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class RAGService:
    """Manages ChromaDB vector indexing and retrieval-augmented generation."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = "darzfusion_documents"
        self._collection = None

    def get_collection(self):
        """Lazy loader for ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    async def index_document_chunks(
        self,
        document_id: str,
        document_name: str,
        chunks: List[Dict[str, Any]],
        user_id: Optional[str] = None,
    ) -> int:
        """Embed and store document chunks into ChromaDB."""
        if not chunks:
            return 0

        collection = self.get_collection()
        texts = [c["text"] for c in chunks]
        embeddings = await embedding_service.get_embeddings(texts, task_type="retrieval_document")

        ids = [f"{document_id}_chunk_{c['chunk_index']}" for c in chunks]
        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "page": int(c.get("page", 1)),
                "chunk_index": int(c.get("chunk_index", 0)),
                "user_id": str(user_id or "public"),
            }
            for c in chunks
        ]

        # Add in batches of 100 to avoid limits
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            collection.upsert(
                ids=ids[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                documents=texts[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

        logger.info(f"Indexed {len(chunks)} chunks for document {document_id} ({document_name})")
        return len(chunks)

    async def query_relevant_chunks(
        self,
        query: str,
        top_k: int = 4,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve the most semantically relevant chunks for a question."""
        collection = self.get_collection()
        query_embedding = await embedding_service.get_embedding(query, task_type="retrieval_query")

        # Build ChromaDB metadata filter
        where_filter: Optional[Dict[str, Any]] = None
        filters = []

        if document_id:
            filters.append({"document_id": document_id})
        elif document_ids:
            if len(document_ids) == 1:
                filters.append({"document_id": document_ids[0]})
            else:
                filters.append({"document_id": {"$in": document_ids}})

        if user_id:
            # Users can see their own documents or public ones
            filters.append({"user_id": {"$in": [user_id, "public"]}})

        if len(filters) == 1:
            where_filter = filters[0]
        elif len(filters) > 1:
            where_filter = {"$and": filters}

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return []

        chunks: List[Dict[str, Any]] = []
        if not results or not results["documents"] or not results["documents"][0]:
            return chunks

        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for i in range(len(docs)):
            meta = metas[i] if i < len(metas) else {}
            dist = distances[i] if i < len(distances) else 1.0
            # Cosine distance to similarity score
            score = round(max(0.0, 1.0 - dist), 4)

            chunks.append(
                {
                    "document_id": meta.get("document_id", ""),
                    "document_name": meta.get("document_name", "Document"),
                    "page": meta.get("page"),
                    "chunk_index": meta.get("chunk_index"),
                    "snippet": docs[i],
                    "score": score,
                }
            )

        return chunks

    async def answer_with_rag(
        self,
        query: str,
        document_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        top_k: int = 4,
    ) -> Dict[str, Any]:
        """Perform full RAG pipeline: retrieval + Gemini grounded answer generation."""
        retrieved_chunks = await self.query_relevant_chunks(
            query=query,
            top_k=top_k,
            document_id=document_id,
            document_ids=document_ids,
            user_id=user_id,
        )

        if not retrieved_chunks:
            return {
                "answer": (
                    "No relevant document content was found to answer your question. "
                    "Please upload relevant documents or check that the selected documents contain related information."
                ),
                "sources": [],
                "has_sufficient_context": False,
                "query": query,
            }

        # Format context for Gemini
        context_blocks = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            doc_name = chunk["document_name"]
            page_info = f" (Page {chunk['page']})" if chunk.get("page") else ""
            context_blocks.append(
                f"--- SOURCE [{i}]: {doc_name}{page_info} ---\n{chunk['snippet']}"
            )

        context_text = "\n\n".join(context_blocks)

        system_instruction = (
            "You are DARZFUSION AI's Retrieval-Augmented Generation (RAG) assistant. "
            "Answer the user's question based strictly on the provided context passages below. "
            "Rules:\n"
            "1. Ground your answer in the provided evidence.\n"
            "2. When stating facts, cite the source document name and page number if available (e.g., [Source 1, Document.pdf, Page 3]).\n"
            "3. If the provided context does not contain enough information to answer the question, state: "
            "'The provided document(s) do not contain sufficient information to answer this question.'\n"
            "4. Do not invent information or extrapolate beyond the provided text."
        )

        prompt = (
            f"DOCUMENT CONTEXT:\n{context_text}\n\n"
            f"USER QUESTION:\n{query}\n\n"
            f"ANSWER:"
        )

        answer = await gemini_service.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2,  # Low temperature for factual precision
        )

        return {
            "answer": answer,
            "sources": retrieved_chunks,
            "has_sufficient_context": True,
            "query": query,
        }

    async def delete_document_chunks(self, document_id: str) -> None:
        """Remove all chunks associated with a document from ChromaDB."""
        try:
            collection = self.get_collection()
            collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector chunks for document: {document_id}")
        except Exception as e:
            logger.warning(f"Error deleting chunks for document {document_id}: {e}")


rag_service = RAGService()
