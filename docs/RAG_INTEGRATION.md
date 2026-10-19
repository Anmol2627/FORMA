# RAG Pipeline Integration Guide

This document is prepared specifically for you (the backend/AI teammate) to implement your custom Retrieval-Augmented Generation (RAG) pipeline for the "Ask Your PDF" study assistant.

All session management, ownership security, message history persistence, PDF upload, and page-by-page text extractions are **already implemented, tested, and waiting for your retrieval logic**.

---

## 1. Where to Implement Your RAG Pipeline

You will implement the abstract class `BaseRAGService` located in [`backend/app/services/chat_service.py`](file:///c:/Users/HP/Desktop/FORMA/backend/app/services/chat_service.py).

```python
class BaseRAGService(ABC):
    @abstractmethod
    def generate_grounded_response(
        self,
        session_id: str,
        document: Document,
        user_query: str,
        chat_history: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieves relevant document chunks and generates a grounded response.
        
        Returns:
            Tuple[assistant_reply_text, citations_list]
        """
        pass
```

Currently, the application runs with `UnimplementedRAGService`, which returns a clean `501 Not Implemented` with error code `rag_pipeline_not_implemented` when students post a chat message.

---

## 2. Input Parameters

When a user calls `POST /api/v1/chat/sessions/{session_id}/messages`, `ChatService` invokes your method with:

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `session_id` | `str` | UUID of the active chat session |
| `document` | `Document` | SQLAlchemy Document model instance (see details below) |
| `user_query` | `str` | Cleaned user prompt/question (e.g., *"What is glycolysis?"*) |
| `chat_history` | `List[Dict]` | Sequential list of prior messages in the session, e.g.: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]` |

### Document Object Attributes Available to You:
- `document.id`: Unique document UUID.
- `document.original_filename`: Name of the uploaded file (e.g., `Biology_Ch3.pdf`).
- `document.storage_path`: Absolute path to the private PDF file on disk.
- `document.page_count`: Total number of pages.
- `document.extracted_text_metadata`: Pre-extracted page-by-page array ready for chunking:
  ```json
  [
    {
      "page_number": 1,
      "char_count": 1420,
      "text": "Chapter 3: Cellular Respiration...\n"
    },
    {
      "page_number": 2,
      "char_count": 1650,
      "text": "Section 3.1: Glycolysis...\n"
    }
  ]
  ```

---

## 3. Required Output & Citation Schema

Your implementation must return a 2-element tuple: `(assistant_reply_text, citations_list)`.

### Format:
```python
assistant_reply = (
    "Glycolysis produces a net yield of 2 ATP and 2 NADH molecules per glucose molecule. "
    "It takes place entirely in the cytoplasm."
)

citations = [
    {
        "page_number": 2,
        "snippet": "Glycolysis yields a net gain of two ATP molecules and two NADH molecules per glucose.",
        "score": 0.89  # Optional similarity score or relevance metric
    }
]

return assistant_reply, citations
```

The citations will be saved directly into `ChatMessage.citations` as JSON and rendered in the frontend to show students exact references.

---

## 4. Step-by-Step Implementation Example

You can create a new file `backend/app/services/rag_service.py`:

```python
from typing import List, Dict, Any, Tuple
from backend.app.models.document import Document
from backend.app.services.chat_service import BaseRAGService

class MyCustomRAGService(BaseRAGService):
    def __init__(self, embedding_model=None, vector_store=None):
        self.embedding_model = embedding_model
        self.vector_store = vector_store

    def generate_grounded_response(
        self,
        session_id: str,
        document: Document,
        user_query: str,
        chat_history: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        # 1. Use document.extracted_text_metadata to chunk or index if not already indexed
        pages = document.extracted_text_metadata or []
        
        # 2. Retrieve top-k chunks matching user_query
        retrieved_chunks = self.retrieve_chunks(document.id, user_query, k=3)
        
        # 3. Construct prompt with retrieved context and chat_history
        context_str = "\n".join([f"[Page {c['page_number']}] {c['text']}" for c in retrieved_chunks])
        
        # 4. Call LLM for grounded answer
        answer = self.call_llm(context_str, chat_history, user_query)
        
        # 5. Format citations
        citations = [
            {"page_number": c["page_number"], "snippet": c["text"][:200]}
            for c in retrieved_chunks
        ]
        
        return answer, citations
```

### Wiring it up in `backend/app/routes/chat.py`:

Simply instantiate `ChatService` with your new RAG service:

```python
from backend.app.services.rag_service import MyCustomRAGService

rag_service = MyCustomRAGService()
chat_service = ChatService(rag_service=rag_service)
```

---

## 5. Error Handling Best Practices
If the PDF text is completely empty (e.g. image-only scanned document):
- Return a helpful grounded message such as: *"The document does not contain readable text. Please upload an OCR-processed or text-based PDF."* with an empty citations list `[]`.
