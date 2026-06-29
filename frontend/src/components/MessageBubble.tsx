import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Bot, Copy, FileSearch, User } from "lucide-react";
import type { ChatMessage } from "@/services/api";
import { cn } from "@/lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  const copyContent = () => {
    navigator.clipboard.writeText(message.content);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}
    >
      <div
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border",
          isUser
            ? "border-jarvis-gold/30 bg-jarvis-gold/10 text-jarvis-gold"
            : "border-cyan-500/30 bg-cyan-500/10 text-cyan-300"
        )}
      >
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div className={cn("max-w-[88%] space-y-2", isUser ? "items-end" : "items-start")}>
        <div
          className={cn(
            "px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "rounded-2xl rounded-tr-sm border border-jarvis-gold/20 bg-jarvis-gold/10 text-slate-100"
              : "glass-panel rounded-2xl rounded-tl-sm"
          )}
        >
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none prose-p:my-2 prose-headings:text-cyan-100">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && (
          <div className="flex flex-wrap items-center gap-2 px-1 text-xs text-slate-400">
            <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-cyan-300">
              {Math.round((message.confidence_score || 0) * 100)}% confidence
            </span>
            <span>{message.provider_used}</span>
            <button
              type="button"
              onClick={copyContent}
              className="btn-ghost !px-2 !py-1"
              aria-label="Copy response"
            >
              <Copy size={14} />
            </button>
          </div>
        )}

        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-2 px-1">
            {message.citations.map((c, i) => (
              <span
                key={`${c.source}-${i}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/15 bg-slate-900/50 px-2 py-1 text-xs text-slate-300"
              >
                <FileSearch size={12} className="text-cyan-400" />
                {c.title || c.source}
                {c.score != null && (
                  <span className="ml-1 text-cyan-400">({c.score.toFixed(2)})</span>
                )}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
