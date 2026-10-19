# Frontend Integration Checklist

This checklist is for your teammate building the frontend interface to integrate smoothly with the backend.

---

## 1. Authentication & Session Management

- [ ] **Registration Screen**: Calls `POST /api/v1/auth/register` with `email`, `password` (min 8 chars), `display_name`.
- [ ] **Login Screen**: Calls `POST /api/v1/auth/login` with `email`, `password`.
- [ ] **Token Storage**: Persist `access_token` in memory or secure storage (e.g., `localStorage` or HttpOnly cookies).
- [ ] **Request Headers**: Attach `Authorization: Bearer <token>` to all subsequent requests.
- [ ] **Token Expiration Handling**: When an API call returns `401 Unauthorized` with `code: "token_expired"`, clear stored token and redirect to `/login`.
- [ ] **Current User Profile**: Call `GET /api/v1/auth/me` on app load to restore student profile and state.

---

## 2. Quiz Management & Exploration

- [ ] **Dashboard Quiz List**: Calls `GET /api/v1/quizzes?include_public=true`.
  - Display cards with `title`, `description`, `question_count`, and badge for `visibility` ("private" vs "public").
- [ ] **Manual Quiz Creator**: Calls `POST /api/v1/quizzes`.
  - Validate form ensures at least 1 question, and each question has at least 2 options with exactly 1 radio button marked as `is_correct`.
- [ ] **Edit Quiz**: Calls `PATCH /api/v1/quizzes/{id}` (available only to the quiz owner).
- [ ] **Delete Quiz**: Calls `DELETE /api/v1/quizzes/{id}` with a confirmation dialog.

---

## 3. Quiz Taking & Secure Scoring Flow

- [ ] **Start Quiz / Exam Mode**: Call `GET /api/v1/quizzes/{id}/take`.
  - *Note*: This endpoint never returns correct answers, so the student cannot inspect network tabs or console to cheat.
- [ ] **Submit Quiz Answers**: Call `POST /api/v1/quizzes/{id}/attempts` with array of `{question_id, selected_option_id}`.
  - Disable submit button during inflight request.
  - Handle score summary returned in response (`score`, `total_questions`, `accuracy_percentage`).
- [ ] **Review Page / Results Screen**: Call `GET /api/v1/attempts/{attempt_id}/results`.
  - Displays each question with:
    - Student's selected option (highlighted green if correct, red if incorrect).
    - True correct option.
    - Pedagogical explanation explaining why the answer is correct.

---

## 4. AI Quiz Generation

- [ ] **AI Quiz Generator Modal/Page**: Calls `POST /api/v1/ai/generate-quiz`.
  - Fields: `topic`, `question_count` (slider 1–20), `difficulty` ("easy", "medium", "hard"), optional `source_text`.
  - Show loading spinner with animated message while model generates.
  - On `201 Created`, navigate directly to take the generated quiz or review it in quiz list.

---

## 5. "Ask Your PDF" & Study Documents

- [ ] **PDF Upload Dropzone**: Calls `POST /api/v1/documents` using `FormData` with `file`.
  - Restrict file selector to `.pdf` up to 10MB.
  - Display upload progress bar.
- [ ] **Document List**: Calls `GET /api/v1/documents` displaying filename, file size, and page count.
- [ ] **Delete Document**: Calls `DELETE /api/v1/documents/{id}`.

---

## 6. Chat Sessions ("Ask Your PDF")

- [ ] **Start Chat Session**: Calls `POST /api/v1/chat/sessions` with `document_id`.
- [ ] **Load Chat History**: Calls `GET /api/v1/chat/sessions/{id}/messages`.
- [ ] **Send Message**: Calls `POST /api/v1/chat/sessions/{id}/messages`.
  - Handle `501 Not Implemented`: Display a notification banner: *"AI RAG Retrieval is currently in final testing and will be active shortly."*

---

## 7. Progress Analytics Dashboard

- [ ] **Student Dashboard**: Calls `GET /api/v1/progress`.
  - Renders metrics:
    - Total Attempts.
    - Questions Answered.
    - Accuracy Percentage (circular progress ring or bar).
    - Recent attempts table with timestamps and scores.
  - Zero state: Renders friendly call-to-action: *"You haven't taken any quizzes yet. Take your first quiz today!"*
