from models import Session, Message
from datetime import datetime
import uuid

sessions: dict[str, Session] = {}
messages: dict[str, list[Message]] = {}
total_queries: int = 0
total_confidence: float = 0.0


def create_session(title: str | None = None) -> Session:
    session_id = str(uuid.uuid4())
    session = Session(
        id=session_id,
        title=title or f"Session {len(sessions) + 1}",
        message_count=0,
    )
    sessions[session_id] = session
    messages[session_id] = []
    return session


def get_session(session_id: str) -> Session | None:
    return sessions.get(session_id)


def list_sessions() -> list[Session]:
    return sorted(sessions.values(), key=lambda s: s.created_at, reverse=True)


def delete_session(session_id: str) -> bool:
    if session_id in sessions:
        del sessions[session_id]
        del messages[session_id]
        return True
    return False


def add_message(message: Message) -> Message:
    global total_queries, total_confidence
    if message.session_id not in messages:
        messages[message.session_id] = []
    messages[message.session_id].append(message)
    if message.session_id in sessions:
        sessions[message.session_id].message_count += 1
        sessions[message.session_id].updated_at = datetime.utcnow().isoformat()
    if message.role == "assistant":
        total_queries += 1
        total_confidence += message.confidence
    return message


def get_messages(session_id: str) -> list[Message]:
    return messages.get(session_id, [])


def get_stats() -> dict:
    avg_confidence = (total_confidence / total_queries) if total_queries > 0 else 0.0
    return {
        "total_queries": total_queries,
        "active_sessions": len(sessions),
        "avg_confidence": round(avg_confidence, 2),
    }
