import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type React from "react";
import { Link } from "react-router-dom";
import { Activity, Database, FileText, Gauge, Home, Layers3, RefreshCw, ShieldCheck, Users } from "lucide-react";
import { api } from "@/services/api";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const { data: analytics } = useQuery({ queryKey: ["analytics"], queryFn: api.getAnalytics });
  const { data: documents = [] } = useQuery({ queryKey: ["documents"], queryFn: api.getDocuments });
  const { data: user } = useQuery({ queryKey: ["me"], queryFn: api.me, retry: false });

  const ingest = useMutation({
    mutationFn: api.triggerIngestion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });
  const reindex = useMutation({
    mutationFn: api.reindexKnowledge,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["analytics"] }),
  });

  const categoryCounts = documents.reduce<Record<string, number>>((acc, doc) => {
    acc[doc.category] = (acc[doc.category] || 0) + 1;
    return acc;
  }, {});

  const coverage = [
    { label: "Characters", key: "characters", note: "heroes, variants, villains" },
    { label: "Movies", key: "movies", note: "Infinity Saga to multiverse era" },
    { label: "Series", key: "series", note: "Disney+ and legacy context" },
    { label: "Organizations", key: "organizations", note: "teams, agencies, nations" },
    { label: "Artifacts", key: "artifacts", note: "stones, rings, tech" },
    { label: "Comics", key: "comics", note: "source-context bridge" },
  ];

  return (
    <div className="min-h-screen p-4">
      <main className="mx-auto max-w-6xl space-y-5">
        <header className="glass-panel flex flex-wrap items-center justify-between gap-3 p-5">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Operations</p>
            <h1 className="font-display text-2xl font-semibold text-cyan-50">MCUVerse Control Center</h1>
          </div>
          <div className="flex gap-2">
            <Link className="btn-ghost" to="/">
              <Home size={17} /> Chat
            </Link>
            <Link className="btn-ghost" to="/login">
              <ShieldCheck size={17} /> Account
            </Link>
          </div>
        </header>

        <section className="grid gap-3 md:grid-cols-4">
          <Metric icon={<FileText />} label="Documents" value={analytics?.document_count ?? 0} />
          <Metric icon={<Database />} label="Embeddings" value={analytics?.embedding_count ?? 0} />
          <Metric icon={<Users />} label="Conversations" value={analytics?.total_conversations ?? 0} />
          <Metric icon={<Gauge />} label="Confidence" value={`${Math.round((analytics?.average_confidence ?? 0) * 100)}%`} />
        </section>

        <section className="glass-panel p-5">
          <div className="mb-4 flex items-center gap-2">
            <Layers3 className="text-cyan-300" size={19} />
            <h2 className="font-display text-lg font-semibold">Knowledge Coverage</h2>
          </div>
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            {coverage.map((item) => (
              <div key={item.key} className="signal-card p-4">
                <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{item.label}</p>
                <p className="mt-2 font-display text-2xl font-semibold text-cyan-50">
                  {categoryCounts[item.key] ?? 0}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">{item.note}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1fr_1.4fr]">
          <div className="glass-panel p-5">
            <div className="mb-4 flex items-center gap-2">
              <Activity className="text-cyan-300" size={19} />
              <h2 className="font-display text-lg font-semibold">Index Operations</h2>
            </div>
            <p className="mb-4 text-sm text-slate-400">
              Signed in as {user?.email ?? "anonymous"}. Admin accounts can ingest and rebuild the retrieval index.
            </p>
            <div className="flex flex-col gap-2">
              <button className="btn-primary justify-center" onClick={() => ingest.mutate()}>
                <RefreshCw size={17} /> Ingest Knowledge
              </button>
              <button className="btn-ghost justify-center" onClick={() => reindex.mutate()}>
                <Database size={17} /> Rebuild FAISS Index
              </button>
            </div>
            {(ingest.isError || reindex.isError) && (
              <p className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                Admin access is required for this operation.
              </p>
            )}
            {(ingest.data || reindex.data) && (
              <p className="mt-4 rounded-lg border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-sm text-cyan-100">
                Operation completed successfully.
              </p>
            )}
          </div>

          <div className="glass-panel overflow-hidden p-5">
            <h2 className="mb-4 font-display text-lg font-semibold">Knowledge Documents</h2>
            <div className="max-h-[420px] overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-500">
                  <tr>
                    <th className="pb-2">Title</th>
                    <th className="pb-2">Category</th>
                    <th className="pb-2">Spoilers</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cyan-500/10">
                  {documents.map((doc) => (
                    <tr key={doc.id}>
                      <td className="py-2 pr-3 text-cyan-50">{doc.title}</td>
                      <td className="py-2 pr-3 text-slate-300">{doc.category}</td>
                      <td className="py-2 text-slate-400">{String(doc.metadata_json?.spoiler_level ?? "none")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number | string }) {
  return (
    <div className="glass-panel p-4">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg border border-cyan-500/20 bg-cyan-500/10 text-cyan-300">
        {icon}
      </div>
      <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-1 font-display text-2xl font-semibold text-cyan-50">{value}</p>
    </div>
  );
}
