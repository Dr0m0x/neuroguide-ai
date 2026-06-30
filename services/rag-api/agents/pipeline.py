"""
Multi-Agent RAG Pipeline for CogniCare
========================================
Five specialised agents:
  1. Retrieval Agent      — Hybrid sparse (TF-IDF) + dense (LSA) retrieval
  2. Reasoning Agent      — Synthesises retrieved evidence using OpenAI
  3. Validation Agent     — Cross-checks response claims against sources
  4. Personalization Agent— Tailors response to user profile if provided
  5. Synthesis Agent      — Formats the final grounded response with citations
"""

from __future__ import annotations
import os, time, re
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
from knowledge.documents import KNOWLEDGE_DOCUMENTS


# ---------------------------------------------------------------------------
# Build the TF-IDF + LSA (dense) index once at module load time
# ---------------------------------------------------------------------------

_vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2),
    max_features=8000,
    sublinear_tf=True,
)
# Title weighted 2× for stronger signal
_corpus = [f"{doc['title']} {doc['title']} {doc['content']}" for doc in KNOWLEDGE_DOCUMENTS]
_tfidf_matrix = _vectorizer.fit_transform(_corpus)

# LSA (Latent Semantic Analysis) — dense semantic representations via SVD
_n_components = min(100, len(KNOWLEDGE_DOCUMENTS) - 1)
_svd = TruncatedSVD(n_components=_n_components, random_state=42)
_lsa_matrix = _svd.fit_transform(_tfidf_matrix)   # shape: (n_docs, n_components)


# ---------------------------------------------------------------------------
# Query expansion — map casual / misspelled terms to indexed vocabulary
# ---------------------------------------------------------------------------

_QUERY_EXPANSIONS: dict[str, str] = {
    "alzheimers":       "alzheimer's disease dementia",
    "alzheimer":        "alzheimer's disease dementia",
    "alz":              "alzheimer's disease dementia",
    "dementia":         "alzheimer's disease dementia cognitive impairment",
    "memory loss":      "alzheimer's disease memory cognitive impairment",
    "memory problems":  "alzheimer's disease memory cognitive decline",
    "forgetfulness":    "memory loss cognitive impairment alzheimer",
    "mci":              "mild cognitive impairment mci",
    "mild cognitive":   "mild cognitive impairment mci",
    "depression":       "depression late-life depressive cognitive",
    "anxiety":          "anxiety generalized cognitive worry",
    "sleep":            "sleep glymphatic insomnia cognitive",
    "exercise":         "exercise physical activity aerobic cognitive brain",
    "diet":             "diet mind mediterranean nutrition cognitive",
    "caregiver":        "caregiver dementia caregiving burnout burden",
    "brain health":     "brain health cognitive reserve neuroplasticity",
    "genetics":         "apoe gene genetic risk alzheimer's",
    "medication":       "treatment cholinesterase inhibitor memantine donepezil",
    "treatment":        "treatment cholinesterase inhibitor memantine lecanemab",
    "gut":              "gut microbiome brain axis cognitive",
    "omega":            "omega-3 fatty acid dha epa cognitive",
    "loneliness":       "social isolation loneliness cognitive dementia",
    "trauma":           "ptsd trauma dementia hippocampus",
    "head injury":      "traumatic brain injury tbi dementia cte",
    "tbi":              "traumatic brain injury tbi dementia",
    "biomarker":        "biomarker amyloid tau blood plasma p-tau",
    "blood test":       "blood biomarker plasma p-tau amyloid",
    "lecanemab":        "lecanemab anti-amyloid immunotherapy clarity ad",
    "leqembi":          "lecanemab anti-amyloid immunotherapy clarity ad",
    "donanemab":        "donanemab anti-amyloid immunotherapy trailblazer",
    "apoe":             "apoe4 genetic risk alzheimer's epsilon",
    "inflammation":     "neuroinflammation microglia trem2 cytokine",
    "vascular":         "vascular cognitive impairment dementia stroke",
    "cognitive reserve":"cognitive reserve education bilingualism brain resilience",
    "social":           "social engagement loneliness isolation cognitive",
    "shap":             "risk factors feature importance explainability",
    "risk":             "risk factors prevention modifiable lifestyle",
}


