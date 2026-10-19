# FORMA

**FORMA** is an AI-powered quiz and study platform built for students to create quizzes, practice questions, understand mistakes, study from PDFs, and track their learning progress.

---

## 🎯 Architecture & Ownership

FORMA is developed by a two-person team with clear separation of concerns:
- **Frontend**: Managed separately (UI, styling, responsive components, API client).
- **Backend & AI Architecture**: Built with Flask, SQLAlchemy, Flask-Migrate, JWT, Pydantic, and PyMuPDF.
- **RAG Pipeline Interface**: Cleanly abstracted for dedicated retrieval and embeddings implementation.

---

## 🚀 Quick Setup & Execution

### Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Git

### 1. Initialize Virtual Environment & Install
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 2. Configure Environment
```powershell
Copy-Item backend\.env.example backend\.env
```

### 3. Run Migrations
```powershell
$env:FLASK_APP="backend.run:app"
flask --app backend.run:app db upgrade -d backend/migrations
```

### 4. Start the Backend API
```powershell
python backend/run.py
```
API endpoint: `http://localhost:5000/api/v1`  
Health check: `http://localhost:5000/api/v1/health`

### 5. Run Tests & Linter
```powershell
pytest
ruff check .
```

---

## 📖 Project Documentation

Complete documentation is located in the `docs/` directory:
- [API Contract](docs/API_CONTRACT.md): Complete REST endpoint specifications, request/response formats, and status codes.
- [Database Schema](docs/DATABASE_SCHEMA.md): Normalized relational schema with Mermaid ER diagram and cascade rules.
- [Backend Architecture](docs/BACKEND_ARCHITECTURE.md): Multi-layer architecture and security boundaries.
- [AI Quiz Generation](docs/AI_GENERATION.md): Provider-agnostic LLM client abstraction and structured validation.
- [RAG Integration Guide](docs/RAG_INTEGRATION.md): Interface documentation for implementing chunking, vector stores, and grounded retrieval.
- [Frontend Integration Checklist](docs/INTEGRATION_CHECKLIST.md): Practical checklist for frontend integration.
- [OpenAPI Specification](docs/openapi.json): Standard OpenAPI 3.0.3 specification file for Swagger or Postman import.
