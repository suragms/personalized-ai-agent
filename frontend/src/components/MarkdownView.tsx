import { Fragment } from "react";
import { cn } from "@/lib/utils";

/** Inline markdown: bold, italic, inline code, links. */
function Inline({ text }: { text: string }) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
        if (part.startsWith("*") && part.endsWith("*") && part.length > 2) return <em key={i}>{part.slice(1, -1)}</em>;
        if (part.startsWith("`") && part.endsWith("`")) {
          return (
            <code key={i} className="rounded bg-muted/20 px-1 py-0.5 font-mono text-[0.9em]">
              {part.slice(1, -1)}
            </code>
          );
        }
        if (part.startsWith("[")) {
          const m = part.match(/\[([^\]]+)\]\(([^)]+)\)/);
          if (m)
            return (
              <a key={i} href={m[2]} target="_blank" rel="noreferrer" className="text-primary underline underline-offset-2">
                {m[1]}
              </a>
            );
        }
        return <Fragment key={i}>{part}</Fragment>;
      })}
    </>
  );
}

/** Lightweight markdown renderer for agent-generated content. */
export function MarkdownView({ content, className }: { content: string; className?: string }) {
  const lines = content.split("\n");
  const blocks: { type: string; text: string; level?: number }[] = [];
  let list: string[] = [];

  function flushList() {
    if (list.length) {
      blocks.push({ type: "list", text: list.join("\n") });
      list = [];
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flushList();
      continue;
    }
    if (line.startsWith("### ")) {
      flushList();
      blocks.push({ type: "h3", text: line.slice(4) });
    } else if (line.startsWith("## ")) {
      flushList();
      blocks.push({ type: "h2", text: line.slice(3) });
    } else if (line.startsWith("# ")) {
      flushList();
      blocks.push({ type: "h1", text: line.slice(2) });
    } else if (/^[-*]\s+/.test(line)) {
      list.push(line.replace(/^[-*]\s+/, ""));
    } else if (/^\d+\.\s+/.test(line)) {
      flushList();
      blocks.push({ type: "ol", text: line });
    } else if (line.startsWith("> ")) {
      flushList();
      blocks.push({ type: "quote", text: line.slice(2) });
    } else if (line.startsWith("```")) {
      flushList();
      blocks.push({ type: "code", text: line.replace(/```/g, "") });
    } else {
      flushList();
      blocks.push({ type: "p", text: line });
    }
  }
  flushList();

  return (
    <div className={cn("space-y-2 text-sm leading-relaxed", className)}>
      {blocks.map((b, i) => {
        switch (b.type) {
          case "h1":
            return (
              <h1 key={i} className="text-lg font-semibold tracking-tight">
                <Inline text={b.text} />
              </h1>
            );
          case "h2":
            return (
              <h2 key={i} className="pt-1 text-base font-semibold">
                <Inline text={b.text} />
              </h2>
            );
          case "h3":
            return (
              <h3 key={i} className="text-sm font-semibold">
                <Inline text={b.text} />
              </h3>
            );
          case "list":
            return (
              <ul key={i} className="space-y-1 pl-4">
                {b.text.split("\n").map((li, j) => (
                  <li key={j} className="list-disc marker:text-muted/50">
                    <Inline text={li} />
                  </li>
                ))}
              </ul>
            );
          case "quote":
            return (
              <blockquote key={i} className="border-l-2 border-primary/40 pl-3 text-muted">
                <Inline text={b.text} />
              </blockquote>
            );
          case "code":
            return (
              <pre key={i} className="overflow-x-auto rounded bg-muted/15 p-3 font-mono text-xs">
                {b.text}
              </pre>
            );
          default:
            return (
              <p key={i}>
                <Inline text={b.text} />
              </p>
            );
        }
      })}
    </div>
  );
}
