import { Settings, Shield } from "lucide-react";
import type { ChatSettings } from "@/services/api";

interface SettingsPanelProps {
  settings: ChatSettings;
  onChange: (settings: ChatSettings) => void;
  open: boolean;
  onClose: () => void;
}

export function SettingsPanel({ settings, onChange, open, onClose }: SettingsPanelProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="glass-panel w-full max-w-md p-6">
        <div className="mb-4 flex items-center gap-2">
          <Settings size={20} className="text-cyan-300" />
          <h2 className="font-display text-lg font-semibold">Settings</h2>
        </div>

        <div className="space-y-4">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-400">LLM Provider</span>
            <select
              className="glass-input w-full"
              value={settings.llm_provider}
              onChange={(e) => onChange({ ...settings, llm_provider: e.target.value })}
            >
              <option value="retrieval_only">Retrieval Only</option>
              <option value="gemini">Gemini</option>
              <option value="openai">OpenAI</option>
              <option value="ollama">Ollama (Local)</option>
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 flex items-center gap-1 text-slate-400">
              <Shield size={14} /> Spoiler Protection
            </span>
            <select
              className="glass-input w-full"
              value={settings.spoiler_preference}
              onChange={(e) =>
                onChange({
                  ...settings,
                  spoiler_preference: e.target.value as ChatSettings["spoiler_preference"],
                })
              }
            >
              <option value="none">Spoiler-Free</option>
              <option value="partial">Partial Spoilers</option>
              <option value="full">Full Knowledge</option>
            </select>
          </label>

          <label className="block text-sm">
            <span className="mb-1 block text-slate-400">Top K Results</span>
            <input
              type="number"
              min={1}
              max={20}
              className="glass-input w-full"
              value={settings.top_k}
              onChange={(e) =>
                onChange({ ...settings, top_k: parseInt(e.target.value, 10) || 5 })
              }
            />
          </label>
        </div>

        <div className="mt-6 flex justify-end">
          <button type="button" className="btn-primary" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
