import { useEffect, useRef, useState, type FormEvent } from "react";
import { Bot, Send, UserRound } from "lucide-react";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { MarkdownView } from "@/components/MarkdownView";
import { useAiCommand } from "@/hooks";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  intent?: string;
  matched?: boolean;
}

const SUGGESTIONS = [
  "Generate today's report",
  "How many commits did I make this week?",
  "Which repository needs attention?",
  "Show project risk",
  "Predict delivery date",
  "Generate a LinkedIn post",
  "Update my resume",
  "Give me my morning briefing",
];

export default function Assistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const command = useAiCommand();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    setMessages((m) => [...m, { role: "user", content: trimmed }]);
    setInput("");
    try {
      const result = await command.mutateAsync(trimmed);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: result.message, intent: result.intent, matched: result.matched },
      ]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: `I hit a snag: ${err instanceof Error ? err.message : "unknown error"}` }]);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void send(input);
  }

  return (
    <div>
      <PageHeader title="AI Assistant" description="Ask in plain English — I'll run the right agent or query." />

      <Card className="flex h-[calc(100vh-13rem)] min-h-[28rem] flex-col">
        <CardContent ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <p className="text-sm font-medium">How can I help today?</p>
              <div className="flex max-w-md flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => void send(s)}
                    className="rounded-full border border-border bg-muted/5 px-3 py-1.5 text-xs text-muted transition-colors hover:border-primary/40 hover:text-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={cn("flex items-start gap-2.5", m.role === "user" && "flex-row-reverse")}>
              <span
                className={cn(
                  "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                  m.role === "user" ? "bg-muted/15" : "bg-gradient-to-br from-[#6366f1] to-[#22d3ee]"
                )}
              >
                {m.role === "user" ? <UserRound className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5 text-white" />}
              </span>
              <div className={cn("max-w-[78%] rounded-xl px-3.5 py-2.5", m.role === "user" ? "bg-primary/12" : "bg-muted/8")}>
                {m.role === "assistant" && m.intent && (
                  <div className="mb-1.5 flex items-center gap-2">
                    <Badge variant={m.matched ? "info" : "warning"}>{m.intent}</Badge>
                    {m.matched === false && <span className="text-[11px] text-muted">didn't match a command</span>}
                  </div>
                )}
                <MarkdownView content={m.content} className="text-[13px]" />
              </div>
            </div>
          ))}

          {command.isPending && (
            <div className="flex items-center gap-2.5">
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br from-[#6366f1] to-[#22d3ee]">
                <Bot className="h-3.5 w-3.5 text-white" />
              </span>
              <span className="rounded-xl bg-muted/8 px-3.5 py-2.5 text-xs text-muted">
                Thinking<span className="animate-pulse">…</span>
              </span>
            </div>
          )}
        </CardContent>

        <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-border p-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Try: 'Predict delivery date' or 'Summarize today's coding'"
            className="flex-1"
          />
          <Button type="submit" disabled={command.isPending || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </Card>
    </div>
  );
}
