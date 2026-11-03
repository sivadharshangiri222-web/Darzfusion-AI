"""AI Study Tools service for notes, summaries, quizzes, flashcards, and concept explanations."""

import json
import logging
from typing import Any, Dict, List, Optional
from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class StudyService:
    """Provides AI study tools powered by Google Gemini."""

    async def summarize(self, text: str, length: str = "medium") -> Dict[str, Any]:
        """Summarize text with specified length."""
        length_guidelines = {
            "short": "Provide a concise 1-paragraph summary (under 80 words) and 3 key takeaways.",
            "medium": "Provide a clear 2-3 paragraph summary and 4-5 bulleted key takeaways.",
            "long": "Provide a comprehensive, detailed multi-section summary with extensive takeaways.",
        }
        guide = length_guidelines.get(length, length_guidelines["medium"])

        prompt = (
            f"TEXT TO SUMMARIZE:\n\"\"\"{text}\"\"\"\n\n"
            f"INSTRUCTIONS:\n{guide}\n\n"
            "Format your output clearly with a Summary section followed by a 'Key Takeaways:' bulleted list."
        )

        response = await gemini_service.generate_text(
            prompt=prompt,
            system_instruction="You are an expert academic and professional summarization assistant.",
            temperature=0.3,
        )

        takeaways = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                takeaways.append(line[2:])

        return {
            "summary": response,
            "key_takeaways": takeaways,
            "word_count": len(text.split()),
        }

    async def generate_notes(self, text: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Convert raw text or study material into clean structured Markdown study notes."""
        suggested_title = title or "Study Notes"

        prompt = (
            f"SOURCE MATERIAL:\n\"\"\"{text}\"\"\"\n\n"
            f"TASK:\nCreate comprehensive, beautifully structured study notes titled '{suggested_title}'.\n"
            "Include:\n"
            "1. # Executive Overview\n"
            "2. ## Core Concepts & Definitions\n"
            "3. ## Detailed Key Points (using bullet points and bold terms)\n"
            "4. ## Summary & Review Questions\n"
        )

        system_instruction = (
            "You are an elite tutor and instructional designer. Transform disorganized notes or dense "
            "texts into clear, readable, structured Markdown notes."
        )

        notes_markdown = await gemini_service.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.4,
        )

        return {
            "title": suggested_title,
            "notes_markdown": notes_markdown,
            "key_concepts": [],
            "summary": f"Generated notes from {len(text.split())} words of study material.",
        }

    async def generate_quiz(
        self,
        text: str,
        question_count: int = 5,
        difficulty: str = "medium",
    ) -> Dict[str, Any]:
        """Generate a multiple-choice quiz with answer keys in structured JSON format."""
        prompt = (
            f"SOURCE TEXT:\n\"\"\"{text}\"\"\"\n\n"
            f"TASK: Generate exactly {question_count} multiple-choice questions testing comprehension "
            f"at a '{difficulty}' difficulty level.\n"
            "You MUST respond ONLY with valid JSON following this exact JSON schema:\n"
            "{\n"
            '  "topic": "Brief topic title",\n'
            '  "questions": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "question": "The question string",\n'
            '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
            '      "correct_answer_index": 0,\n'
            '      "explanation": "Why this option is correct."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        system_instruction = (
            "You are an assessment and examination specialist. Create rigorous, high quality "
            "multiple-choice questions with plausible distractors."
        )

        try:
            quiz_data = await gemini_service.generate_json(
                prompt=prompt,
                system_instruction=system_instruction,
            )
            return {
                "topic": quiz_data.get("topic", "Quiz"),
                "total_questions": len(quiz_data.get("questions", [])),
                "questions": quiz_data.get("questions", []),
            }
        except Exception as e:
            logger.warning(f"Structured quiz generation fallback due to: {e}")
            # Fallback sample quiz format if JSON decoding failed
            return {
                "topic": "Generated Quiz",
                "total_questions": 1,
                "questions": [
                    {
                        "id": 1,
                        "question": "What is the primary topic discussed in the provided text?",
                        "options": ["Core topic of text", "Unrelated option", "Incorrect detail", "Alternative topic"],
                        "correct_answer_index": 0,
                        "explanation": "Derived directly from the source material.",
                    }
                ],
            }

    async def generate_flashcards(
        self,
        text: str,
        card_count: int = 6,
    ) -> Dict[str, Any]:
        """Generate flashcard pairs (front/back/hint) in structured JSON format."""
        prompt = (
            f"SOURCE TEXT:\n\"\"\"{text}\"\"\"\n\n"
            f"TASK: Create {card_count} high-yield flashcards for active recall study.\n"
            "Output ONLY valid JSON with this exact schema:\n"
            "{\n"
            '  "topic": "Flashcard deck title",\n'
            '  "flashcards": [\n'
            "    {\n"
            '      "id": 1,\n'
            '      "front": "Prompt, term, or question",\n'
            '      "back": "Clear, concise definition or answer",\n'
            '      "hint": "Optional hint or mnemonic"\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        system_instruction = (
            "You are an expert in active recall and spaced repetition learning systems like Anki."
        )

        try:
            cards_data = await gemini_service.generate_json(
                prompt=prompt,
                system_instruction=system_instruction,
            )
            return {
                "topic": cards_data.get("topic", "Flashcards"),
                "total_cards": len(cards_data.get("flashcards", [])),
                "flashcards": cards_data.get("flashcards", []),
            }
        except Exception as e:
            logger.warning(f"Flashcards JSON generation fallback due to: {e}")
            return {
                "topic": "Flashcards",
                "total_cards": 1,
                "flashcards": [
                    {
                        "id": 1,
                        "front": "Main Concept",
                        "back": "Key takeaway from the provided text.",
                        "hint": "Review the summary.",
                    }
                ],
            }

    async def explain_concept(
        self,
        concept: str,
        level: str = "intermediate",
    ) -> Dict[str, Any]:
        """Explain a complex concept simply with analogies and progressive breakdown."""
        prompt = (
            f"CONCEPT TO EXPLAIN: '{concept}'\n"
            f"TARGET AUDIENCE / LEVEL: '{level}'\n\n"
            "Provide:\n"
            "1. An intuitive high-level explanation\n"
            "2. A real-world analogy to make it memorable\n"
            "3. Key takeaways or components\n"
            "4. A common misconception and clarification"
        )

        system_instruction = (
            "You are DARZFUSION AI's Concept Explainer, known for turning complex ideas into "
            "lucid, unforgettable explanations using analogies and clear language."
        )

        explanation = await gemini_service.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.5,
        )

        return {
            "concept": concept,
            "level": level,
            "explanation": explanation,
            "analogies": [],
            "key_points": [],
        }


study_service = StudyService()
