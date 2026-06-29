import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BarChart3,
  Brain,
  Database,
  Film,
  Loader2,
  LogIn,
  LogOut,
  Network,
  Send,
  Settings,
  Shield,
} from "lucide-react";
import { Link } from "react-router-dom";
import { MessageBubble } from "@/components/MessageBubble";
import { SettingsPanel } from "@/components/SettingsPanel";
import { Sidebar } from "@/components/Sidebar";
import { api, authStorage, defaultSettings, type ChatSettings } from "@/services/api";

const SUGGESTIONS = [
  "Compare Black Panther and Killmonger.",
  "Explain Loki's variant timeline.",
  "Who are the main Moon Knight identities?",
  "Show Ant-Man's role in the Time Heist.",
  "Which heroes are connected to Wakanda?",
  "Who wielded or protected Infinity Stones?",
];

export function ChatPage() {
  const [activeId, setActiveId] = useState<string>();
  const [input, setInput] = useState("");
  const [settings, setSettings] = useState<ChatSettings>(defaultSettings);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  const { data: conversations = [] } = useQuery({
    queryKey: ["conversations"],
    queryFn: api.listConversations,
  });

  const { data: messages = [], isLoading: loadingMessages } = useQuery({
    queryKey: ["messages", activeId],
    queryFn: () => api.getMessages(activeId!),
    enabled: !!activeId,
  });

  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: api.getAnalytics,
    refetchInterval: 30000,
  });

  const { data: user } = useQuery({
    queryKey: ["me"],
    queryFn: api.me,
    retry: false,
    enabled: !!authStorage.getToken(),
  });

  const createConv = useMutation({
    mutationFn: () => api.createConversation(),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setActiveId(conv.id);
    },
  });

  const sendMsg = useMutation({
    mutationFn: (content: string) => api.sendMessage(activeId!, content, settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", activeId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  const deleteConv = useMutation({
    mutationFn: api.deleteConversation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setActiveId(undefined);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sendMsg.isPending]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || !activeId || sendMsg.isPending) return;
    setInput("");
    sendMsg.mutate(text);
  };

  const title = activeId
    ? conversations.find((conversation) => conversation.id === activeId)?.title || "Chat"
    : "MCU Knowledge Engine";

  return (
    <div className="flex h-screen gap-4 overflow-hidden p-3 md:p-4">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={() => createConv.mutate()}
        onDelete={(id) => deleteConv.mutate(id)}
      />

      <main className="glass-panel flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-cyan-500/10 px-4 py-4 md:px-6">
          <div>
            <div className="mb-1 flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-cyan-300/80">
              <Brain size={13} />
              Knowledge Intelligence
            </div>
            <h2 className="font-display text-xl font-semibold text-cyan-50 md:text-2xl">
              {title}
            </h2>
            <p className="text-xs text-slate-400">
              Hybrid search · knowledge graph · spoiler-aware retrieval
            </p>
          </div>

          <div className="flex items-center gap-2">
            {analytics && (
              <div className="hidden items-center gap-3 rounded-xl border border-cyan-500/15 bg-slate-950/35 px-3 py-2 text-xs text-slate-400 lg:flex">
                <span className="flex items-center gap-1.5">
                  <Database size={14} className="text-cyan-400" />
                  {analytics.document_count} docs
                </span>
                <span className="h-4 w-px bg-cyan-500/15" />
                <span className="flex items-center gap-1.5">
                  <Network size={14} className="text-jarvis-gold" />
                  {analytics.entity_count} entities
                </span>
                <span className="h-4 w-px bg-cyan-500/15" />
                <span>{analytics.embedding_count} vectors</span>
              </div>
            )}
            <button
              type="button"
              className="btn-ghost"
              onClick={() => setSettingsOpen(true)}
              aria-label="Open settings"
            >
              <Settings size={18} />
            </button>
            <Link className="btn-ghost" to="/dashboard" aria-label="Open dashboard">
              <BarChart3 size={18} />
            </Link>
            {user ? (
              <button
                type="button"
                className="btn-ghost"
                onClick={() => {
                  authStorage.clear();
                  queryClient.clear();
                }}
                aria-label="Logout"
              >
                <LogOut size={18} />
              </button>
            ) : (
              <Link className="btn-ghost" to="/login" aria-label="Login">
                <LogIn size={18} />
              </Link>
            )}
          </div>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-5 md:px-6 md:py-6">
          {!activeId ? (
            <EmptyState onStart={() => createConv.mutate()} />
          ) : loadingMessages ? (
            <div className="flex h-full items-center justify-center text-slate-400">
              <Loader2 className="animate-spin" />
            </div>
          ) : (
            <div className="mx-auto max-w-4xl space-y-6">
              {messages.length === 0 && (
                <div className="mb-8 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {SUGGESTIONS.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => setInput(suggestion)}
                      className="signal-card min-h-[82px] px-4 py-3 text-left text-sm text-slate-300 transition hover:border-cyan-400/35 hover:bg-cyan-500/5"
                    >
                      <span className="mb-2 flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-500/10 text-cyan-300">
                        <Film size={15} />
                      </span>
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {sendMsg.isPending && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex items-center gap-2 text-sm text-cyan-300"
                >
                  <Loader2 className="animate-spin" size={16} />
                  Searching graph, timeline, and knowledge index...
                </motion.div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="border-t border-cyan-500/10 bg-slate-950/20 p-3 md:p-4">
          <div className="mx-auto flex max-w-4xl gap-3">
            <input
              className="glass-input flex-1"
              placeholder={
                activeId
                  ? "Ask about characters, movies, series, artifacts, timelines..."
                  : "Start a new chat first"
              }
              value={input}
              disabled={!activeId || sendMsg.isPending}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && !event.shiftKey && handleSend()}
            />
            <button
              type="button"
              className="btn-primary"
              disabled={!activeId || !input.trim() || sendMsg.isPending}
              onClick={handleSend}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </main>

      <SettingsPanel
        settings={settings}
        onChange={setSettings}
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
      />
    </div>
  );
}

function EmptyState({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="mb-6 flex h-20 w-20 items-center justify-center rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-400/20 to-jarvis-gold/10 shadow-glow"
      >
        <span className="font-display text-2xl font-bold text-cyan-300">MV</span>
      </motion.div>
      <h3 className="font-display text-3xl font-semibold text-cyan-50">
        MCUVerse AI Command Center
      </h3>
      <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">
        Ask about characters, films, Disney+ arcs, timelines, artifacts, teams,
        villains, and relationship paths. The answer engine combines vector search,
        keyword recall, and graph reasoning.
      </p>
      <div className="mt-6 grid w-full max-w-2xl gap-3 sm:grid-cols-3">
        <div className="signal-card p-4 text-left">
          <Network className="mb-3 text-cyan-300" size={18} />
          <p className="text-sm font-semibold text-cyan-50">Graph Reasoning</p>
          <p className="mt-1 text-xs text-slate-500">Mentors, enemies, wielders, teams</p>
        </div>
        <div className="signal-card p-4 text-left">
          <Shield className="mb-3 text-jarvis-gold" size={18} />
          <p className="text-sm font-semibold text-cyan-50">Spoiler Controls</p>
          <p className="mt-1 text-xs text-slate-500">Filter by knowledge level</p>
        </div>
        <div className="signal-card p-4 text-left">
          <Database className="mb-3 text-cyan-300" size={18} />
          <p className="text-sm font-semibold text-cyan-50">Structured MCU Data</p>
          <p className="mt-1 text-xs text-slate-500">Characters, series, events</p>
        </div>
      </div>
      <button type="button" className="btn-primary mt-6" onClick={onStart}>
        Start New Conversation
      </button>
    </div>
  );
}
