import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { LogIn, Shield, UserPlus, Zap } from "lucide-react";
import { api } from "@/services/api";

type Mode = "login" | "register";

export function LoginPage() {
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const authMutation = useMutation({
    mutationFn: () =>
      mode === "login"
        ? api.login({ email, password })
        : api.register({ email, password, full_name: fullName || undefined }),
    onSuccess: () => navigate("/"),
  });

  const guestMutation = useMutation({
    mutationFn: api.createGuest,
    onSuccess: () => navigate("/"),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    authMutation.mutate();
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="glass-panel w-full max-w-md p-6">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 shadow-glow">
            <Zap size={22} />
          </div>
          <div>
            <h1 className="font-display text-xl font-semibold text-cyan-50">MCUVerse AI</h1>
            <p className="text-sm text-slate-400">Secure knowledge workspace</p>
          </div>
        </div>

        <div className="mb-5 grid grid-cols-2 gap-2 rounded-xl border border-cyan-500/10 bg-slate-950/40 p-1">
          <button
            type="button"
            className={mode === "login" ? "btn-primary justify-center" : "btn-ghost justify-center"}
            onClick={() => setMode("login")}
          >
            <LogIn size={16} /> Login
          </button>
          <button
            type="button"
            className={mode === "register" ? "btn-primary justify-center" : "btn-ghost justify-center"}
            onClick={() => setMode("register")}
          >
            <UserPlus size={16} /> Register
          </button>
        </div>

        <form className="space-y-4" onSubmit={submit}>
          {mode === "register" && (
            <label className="block text-sm">
              <span className="mb-1 block text-slate-400">Name</span>
              <input
                className="glass-input w-full"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Tony Stark"
              />
            </label>
          )}
          <label className="block text-sm">
            <span className="mb-1 block text-slate-400">Email</span>
            <input
              className="glass-input w-full"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-400">Password</span>
            <input
              className="glass-input w-full"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              minLength={8}
              required
            />
          </label>

          {authMutation.isError && (
            <p className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              Authentication failed. Check your credentials and try again.
            </p>
          )}

          <button className="btn-primary w-full justify-center" type="submit">
            <Shield size={17} />
            {mode === "login" ? "Enter Workspace" : "Create Account"}
          </button>
        </form>

        <button
          type="button"
          className="btn-ghost mt-3 w-full justify-center"
          onClick={() => guestMutation.mutate()}
        >
          Continue as Guest
        </button>

        <Link to="/" className="mt-5 block text-center text-sm text-cyan-300 hover:text-cyan-100">
          Back to chat
        </Link>
      </div>
    </div>
  );
}
