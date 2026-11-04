"""Generative AI Chat API endpoints using Google Gemini."""

import logging
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user_optional
from app.database.connection import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.gemini_service import gemini_service
from app.services.rag_service import rag_service
from app.services.web_search_service import web_search_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


@router.get("/models")
def list_available_models():
    """List available Gemini and assistant models for chat."""
    return [
        {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash (Fast, Multimodal, Recommended)"},
        {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro (Complex Reasoning)"},
        {"id": "gemini-1.5-flash", "label": "Gemini 1.5 Flash (High Speed)"},
        {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash (Next-Gen Multimodal)"},
    ]


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Generate context-aware AI responses using Google Gemini API."""
    user_message = req.get_message_content()
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty.",
        )

    conversation_id = req.get_conversation_id()
    model_name = req.model or settings.DEFAULT_MODEL
    user_id = current_user.id if current_user else None

    # Load or create conversation record
    conv = None
    if conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()

    if not conv:
        # Generate new conversation ID
        new_conv_id = conversation_id or str(uuid.uuid4())
        conv = Conversation(
            id=new_conv_id,
            user_id=user_id,
            title=user_message[:48] if user_message else "New conversation",
            model=model_name,
            system_instruction=req.system_instruction,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Gather auxiliary context (RAG or Web Search)
    sources: List[Dict[str, Any]] = []
    grounded_context_prefix = ""

    if req.get_use_web_research():
        try:
            search_result = await web_search_service.search_and_ground(
                query=user_message,
                depth="standard",
                max_results=4,
            )
            sources.extend(search_result.get("sources", []))
            if sources:
                grounded_context_prefix += (
                    f"\n[LIVE WEB SEARCH EVIDENCE]:\n{search_result.get('summary', '')}\n"
                )
        except Exception as e:
            logger.warning(f"Web research toggle error: {e}")

    if req.get_use_documents():
        try:
            rag_result = await rag_service.query_relevant_chunks(
                query=user_message,
                top_k=4,
                user_id=user_id,
            )
            if rag_result:
                sources.extend(rag_result)
                doc_snippets = "\n".join(
                    f"[{c['document_name']} Page {c.get('page', 1)}]: {c['snippet']}"
                    for c in rag_result
                )
                grounded_context_prefix += f"\n[DOCUMENT EVIDENCE]:\n{doc_snippets}\n"
        except Exception as e:
            logger.warning(f"RAG document query error: {e}")

    # Build messages history for Gemini
    formatted_messages: List[Dict[str, str]] = []

    # If frontend provided explicit message history array
    if req.messages and len(req.messages) > 0:
        for m in req.messages:
            formatted_messages.append({"role": m.role, "content": m.content})
    else:
        # Load from database messages history
        past_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        for pm in past_messages:
            formatted_messages.append({"role": pm.role, "content": pm.content})

        # Append current user prompt
        full_user_content = user_message
        if grounded_context_prefix:
            full_user_content = f"{grounded_context_prefix}\n\nUser Question: {user_message}"

        formatted_messages.append({"role": "user", "content": full_user_content})

    # Call Gemini model
    system_inst = req.system_instruction or conv.system_instruction or (
        "You are DARZFUSION AI, a state-of-the-art multimodal AI assistant. "
        "Provide thorough, articulate, helpful, and grounded answers. "
        "If sources or citations are provided, reference them clearly."
    )

    try:
        assistant_text = await gemini_service.chat(
            messages=formatted_messages,
            model_name=model_name,
            system_instruction=system_inst,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as e:
        logger.error(f"Chat generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI generation failed: {str(e)}",
        )

    # Persist user message and assistant reply to database
    try:
        user_db_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="user",
            content=user_message,
            attachments=req.attachments or [],
        )
        assistant_db_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=conv.id,
            role="assistant",
            content=assistant_text,
            sources=sources,
        )
        db.add(user_db_msg)
        db.add(assistant_db_msg)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to record message history in DB: {e}")
        db.rollback()

    is_demo = not gemini_service.is_available()

    return ChatResponse(
        answer=assistant_text,
        content=assistant_text,
        conversation_id=conv.id,
        sources=sources,
        model=model_name,
        demo=is_demo,
    )


@router.post("/chat/feedback")
def submit_chat_feedback(
    feedback_data: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """Record user feedback (thumbs up / thumbs down) on conversation messages."""
    message_id = feedback_data.get("message_id") or feedback_data.get("messageId")
    feedback_value = feedback_data.get("feedback")  # "up" or "down"

    if message_id:
        msg = db.query(Message).filter(Message.id == message_id).first()
        if msg:
            msg.feedback = feedback_value
            db.commit()

    return {"status": "ok", "message": "Feedback recorded"}
