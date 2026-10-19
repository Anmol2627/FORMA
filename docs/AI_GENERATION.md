# AI Quiz Generation

## 1. Overview
FORMA allows students to generate customized multiple-choice practice quizzes on any academic topic or based on custom lecture notes.

```
[Student Request] ──► [AIQuizGenerator] ──► [BaseLLMClient] ──► [OpenAI / Compatible API]
                                                 │
[Saved Quiz] ◄── [Pydantic Validation] ◄─────────┘
```

---

## 2. LLM Provider Abstraction

The LLM integration is built behind an abstract interface in `backend/app/ai/llm_client.py`:

```python
class BaseLLMClient(ABC):
    @abstractmethod
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        pass
```

### Supported Implementations

1. **`OpenAILLMClient`**
   - Compatible with OpenAI (`gpt-4o-mini`, `gpt-4o`), Groq, Together AI, vLLM, or any OpenAI-compatible API base URL.
   - Enforces `{"type": "json_object"}` structured response format.
   - Manages timeouts, API errors, and invalid authentication.

2. **`MockLLMClient`**
   - Used for zero-cost, deterministic automated test suites.
   - Requires no network connection and no API keys.

---

## 3. Switching Providers

To use a custom local model or alternative provider (e.g., Ollama or Groq), configure the environment variables in `.env`:

```env
# Example for local Ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=llama3.1

# Example for Groq
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=gsk_...
OPENAI_MODEL=llama-3.3-70b-versatile
```

No code modifications in route handlers or services are required.

---

## 4. Structured Output Validation

To prevent malformed LLM outputs from corrupting quiz records, the generator validates the model output against Pydantic schemas:
- **`AIQuestionSchema`**: Ensures prompt length, at least 2 options, and **exactly one** option where `is_correct == true`.
- **`AIGeneratedQuizPayload`**: Ensures title, description, and list of validated questions.
- If the model returns invalid JSON, an explicit `502 Bad Gateway` with error code `llm_malformed_response` is returned with clear diagnostics.
