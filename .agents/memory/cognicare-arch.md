---
name: CogniCare 5-agent pipeline and integration points
description: Key non-obvious decisions in the CogniCare multi-agent RAG system.
---

**5-agent order:** PersonalizationAgent (4th) runs FIRST to build context → RetrievalAgent → ReasoningAgent → ValidationAgent → SynthesisAgent (5th). Personalisation before retrieval so the LLM prompt already contains user profile context.

**Hybrid retrieval:** TF-IDF sparse (sklearn) + LSA/TruncatedSVD dense, blended 0.45 sparse + 0.55 dense after per-query min-max normalisation. Index built at module load time (singleton). Query expansion dict maps casual terms to indexed vocabulary.

**Risk model:** RandomForest trained on 2000 synthetic samples with Lancet Commission 2024 risk-factor weights. Labels use 40th/75th percentile thresholds (Low/Moderate/High). SHAP TreeExplainer for XAI. Model is a singleton loaded in FastAPI lifespan.

**Frontend integration:** Risk Profile panel lives in the Chat page sidebar (not a separate page). Profile stored in localStorage, passed as `user_profile` to every chat message. Profile badge shown in chat header when active.

**Why singleton pipeline/model:** FastAPI lifespan pre-warms both at startup; avoids cold-start latency on first request.
