import json
from backend.app.ai.llm_client import BaseLLMClient, LLMError
from backend.app.schemas.ai import AIGeneratedQuizPayload, QuizGenerateRequest


class AIQuizGenerator:
    def __init__(self, llm_client: BaseLLMClient):
        self.llm_client = llm_client

    def generate_quiz(self, req: QuizGenerateRequest) -> AIGeneratedQuizPayload:
        system_prompt = (
            "You are an expert educational assessment creator. "
            "Generate high-quality multiple choice quizzes for students based strictly on requested topics. "
            "IMPORTANT RULES:\n"
            "1. Output MUST be valid JSON adhering strictly to this schema:\n"
            "{\n"
            '  "title": "Quiz Title",\n'
            '  "description": "Short overview of the quiz",\n'
            '  "questions": [\n'
            "    {\n"
            '      "prompt": "Question text here?",\n'
            '      "explanation": "Overall explanation: why the correct answer is right",\n'
            '      "difficulty": "easy" | "medium" | "hard",\n'
            '      "options": [\n'
            '        {"option_text": "Option A", "is_correct": true, "option_explanation": "This is correct because ..."},\n'
            '        {"option_text": "Option B", "is_correct": false, "option_explanation": "This is wrong because ..."},\n'
            '        {"option_text": "Option C", "is_correct": false, "option_explanation": "This is wrong because ..."},\n'
            '        {"option_text": "Option D", "is_correct": false, "option_explanation": "This is wrong because ..."}\n'
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "2. Each question MUST contain exactly 4 options, with EXACTLY ONE option having is_correct=true.\n"
            "3. Every option MUST include an option_explanation (1-2 sentences explaining why it is correct or incorrect).\n"
            "4. Generate EXACTLY the number of questions requested.\n"
            "5. The overall 'explanation' field should be a clear educational summary of why the correct answer is right.\n"
            "6. Do NOT output markdown ticks (like ```json), output raw JSON only."
        )

        user_content = (
            f"Topic: {req.topic}\n"
            f"Difficulty: {req.difficulty}\n"
            f"Number of Questions: {req.question_count}\n"
        )
        if req.source_text:
            # Bound the source text
            trimmed_source = req.source_text[:12000]
            user_content += f"\nReference Material:\n{trimmed_source}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        raw_response = self.llm_client.generate_chat_completion(messages, json_mode=True)

        try:
            parsed_json = json.loads(raw_response)
        except json.JSONDecodeError as e:
            raise LLMError(
                f"LLM produced malformed non-JSON output: {str(e)}",
                code="llm_malformed_response",
                status_code=502
            ) from e

        # Validate structured schema via Pydantic
        try:
            validated = AIGeneratedQuizPayload.model_validate(parsed_json)
        except Exception as e:
            raise LLMError(
                f"Generated quiz structure validation failed: {str(e)}",
                code="llm_invalid_structure",
                status_code=502
            ) from e

        # Check question count
        if len(validated.questions) == 0:
            raise LLMError(
                "LLM did not generate any questions.",
                code="llm_empty_questions",
                status_code=502
            )

        # Slice to requested count if model over-generated
        if len(validated.questions) > req.question_count:
            validated.questions = validated.questions[:req.question_count]

        return validated
