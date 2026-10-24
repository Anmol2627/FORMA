"""
Simple RAG (Retrieval-Augmented Generation) pipeline for FORMA.

Strategy (keyword/TF-IDF retrieval — no vector DB required):
1. Load the document's extracted page text from the DB.
2. Score each page against the user query using TF-IDF-style keyword overlap.
3. Pick the top-k pages as context.
4. Send context + query + chat history to the LLM (Groq/OpenAI-compatible).
5. Return the assistant's grounded answer with page citations.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from backend.app.ai.llm_client import BaseLLMClient, LLMError
from backend.app.models.document import Document
from backend.app.services.chat_service import BaseRAGService


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    return re.findall(r"\b[a-z]+\b", text.lower())


def _tf_idf_score(query_tokens: List[str], page_tokens: List[str], idf: Dict[str, float]) -> float:
    """Score a page against a query using TF × IDF overlap."""
    if not page_tokens:
        return 0.0
    tf = Counter(page_tokens)
    total = len(page_tokens)
    score = 0.0
    for token in set(query_tokens):
        tf_val = tf.get(token, 0) / total
        idf_val = idf.get(token, 0.0)
        score += tf_val * idf_val
    return score


def _build_idf(pages: List[Dict[str, Any]]) -> Dict[str, float]:
    """Build an IDF table from extracted page texts."""
    N = len(pages)
    if N == 0:
        return {}
    df: Dict[str, int] = Counter()
    for page in pages:
        unique_tokens = set(_tokenize(page.get("text", "")))
        for t in unique_tokens:
            df[t] += 1
    return {term: math.log((N + 1) / (count + 1)) + 1.0 for term, count in df.items()}


def _retrieve_top_pages(
    query: str,
    pages: List[Dict[str, Any]],
    top_k: int = 4,
    max_chars_per_page: int = 1500
) -> List[Dict[str, Any]]:
    """Return the top-k most relevant pages for the query, text truncated to max_chars_per_page."""
    if not pages:
        return []

    idf = _build_idf(pages)
    query_tokens = _tokenize(query)

    scored = []
    for page in pages:
        tokens = _tokenize(page.get("text", ""))
        score = _tf_idf_score(query_tokens, tokens, idf)
        scored.append((score, page))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [p for _, p in scored[:top_k] if p.get("text", "").strip()]

    # Truncate text to avoid blowing out the context window
    result = []
    for p in top:
        text = p.get("text", "")[:max_chars_per_page]
        result.append({"page_number": p["page_number"], "text": text})

    return result


# ---------------------------------------------------------------------------
# RAG Service Implementation
# ---------------------------------------------------------------------------

class SimpleRAGService(BaseRAGService):
    """
    Keyword-based RAG service — no external vector DB required.
    Uses TF-IDF retrieval over extracted page text stored in the Document model.
    """

    def __init__(self, llm_client: BaseLLMClient, top_k: int = 4, history_turns: int = 6):
        self.llm_client = llm_client
        self.top_k = top_k
        self.history_turns = history_turns  # number of recent messages to include as context

    def generate_grounded_response(
        self,
        session_id: str,
        document: Document,
        user_query: str,
        chat_history: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        1. Retrieve relevant pages from extracted_text_metadata.
        2. Build a grounded prompt with context + history.
        3. Call the LLM and return the answer + citations.
        """
        pages: List[Dict[str, Any]] = document.extracted_text_metadata or []

        if not pages:
            return (
                "I couldn't find any text content in this document. "
                "The PDF may contain only images or scanned content. "
                "Please try uploading a text-based PDF.",
                []
            )

        # Retrieve relevant pages
        top_pages = _retrieve_top_pages(user_query, pages, top_k=self.top_k)

        if not top_pages:
            return (
                "I couldn't find relevant content in this document to answer your question. "
                "Try rephrasing or asking about a different topic covered in the document.",
                []
            )

        # Build context block
        context_block = "\n\n".join(
            f"[Page {p['page_number']}]\n{p['text']}"
            for p in top_pages
        )

        # Build conversation history (last N turns, excluding the latest user message)
        recent_history = []
        for msg in chat_history[-(self.history_turns * 2):-1]:  # -1 excludes current user msg
            role = msg.get("role")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                recent_history.append({"role": role, "content": content})

        system_prompt = (
            "You are FORMA Study Assistant — an expert academic tutor. "
            "You help students understand their study materials by answering questions "
            "STRICTLY based on the provided document excerpts. "
            "\n\nRules:"
            "\n1. Answer ONLY using the provided document context. Do not use outside knowledge."
            "\n2. If the answer is not in the document, say 'I couldn't find this in the document.' "
            "Do NOT fabricate information."
            "\n3. Always cite the page number(s) you drew information from, e.g. '(Page 3)'."
            "\n4. Be concise, clear, and helpful. Use bullet points for complex answers."
            "\n5. If a concept is partially covered, explain what the document says and note the limitation."
            "\n\nDocument Excerpts:\n"
            "---\n"
            f"{context_block}\n"
            "---"
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(recent_history)
        messages.append({"role": "user", "content": user_query})

        try:
            reply_text = self.llm_client.generate_chat_completion(
                messages=messages,
                json_mode=False,
                timeout=45
            )
        except LLMError as e:
            raise e

        # Build citations list
        citations = [
            {
                "page_number": p["page_number"],
                "snippet": p["text"][:200] + ("..." if len(p["text"]) > 200 else ""),
            }
            for p in top_pages
        ]

        return reply_text.strip(), citations


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_rag_service(llm_client: Optional[BaseLLMClient]) -> BaseRAGService:
    """
    Returns a SimpleRAGService if an LLM client is available,
    otherwise falls back gracefully to UnimplementedRAGService.
    """
    from backend.app.services.chat_service import UnimplementedRAGService

    if llm_client is None:
        return UnimplementedRAGService()
    return SimpleRAGService(llm_client=llm_client)
