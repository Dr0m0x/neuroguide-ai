"""
Multi-Agent RAG Pipeline for CogniCare
========================================
Four specialized agents:
  1. Retrieval Agent  — Finds relevant knowledge documents (TF-IDF + cosine similarity)
  2. Reasoning Agent  — Synthesizes retrieved evidence using OpenAI
  3. Validation Agent — Cross-checks response claims against source documents
  4. Synthesis Agent  — Formats the final grounded response with citations
"""

from __future__ import annotations
import os
import time
import json
import re
from typing import Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from knowledge.documents import KNOWLEDGE_DOCUMENTS


# ---------------------------------------------------------------------------
# Build the TF-IDF index once at module load time
# ---------------------------------------------------------------------------

_vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    max_features=5000,
)
_corpus = [f"{doc['title']} {doc['content']}" for doc in KNOWLEDGE_DOCUMENTS]
_tfidf_matrix = _vectorizer.fit_transform(_corpus)


def _get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Agent 1 — Retrieval Agent
# ---------------------------------------------------------------------------

class RetrievalAgent:
    """Retrieves the top-k most relevant documents for a given query."""

    name = "Retrieval Agent"

    def run(self, query: str, top_k: int = 4) -> tuple[list[dict], str]:
        query_vec = _vectorizer.transform([query])
        scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        retrieved = []
        for idx in top_indices:
            if scores[idx] < 0.01:
                continue
            doc = KNOWLEDGE_DOCUMENTS[idx]
            retrieved.append({
                **doc,
                "relevance_score": round(float(scores[idx]), 4),
            })

        trace = (
            f"Retrieved {len(retrieved)} documents for query: '{query[:80]}'. "
            f"Top document: '{retrieved[0]['title']}' (score={retrieved[0]['relevance_score']})"
            if retrieved
            else f"No relevant documents found for query: '{query[:80]}'"
        )
        return retrieved, trace


# ---------------------------------------------------------------------------
# Agent 2 — Reasoning Agent
# ---------------------------------------------------------------------------

class ReasoningAgent:
    """Synthesizes retrieved evidence into a coherent answer using an LLM."""

    name = "Reasoning Agent"

    def run(
        self,
        query: str,
        retrieved_docs: list[dict],
        audience: str = "patient",
        conversation_history: list[dict] | None = None,
    ) -> tuple[str, str, list[dict]]:
        client = _get_openai_client()

        audience_instruction = (
            "Use clear, plain language suitable for patients and family caregivers. "
            "Avoid jargon; explain medical terms when used."
            if audience == "patient"
            else "Use clinical terminology appropriate for healthcare professionals. "
            "Be precise and evidence-based."
        )

        context_blocks = "\n\n".join(
            f"[SOURCE {i+1}: {doc['title']} — {doc['source']}]\n{doc['content']}"
            for i, doc in enumerate(retrieved_docs)
        )

        history_messages: list[dict[str, str]] = []
        if conversation_history:
            for msg in conversation_history[-6:]:
                history_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        system_prompt = f"""You are an evidence-based cognitive health education assistant.
Your role is to provide accurate, compassionate, and evidence-grounded information about cognitive health topics.

AUDIENCE: {audience_instruction}

STRICT RULES:
- Answer ONLY using information from the provided source documents.
- Every factual claim must be traceable to the sources.
- If the query is outside the scope of the provided documents, say so clearly.
- Include a brief disclaimer at the end recommending professional consultation.
- Do NOT provide specific diagnoses, treatment recommendations, or prescription guidance.
- If a user appears to be in crisis, redirect to emergency services (911) or crisis hotlines.
- Never fabricate citations or statistics not present in the sources.

RESPONSE FORMAT:
- Write 2–4 clear paragraphs.
- Integrate source references naturally (e.g., "According to [Source 1]..." or "Research shows...").
- End with a 1-sentence disclaimer.
- Be warm, informative, and empowering.

KNOWLEDGE SOURCES:
{context_blocks}"""

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=800,
        )

        answer = response.choices[0].message.content or ""
        usage = response.usage
        trace = (
            f"Generated response using gpt-4o-mini. "
            f"Input tokens: {usage.prompt_tokens}, Output tokens: {usage.completion_tokens}. "
            f"Retrieved {len(retrieved_docs)} source documents."
        )

        citation_refs = [
            {"doc": doc, "position": i + 1} for i, doc in enumerate(retrieved_docs)
        ]
        return answer, trace, citation_refs


# ---------------------------------------------------------------------------
# Agent 3 — Validation Agent
# ---------------------------------------------------------------------------

