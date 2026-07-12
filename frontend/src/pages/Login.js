import React, { useState } from "react";
import { useNavigate, Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { api, formatApiError } from "@/lib/api";
import { AUTH } from "@/constants/testIds";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ArrowRight, Sparkles, Boxes, Shield, Activity } from "lucide-react";

export default function LoginPage() {
    const { user, login, register } = useAuth();
    const nav = useNavigate();
    const [mode, setMode] = useState("login"); // login | register | forgot
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState("");

    if (user) return <Navigate to="/dashboard" replace />;

    const submit = async (e) => {
        e.preventDefault();
        setErr(""); setBusy(true);
        try {
            if (mode === "login") {
                const r = await login(email.trim(), password);
                if (!r.ok) { setErr(r.error); return; }
                toast.success("Welcome back");
                nav("/dashboard");
            } else if (mode === "register") {
                const r = await register(name.trim(), email.trim(), password);
                if (!r.ok) { setErr(r.error); return; }
                toast.success("Account created");
                nav("/dashboard");
            } else if (mode === "forgot") {
                await api.post("/auth/forgot-password", { email: email.trim() });
                toast.success("If that email exists, a reset link was sent (check server logs in dev).");
                setMode("login");
            }
        } catch (e2) {
            setErr(formatApiError(e2));
        } finally {
            setBusy(false);
        }
    };

    const google = () => {
        // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
        const redirectUrl = window.location.origin + "/dashboard";
        window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
    };

    return (
        <div className="min-h-screen relative grain" style={{ background: "var(--af-bg)" }}>
            {/* Background gradient */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full" style={{ background: "radial-gradient(circle, rgba(0,255,148,0.10), transparent 60%)", filter: "blur(60px)" }} />
                <div className="absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full" style={{ background: "radial-gradient(circle, rgba(0,229,255,0.10), transparent 60%)", filter: "blur(60px)" }} />
            </div>

            <div className="relative z-10 min-h-screen grid lg:grid-cols-2">
                {/* Left brand column */}
                <div className="hidden lg:flex flex-col justify-between p-10 xl:p-14 border-r border-white/5">
                    <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-md" style={{ background: "linear-gradient(135deg,#00FF94,#00E5FF)" }} />
                        <span className="font-display text-lg font-medium tracking-tight">AssetFlow</span>
                    </div>

                    <div className="max-w-md">
                        <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-4">Enterprise Asset & Resource OS</p>
                        <h1 className="font-display text-5xl xl:text-6xl font-medium tracking-tighter leading-[1.02]">
                            Track everything.
                            <br />
                            <span style={{ background: "linear-gradient(90deg,#00FF94,#00E5FF)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                                Lose nothing.
                            </span>
                        </h1>
                        <p className="mt-6 text-white/60 leading-relaxed">
                            One workspace for allocation, booking, maintenance and audits — built for teams that treat inventory as infrastructure.
                        </p>
                        <div className="mt-10 grid grid-cols-3 gap-4">
                            {[
                                { icon: Boxes, label: "Registry" },
                                { icon: Activity, label: "Allocation" },
                                { icon: Shield, label: "Audit" },
                            ].map((f) => (
                                <div key={f.label} className="p-4 rounded-lg border border-white/5 bg-white/[0.02]">
                                    <f.icon size={16} strokeWidth={1.5} className="text-white/60 mb-2" />
                                    <p className="text-xs text-white/70">{f.label}</p>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="text-xs text-white/30 tabular-nums">v1.0 · dark mode · optimized for desktop</div>
                </div>

                {/* Right form column */}
                <div className="flex items-center justify-center p-6 sm:p-10">
                    <div className="w-full max-w-md">
                        <div className="lg:hidden mb-8 flex items-center gap-2.5">
                            <div className="w-7 h-7 rounded-md" style={{ background: "linear-gradient(135deg,#00FF94,#00E5FF)" }} />
                            <span className="font-display text-lg font-medium tracking-tight">AssetFlow</span>
                        </div>

                        <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-3">
                            {mode === "login" && "Sign in"}
                            {mode === "register" && "Create account"}
                            {mode === "forgot" && "Recover access"}
                        </p>
                        <h2 className="font-display text-3xl font-medium tracking-tight mb-2">
                            {mode === "login" && "Welcome back."}
                            {mode === "register" && "Start with AssetFlow."}
                            {mode === "forgot" && "We'll send a reset link."}
                        </h2>
                        <p className="text-white/50 text-sm mb-8">
                            {mode === "login" && "Continue to your workspace."}
                            {mode === "register" && "Signup creates an Employee account. Admins can promote roles later."}
                            {mode === "forgot" && "Enter your email address to receive reset instructions."}
                        </p>

                        <form onSubmit={submit} className="space-y-4">
                            {mode === "register" && (
                                <div className="space-y-1.5">
                                    <Label className="text-xs text-white/60">Full name</Label>
                                    <Input
                                        data-testid={AUTH.registerName}
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        placeholder="Ada Lovelace"
                                        className="h-11 bg-white/[0.03] border-white/10 focus-visible:ring-white/20 focus-visible:ring-1"
                                        required
                                    />
                                </div>
                            )}
                            <div className="space-y-1.5">
                                <Label className="text-xs text-white/60">Email</Label>
                                <Input
                                    type="email"
                                    data-testid={mode === "register" ? AUTH.registerEmail : mode === "forgot" ? AUTH.forgotEmail : AUTH.loginEmail}
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="you@company.com"
                                    className="h-11 bg-white/[0.03] border-white/10 focus-visible:ring-white/20 focus-visible:ring-1"
                                    required
                                />
                            </div>
                            {mode !== "forgot" && (
                                <div className="space-y-1.5">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-xs text-white/60">Password</Label>
                                        {mode === "login" && (
                                            <button
                                                type="button"
                                                data-testid={AUTH.toggleForgot}
                                                onClick={() => setMode("forgot")}
                                                className="text-xs text-white/40 hover:text-white/70"
                                            >
                                                Forgot?
                                            </button>
                                        )}
                                    </div>
                                    <Input
                                        type="password"
                                        data-testid={mode === "register" ? AUTH.registerPassword : AUTH.loginPassword}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        className="h-11 bg-white/[0.03] border-white/10 focus-visible:ring-white/20 focus-visible:ring-1"
                                        required
                                        minLength={6}
                                    />
                                </div>
                            )}

                            {err && (
                                <div
                                    data-testid="auth-error"
                                    className="text-sm rounded-lg px-3 py-2"
                                    style={{ color: "#FF3366", background: "rgba(255,51,102,0.08)", border: "1px solid rgba(255,51,102,0.2)" }}
                                >
                                    {err}
                                </div>
                            )}

                            <Button
                                type="submit"
                                data-testid={mode === "register" ? AUTH.registerSubmit : mode === "forgot" ? AUTH.forgotSubmit : AUTH.loginSubmit}
                                disabled={busy}
                                className="w-full h-11 bg-white text-black font-medium hover:bg-white/90 transition-colors group"
                            >
                                {busy ? "…" : mode === "login" ? "Sign in" : mode === "register" ? "Create account" : "Send reset link"}
                                <ArrowRight size={16} className="ml-1.5 -mr-0.5 group-hover:translate-x-0.5 transition-transform" />
                            </Button>
                        </form>

                        {mode !== "forgot" && (
                            <>
                                <div className="my-6 flex items-center gap-4">
                                    <div className="flex-1 h-px bg-white/5" />
                                    <span className="text-[10px] uppercase tracking-[0.2em] text-white/40">or</span>
                                    <div className="flex-1 h-px bg-white/5" />
                                </div>
                                <button
                                    type="button"
                                    data-testid={AUTH.googleButton}
                                    onClick={google}
                                    className="w-full h-11 rounded-md border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-colors flex items-center justify-center gap-2.5 text-sm"
                                >
                                    <GoogleG />
                                    Continue with Google
                                </button>
                            </>
                        )}

                        <p className="mt-8 text-sm text-white/50 text-center">
                            {mode === "login" && (
                                <>
                                    New to AssetFlow?{" "}
                                    <button data-testid={AUTH.toggleRegister} onClick={() => { setMode("register"); setErr(""); }} className="text-white hover:underline">
                                        Create account
                                    </button>
                                </>
                            )}
                            {mode === "register" && (
                                <>
                                    Already have an account?{" "}
                                    <button data-testid={AUTH.toggleLogin} onClick={() => { setMode("login"); setErr(""); }} className="text-white hover:underline">
                                        Sign in
                                    </button>
                                </>
                            )}
                            {mode === "forgot" && (
                                <button onClick={() => { setMode("login"); setErr(""); }} className="text-white hover:underline">Back to sign in</button>
                            )}
                        </p>

                        <div className="mt-8 rounded-lg border border-white/5 bg-white/[0.02] p-3 text-[11px] text-white/50 leading-relaxed">
                            <p className="text-white/70 mb-1 flex items-center gap-1"><Sparkles size={11} /> Demo credentials</p>
                            <span className="font-mono-af">admin@assetflow.io / admin123</span> ·{" "}
                            <span className="font-mono-af">manager@assetflow.io / manager123</span> ·{" "}
                            <span className="font-mono-af">employee@assetflow.io / employee123</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function GoogleG() {
    return (
        <svg width="16" height="16" viewBox="0 0 24 24">
            <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.4-1.7 4-5.5 4-3.3 0-6-2.7-6-6.1s2.7-6.1 6-6.1c1.9 0 3.1.8 3.9 1.5l2.6-2.5C16.9 3.3 14.7 2.3 12 2.3 6.5 2.3 2 6.8 2 12.3s4.5 10 10 10c5.8 0 9.6-4.1 9.6-9.8 0-.7-.1-1.2-.2-1.7H12z" />
        </svg>
    );
}