def _expand_query(query: str) -> str:
    q_lower = query.lower().strip()
    parts = [query]
    for key, expansion in _QUERY_EXPANSIONS.items():
        if key in q_lower:
            parts.append(expansion)
    return " ".join(parts)


def _get_openai_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Agent 1 — Retrieval Agent  (Hybrid: TF-IDF sparse + LSA dense)
# ---------------------------------------------------------------------------

class RetrievalAgent:
    """
    Hybrid retrieval combining sparse TF-IDF cosine similarity with dense
    Latent Semantic Analysis (LSA/SVD) embeddings for semantic matching.
    Final score = 0.45 × sparse + 0.55 × dense.
    """

    name = "Retrieval Agent"

    def run(self, query: str, top_k: int = 5) -> tuple[list[dict], str]:
        expanded = _expand_query(query)

        # Sparse (TF-IDF)
        q_tfidf = _vectorizer.transform([expanded])
        sparse_scores = cosine_similarity(q_tfidf, _tfidf_matrix).flatten()

        # Dense (LSA semantic)
        q_lsa = _svd.transform(q_tfidf)          # shape: (1, n_components)
        dense_scores = cosine_similarity(q_lsa, _lsa_matrix).flatten()

        # Hybrid — normalise each to [0,1] then blend
        def _norm(arr: np.ndarray) -> np.ndarray:
            mn, mx = arr.min(), arr.max()
            return (arr - mn) / (mx - mn + 1e-9)

        hybrid = 0.45 * _norm(sparse_scores) + 0.55 * _norm(dense_scores)
        top_indices = np.argsort(hybrid)[::-1][:top_k]

        retrieved = []
        for idx in top_indices:
            doc = KNOWLEDGE_DOCUMENTS[idx]
            retrieved.append({
                **doc,
                "relevance_score": round(float(hybrid[idx]), 4),
                "sparse_score":    round(float(sparse_scores[idx]), 4),
                "dense_score":     round(float(dense_scores[idx]), 4),
            })

        top = retrieved[0] if retrieved else None
        trace = (
            f"Hybrid retrieval: TF-IDF + LSA over {len(KNOWLEDGE_DOCUMENTS)} documents "
            f"({len(expanded.split())} query terms after expansion). "
            f"Top: '{top['title']}' — hybrid={top['relevance_score']:.3f} "
            f"(sparse={top['sparse_score']:.3f}, dense={top['dense_score']:.3f})."
            if top else "No documents retrieved."
        )
        return retrieved, trace


# ---------------------------------------------------------------------------
# Agent 2 — Reasoning Agent
# ---------------------------------------------------------------------------