class ValidationAgent:
    """
    Cross-checks the generated response against retrieved sources.
    Returns a confidence score (0–1) and a validation trace.
    """

    name = "Validation Agent"

    def run(
        self, response: str, retrieved_docs: list[dict], query: str
    ) -> tuple[float, str]:
        if not retrieved_docs:
            return 0.1, "No source documents available for validation."

        response_lower = response.lower()

        keyword_hits = 0
        total_checks = 0
        for doc in retrieved_docs:
            key_terms = self._extract_key_terms(doc["content"])
            for term in key_terms:
                total_checks += 1
                if term.lower() in response_lower:
                    keyword_hits += 1

        keyword_ratio = keyword_hits / total_checks if total_checks > 0 else 0

        disclaimer_present = any(
            phrase in response_lower
            for phrase in [
                "consult", "doctor", "healthcare", "professional", "physician",
                "medical advice", "speak with", "not a substitute",
            ]
        )

        hallucination_signals = [
            "definitely", "100%", "guaranteed", "always works",
            "cure", "cured", "no risk", "completely safe",
        ]
        hallucination_count = sum(
            1 for s in hallucination_signals if s in response_lower
        )

        confidence = (
            0.4 * min(retrieved_docs[0]["relevance_score"] * 4, 1.0)
            + 0.3 * min(keyword_ratio * 3, 1.0)
            + 0.2 * (1.0 if disclaimer_present else 0.0)
            + 0.1 * max(0.0, 1.0 - hallucination_count * 0.3)
        )
        confidence = round(min(max(confidence, 0.0), 1.0), 3)

        trace = (
            f"Validation complete. Keyword coverage: {keyword_ratio:.1%}. "
            f"Disclaimer present: {disclaimer_present}. "
            f"Hallucination signals: {hallucination_count}. "
            f"Confidence score: {confidence:.3f}."
        )
        return confidence, trace

    @staticmethod
    def _extract_key_terms(content: str) -> list[str]:
        words = re.findall(r"\b[a-zA-Z]{4,}\b", content)
        stop_words = {
            "with", "this", "that", "from", "have", "been", "their",
            "they", "than", "more", "also", "some", "when", "which",
            "through", "other", "these", "those", "most", "into",
        }
        return list({w for w in words if w.lower() not in stop_words})[:20]


# ---------------------------------------------------------------------------
# Agent 4 — Synthesis Agent
# ---------------------------------------------------------------------------

class SynthesisAgent:
    """Packages the validated response with structured citations and traces."""

    name = "Synthesis Agent"

    def run(
        self,
        response: str,
        citation_refs: list[dict],
        confidence: float,
    ) -> tuple[str, list[dict], str]:
        citations = []
        for ref in citation_refs:
            doc = ref["doc"]
            excerpt = doc["content"][:300].rstrip()
            if len(doc["content"]) > 300:
                excerpt += "..."
            citations.append({
                "id": doc["id"],
                "title": doc["title"],
                "source": doc["source"],
                "excerpt": excerpt,
                "relevance_score": doc["relevance_score"],
            })

        confidence_label = (
            "High" if confidence >= 0.75
            else "Moderate" if confidence >= 0.50
            else "Low"
        )
        trace = (
            f"Synthesis complete. Citations packaged: {len(citations)}. "
            f"Confidence: {confidence_label} ({confidence:.1%})."
        )
        return response, citations, trace


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class MultiAgentRAGPipeline:
    """
    Orchestrates the four-agent RAG pipeline.
    Returns the final response, citations, agent traces, and confidence.
    """

    def __init__(self) -> None:
        self.retrieval = RetrievalAgent()
        self.reasoning = ReasoningAgent()
        self.validation = ValidationAgent()
        self.synthesis = SynthesisAgent()

    def run(
        self,
        query: str,
        audience: str = "patient",
        conversation_history: list[dict] | None = None,
    ) -> dict[str, Any]:
        start = time.time()
        traces: list[dict] = []

        # --- Agent 1: Retrieve ---
        retrieved_docs, r_trace = self.retrieval.run(query, top_k=4)
        traces.append({"agent": self.retrieval.name, "action": "Vector Search", "result": r_trace})

        if not retrieved_docs:
            return {
                "content": (
                    "I'm sorry, I couldn't find relevant information in my knowledge base "
                    "for that query. Please try rephrasing your question or ask about "
                    "Alzheimer's disease, MCI, depression, anxiety, cognitive interventions, "
                    "caregiving, or general brain health."
                ),
                "citations": [],
                "agent_trace": traces,
                "confidence": 0.0,
                "latency_ms": int((time.time() - start) * 1000),
            }

        # --- Agent 2: Reason ---
        answer, rz_trace, citation_refs = self.reasoning.run(
            query, retrieved_docs, audience, conversation_history
        )
        traces.append({"agent": self.reasoning.name, "action": "LLM Synthesis", "result": rz_trace})

        # --- Agent 3: Validate ---
        confidence, v_trace = self.validation.run(answer, retrieved_docs, query)
        traces.append({"agent": self.validation.name, "action": "Fact Verification", "result": v_trace})

        # --- Agent 4: Synthesize ---
        final_answer, citations, s_trace = self.synthesis.run(answer, citation_refs, confidence)
        traces.append({"agent": self.synthesis.name, "action": "Response Packaging", "result": s_trace})

        return {
            "content": final_answer,
            "citations": citations,
            "agent_trace": traces,
            "confidence": confidence,
            "latency_ms": int((time.time() - start) * 1000),
        }


_pipeline: MultiAgentRAGPipeline | None = None


def get_pipeline() -> MultiAgentRAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MultiAgentRAGPipeline()
    return _pipeline
