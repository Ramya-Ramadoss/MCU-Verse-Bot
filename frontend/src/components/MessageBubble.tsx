import { motion } from "framer-motion";
import type { ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import { Bot, Copy, FileSearch, Info, Network, Tag, User } from "lucide-react";
import type { ChatMessage, Citation } from "@/services/api";
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
          <div className="space-y-2 px-1">
            {message.citations.map((c, i) => (
              <div
                key={`${c.source}-${i}`}
                className="rounded-lg border border-cyan-500/15 bg-slate-900/50 px-2.5 py-2 text-xs text-slate-300"
              >
                <div className="flex flex-wrap items-center gap-1.5">
                  <FileSearch size={12} className="text-cyan-400" />
                  <span className="font-medium text-slate-200">{c.title || c.source}</span>
                  {c.score != null && <EvidencePill>{c.score.toFixed(2)}</EvidencePill>}
                  {c.source_type && <EvidencePill icon={<Network size={11} />}>{c.source_type}</EvidencePill>}
                  {c.category && <EvidencePill icon={<Tag size={11} />}>{c.category}</EvidencePill>}
                  {c.continuity && <EvidencePill>{c.continuity}</EvidencePill>}
                  {c.canon_status && <EvidencePill>{c.canon_status}</EvidencePill>}
                  {c.knowledge_type && <EvidencePill>{c.knowledge_type}</EvidencePill>}
                  {c.earth && <EvidencePill>{c.earth}</EvidencePill>}
                  {c.universe && <EvidencePill>{c.universe}</EvidencePill>}
                </div>
                <CitationDetails citation={c} />
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function EvidencePill({ children, icon }: { children: ReactNode; icon?: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-cyan-500/10 px-2 py-0.5 text-[11px] text-cyan-300">
      {icon}
      {children}
    </span>
  );
}

function CitationDetails({ citation }: { citation: Citation }) {
  const linkedEntities = citation.linked_entities?.filter(Boolean) || [];
  if (!citation.reason && linkedEntities.length === 0) return null;

  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
      {citation.reason && (
        <span className="inline-flex items-center gap-1">
          <Info size={11} className="text-cyan-400" />
          {citation.reason}
        </span>
      )}
      {linkedEntities.length > 0 && (
        <span className="inline-flex items-center gap-1 text-jarvis-gold">
          <Network size={11} />
          {linkedEntities.join(", ")}
        </span>
      )}
    </div>
  );
}
