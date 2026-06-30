import React from "react";
import { useSessions, useCreateSession, useDeleteSession, useMessages, useSendMessage, useHealthz, useRiskAssessment } from "@/hooks/use-rag";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Checkbox } from "@/components/ui/checkbox";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertCircle, FileText, Send, Trash2, User, Bot, Plus, Loader2,
  Link2, ShieldAlert, AlertTriangle, CheckCircle2, Brain,
  ChevronDown, ChevronRight, Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { RiskResult, UserProfile } from "@/lib/api";

// ── Risk factor definitions ────────────────────────────────────────────────

const APOE4_OPTIONS = [
  { value: 0, label: "No APOE ε4 alleles",         sublabel: "ε2/ε2, ε2/ε3, ε3/ε3" },
  { value: 1, label: "1 APOE ε4 allele",           sublabel: "Heterozygous — ε3/ε4" },
  { value: 2, label: "2 APOE ε4 alleles (4/4)",    sublabel: "Homozygous — ε4/ε4" },
];

const BINARY_FACTORS = [
  { key: "hypertension",        label: "Hypertension" },
  { key: "obesity",             label: "Obesity (BMI ≥ 30)" },
  { key: "smoking",             label: "Current / Former Smoker" },
  { key: "depression",          label: "History of Depression" },
  { key: "physical_inactivity", label: "Physically Inactive" },
  { key: "diabetes",            label: "Type 2 Diabetes" },
  { key: "social_isolation",    label: "Social Isolation" },
  { key: "hearing_loss",        label: "Untreated Hearing Loss" },
  { key: "excess_alcohol",      label: "Excess Alcohol" },
  { key: "tbi_history",         label: "History of TBI" },
  { key: "high_cholesterol",    label: "High LDL Cholesterol" },
  { key: "vision_loss",         label: "Untreated Vision Loss" },
];

// ── SHAP bar chart component ───────────────────────────────────────────────

