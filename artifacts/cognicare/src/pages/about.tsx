import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BrainCircuit, Database, FileSearch, ShieldCheck, Cpu } from "lucide-react";

export function About() {
  return (
    <div className="flex-1 flex flex-col p-6 md:p-12 overflow-y-auto bg-background">
      <div className="max-w-4xl w-full mx-auto space-y-12">
        <section className="space-y-4">
          <h1 className="text-4xl font-bold font-serif tracking-tight text-primary" data-testid="text-about-title">
            About Neuroguide AI
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Neuroguide AI is an advanced educational platform designed to bridge the gap between complex medical literature and accessible health information. Utilizing a multi-agent Retrieval-Augmented Generation (RAG) architecture, it synthesizes peer-reviewed evidence into clear, understandable insights for both patients and clinicians.
          </p>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold font-serif border-b pb-2">System Architecture</h2>
          <p className="text-muted-foreground">
            When you ask a question, four specialized AI agents collaborate to formulate your answer. This pipelined approach ensures high accuracy and reduces hallucinations.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
            <AgentStep 
              number={1}
              icon={FileSearch}
              title="Retrieval"
              desc="Searches the vector database for relevant medical literature and clinical guidelines."
            />
            <AgentStep 
              number={2}
              icon={BrainCircuit}
              title="Reasoning"
              desc="Analyzes retrieved documents to extract facts relevant to your specific query."
            />
            <AgentStep 
              number={3}
              icon={ShieldCheck}
              title="Validation"
              desc="Cross-references extracted facts against sources to ensure no hallucinatory claims."
            />
            <AgentStep 
              number={4}
              icon={Cpu}
              title="Synthesis"
              desc="Drafts the final response tailored to your selected audience (Patient or Clinician)."
            />
          </div>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold font-serif border-b pb-2">Knowledge Sources</h2>
          <p className="text-muted-foreground mb-4">
            Our database is continuously updated with public-domain and open-access materials from leading health organizations.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <SourceCard name="PubMed Central" />
            <SourceCard name="Alzheimer's Association" />
            <SourceCard name="NIH MedlinePlus" />
            <SourceCard name="Cochrane Reviews" />
            <SourceCard name="CDC Guidelines" />
            <SourceCard name="WHO Reports" />
          </div>
        </section>

        <section className="mt-12 p-6 bg-muted rounded-xl border border-muted-foreground/20 text-center space-y-3">
          <h3 className="font-bold text-foreground uppercase tracking-wide text-sm">Disclaimer</h3>
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            Neuroguide AI is designed strictly for educational and informational purposes. It is not a diagnostic tool, nor does it provide medical advice, treatment recommendations, or professional clinical judgments. Always consult with a qualified healthcare provider regarding any medical condition or health objectives.
          </p>
        </section>
      </div>
    </div>
  );
}

function AgentStep({ number, icon: Icon, title, desc }: { number: number, icon: any, title: string, desc: string }) {
  return (
    <Card className="relative overflow-hidden border-muted shadow-sm">
      <div className="absolute top-0 right-0 p-4 opacity-5">
        <Icon className="w-24 h-24" />
      </div>
      <CardHeader className="pb-2">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
            {number}
          </div>
          <CardTitle className="text-base text-primary">{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground relative z-10">{desc}</p>
      </CardContent>
    </Card>
  );
}

function SourceCard({ name }: { name: string }) {
  return (
    <div className="flex items-center gap-3 p-4 bg-card border rounded-lg shadow-sm">
      <Database className="w-4 h-4 text-secondary" />
      <span className="font-medium text-sm text-card-foreground">{name}</span>
    </div>
  );
}
