export type Session = { id: string; title: string; message_count: number; created_at: string; updated_at: string }
export type Citation = { id: string; title: string; source: string; excerpt: string; relevance_score: number }
export type AgentTrace = { agent: string; action: string; result: string }
export type Message = { id: string; session_id: string; role: "user" | "assistant"; content: string; citations: Citation[]; agent_trace: AgentTrace[]; confidence: number; created_at: string }
export type Topic = { id: string; name: string; description: string; document_count: number; icon: string }
export type Stats = { total_queries: number; active_sessions: number; knowledge_documents: number; avg_confidence: number; topics_covered: number; avg_response_time_ms: number }
export type Healthz = { status: string; openai_configured: boolean; knowledge_documents: number }

const API_BASE = '/rag';

export const api = {
  getSessions: async (): Promise<Session[]> => {
    const res = await fetch(`${API_BASE}/sessions`);
    if (!res.ok) throw new Error('Failed to fetch sessions');
    return res.json();
  },
  createSession: async (title?: string): Promise<Session> => {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error('Failed to create session');
    return res.json();
  },
  deleteSession: async (id: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/sessions/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete session');
  },
  getMessages: async (sessionId: string): Promise<Message[]> => {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
    if (!res.ok) throw new Error('Failed to fetch messages');
    return res.json();
  },
  sendMessage: async (data: { session_id: string; content: string; audience: "patient"|"clinician" }): Promise<Message> => {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to send message');
    return res.json();
  },
  getTopics: async (): Promise<Topic[]> => {
    const res = await fetch(`${API_BASE}/topics`);
    if (!res.ok) throw new Error('Failed to fetch topics');
    return res.json();
  },
  getStats: async (): Promise<Stats> => {
    const res = await fetch(`${API_BASE}/stats`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },
  getHealthz: async (): Promise<Healthz> => {
    const res = await fetch(`${API_BASE}/healthz`);
    if (!res.ok) throw new Error('Failed to fetch health');
    return res.json();
  }
};
