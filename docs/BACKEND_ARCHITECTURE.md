# FORMA Backend Architecture

## 1. Architectural Philosophy

FORMA's backend follows a strict **Layered Clean Architecture** designed for long-term maintainability, independent testability, and seamless team collaboration:

```
                  ┌───────────────────────────────┐
                  │        HTTP Clients           │
                  │   (Frontend React / Mobile)   │
                  └──────────────┬────────────────┘
                                 │ HTTP / JSON / Bearer JWT
                                 ▼
                  ┌───────────────────────────────┐
                  │         Routes Layer          │
                  │ (Flask Blueprints: /api/v1/*) │
                  └──────────────┬────────────────┘
                                 │ Validates Request with Pydantic
                                 ▼
                  ┌───────────────────────────────┐
                  │        Services Layer         │
                  │ (Business logic, orchestration│
                  │  security checks, AI/RAG intf)│
                  └──────────────┬────────────────┘
                                 │ Executes domain queries & mutations
                                 ▼
                  ┌───────────────────────────────┐
                  │      Repositories Layer       │
                  │ (Data access & transactions)  │
                  └──────────────┬────────────────┘
                                 │ SQLAlchemy ORM
                                 ▼
                  ┌───────────────────────────────┐
                  │      Database (PostgreSQL)    │
                  └───────────────────────────────┘
```

---

## 2. Directory Layout & Module Responsibilities

- **`backend/app/config.py`**: Centralized configuration supporting `development`, `testing`, and `production`.
- **`backend/app/extensions.py`**: Instantiates Flask extensions (`SQLAlchemy`, `Flask-Migrate`, `JWTManager`, `CORS`) avoiding circular dependencies.
- **`backend/app/models/`**: Normalized relational entities with explicit cascades and foreign keys.
- **`backend/app/schemas/`**: Pydantic v2 schemas providing compile-time type hints and runtime validation for every inbound request and AI payload.
- **`backend/app/repositories/`**: Encapsulates all SQLAlchemy queries and transactional boundaries.
- **`backend/app/services/`**: Implements core domain behaviors: scoring logic, answer masking, file security, and RAG boundaries.
- **`backend/app/ai/`**: Replaceable LLM client abstraction (`BaseLLMClient`, `OpenAILLMClient`, `MockLLMClient`) and prompt orchestrator (`AIQuizGenerator`).
- **`backend/app/routes/`**: Slim Flask blueprints parsing requests, enforcing JWT claims, and returning standard status codes.
- **`backend/app/utils/`**: Unified error handling (`AppError` hierarchy) and validation decorators.

---

## 3. Critical Security Boundaries

### A. Quiz-Taking Security Boundary
A common vulnerability in student testing applications is returning the entire question object (including `is_correct` flags or explanations) to the client during a test.
- **Enforcement**: `GET /api/v1/quizzes/{id}/take` uses `Question.to_take_dict()` and `QuestionOption.to_take_dict()`. Correctness flags, explanations, and answer keys are physically excluded from the serialized JSON payload.
- **Server-Side Scoring**: All grading is performed server-side by `AttemptService`. The student cannot forge or tamper with their score.

### B. Ownership Verification
Every private quiz, attempt, document, and chat session is explicitly verified against the JWT identity of the caller:
```python
if entity.owner_id != current_user_id:
    raise ForbiddenError("You are not authorized to access this resource.")
```
Client-supplied user IDs in request bodies are ignored.

### C. Private File Storage Isolation
Uploaded PDFs are renamed to random UUIDs (`doc_<uuid>.pdf`) and stored outside any publicly accessible static directory. Filenames and full file paths are never exposed over the API.

### D. LLM Credential Isolation
API keys for LLM providers remain strictly backend environment variables and are never surfaced to clients or logged.
