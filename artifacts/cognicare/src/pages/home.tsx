import { useStats, useTopics } from "@/hooks/use-rag";
import { Link } from "wouter";
import { ArrowRight, Brain, Activity, BookOpen, Clock, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export function Home() {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: topics, isLoading: topicsLoading } = useTopics();

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 md:p-12 overflow-y-auto">
      <div className="max-w-4xl w-full space-y-12">
        <section className="text-center space-y-6">
          <h1 className="text-4xl md:text-6xl font-bold font-serif tracking-tight text-primary" data-testid="text-home-title">
            Evidence-Based Cognitive Health
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto" data-testid="text-home-subtitle">
            Neuroguide AI is an intelligent, multi-agent research library. Ask questions and get answers grounded in peer-reviewed medical literature.
          </p>
          <div className="pt-4">
            <Link href="/chat">
              <Button size="lg" className="text-lg px-8 py-6 h-auto rounded-full font-medium shadow-md hover:shadow-lg transition-all" data-testid="button-start-chat">
                Start a Conversation <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
        </section>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {statsLoading ? (
            Array(4).fill(0).map((_, i) => <Skeleton key={i} className="h-32 w-full rounded-xl" />)
          ) : stats ? (
            <>
              <StatCard icon={BookOpen} label="Documents" value={stats.knowledge_documents.toLocaleString()} />
              <StatCard icon={Activity} label="Topics Covered" value={stats.topics_covered.toLocaleString()} />
              <StatCard icon={ShieldCheck} label="Avg. Confidence" value={`${(stats.avg_confidence * 100).toFixed(1)}%`} />
              <StatCard icon={Clock} label="Response Time" value={`${stats.avg_response_time_ms}ms`} />
            </>
          ) : null}
        </section>

        <section className="space-y-6 pt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold font-serif">Explore Topics</h2>
            <Link href="/topics">
              <Button variant="ghost" className="text-primary hover:text-primary/80" data-testid="link-all-topics">
                View all <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {topicsLoading ? (
              Array(3).fill(0).map((_, i) => <Skeleton key={i} className="h-40 w-full rounded-xl" />)
            ) : topics ? (
              topics.slice(0, 3).map((topic) => (
                <Card key={topic.id} className="hover:shadow-md transition-shadow group cursor-pointer border-muted">
                  <CardHeader className="pb-2">
                    <CardTitle className="flex items-center gap-2 text-lg text-primary group-hover:text-secondary transition-colors" data-testid={`text-topic-${topic.id}`}>
                      <span className="text-2xl" aria-hidden="true">{topic.icon}</span>
                      {topic.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="line-clamp-2 mb-4">{topic.description}</CardDescription>
                    <div className="text-xs font-medium text-muted-foreground bg-muted inline-flex px-2 py-1 rounded-md">
                      {topic.document_count} Documents
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : null}
          </div>
        </section>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) {
  return (
    <div className="bg-card border rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-sm" data-testid={`stat-${label.toLowerCase().replace(/ /g, '-')}`}>
      <div className="p-3 bg-primary/10 rounded-full text-primary mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <div className="text-2xl font-bold text-foreground">{value}</div>
      <div className="text-sm font-medium text-muted-foreground mt-1">{label}</div>
    </div>
  );
}
