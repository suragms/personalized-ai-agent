import { Check, ExternalLink, GraduationCap, ListChecks } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { EmptyState } from "@/components/ui/empty-state";
import { useCompleteLearningItem, useLearningItems, useLearningRoadmap, useLearningSuggestions, useLearningTrends } from "@/hooks";

export default function Learning() {
  const { data: items } = useLearningItems();
  const { data: suggestions } = useLearningSuggestions();
  const { data: roadmap } = useLearningRoadmap();
  const { data: trends } = useLearningTrends();
  const complete = useCompleteLearningItem();

  const learningItems = items?.results ?? [];

  return (
    <div>
      <PageHeader title="Learning" description="Trends, suggestions, and your roadmap — generated from your stack." />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <Tabs defaultValue="suggestions">
            <TabsList>
              <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
              <TabsTrigger value="tracked">Tracked ({learningItems.length})</TabsTrigger>
              <TabsTrigger value="trends">Trends</TabsTrigger>
            </TabsList>

            <TabsContent value="suggestions">
              <Card>
                <CardContent className="space-y-2 p-4">
                  {(suggestions ?? []).length === 0 && (
                    <EmptyState title="No suggestions yet" description="Run the Learning agent to generate today's picks." />
                  )}
                  {(suggestions ?? []).map((s) => (
                    <div key={s.id} className="flex items-start gap-3 rounded-md border border-border/70 p-3">
                      <GraduationCap className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{s.title}</p>
                        <p className="text-xs text-muted">{s.reason}</p>
                      </div>
                      <Badge variant="info">{s.kind}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="tracked">
              <Card>
                <CardContent className="p-4">
                  <div className="space-y-2">
                    {learningItems.length === 0 && <EmptyState title="No tracked items" description="Add resources you want to learn from." />}
                    {learningItems.map((item) => (
                      <div key={item.id} className="flex items-center gap-3 rounded-md border border-border/70 p-3">
                        <button
                          className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-muted/40 transition-colors hover:border-primary"
                          onClick={() => {
                            complete.mutate(item.id);
                            toast.success(`Completed: ${item.title}`);
                          }}
                          aria-label={`Mark ${item.title} complete`}
                        >
                          {item.completed && <Check className="h-3 w-3 text-primary" />}
                        </button>
                        <div className="min-w-0 flex-1">
                          <p className={`truncate text-sm ${item.completed ? "line-through opacity-60" : ""}`}>{item.title}</p>
                          {item.reason && <p className="truncate text-xs text-muted">{item.reason}</p>}
                        </div>
                        {item.url && (
                          <a href={item.url} target="_blank" rel="noreferrer" className="text-muted hover:text-foreground">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <Badge variant="info">{item.kind}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="trends">
              <Card>
                <CardContent className="space-y-2 p-4">
                  {(trends?.trends ?? []).map((t) => (
                    <div key={t.title} className="flex items-start gap-3 rounded-md border border-border/70 p-3">
                      <ListChecks className="mt-0.5 h-4 w-4 shrink-0 text-[#22d3ee]" />
                      <div className="flex-1">
                        <p className="text-sm font-medium">{t.title}</p>
                        <p className="text-xs text-muted">{t.reason}</p>
                      </div>
                      <Badge variant="info">{t.kind}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Roadmap */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Your roadmap</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {roadmap ? (
              roadmap.items.map((item, i) => (
                <div key={i} className="relative pl-4">
                  <span className="absolute left-0 top-1.5 h-2 w-2 rounded-full bg-gradient-to-br from-[#6366f1] to-[#22d3ee]" />
                  <p className="text-sm font-medium">{item.topic}</p>
                  <p className="text-xs text-muted">{item.resource}</p>
                  <p className="text-xs text-muted/70">{item.why}</p>
                </div>
              ))
            ) : (
              <EmptyState title="No roadmap yet" />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
