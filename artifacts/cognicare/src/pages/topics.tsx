import { useTopics } from "@/hooks/use-rag";
import { Link } from "wouter";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BookOpen, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import React from "react";

export function Topics() {
  const { data: topics, isLoading } = useTopics();
  const [search, setSearch] = React.useState("");

  const filteredTopics = topics?.filter(t => t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="flex-1 flex flex-col p-6 md:p-12 overflow-y-auto bg-background">
      <div className="max-w-6xl w-full mx-auto space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl font-bold font-serif tracking-tight text-primary" data-testid="text-topics-title">
            Knowledge Topics
          </h1>
          <p className="text-lg text-muted-foreground max-w-3xl">
            Browse the specialized areas of our medical knowledge base. Our agents retrieve peer-reviewed information from these curated categories.
          </p>
        </div>

        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input 
            placeholder="Search topics..." 
            className="pl-10 bg-card border-muted"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="input-search-topics"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {isLoading ? (
             Array(8).fill(0).map((_, i) => <Skeleton key={i} className="h-48 w-full rounded-xl" />)
          ) : filteredTopics?.map(topic => (
            <Link key={topic.id} href="/chat">
              <Card className="h-full hover:shadow-md transition-shadow group cursor-pointer border-muted bg-card">
                <CardHeader className="pb-3">
                  <CardTitle className="flex items-center gap-3 text-lg text-primary group-hover:text-secondary transition-colors" data-testid={`text-topic-card-${topic.id}`}>
                    <span className="text-3xl bg-muted/50 p-2 rounded-lg" aria-hidden="true">{topic.icon}</span>
                    <span className="leading-tight">{topic.name}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <CardDescription className="line-clamp-3 leading-relaxed text-sm">
                    {topic.description}
                  </CardDescription>
                  <div className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground bg-muted/50 w-fit px-2.5 py-1 rounded-md border border-muted">
                    <BookOpen className="w-3.5 h-3.5" />
                    {topic.document_count} sources
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
          {filteredTopics?.length === 0 && (
            <div className="col-span-full py-12 text-center text-muted-foreground">
              No topics found matching "{search}"
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
