# Frontend & Backend Integration Checklist

This document tracks the integration between the **Python Tkinter Desktop GUI** (`desktop_app`) and the **Flask REST API** (`backend`).

---

## 1. Authentication & Session Management

- [x] **Registration Screen**: `POST /api/v1/auth/register` with `email`, `password` (min 8 chars), `display_name`.
- [x] **Login Screen**: `POST /api/v1/auth/login` with `email`, `password`.
- [x] **Token Storage**: Persists `access_token` in application session state (`self.access_token`).
- [x] **Request Headers**: Automatically attaches `Authorization: Bearer <token>` in `api_client.py`.
- [x] **Token Expiration Handling**: `401 Unauthorized` raises `AuthenticationError` and prompts re-authentication.
- [x] **Current User Profile**: `GET /api/v1/auth/me` retrieves profile and updates UI profile dropdown.

---

## 2. Quiz Management & Exploration

- [x] **Explore Quizzes Screen**: Calls `GET /api/v1/quizzes?include_public=true`.
  - Displays subject cards with question count and difficulty level.
- [x] **Manual Quiz Creator**: Calls `POST /api/v1/quizzes`.
  - Validates title, question prompt, 4 options, and radio button for correct option.
- [x] **My Quizzes Library**: Calls `GET /api/v1/quizzes?include_public=false`.
  - Lists student's owned quizzes with action buttons.
- [x] **Delete Quiz**: Calls `DELETE /api/v1/quizzes/{id}` with confirmation prompt.

---

## 3. Quiz Taking & Secure Scoring Flow

- [x] **Start Quiz / Exam Mode**: Calls `GET /api/v1/quizzes/{id}/take`.
  - **Security Verified**: Correct options, answer keys, and explanations are excluded from payload during taking mode.
- [x] **Submit Quiz Answers**: Calls `POST /api/v1/quizzes/{id}/attempts` with array of `{question_id, selected_option_id}`.
  - Server calculates score authoritatively.
- [x] **Review Page / Results Screen**: Calls `GET /api/v1/attempts/{attempt_id}/results`.
  - Displays score, accuracy percentage, selected answers (color coded), correct options, and explanations.

---

## 4. AI Quiz Generation

- [x] **AI Quiz Generator**: Calls `POST /api/v1/ai/generate-quiz`.
  - Parameters: `topic`, `question_count` (1–20), `difficulty` (easy, medium, hard), and optional source notes.
  - Generates structured JSON questions via LLM abstraction and saves as private quiz owned by the student.

---

## 5. "Ask Your PDF" & Study Documents

- [x] **PDF Upload Dropzone / File Picker**: Calls `POST /api/v1/documents` via multipart file upload.
  - Validates `.pdf` extension, extracts page-by-page text using PyMuPDF (`fitz`), and returns page count.
- [x] **Document Listing**: Calls `GET /api/v1/documents` displaying filename, file size, and page count.
- [x] **Delete Document**: Calls `DELETE /api/v1/documents/{id}` and cleans up filesystem storage.

---

## 6. Chat Sessions ("Ask Your PDF") & RAG Boundary

- [x] **Start Chat Session**: Calls `POST /api/v1/chat/sessions` with `document_id`.
- [x] **Load Chat History**: Calls `GET /api/v1/chat/sessions/{id}/messages`.
- [x] **Send Message**: Calls `POST /api/v1/chat/sessions/{id}/messages`.
  - **RAG Boundary Handled**: When the backend returns HTTP 501 (`rag_pipeline_not_implemented`), the GUI displays the friendly notice:
    *"ℹ️ Your question was recorded! The RAG retrieval pipeline is currently being developed and will be active shortly."*

---

## 7. Progress Analytics Dashboard

- [x] **Student Dashboard**: Calls `GET /api/v1/progress`.
  - Displays metrics: Total Attempts, Questions Answered, Correct Answers, Overall Accuracy %.
  - Recent attempts history table with scores and timestamps.
  - Safe empty state when student has 0 attempts.