function ShapChart({ attributions }: { attributions: RiskResult["top_attributions"] }) {
  const maxAbs = Math.max(...attributions.map(a => Math.abs(a.shap_value)), 0.001);
  return (
    <div className="space-y-1.5 mt-2">
      {attributions.map((a) => {
        const pct = Math.abs(a.shap_value) / maxAbs * 100;
        const isRisk = a.impact === "risk";
        return (
          <div key={a.key} className="text-[10px]">
            <div className="flex justify-between text-muted-foreground mb-0.5">
              <span className="truncate max-w-[140px]">{a.feature}</span>
              <span className={cn("font-mono", isRisk ? "text-red-500" : "text-emerald-500")}>
                {isRisk ? "+" : "−"}{Math.abs(a.shap_value).toFixed(3)}
              </span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div
                className={cn("h-full rounded-full transition-all", isRisk ? "bg-red-400" : "bg-emerald-400")}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
      <p className="text-[9px] text-muted-foreground/60 pt-1 leading-tight">
        SHAP values show each factor's contribution to the predicted risk category.
      </p>
    </div>
  );
}

// ── Risk panel component ───────────────────────────────────────────────────

function RiskPanel({
  onProfileChange,
}: {
  onProfileChange: (profile: UserProfile | null) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [age, setAge] = React.useState(65);
  const [edu, setEdu] = React.useState(12);
  const [apoe4, setApoe4] = React.useState<0 | 1 | 2>(0);
  const [checked, setChecked] = React.useState<Record<string, boolean>>({});
  const [result, setResult] = React.useState<RiskResult | null>(() => {
    const saved = localStorage.getItem("riskResult");
    return saved ? JSON.parse(saved) : null;
  });

  const assess = useRiskAssessment();

  // Restore profile on mount
  React.useEffect(() => {
    const saved = localStorage.getItem("userProfile");
    if (saved) {
      const p = JSON.parse(saved) as UserProfile & { apoe4_alleles?: number };
      setAge(p.age);
      setEdu(p.education_years);
      if (p.apoe4_alleles !== undefined) setApoe4(p.apoe4_alleles as 0 | 1 | 2);
      const c: Record<string, boolean> = {};
      p.risk_factors.forEach(k => { c[k] = true; });
      setChecked(c);
      onProfileChange(p);
    }
  }, []);

  const handleAssess = () => {
    const activeFactors = BINARY_FACTORS.filter(f => checked[f.key]).map(f => f.key);
    const input = {
      age,
      education_years: edu,
      apoe4_alleles: apoe4,
      hypertension:        checked["hypertension"]        ?? false,
      obesity:             checked["obesity"]             ?? false,
      smoking:             checked["smoking"]             ?? false,
      depression:          checked["depression"]          ?? false,
      physical_inactivity: checked["physical_inactivity"] ?? false,
      diabetes:            checked["diabetes"]            ?? false,
      social_isolation:    checked["social_isolation"]    ?? false,
      hearing_loss:        checked["hearing_loss"]        ?? false,
      excess_alcohol:      checked["excess_alcohol"]      ?? false,
      tbi_history:         checked["tbi_history"]         ?? false,
      high_cholesterol:    checked["high_cholesterol"]    ?? false,
      vision_loss:         checked["vision_loss"]         ?? false,
    };

    assess.mutate(input, {
      onSuccess: (res) => {
        setResult(res);
        localStorage.setItem("riskResult", JSON.stringify(res));
        const profile: UserProfile = {
          age,
          education_years: edu,
          risk_factors: activeFactors,
          risk_category: res.risk_category,
        };
        localStorage.setItem("userProfile", JSON.stringify({ ...profile, apoe4_alleles: apoe4 }));
        onProfileChange(profile);
      },
    });
  };

  const riskColors: Record<string, string> = {
    Low:      "text-emerald-700 bg-emerald-50 border-emerald-200",
    Moderate: "text-amber-700   bg-amber-50   border-amber-200",
    High:     "text-red-700     bg-red-50     border-red-200",
  };

  return (
    <div className="border-t">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-semibold text-primary hover:bg-muted/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4" />
          <span>Risk Profile</span>
          {result && (
            <span className={cn("text-[10px] border px-1.5 py-0.5 rounded-full font-medium", riskColors[result.risk_category])}>
              {result.risk_category}
            </span>
          )}
        </div>
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-3">
          {/* Numeric inputs */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-[10px] text-muted-foreground uppercase tracking-wide">Age</Label>
              <input
                type="number" min={18} max={110} value={age}
                onChange={e => setAge(Number(e.target.value))}
                className="w-full mt-1 px-2 py-1.5 text-sm border rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
            <div>
              <Label className="text-[10px] text-muted-foreground uppercase tracking-wide">Edu (yrs)</Label>
              <input
                type="number" min={0} max={30} value={edu}
                onChange={e => setEdu(Number(e.target.value))}
                className="w-full mt-1 px-2 py-1.5 text-sm border rounded-md bg-background focus:outline-none focus:ring-1 focus:ring-ring"
              />
            </div>
          </div>

          {/* APOE4 status */}
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-2">APOE ε4 Status</p>
            <div className="space-y-1">
              {APOE4_OPTIONS.map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setApoe4(opt.value as 0 | 1 | 2)}
                  className={cn(
                    "w-full text-left px-2.5 py-1.5 rounded-md border text-xs transition-colors",
                    apoe4 === opt.value
                      ? "border-primary bg-primary/10 text-primary font-medium"
                      : "border-muted bg-background text-muted-foreground hover:border-primary/50"
                  )}
                >
                  <div className="font-medium leading-tight">{opt.label}</div>
                  <div className="text-[10px] opacity-60 mt-0.5">{opt.sublabel}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Risk factor checkboxes */}
          <div>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-2">Modifiable Risk Factors</p>
            <div className="space-y-1.5 max-h-44 overflow-y-auto pr-1">
              {BINARY_FACTORS.map(f => (
                <div key={f.key} className="flex items-center gap-2">
                  <Checkbox
                    id={f.key}
                    checked={!!checked[f.key]}
                    onCheckedChange={v => setChecked(c => ({ ...c, [f.key]: !!v }))}
                    className="h-3.5 w-3.5"
                  />
                  <label htmlFor={f.key} className="text-xs text-muted-foreground cursor-pointer leading-tight">
                    {f.label}
                  </label>
                </div>
              ))}
            </div>
          </div>

          <Button
            size="sm" className="w-full text-xs" onClick={handleAssess}
            disabled={assess.isPending}
          >
            {assess.isPending ? <><Loader2 className="w-3 h-3 mr-1 animate-spin" />Assessing…</> : "Assess Risk"}
          </Button>

          {/* Result card */}
          {result && (
            <div className={cn("border rounded-lg p-3 space-y-2", riskColors[result.risk_category])}>
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold">Educational Risk</span>
                <span className="text-sm font-bold">{result.risk_category}</span>
              </div>
              <div className="flex gap-1 text-[10px]">
                {Object.entries(result.probabilities).map(([k, v]) => (
                  <div key={k} className="flex-1 text-center bg-white/50 rounded p-1">
                    <div className="font-bold">{(v * 100).toFixed(0)}%</div>
                    <div className="opacity-70">{k}</div>
                  </div>
                ))}
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-wide mb-1 opacity-70">SHAP Feature Attribution</p>
                <ShapChart attributions={result.top_attributions} />
              </div>
              <p className="text-[9px] opacity-60 leading-tight">{result.disclaimer}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Chat component ────────────────────────────────────────────────────

export function Chat() {
  const [sessionId, setSessionId] = React.useState<string | null>(
    () => sessionStorage.getItem("activeSessionId")
  );
  const [audience, setAudience] = React.useState<"patient" | "clinician">(
    () => (localStorage.getItem("audience") as "patient" | "clinician") || "patient"
  );
  const [input, setInput] = React.useState("");
  const [userProfile, setUserProfile] = React.useState<UserProfile | null>(null);

  const { data: health }   = useHealthz();
  const { data: sessions, isLoading: sessionsLoading } = useSessions();
  const { data: messages,  isLoading: messagesLoading } = useMessages(sessionId || undefined);

  const createSession = useCreateSession();
  const deleteSession = useDeleteSession();
  const sendMessage   = useSendMessage();

  const scrollRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (sessionId) sessionStorage.setItem("activeSessionId", sessionId);
  }, [sessionId]);

  React.useEffect(() => {
    localStorage.setItem("audience", audience);
  }, [audience]);

  // Validate / auto-create session
  React.useEffect(() => {
    if (sessionsLoading || createSession.isPending) return;

    if (!sessions || sessions.length === 0) {
      sessionStorage.removeItem("activeSessionId");
      createSession.mutate(undefined, {
        onSuccess: (s) => setSessionId(s.id),
      });
      return;
    }

    const stillExists = sessionId && sessions.some(s => s.id === sessionId);
    if (!stillExists) {
      sessionStorage.removeItem("activeSessionId");
      setSessionId(sessions[0].id);
    }
  }, [sessions, sessionsLoading, createSession.isPending]);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, sendMessage.isPending]);

  const handleSend = () => {
    if (!input.trim() || !sessionId) return;
    const content = input;
    setInput("");
    sendMessage.mutate(
      { session_id: sessionId, content, audience, user_profile: userProfile },
      {
        onError: (err) => {
          if (err.message?.includes("404") || err.message?.includes("Session not found")) {
            sessionStorage.removeItem("activeSessionId");
            setSessionId(null);
            createSession.mutate(undefined, {
              onSuccess: (newSession) => {
                setSessionId(newSession.id);
                sendMessage.mutate({ session_id: newSession.id, content, audience, user_profile: userProfile });
              },
            });
          }
        },
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleDeleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteSession.mutate(id, {
      onSuccess: () => { if (id === sessionId) setSessionId(null); },
    });
  };

  const isConfigured = health?.openai_configured !== false;

  return (
    <div className="flex-1 flex overflow-hidden bg-background">
      {/* ── Sidebar ── */}
      <div className="w-64 border-r bg-card flex flex-col">
        {/* Sessions header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="font-semibold text-lg text-primary" data-testid="text-sidebar-title">Sessions</h2>
          <Button
            variant="ghost" size="icon"
            onClick={() => createSession.mutate(undefined, { onSuccess: (s) => setSessionId(s.id) })}
            disabled={createSession.isPending}
            data-testid="button-new-session"
          >
            <Plus className="w-4 h-4" />
          </Button>
        </div>

        {/* Session list — capped so Risk Profile stays visible */}
        <ScrollArea className="max-h-48 overflow-y-auto">
          <div className="p-2 space-y-1">
            {sessionsLoading ? (
              <div className="p-4 text-center text-sm text-muted-foreground">Loading…</div>
            ) : sessions?.length === 0 ? (
              <div className="p-4 text-center text-sm text-muted-foreground">No sessions</div>
            ) : (
              sessions?.map(session => (
                <div
                  key={session.id}
                  onClick={() => setSessionId(session.id)}
                  className={cn(
                    "flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors group text-sm",
                    sessionId === session.id
                      ? "bg-primary/10 text-primary font-medium"
                      : "hover:bg-muted text-muted-foreground hover:text-foreground"
                  )}
                  data-testid={`session-item-${session.id}`}
                >
                  <div className="truncate flex-1">{session.title || "New Conversation"}</div>
                  <Button
                    variant="ghost" size="icon"
                    className="h-6 w-6 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    data-testid={`button-delete-session-${session.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </ScrollArea>

        {/* ── Risk Profile Panel (integrated) ── */}
        <RiskPanel onProfileChange={setUserProfile} />
      </div>

      {/* ── Main Chat Area ── */}
      <div className="flex-1 flex flex-col relative min-w-0">
        {!isConfigured && (
          <Alert variant="destructive" className="m-4 border-destructive/50 bg-destructive/10 text-destructive-foreground">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>API Key Not Configured</AlertTitle>
            <AlertDescription>
              The OpenAI API key is missing. The system cannot generate answers until configured.
            </AlertDescription>
          </Alert>
        )}

        {/* Top bar */}
        <div className="h-14 border-b flex items-center justify-between px-4 bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="text-sm font-medium text-muted-foreground md:hidden truncate max-w-[200px]">
            {sessions?.find(s => s.id === sessionId)?.title || "Chat"}
          </div>
          <div className="flex items-center gap-3 ml-auto bg-muted/50 p-1.5 rounded-lg border">
            <Label
              htmlFor="audience-toggle"
              className={cn("text-xs font-medium cursor-pointer", audience === "patient" ? "text-primary" : "text-muted-foreground")}
            >
              Patient
            </Label>
            <Switch
              id="audience-toggle"
              checked={audience === "clinician"}
              onCheckedChange={(c) => setAudience(c ? "clinician" : "patient")}
              data-testid="switch-audience"
            />
            <Label
              htmlFor="audience-toggle"
              className={cn("text-xs font-medium cursor-pointer", audience === "clinician" ? "text-primary" : "text-muted-foreground")}
            >
              Clinician
            </Label>
          </div>
        </div>

        {/* Active profile badge */}
        {userProfile?.risk_category && (
          <div className="px-4 pt-3 pb-0">
            <div className="max-w-4xl mx-auto">
              <div className="inline-flex items-center gap-2 text-[11px] bg-primary/5 border border-primary/20 text-primary px-3 py-1.5 rounded-full">
                <Activity className="w-3 h-3" />
                Personalisation active — {userProfile.risk_category} risk profile · age {userProfile.age} · {userProfile.risk_factors.length} risk factors
              </div>
            </div>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6" ref={scrollRef}>
          {messagesLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : !messages?.length ? (
            <div className="h-full flex flex-col items-center justify-center text-center space-y-4 max-w-md mx-auto p-8">
              <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center mb-4">
                <Brain className="w-8 h-8" />
              </div>
              <h3 className="text-2xl font-serif font-semibold text-primary">How can I help?</h3>
              <p className="text-muted-foreground">
                Ask a question about cognitive health, Alzheimer's disease, or memory care.
                Fill in your Risk Profile in the sidebar to receive personalised responses.
              </p>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={cn("flex gap-4 max-w-4xl mx-auto", msg.role === "user" ? "flex-row-reverse" : "flex-row")}
                data-testid={`message-${msg.id}`}
              >
                <div className={cn(
                  "w-8 h-8 shrink-0 rounded-full flex items-center justify-center shadow-sm",
                  msg.role === "user" ? "bg-secondary text-secondary-foreground" : "bg-primary text-primary-foreground"
                )}>
                  {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div className={cn("flex flex-col gap-2 min-w-0 max-w-[85%]", msg.role === "user" ? "items-end" : "items-start")}>
                  <div className={cn(
                    "p-4 rounded-2xl shadow-sm text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-secondary text-secondary-foreground rounded-tr-sm"
                      : "bg-card border rounded-tl-sm text-card-foreground whitespace-pre-wrap"
                  )}>
                    {msg.content}
                  </div>

                  {msg.role === "assistant" && msg.confidence !== undefined && (
                    <div className="flex items-center gap-2 mt-1">
                      <ConfidenceBadge score={msg.confidence} />
                    </div>
                  )}

                  {/* Citations */}
                  {msg.role === "assistant" && msg.citations?.length > 0 && (
                    <Accordion type="single" collapsible className="w-full mt-2 bg-card border rounded-lg overflow-hidden shadow-sm" data-testid={`citations-${msg.id}`}>
                      <AccordionItem value="citations" className="border-none">
                        <AccordionTrigger className="px-4 py-2 hover:bg-muted/50 text-xs font-medium text-muted-foreground data-[state=open]:border-b">
                          <div className="flex items-center gap-2">
                            <FileText className="w-3.5 h-3.5" />
                            {msg.citations.length} Sources Referenced
                          </div>
                        </AccordionTrigger>
                        <AccordionContent className="p-0">
                          <div className="divide-y max-h-[300px] overflow-y-auto bg-muted/20">
                            {msg.citations.map((cit, i) => (
                              <div key={i} className="p-4 text-xs space-y-2 hover:bg-muted/50 transition-colors">
                                <div className="flex items-start justify-between gap-4">
                                  <div className="font-semibold text-foreground line-clamp-1">{cit.title}</div>
                                  <div className="text-[10px] bg-background border px-1.5 py-0.5 rounded text-muted-foreground whitespace-nowrap">
                                    Score: {cit.relevance_score.toFixed(2)}
                                  </div>
                                </div>
                                <div className="text-muted-foreground flex items-center gap-1.5">
                                  <Link2 className="w-3 h-3" />
                                  <span className="truncate">{cit.source}</span>
                                </div>
                                <div className="p-2.5 bg-background border rounded text-muted-foreground italic leading-relaxed">
                                  "{cit.excerpt}"
                                </div>
                              </div>
                            ))}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  )}

                  {/* Agent Trace */}
                  {msg.role === "assistant" && msg.agent_trace?.length > 0 && (
                    <Accordion type="single" collapsible className="w-full mt-2" data-testid={`trace-${msg.id}`}>
                      <AccordionItem value="trace" className="border rounded-lg bg-card/50 shadow-sm overflow-hidden">
                        <AccordionTrigger className="px-4 py-2 hover:bg-muted/50 text-[11px] font-mono text-muted-foreground uppercase tracking-wider">
                          View Agent Trace ({msg.agent_trace.length} agents)
                        </AccordionTrigger>
                        <AccordionContent className="px-4 py-3 bg-muted/30 font-mono text-xs text-muted-foreground space-y-3">
                          {msg.agent_trace.map((trace, i) => (
                            <div key={i} className="flex flex-col gap-1">
                              <div className="flex items-center gap-2 text-foreground font-semibold">
                                <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded border border-primary/20">
                                  {trace.agent}
                                </span>
                                <span>{trace.action}</span>
                              </div>
                              <div className="pl-2 border-l-2 border-muted ml-1 italic text-muted-foreground/80">
                                {trace.result}
                              </div>
                            </div>
                          ))}
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  )}
                </div>
              </div>
            ))
          )}

          {sendMessage.isPending && (
            <div className="flex gap-4 max-w-4xl mx-auto">
              <div className="w-8 h-8 shrink-0 bg-primary text-primary-foreground rounded-full flex items-center justify-center shadow-sm">
                <Bot className="w-4 h-4" />
              </div>
              <div className="p-4 rounded-2xl bg-card border rounded-tl-sm text-card-foreground shadow-sm flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Thinking…</span>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-background border-t">
          <div className="max-w-4xl mx-auto relative flex items-end gap-2">
            <textarea
              className="flex min-h-[56px] w-full rounded-xl border border-input bg-card px-4 py-3 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 resize-none pr-12"
              placeholder="Ask about symptoms, treatments, or research…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={sendMessage.isPending || !sessionId || !isConfigured}
              rows={Math.min(5, input.split("\n").length)}
              data-testid="input-chat"
            />
            <Button
              size="icon"
              className="absolute right-2 bottom-2 h-10 w-10 rounded-lg shrink-0"
              onClick={handleSend}
              disabled={!input.trim() || sendMessage.isPending || !sessionId || !isConfigured}
              data-testid="button-send"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <div className="text-center mt-2">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wide font-medium">
              Educational purposes only. Not medical advice.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBadge({ score }: { score: number }) {
  if (score >= 0.75) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
        <CheckCircle2 className="w-3 h-3" /> High Confidence
      </span>
    );
  }
  if (score >= 0.50) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
        <AlertTriangle className="w-3 h-3" /> Moderate Confidence
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-destructive bg-destructive/10 border border-destructive/20 px-2 py-0.5 rounded-full">
      <ShieldAlert className="w-3 h-3" /> Low Confidence
    </span>
  );
}
