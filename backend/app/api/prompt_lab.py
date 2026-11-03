"""Prompt Engineering Lab API endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.schemas.prompt_lab import (
    PromptCapabilitiesResponse,
    PromptLabRequest,
    PromptLabResponse,
)
from app.services.gemini_service import gemini_service

router = APIRouter(prefix="/prompt", tags=["Prompt Lab"])


@router.get("/capabilities", response_model=PromptCapabilitiesResponse)
def get_prompt_capabilities():
    """Report backend support for temperature and token adjustments."""
    return PromptCapabilitiesResponse(temperature=True, maxTokens=True)


@router.post("/run", response_model=PromptLabResponse)
async def run_prompt_lab(req: PromptLabRequest):
    """Run prompt with specific prompt engineering technique."""
    user_prompt = req.get_user_prompt()
    if not user_prompt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty.",
        )

    # Build prompt and system instructions according to technique
    system_inst = req.system or ""
    if req.technique == "role" and req.role:
        system_inst = f"You are {req.role}. {system_inst}".strip()

    final_user_prompt = user_prompt

    if req.technique == "few-shot" and req.examples:
        example_strs = []
        for i, ex in enumerate(req.examples, 1):
            example_strs.append(f"Example {i}:\nInput: {ex.input}\nOutput: {ex.output}")
        examples_block = "\n\n".join(example_strs)
        final_user_prompt = f"{examples_block}\n\nTask Input: {user_prompt}\nTask Output:"

    elif req.technique == "structured" and req.output_format:
        final_user_prompt = (
            f"{user_prompt}\n\nYou MUST format your response strictly according to this schema:\n"
            f"{req.output_format}"
        )

    elif req.technique == "step-by-step":
        final_user_prompt = (
            f"{user_prompt}\n\nPlease think step by step, showing each reasoning stage clearly "
            "before arriving at your final conclusion."
        )

    try:
        response_text = await gemini_service.generate_text(
            prompt=final_user_prompt,
            system_instruction=system_inst if system_inst else None,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt execution failed: {str(e)}",
        )

    is_demo = not gemini_service.is_available()

    return PromptLabResponse(
        response=response_text,
        technique=req.technique,
        demo=is_demo,
    )