class ReasoningAgent:
    """Synthesises retrieved evidence into a coherent answer using OpenAI."""

    name = "Reasoning Agent"

    def run(
        self,
        query: str,
        retrieved_docs: list[dict],
        audience: str = "patient",
        conversation_history: list[dict] | None = None,
        personalization_context: str = "",
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
                history_messages.append({"role": msg["role"], "content": msg["content"]})

        personalization_block = (
            f"\nUSER PROFILE CONTEXT:\n{personalization_context}\n"
            if personalization_context else ""
        )

        system_prompt = f"""You are an evidence-based cognitive health education assistant.
Your role is to provide accurate, compassionate, and evidence-grounded information about cognitive health topics.

AUDIENCE: {audience_instruction}
{personalization_block}
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
            max_tokens=900,
        )

        answer = response.choices[0].message.content or ""
        usage  = response.usage
        trace  = (
            f"Synthesised response via gpt-4o-mini. "
            f"Tokens — input: {usage.prompt_tokens}, output: {usage.completion_tokens}. "
            f"Sources used: {len(retrieved_docs)}."
            + (f" Personalisation context applied." if personalization_context else "")
        )
        citation_refs = [{"doc": doc, "position": i + 1} for i, doc in enumerate(retrieved_docs)]
        return answer, trace, citation_refs


# ---------------------------------------------------------------------------
# Agent 3 — Validation Agent
# ---------------------------------------------------------------------------

class ValidationAgent:
    """Cross-checks the generated response against retrieved sources."""

    name = "Validation Agent"

    def run(self, response: str, retrieved_docs: list[dict], query: str) -> tuple[float, str]:
        if not retrieved_docs:
            return 0.1, "No source documents available for validation."

        resp_lower = response.lower()

        keyword_hits = 0
        total_checks = 0
        for doc in retrieved_docs:
            for term in self._extract_key_terms(doc["content"]):
                total_checks += 1
                if term.lower() in resp_lower:
                    keyword_hits += 1

        keyword_ratio = keyword_hits / total_checks if total_checks > 0 else 0

        disclaimer_present = any(
            p in resp_lower
            for p in ["consult", "doctor", "healthcare", "professional", "physician",
                       "medical advice", "speak with", "not a substitute"]
        )

        hallucination_signals = [
            "definitely", "100%", "guaranteed", "always works",
            "cure", "cured", "no risk", "completely safe",
        ]
        hall_count = sum(1 for s in hallucination_signals if s in resp_lower)

        confidence = (
              0.4 * min(retrieved_docs[0]["relevance_score"] * 4, 1.0)
            + 0.3 * min(keyword_ratio * 3, 1.0)
            + 0.2 * (1.0 if disclaimer_present else 0.0)
            + 0.1 * max(0.0, 1.0 - hall_count * 0.3)
        )
        confidence = round(min(max(confidence, 0.0), 1.0), 3)

        trace = (
            f"Validation complete. Keyword coverage: {keyword_ratio:.1%}. "
            f"Disclaimer present: {disclaimer_present}. "
            f"Hallucination signals: {hall_count}. "
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
# Agent 4 — Personalization Agent
# ---------------------------------------------------------------------------

class PersonalizationAgent:
    """
    Generates a personalised context string from the user's risk profile
    so the Reasoning Agent can tailor its response appropriately.
    Returns an empty string (no-op) when no profile is provided.
    """

    name = "Personalization Agent"

    _FACTOR_LABELS: dict[str, str] = {
        "hypertension":        "hypertension",
        "obesity":             "obesity",
        "smoking":             "smoking history",
        "depression":          "history of depression",
        "physical_inactivity": "physical inactivity",
        "diabetes":            "type 2 diabetes",
        "social_isolation":    "social isolation",
        "hearing_loss":        "untreated hearing loss",
        "excess_alcohol":      "excess alcohol consumption",
        "tbi_history":         "history of traumatic brain injury",
        "high_cholesterol":    "high LDL cholesterol",
        "vision_loss":         "untreated vision loss",
    }

    def run(self, user_profile: dict | None) -> tuple[str, str]:
        if not user_profile:
            return "", "No user profile provided — personalisation skipped."

        age            = user_profile.get("age")
        edu            = user_profile.get("education_years")
        risk_category  = user_profile.get("risk_category", "Unknown")
        raw_factors    = user_profile.get("risk_factors", [])

        active = [
            self._FACTOR_LABELS[f]
            for f in raw_factors
            if f in self._FACTOR_LABELS
        ]

        parts: list[str] = []
        if age:
            parts.append(f"The user is {age} years old.")
        if edu:
            parts.append(f"They completed {edu} years of formal education.")
        if active:
            parts.append(
                f"Their reported modifiable risk factors include: {', '.join(active)}."
            )
        if risk_category and risk_category != "Unknown":
            parts.append(
                f"Their educational risk profile is classified as {risk_category}. "
                "Where relevant, tailor examples, lifestyle recommendations, and "
                "communication style to this profile. Emphasise actionable modifiable "
                "factors most relevant to their situation."
            )

        context = " ".join(parts) if parts else ""

        trace = (
            f"Personalisation applied — age: {age}, education: {edu} yrs, "
            f"risk category: {risk_category}, "
            f"active risk factors: {len(active)} ({', '.join(active[:3])}{'…' if len(active) > 3 else ''})."
            if parts else "Personalisation agent: no profile data to apply."
        )
        return context, trace


# ---------------------------------------------------------------------------
# Agent 5 — Synthesis Agent
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
            doc    = ref["doc"]
            excerpt = doc["content"][:300].rstrip()
            if len(doc["content"]) > 300:
                excerpt += "..."
            citations.append({
                "id":              doc["id"],
                "title":           doc["title"],
                "source":          doc["source"],
                "excerpt":         excerpt,
                "relevance_score": doc["relevance_score"],
            })

        label = (
            "High"     if confidence >= 0.75
            else "Moderate" if confidence >= 0.50
            else "Low"
        )
        trace = (
            f"Synthesis complete. Citations packaged: {len(citations)}. "
            f"Confidence: {label} ({confidence:.1%})."
        )
        return response, citations, trace


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class MultiAgentRAGPipeline:
    """Five-agent RAG pipeline: Retrieval → Reasoning → Validation → Personalisation → Synthesis."""

    def __init__(self) -> None:
        self.retrieval       = RetrievalAgent()
        self.reasoning       = ReasoningAgent()
        self.validation      = ValidationAgent()
        self.personalization = PersonalizationAgent()
        self.synthesis       = SynthesisAgent()

    def run(
        self,
        query: str,
        audience: str = "patient",
        conversation_history: list[dict] | None = None,
        user_profile: dict | None = None,
    ) -> dict[str, Any]:
        start  = time.time()
        traces: list[dict] = []

        # Agent 4 — Personalisation (runs first to build context for Agent 2)
        persona_ctx, p_trace = self.personalization.run(user_profile)
        traces.append({
            "agent":  self.personalization.name,
            "action": "Profile Analysis",
            "result": p_trace,
        })

        # Agent 1 — Retrieve
        retrieved_docs, r_trace = self.retrieval.run(query, top_k=5)
        traces.append({
            "agent":  self.retrieval.name,
            "action": "Hybrid Vector Search",
            "result": r_trace,
        })

        if not retrieved_docs:
            return {
                "content": (
                    "I'm sorry, I couldn't find relevant information in my knowledge base "
                    "for that query. Please try rephrasing your question or ask about "
                    "Alzheimer's disease, MCI, depression, anxiety, cognitive interventions, "
                    "caregiving, or general brain health."
                ),
                "citations":    [],
                "agent_trace":  traces,
                "confidence":   0.0,
                "latency_ms":   int((time.time() - start) * 1000),
            }

        # Agent 2 — Reason
        answer, rz_trace, citation_refs = self.reasoning.run(
            query, retrieved_docs, audience, conversation_history, persona_ctx
        )
        traces.append({"agent": self.reasoning.name, "action": "LLM Synthesis", "result": rz_trace})

        # Agent 3 — Validate
        confidence, v_trace = self.validation.run(answer, retrieved_docs, query)
        traces.append({"agent": self.validation.name, "action": "Fact Verification", "result": v_trace})

        # Agent 5 — Synthesise
        final_answer, citations, s_trace = self.synthesis.run(answer, citation_refs, confidence)
        traces.append({"agent": self.synthesis.name, "action": "Response Packaging", "result": s_trace})

        return {
            "content":     final_answer,
            "citations":   citations,
            "agent_trace": traces,
            "confidence":  confidence,
            "latency_ms":  int((time.time() - start) * 1000),
        }


_pipeline: MultiAgentRAGPipeline | None = None


def get_pipeline() -> MultiAgentRAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = MultiAgentRAGPipeline()
    return _pipeline
