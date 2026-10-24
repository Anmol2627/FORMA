# FORMA

**FORMA** is an AI-powered quiz and study platform built for students to create quizzes, practice questions, understand mistakes, study from PDFs, and track their learning progress.

The application consists of a **Python Tkinter Desktop GUI** frontend integrated with a **Flask REST API** backend powered by SQLAlchemy, PostgreSQL / SQLite, and PyMuPDF.

---

## 🎯 Architecture & Ownership

- **Frontend (Desktop GUI)**: Built with Python Tkinter, structured with a clean API client (`desktop_app/services/api_client.py`), responsive custom styling (`desktop_app/theme.py`), and multi-page views (`desktop_app/app.py`).
- **Backend (REST API)**: Built with Flask, SQLAlchemy, Flask-Migrate, JWT authentication, Pydantic validation, and PyMuPDF document extraction.
- **RAG Pipeline Interface**: Abstracted interface (`BaseRAGService`) prepared for custom retrieval, vector embeddings, and grounded answer generation.

---

## 🚀 Quick Setup & Execution (Windows / PowerShell)

### Prerequisites
- Python 3.10+ (Python 3.11–3.13 supported)
- Built-in Tkinter

### 1. Initialize Virtual Environment & Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 2. Configure Environment
```powershell
Copy-Item backend\.env.example backend\.env
```

### 3. Apply Database Migrations
```powershell
$env:FLASK_APP="backend.run:app"
flask --app backend.run:app db upgrade -d backend/migrations
```

### 4. Start the Backend API
In one terminal:
```powershell
python backend/run.py
```
- API Base URL: `http://localhost:5000/api/v1`
- Health check: `http://localhost:5000/api/v1/health`

### 5. Launch the Desktop Application
In a second terminal:
```powershell
python -m desktop_app.main
```

### 6. Run Automated Tests
```powershell
pytest
ruff check .
```

---

## 📖 Project Documentation

Complete documentation is located in the [`docs/`](docs/) directory:
- [API Contract](docs/API_CONTRACT.md): Complete REST endpoint specifications, request/response formats, and status codes.
- [Database Schema](docs/DATABASE_SCHEMA.md): Normalized relational schema with Mermaid ER diagram and cascade rules.
- [Backend Architecture](docs/BACKEND_ARCHITECTURE.md): Multi-layer architecture and security boundaries.
- [AI Quiz Generation](docs/AI_GENERATION.md): Provider-agnostic LLM client abstraction and structured validation.
- [RAG Integration Guide](docs/RAG_INTEGRATION.md): Interface documentation for implementing chunking, vector stores, and grounded retrieval.
- [Frontend Integration Checklist](docs/INTEGRATION_CHECKLIST.md): Practical checklist for frontend integration.
- [OpenAPI Specification](docs/openapi.json): Standard OpenAPI 3.0.3 specification file for Swagger or Postman import.
