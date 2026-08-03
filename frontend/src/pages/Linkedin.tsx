import { CalendarClock, Linkedin as LinkedinIcon, PenLine, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { RadialScore } from "@/components/charts/RadialScore";
import { EmptyState } from "@/components/ui/empty-state";
import { useGeneratePost, useLinkedinAnalyze, useLinkedinPosts, useLinkedinProfile, usePostingTime } from "@/hooks";

export default function Linkedin() {
  const { data: analyze } = useLinkedinAnalyze();
  const { data: profile } = useLinkedinProfile();
  const { data: posts } = useLinkedinPosts();
  const { data: postingTime } = usePostingTime();
  const generatePost = useGeneratePost();

  const breakdown = analyze?.breakdown ?? {};
  const suggestions = analyze?.suggestions ?? [];
  const postList = posts?.results ?? [];

  async function onGeneratePost() {
    try {
      await generatePost.mutateAsync();
      toast.success("LinkedIn post drafted from your recent work");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Post generation failed");
    }
  }

  return (
    <div>
      <PageHeader
        title="LinkedIn Optimization"
        description="Profile score, suggestions, and post ideas — powered by your work data."
        action={
          <Button onClick={onGeneratePost} disabled={generatePost.isPending}>
            <PenLine className="h-4 w-4" /> Generate post idea
          </Button>
        }
      />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Score */}
        <Card>
          <CardContent className="flex flex-col items-center gap-2 p-4">
            <p className="text-sm font-medium">Profile score</p>
            <RadialScore value={analyze?.score ?? 0} label="recruiter visibility" size={160} />
            <p className="text-center text-xs text-muted">
              Headline, About, experience, skills, and keyword coverage.
            </p>
            {profile && (
              <div className="w-full rounded-lg bg-muted/10 p-3 text-center">
                <p className="text-sm font-medium">{profile.headline || "No headline yet"}</p>
                <p className="text-xs text-muted">{profile.skills.length} skills · {profile.experience.length} roles</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Breakdown + suggestions */}
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Analysis breakdown</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              {Object.entries(breakdown).map(([key, value]) => {
                const max = key === "headline" ? 20 : key === "about" ? 25 : key === "experience" ? 25 : key === "skills" ? 20 : 10;
                return (
                  <div key={key} className="rounded-lg border border-border/70 p-2 text-center">
                    <p className="text-lg font-semibold tabular-nums">{Math.round(value)}</p>
                    <p className="text-[11px] text-muted capitalize">{key} /{max}</p>
                    <Progress value={(value / max) * 100} className="mt-1 h-1" tone={value / max > 0.6 ? "success" : value / max > 0.3 ? "warning" : "critical"} />
                  </div>
                );
              })}
            </div>

            <div className="rounded-lg bg-muted/5 p-3">
              <p className="mb-2 flex items-center gap-1.5 text-sm font-medium">
                <Sparkles className="h-4 w-4" /> Suggestions
              </p>
              <ul className="space-y-1">
                {suggestions.length === 0 && <li className="text-xs text-muted">Run the analysis to see suggestions.</li>}
                {suggestions.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-muted">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#6366f1]" /> {s}
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        {/* Post ideas */}
        <div className="xl:col-span-2 space-y-3">
          {postList.length === 0 && <EmptyState title="No post ideas yet" description="Generate one from your recent work." />}
          {postList.map((post) => (
            <Card key={post.id} className="p-4">
              <div className="mb-2 flex items-center justify-between">
                <p className="text-sm font-medium">{post.topic}</p>
                <Badge variant="info">{post.source}</Badge>
              </div>
              <p className="whitespace-pre-line text-sm leading-relaxed text-muted">{post.content}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {post.hashtags.map((h) => (
                  <Badge key={h} variant="primary">{h}</Badge>
                ))}
              </div>
            </Card>
          ))}
        </div>

        {/* Best time to post */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <CalendarClock className="h-4 w-4" /> Best time to post
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(postingTime?.windows ?? []).map((w) => (
              <div key={w.window} className="rounded-md bg-muted/10 p-3">
                <p className="text-sm font-medium">{w.window}</p>
                <p className="text-xs text-muted">{w.reason}</p>
              </div>
            ))}
            <p className="pt-1 text-xs text-muted">{postingTime?.reason}</p>
            <div className="mt-2 flex items-center gap-2 text-xs text-muted">
              <LinkedinIcon className="h-3.5 w-3.5" /> Weekly cadence: 3 posts · highlight shipped work
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
