# FORMA Backend

Flask RESTful API powering the FORMA AI quiz and study platform.

---

## 🚀 Quickstart for Windows Developers (VS Code / PowerShell)

### 1. Create and Activate Virtual Environment
Open PowerShell in the project root:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts script execution, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

### 2. Install Dependencies
```powershell
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` inside `backend/`:
```powershell
Copy-Item backend\.env.example backend\.env
```
Default SQLite database (`sqlite:///forma.db`) works immediately out-of-the-box without installing PostgreSQL.

For PostgreSQL (e.g., in production or shared staging):
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/forma
```

### 4. Run Database Migrations
Apply database migrations using Flask-Migrate / Alembic:
```powershell
$env:FLASK_APP="backend.run:app"
flask --app backend.run:app db upgrade -d backend/migrations
```

### 5. Start the Development Server
```powershell
python backend/run.py
```
The API is available at: `http://localhost:5000/api/v1`  
Check service health: `http://localhost:5000/api/v1/health`

---

## 🧪 Testing and Quality Control

### Run Automated Tests
```powershell
pytest
```
Runs 32 unit and integration tests using an isolated in-memory SQLite database and mocked LLM client (no paid API keys required).

### Run Ruff Linter & Formatter
```powershell
ruff check .
ruff format .
```

---

## 📂 Architecture & Directory Layout

```
backend/
├── app/
│   ├── __init__.py        # Application factory (create_app)
│   ├── config.py          # Development, Testing, Production configs
│   ├── extensions.py      # SQLAlchemy, Migrate, JWT, CORS
│   ├── models/            # User, Quiz, Question, Option, Attempt, Document, Chat
│   ├── schemas/           # Pydantic v2 schemas and validators
│   ├── routes/            # Blueprint routes (/auth, /quizzes, /documents, /chat, etc.)
│   ├── services/          # Core domain business logic & security policies
│   ├── repositories/      # Encapsulated SQLAlchemy database queries
│   ├── ai/                # LLM client abstraction and AI quiz generator
│   └── utils/             # Unified error handling and response envelopes
├── migrations/            # Alembic schema versioning
├── tests/                 # Comprehensive pytest test suite
├── requirements.txt       # Pinned dependencies
├── run.py                 # Application launcher
└── .env.example           # Environment template
```

---

## 📚 Documentation Reference

Detailed documentation is available in the [`docs/`](../docs/) directory:
- [API Contract](../docs/API_CONTRACT.md): Comprehensive request/response specification for all endpoints.
- [Database Schema](../docs/DATABASE_SCHEMA.md): Entity relationship diagram, table structures, and constraints.
- [Backend Architecture](../docs/BACKEND_ARCHITECTURE.md): Layered architecture, security boundaries, and design decisions.
- [AI Generation](../docs/AI_GENERATION.md): LLM provider abstraction, structured JSON prompting, and mocking.
- [RAG Integration](../docs/RAG_INTEGRATION.md): Step-by-step instructions for implementing your custom RAG pipeline.
- [Integration Checklist](../docs/INTEGRATION_CHECKLIST.md): UI and frontend developer checklist.
