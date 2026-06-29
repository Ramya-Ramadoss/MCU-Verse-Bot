import { motion } from "framer-motion";
import { BotMessageSquare, MessageSquarePlus, Sparkles, Trash2, Zap } from "lucide-react";
import type { Conversation } from "@/services/api";
import { cn } from "@/lib/utils";

interface SidebarProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: SidebarProps) {
  return (
    <aside className="glass-panel hidden h-full w-72 shrink-0 flex-col p-4 md:flex">
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-300 to-cyan-600 shadow-glow">
          <Zap className="text-slate-950" size={20} />
        </div>
        <div>
          <h1 className="font-display text-lg font-semibold tracking-wide text-cyan-100">
            MCUVerse AI
          </h1>
          <p className="text-xs text-slate-400">Cinematic knowledge OS</p>
        </div>
      </div>

      <button type="button" onClick={onNew} className="btn-primary mb-4 w-full">
        <MessageSquarePlus size={18} />
        New Chat
      </button>

      <div className="mb-4 rounded-2xl border border-cyan-500/10 bg-slate-950/35 p-3">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">
          <Sparkles size={14} />
          Knowledge Packs
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
          <span className="rounded-lg bg-cyan-500/5 px-2 py-1">Heroes</span>
          <span className="rounded-lg bg-cyan-500/5 px-2 py-1">Series</span>
          <span className="rounded-lg bg-cyan-500/5 px-2 py-1">Artifacts</span>
          <span className="rounded-lg bg-cyan-500/5 px-2 py-1">Timeline</span>
        </div>
      </div>

      <div className="flex-1 space-y-1 overflow-y-auto">
        {conversations.length === 0 && (
          <div className="rounded-2xl border border-dashed border-cyan-500/15 px-3 py-5 text-center text-sm text-slate-500">
            <BotMessageSquare className="mx-auto mb-2 text-cyan-500/60" size={22} />
            Start a chat to explore the MCU graph.
          </div>
        )}
        {conversations.map((conv) => (
          <motion.button
            key={conv.id}
            type="button"
            whileHover={{ x: 2 }}
            onClick={() => onSelect(conv.id)}
            className={cn(
              "group flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition",
              activeId === conv.id
                ? "bg-cyan-500/15 text-cyan-100 border border-cyan-500/25"
                : "text-slate-300 hover:bg-slate-800/50"
            )}
          >
            <span className="truncate pr-2">{conv.title}</span>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 text-slate-500 hover:text-red-400 transition"
              aria-label="Delete conversation"
            >
              <Trash2 size={14} />
            </button>
          </motion.button>
        ))}
      </div>
    </aside>
  );
}
