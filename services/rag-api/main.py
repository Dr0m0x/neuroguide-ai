"""
CogniCare RAG API
=================
FastAPI backend serving the multi-agent RAG pipeline at /rag/.
"""

import os
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import (
    Message, MessageInput, Session, SessionCreate,
    Topic, Stats, RiskInput, RiskResult, ShapAttribution,
)
from storage import (
    create_session, get_session, list_sessions, delete_session,
    add_message, get_messages, get_stats,
)
from knowledge.documents import TOPIC_CATEGORIES, KNOWLEDGE_DOCUMENTS


@asynccontextmanager
async def lifespan(app: FastAPI):
    from agents.pipeline import get_pipeline
    from agents.risk_model import get_risk_model
    get_pipeline()
    get_risk_model()
    yield


app = FastAPI(
    title="CogniCare RAG API",
    description="Multi-agent Retrieval-Augmented Generation for cognitive health education",
    version="2.0.0",
    lifespan=lifespan,
    root_path="/rag",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Routes: Health
# ---------------------------------------------------------------------------

@app.get("/healthz")
def health_check():
    openai_configured = bool(os.environ.get("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "openai_configured": openai_configured,
        "knowledge_documents": len(KNOWLEDGE_DOCUMENTS),
    }


# ---------------------------------------------------------------------------
# Routes: Sessions
# ---------------------------------------------------------------------------

@app.get("/sessions", response_model=list[Session])
def list_all_sessions():
    return list_sessions()


@app.post("/sessions", response_model=Session, status_code=201)
def create_new_session(body: SessionCreate):
    return create_session(body.title)


@app.delete("/sessions/{session_id}", status_code=204)
def delete_session_route(session_id: str):
    if not delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions/{session_id}/messages", response_model=list[Message])
def get_session_messages(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return get_messages(session_id)


# ---------------------------------------------------------------------------
# Routes: Chat
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=Message)
def chat(body: MessageInput):
    from agents.pipeline import get_pipeline

    session = get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_msg = Message(
        id=str(uuid.uuid4()),
        session_id=body.session_id,
        role="user",
        content=body.content,
    )
    add_message(user_msg)

    history = [
        {"role": m.role, "content": m.content}
        for m in get_messages(body.session_id)[:-1]
    ]

    try:
        pipeline = get_pipeline()
        result = pipeline.run(
            query=body.content,
            audience=body.audience,
            conversation_history=history,
            user_profile=body.user_profile,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        err = str(e)
        if "insufficient_quota" in err or "RateLimitError" in type(e).__name__:
            raise HTTPException(
                status_code=402,
                detail="OpenAI quota exceeded. Please add billing credits at platform.openai.com → Billing.",
            )
        if "AuthenticationError" in type(e).__name__ or "invalid_api_key" in err:
            raise HTTPException(
                status_code=401,
                detail="Invalid OpenAI API key. Please check your key in the Secrets panel.",
            )
        raise HTTPException(status_code=500, detail=f"Pipeline error: {err}")

    assistant_msg = Message(
        id=str(uuid.uuid4()),
        session_id=body.session_id,
        role="assistant",
        content=result["content"],
        citations=result["citations"],
        agent_trace=result["agent_trace"],
        confidence=result["confidence"],
    )
    add_message(assistant_msg)
    return assistant_msg


# ---------------------------------------------------------------------------
# Routes: Risk Assessment (XAI)
# ---------------------------------------------------------------------------

@app.post("/risk-assessment", response_model=RiskResult)
def risk_assessment(body: RiskInput):
    from agents.risk_model import get_risk_model

    features = body.model_dump()
    try:
        result = get_risk_model().predict(features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk model error: {e}")

    return RiskResult(
        risk_category=result["risk_category"],
        risk_color=result["risk_color"],
        probabilities=result["probabilities"],
        top_attributions=[ShapAttribution(**a) for a in result["top_attributions"]],
        disclaimer=result["disclaimer"],
    )


# ---------------------------------------------------------------------------
# Routes: Topics & Stats
# ---------------------------------------------------------------------------

@app.get("/topics", response_model=list[Topic])
def get_topics():
    return [
        Topic(
            id=t["id"], name=t["name"], description=t["description"],
            document_count=t["document_count"], icon=t["icon"],
        )
        for t in TOPIC_CATEGORIES
    ]


@app.get("/stats", response_model=Stats)
def get_system_stats():
    storage_stats = get_stats()
    return Stats(
        total_queries=storage_stats["total_queries"],
        active_sessions=storage_stats["active_sessions"],
        knowledge_documents=len(KNOWLEDGE_DOCUMENTS),
        avg_confidence=storage_stats["avg_confidence"],
        topics_covered=len(TOPIC_CATEGORIES),
        avg_response_time_ms=2400,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "5001"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
