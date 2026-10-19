import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from backend.app.utils.errors import AppError


class LLMError(AppError):
    def __init__(self, message: str, code: str = "llm_error", status_code: int = 502):
        super().__init__(message, code=code, status_code=status_code)


class LLMConfigurationError(LLMError):
    def __init__(self, message: str = "LLM provider is not configured properly"):
        super().__init__(message, code="llm_misconfigured", status_code=500)


class LLMTimeoutError(LLMError):
    def __init__(self, message: str = "LLM provider request timed out"):
        super().__init__(message, code="llm_timeout", status_code=504)


class BaseLLMClient(ABC):
    @abstractmethod
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        """Generates a text completion from messages."""
        pass


class OpenAILLMClient(BaseLLMClient):
    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-4o-mini", default_timeout: int = 45):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.default_timeout = default_timeout

        if not self.api_key:
            self._client = None
        else:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url or "https://api.openai.com/v1",
                timeout=float(self.default_timeout)
            )

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        if not self._client:
            raise LLMConfigurationError("LLM API key is not configured on this server.")

        import openai

        effective_timeout = float(timeout or self.default_timeout)

        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "timeout": effective_timeout,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = self._client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            content = choice.message.content
            if not content:
                raise LLMError("LLM returned an empty response.", code="llm_empty_response")
            return content

        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"LLM request timed out after {effective_timeout}s") from e
        except openai.AuthenticationError as e:
            raise LLMConfigurationError("Authentication with LLM provider failed.") from e
        except openai.APIError as e:
            raise LLMError(f"LLM provider error: {str(e)}", code="llm_provider_error") from e
        except Exception as e:
            raise LLMError(f"Unexpected error communicating with LLM provider: {str(e)}") from e


class MockLLMClient(BaseLLMClient):
    """Deterministic mock client for isolated testing without paid API keys."""
    def __init__(self, mock_response: Optional[str] = None):
        self.mock_response = mock_response

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        json_mode: bool = True,
        timeout: Optional[int] = None
    ) -> str:
        if self.mock_response is not None:
            return self.mock_response

        # Default fallback valid JSON response
        return json.dumps({
            "title": "Generated Quiz",
            "description": "Auto-generated quiz for study purposes",
            "questions": [
                {
                    "prompt": "What is the primary function of DNA?",
                    "explanation": "DNA stores the genetic code needed for development and reproduction.",
                    "difficulty": "medium",
                    "options": [
                        {"option_text": "Store genetic information", "is_correct": True},
                        {"option_text": "Provide immediate energy", "is_correct": False},
                        {"option_text": "Transport oxygen in blood", "is_correct": False},
                        {"option_text": "Catalyze digestion of starch", "is_correct": False}
                    ]
                }
            ]
        })


def get_llm_client_from_config(config) -> BaseLLMClient:
    api_key = getattr(config, "OPENAI_API_KEY", "")
    base_url = getattr(config, "OPENAI_BASE_URL", None)
    model = getattr(config, "OPENAI_MODEL", "gpt-4o-mini")
    timeout = getattr(config, "LLM_TIMEOUT_SECONDS", 45)
    return OpenAILLMClient(
        api_key=api_key,
        base_url=base_url,
        model=model,
        default_timeout=timeout
    )
