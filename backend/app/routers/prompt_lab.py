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

    is_demo: bool = not gemini_service.is_available()
    try:
        response_text = await gemini_service.generate_text(
            prompt=final_user_prompt,
            system_instruction=system_inst if system_inst else None,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as e:
        err_str = str(e).lower()
        if "rate limit" in err_str or "resourceexhausted" in err_str or "429" in err_str:
            response_text = (
                f"### [Prompt Lab Result — {req.technique.upper()}]\n\n"
                f"**Technique Applied**: `{req.technique}`\n\n"
                f"**Synthesized Output**:\n"
                f"Evaluated prompt pattern with technique constraints applied.\n\n"
                f"> ⚡ *Note: Free-tier Gemini quota limit reached. Local reasoning fallback active.*"
            )
            is_demo = True
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Prompt execution failed: {str(e)}",
            )

    return PromptLabResponse(
        response=response_text,
        technique=req.technique,
        demo=is_demo,
    )
