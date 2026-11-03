"""Document management and upload API endpoints."""

import os
import shutil
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user_optional
from app.database.connection import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentDeleteResponse, DocumentResponse
from app.services.document_service import document_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Upload, extract, clean, chunk, and index a document (PDF, TXT, DOCX)."""
    # 1. Validate file extension and clean filename
    safe_filename, file_ext = document_service.validate_file(file)

    # 2. Check file size during streaming write to disk
    doc_id = str(uuid.uuid4())
    stored_filename = f"{doc_id}_{safe_filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    total_bytes = 0
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    buffer.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum size limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )

    # 3. Extract text from file
    try:
        pages_content = document_service.extract_text(file_path, file_ext)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract text: {str(e)}",
        )

    page_count = len(pages_content)

    # 4. Chunk document preserving page metadata
    chunks = document_service.chunk_document(pages_content, chunk_size=900, chunk_overlap=150)
    chunk_count = len(chunks)

    # 5. Index into ChromaDB vector store
    user_id = current_user.id if current_user else None
    try:
        await rag_service.index_document_chunks(
            document_id=doc_id,
            document_name=safe_filename,
            chunks=chunks,
            user_id=user_id,
        )
    except Exception as e:
        # Don't fail the whole upload if vector store indexing encounters issue
        logger_error = str(e)

    # 6. Save document record in relational database
    db_doc = Document(
        id=doc_id,
        user_id=user_id,
        filename=stored_filename,
        original_filename=safe_filename,
        file_path=file_path,
        file_type=file_ext.lstrip("."),
        file_size=total_bytes,
        page_count=page_count,
        chunk_count=chunk_count,
        status="ready",
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    return DocumentResponse(
        id=db_doc.id,
        name=db_doc.original_filename,
        original_filename=db_doc.original_filename,
        file_type=db_doc.file_type,
        size=db_doc.file_size,
        page_count=db_doc.page_count,
        chunk_count=db_doc.chunk_count,
        status=db_doc.status,
        progress=100,
        uploadedAt=db_doc.created_at,
        created_at=db_doc.created_at,
        error_message=db_doc.error_message,
        demo=False,
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """List documents accessible to the current user."""
    query = db.query(Document)
    if current_user:
        query = query.filter((Document.user_id == current_user.id) | (Document.user_id == None))
    else:
        query = query.filter(Document.user_id == None)

    docs = query.order_by(Document.created_at.desc()).all()
    return [
        DocumentResponse(
            id=d.id,
            name=d.original_filename,
            original_filename=d.original_filename,
            file_type=d.file_type,
            size=d.file_size,
            page_count=d.page_count,
            chunk_count=d.chunk_count,
            status=d.status,
            progress=100,
            uploadedAt=d.created_at,
            created_at=d.created_at,
            error_message=d.error_message,
            demo=False,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific document with ownership check."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Ownership check
    if current_user and doc.user_id and doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this document.",
        )

    return DocumentResponse(
        id=doc.id,
        name=doc.original_filename,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        size=doc.file_size,
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        status=doc.status,
        progress=100,
        uploadedAt=doc.created_at,
        created_at=doc.created_at,
        error_message=doc.error_message,
        demo=False,
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Delete a document from database, ChromaDB vector store, and filesystem."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    # Enforce ownership check
    if current_user and doc.user_id and doc.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document.",
        )

    # 1. Delete ChromaDB vector embeddings
    await rag_service.delete_document_chunks(doc.id)

    # 2. Delete file from storage
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 3. Delete from database
    db.delete(doc)
    db.commit()

    return DocumentDeleteResponse(id=document_id, deleted=True)
