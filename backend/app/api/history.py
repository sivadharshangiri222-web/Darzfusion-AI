"""Conversation history management API endpoints."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user_optional
from app.database.connection import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.history import (
    ConversationCreate,
    ConversationDetail,
    ConversationRename,
    ConversationSummary,
    MessageItem,
)

router = APIRouter(prefix="/history", tags=["History"])


@router.get("", response_model=List[ConversationSummary])
def list_conversations(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """List conversations for the current user, ordered by most recently updated."""
    query = db.query(Conversation)
    if current_user:
        query = query.filter(
            (Conversation.user_id == current_user.id) | (Conversation.user_id == None)
        )
    else:
        query = query.filter(Conversation.user_id == None)

    conversations = query.order_by(Conversation.updated_at.desc()).all()
    results = []
    for c in conversations:
        msg_count = db.query(Message).filter(Message.conversation_id == c.id).count()
        results.append(
            ConversationSummary(
                id=c.id,
                title=c.title,
                model=c.model,
                createdAt=c.created_at,
                updatedAt=c.updated_at,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=msg_count,
            )
        )
    return results


@router.post("", response_model=ConversationDetail, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_data: ConversationCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Create a new conversation."""
    user_id = current_user.id if current_user else None
    conv = Conversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=conv_data.title or "New conversation",
        model=conv_data.model or "gemini-2.5-flash",
        system_instruction=conv_data.system_instruction,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        model=conv.model,
        system_instruction=conv.system_instruction,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[],
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve full conversation history and messages with ownership enforcement."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    # Ownership check
    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this conversation.",
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    msg_items = [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources or [],
            attachments=m.attachments or [],
            feedback=m.feedback,
            createdAt=m.created_at,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return ConversationDetail(
        id=conv.id,
        title=conv.title,
        model=conv.model,
        system_instruction=conv.system_instruction,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=msg_items,
    )


@router.patch("/{conversation_id}", response_model=ConversationSummary)
def rename_conversation(
    conversation_id: str,
    rename_data: ConversationRename,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Rename a conversation."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this conversation.",
        )

    conv.title = rename_data.title.strip() or conv.title
    db.commit()
    db.refresh(conv)

    msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()
    return ConversationSummary(
        id=conv.id,
        title=conv.title,
        model=conv.model,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=msg_count,
    )


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this conversation.",
        )

    db.delete(conv)
    db.commit()
    return {"id": conversation_id, "deleted": True}


@router.delete("/{conversation_id}/clear")
def clear_conversation_messages(
    conversation_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Clear all messages within a conversation while keeping the session."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    if current_user and conv.user_id and conv.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to clear this conversation.",
        )

    db.query(Message).filter(Message.conversation_id == conv.id).delete()
    conv.title = "New conversation"
    db.commit()
    return {"id": conversation_id, "cleared": True}
