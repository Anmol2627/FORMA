# FORMA Backend API Contract

Version: `1.0.0`  
Base URL Prefix: `/api/v1`  
Authentication Scheme: `Bearer <jwt_token>` via `Authorization` HTTP Header

---

## 1. Global Response & Error Convention

All endpoints return JSON responses. Errors consistently follow this specification:

```json
{
  "error": {
    "code": "error_code_string",
    "message": "Human-readable explanation of what went wrong",
    "details": [
      {
        "field": "body.field_name",
        "message": "Field is required"
      }
    ]
  }
}
```

### Common HTTP Status Codes

| Status Code | Meaning | Example Error Code |
| :--- | :--- | :--- |
| `200 OK` | Request succeeded | N/A |
| `201 Created` | Resource created | N/A |
| `400 Bad Request` | Malformed syntax or domain violation | `invalid_request`, `corrupt_pdf` |
| `401 Unauthorized` | Missing, invalid, or expired JWT | `unauthorized`, `token_expired`, `invalid_credentials` |
| `403 Forbidden` | Access to resource not allowed for user | `forbidden_quiz_access`, `forbidden_attempt_access` |
| `404 Not Found` | Requested entity not found | `quiz_not_found`, `document_not_found` |
| `409 Conflict` | Unique constraint violated | `user_already_exists` |
| `422 Unprocessable` | Pydantic schema validation failure | `validation_error` |
| `501 Not Implemented` | Planned feature awaiting implementation | `rag_pipeline_not_implemented` |
| `502 Bad Gateway` | Upstream LLM provider failure | `llm_error`, `llm_malformed_response` |

---

## 2. Health & Readiness

### `GET /api/v1/health`
Checks API service liveness.
- **Auth**: None
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "FORMA Backend API",
  "version": "1.0.0"
}
```

### `GET /api/v1/health/ready`
Checks database connectivity and readiness.
- **Auth**: None
- **Response `200 OK`**:
```json
{
  "status": "ready",
  "database": "connected"
}
```

---

## 3. Authentication & Profile

### `POST /api/v1/auth/register`
Registers a new student account.
- **Auth**: None
- **Request Body**:
```json
{
  "email": "student@forma.edu",
  "password": "Minimum8Characters!",
  "display_name": "Alex Student"
}
```
- **Validation**:
  - `email`: Valid RFC email format, normalized to lowercase and trimmed.
  - `password`: String, min 8 characters.
  - `display_name`: String, 1–100 non-blank characters.
- **Response `201 Created`**:
```json
{
  "user": {
    "id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
    "email": "student@forma.edu",
    "display_name": "Alex Student",
    "account_status": "active",
    "created_at": "2026-10-19T13:45:00Z",
    "updated_at": "2026-10-19T13:45:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
- **Errors**: `409 Conflict` (`user_already_exists`), `422 Unprocessable Entity`.

---

### `POST /api/v1/auth/login`
Authenticates existing student credentials.
- **Auth**: None
- **Request Body**:
```json
{
  "email": "student@forma.edu",
  "password": "Minimum8Characters!"
}
```
- **Response `200 OK`**:
```json
{
  "user": {
    "id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
    "email": "student@forma.edu",
    "display_name": "Alex Student",
    "account_status": "active",
    "created_at": "2026-10-19T13:45:00Z",
    "updated_at": "2026-10-19T13:45:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsIn..."
}
```
- **Errors**: `401 Unauthorized` (`invalid_credentials`), `422 Unprocessable Entity`.

---

### `GET /api/v1/auth/me`
Retrieves authenticated user profile.
- **Auth**: Bearer token
- **Response `200 OK`**:
```json
{
  "user": {
    "id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
    "email": "student@forma.edu",
    "display_name": "Alex Student",
    "account_status": "active",
    "created_at": "2026-10-19T13:45:00Z",
    "updated_at": "2026-10-19T13:45:00Z"
  }
}
```

---

## 4. Quizzes

### `GET /api/v1/quizzes`
Lists accessible quizzes (all quizzes owned by user, plus public quizzes if `include_public=true`).
- **Auth**: Bearer token
- **Query Parameters**:
  - `include_public` (boolean, default: `true`)
- **Response `200 OK`**:
```json
{
  "quizzes": [
    {
      "id": "8bbbb551-7871-4820-9988-cb94d3a01a39",
      "owner_id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
      "title": "Cellular Biology Fundamentals",
      "description": "Midterm preparation quiz",
      "visibility": "private",
      "generation_metadata": null,
      "question_count": 5,
      "created_at": "2026-10-19T14:00:00Z",
      "updated_at": "2026-10-19T14:00:00Z"
    }
  ]
}
```

---

### `POST /api/v1/quizzes`
Creates a new quiz manually.
- **Auth**: Bearer token
- **Request Body**:
```json
{
  "title": "General Chemistry I",
  "description": "Stoichiometry and atomic structure",
  "visibility": "private",
  "questions": [
    {
      "prompt": "What is the atomic number of Carbon?",
      "explanation": "Carbon has 6 protons in its nucleus.",
      "display_position": 0,
      "topic": "Periodic Table",
      "difficulty": "easy",
      "options": [
        {"option_text": "6", "is_correct": true},
        {"option_text": "12", "is_correct": false},
        {"option_text": "14", "is_correct": false},
        {"option_text": "8", "is_correct": false}
      ]
    }
  ]
}
```
- **Validation**:
  - `title`: 1–200 non-blank chars.
  - `visibility`: `"private"` or `"public"`.
  - `questions`: 1–100 questions.
  - Each question must contain 2–10 options and **EXACTLY ONE** option where `is_correct == true`.
- **Response `201 Created`**: Returns full quiz object with nested questions and options.

---

### `GET /api/v1/quizzes/{quiz_id}`
Retrieves a full quiz.
- **Auth**: Bearer token
- **Authorization**: If quiz is `"private"`, only owner can access (`403 Forbidden`).
- **Response `200 OK`**: Returns full quiz object including questions and options.

---

### `PATCH /api/v1/quizzes/{quiz_id}`
Updates quiz title, description, visibility, or questions.
- **Auth**: Bearer token
- **Authorization**: Only owner can update (`403 Forbidden`).
- **Response `200 OK`**: Returns updated quiz object.

---

### `DELETE /api/v1/quizzes/{quiz_id}`
Deletes a quiz and all associated attempts and questions.
- **Auth**: Bearer token
- **Authorization**: Only owner can delete (`403 Forbidden`).
- **Response `200 OK`**: `{"message": "Quiz deleted successfully."}`

---

## 5. Quiz Taking & Scoring (Security Boundary)

### `GET /api/v1/quizzes/{quiz_id}/take`
Returns the quiz in student taking mode.
- **Auth**: Bearer token
- **Security Boundary**: **NEVER** includes answer keys, `is_correct` flags, or `explanation` texts.
- **Response `200 OK`**:
```json
{
  "quiz": {
    "id": "8bbbb551-7871-4820-9988-cb94d3a01a39",
    "title": "General Chemistry I",
    "description": "Stoichiometry and atomic structure",
    "question_count": 1,
    "questions": [
      {
        "id": "31bb73ba-d4f1-419b-ab00-e76e1aef71a2",
        "prompt": "What is the atomic number of Carbon?",
        "display_position": 0,
        "topic": "Periodic Table",
        "difficulty": "easy",
        "options": [
          {"id": "c1f7de7b-4bb9-45bb-87a2-f94dd36802b1", "option_text": "6"},
          {"id": "9b1ae3fb-500b-4632-ae6b-167817ebdb3e", "option_text": "12"},
          {"id": "8f8b89d4-cba0-42cf-9ca5-8db5877f2d57", "option_text": "14"},
          {"id": "6732cb41-3211-4770-ae61-9f939e658ec3", "option_text": "8"}
        ]
      }
    ]
  }
}
```

---

### `POST /api/v1/quizzes/{quiz_id}/attempts`
Submits student answers for server-side evaluation.
- **Auth**: Bearer token
- **Request Body**:
```json
{
  "answers": [
    {
      "question_id": "31bb73ba-d4f1-419b-ab00-e76e1aef71a2",
      "selected_option_id": "c1f7de7b-4bb9-45bb-87a2-f94dd36802b1"
    }
  ]
}
```
- **Scoring & Validation Rules**:
  - Duplicate submissions for the same `question_id` return `422 Unprocessable Entity`.
  - Questions omitted from `answers` are scored as unanswered (`is_correct = false`).
  - Score is computed strictly on backend.
- **Response `201 Created`**:
```json
{
  "attempt": {
    "id": "4b684cb2-6aa1-4e7a-9a99-b14eb8784fc2",
    "quiz_id": "8bbbb551-7871-4820-9988-cb94d3a01a39",
    "quiz_title": "General Chemistry I",
    "score": 1,
    "total_questions": 1,
    "accuracy_percentage": 100.0,
    "submitted_at": "2026-10-19T14:10:00Z"
  }
}
```

---

### `GET /api/v1/attempts/{attempt_id}/results`
Full attempt review with explanations and answer keys.
- **Auth**: Bearer token
- **Authorization**: Only the student who submitted the attempt can access (`403 Forbidden`).
- **Response `200 OK`**:
```json
{
  "attempt": {
    "id": "4b684cb2-6aa1-4e7a-9a99-b14eb8784fc2",
    "quiz_id": "8bbbb551-7871-4820-9988-cb94d3a01a39",
    "quiz_title": "General Chemistry I",
    "score": 1,
    "total_questions": 1,
    "accuracy_percentage": 100.0,
    "submitted_at": "2026-10-19T14:10:00Z",
    "answers": [
      {
        "id": "18f9e685-6bb2-4148-bd08-8e8e78a63583",
        "question_id": "31bb73ba-d4f1-419b-ab00-e76e1aef71a2",
        "question_prompt": "What is the atomic number of Carbon?",
        "explanation": "Carbon has 6 protons in its nucleus.",
        "selected_option_id": "c1f7de7b-4bb9-45bb-87a2-f94dd36802b1",
        "selected_option_text": "6",
        "correct_option": {
          "id": "c1f7de7b-4bb9-45bb-87a2-f94dd36802b1",
          "option_text": "6"
        },
        "is_correct": true,
        "answered_at": "2026-10-19T14:10:00Z"
      }
    ]
  }
}
```

---

## 6. AI Quiz Generation

### `POST /api/v1/ai/generate-quiz`
Generates a multiple choice quiz using an LLM and saves it directly as a private quiz owned by the user.
- **Auth**: Bearer token
- **Request Body**:
```json
{
  "topic": "Mitochondrial Electron Transport Chain",
  "question_count": 5,
  "difficulty": "medium",
  "source_text": "Optional notes or text snippet from lecture..."
}
```
- **Validation**:
  - `topic`: 2–200 characters.
  - `question_count`: Integer between 1 and 20.
  - `difficulty`: `"easy"`, `"medium"`, or `"hard"`.
  - `source_text`: Optional, up to 15,000 characters.
- **Response `201 Created`**:
```json
{
  "message": "AI quiz generated and saved successfully.",
  "quiz": {
    "id": "90ca74bd-12c8-47c0-a7d1-e6a3f0f5b9d3",
    "owner_id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
    "title": "Mitochondrial Electron Transport Chain Quiz",
    "description": "Generated quiz on 'Mitochondrial Electron Transport Chain' (medium difficulty).",
    "visibility": "private",
    "generation_metadata": {
      "generated_by": "ai",
      "topic": "Mitochondrial Electron Transport Chain",
      "difficulty": "medium",
      "question_count": 5,
      "disclaimer": "AI-generated questions may require human review."
    },
    "question_count": 5,
    "questions": [...]
  }
}
```

---

## 7. Documents (PDF Upload & Extraction)

### `POST /api/v1/documents`
Uploads a study PDF and extracts page-by-page text using PyMuPDF.
- **Auth**: Bearer token
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `file`: PDF binary file (max 10MB by default).
- **Response `201 Created`**:
```json
{
  "message": "Document uploaded and processed successfully.",
  "document": {
    "id": "76495200-a5fb-4299-92c9-a54eb4470bc5",
    "owner_id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
    "original_filename": "biology_chapter_3.pdf",
    "file_size_bytes": 1048576,
    "processing_status": "ready",
    "page_count": 12,
    "created_at": "2026-10-19T14:15:00Z",
    "updated_at": "2026-10-19T14:15:00Z"
  }
}
```

---

### `GET /api/v1/documents`
Lists documents uploaded by the authenticated user.
- **Auth**: Bearer token
- **Response `200 OK`**: Returns array of documents (omits raw server path and extracted page text for performance).

---

### `GET /api/v1/documents/{document_id}`
Retrieves document details including page-by-page extracted text metadata.
- **Auth**: Bearer token
- **Authorization**: Owner only (`403 Forbidden`).
- **Response `200 OK`**:
```json
{
  "document": {
    "id": "76495200-a5fb-4299-92c9-a54eb4470bc5",
    "owner_id": "e672ce3e-63f5-46b0-9db0-5e363991c49b",
    "original_filename": "biology_chapter_3.pdf",
    "file_size_bytes": 1048576,
    "processing_status": "ready",
    "page_count": 2,
    "extracted_text_metadata": [
      {
        "page_number": 1,
        "char_count": 1420,
        "text": "Chapter 3: Cellular Respiration...\n"
      },
      {
        "page_number": 2,
        "char_count": 1650,
        "text": "Section 3.1: Glycolysis pathway...\n"
      }
    ],
    "created_at": "2026-10-19T14:15:00Z",
    "updated_at": "2026-10-19T14:15:00Z"
  }
}
```

---

### `DELETE /api/v1/documents/{document_id}`
Deletes document record and cleans up the private PDF file from disk storage.
- **Auth**: Bearer token
- **Authorization**: Owner only (`403 Forbidden`).
- **Response `200 OK`**: `{"message": "Document deleted successfully."}`

---

## 8. Chat Sessions & Messages (RAG Boundary)

### `POST /api/v1/chat/sessions`
Initializes a chat session linked to an owned document.
- **Auth**: Bearer token
- **Request Body**:
```json
{
  "document_id": "76495200-a5fb-4299-92c9-a54eb4470bc5",
  "title": "Discussion on Glycolysis"
}
```
- **Response `201 Created`**: Returns created chat session.

---

### `GET /api/v1/chat/sessions`
Lists chat sessions for the authenticated user.
- **Auth**: Bearer token
- **Response `200 OK`**: Returns array of sessions.

---

### `GET /api/v1/chat/sessions/{session_id}/messages`
Retrieves message history for a chat session.
- **Auth**: Bearer token
- **Authorization**: Owner only (`403 Forbidden`).
- **Response `200 OK`**:
```json
{
  "messages": [
    {
      "id": "e305e55e-2f76-46c0-9d41-3b7d18a02c84",
      "session_id": "713f0a99-9941-4c6e-827d-949e62319ef5",
      "role": "user",
      "content": "What is the net yield of ATP in glycolysis?",
      "citations": [],
      "created_at": "2026-10-19T14:20:00Z"
    }
  ]
}
```

---

### `POST /api/v1/chat/sessions/{session_id}/messages`
Sends a message in the chat session.
- **Auth**: Bearer token
- **Request Body**:
```json
{
  "content": "What is the net yield of ATP in glycolysis?"
}
```
- **Status Until User RAG Implementation**:
  - The message is validated and persisted to the database.
  - The endpoint returns **`501 Not Implemented`** clearly explaining that the RAG retrieval pipeline is awaiting user implementation.
- **Response `501 Not Implemented`**:
```json
{
  "error": {
    "code": "rag_pipeline_not_implemented",
    "message": "The RAG retrieval and answer generation pipeline is currently awaiting implementation. The chat session and message infrastructure are ready. Please implement BaseRAGService as documented in docs/RAG_INTEGRATION.md."
  }
}
```

---

## 9. Progress Analytics

### `GET /api/v1/progress`
Retrieves live database-derived analytics on quizzes taken by the authenticated student.
- **Auth**: Bearer token
- **Response `200 OK`**:
```json
{
  "progress": {
    "total_attempts": 3,
    "total_questions_answered": 15,
    "total_correct_answers": 12,
    "overall_accuracy_percentage": 80.0,
    "recent_attempts": [
      {
        "id": "4b684cb2-6aa1-4e7a-9a99-b14eb8784fc2",
        "quiz_id": "8bbbb551-7871-4820-9988-cb94d3a01a39",
        "quiz_title": "General Chemistry I",
        "score": 1,
        "total_questions": 1,
        "accuracy_percentage": 100.0,
        "submitted_at": "2026-10-19T14:10:00Z"
      }
    ]
  }
}
```
- **Zero Attempts Behavior**: Safely returns `total_attempts = 0`, `overall_accuracy_percentage = 0.0`, and empty list `recent_attempts = []`.
