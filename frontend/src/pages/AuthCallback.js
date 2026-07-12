import React, { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
    const nav = useNavigate();
    const { setUser } = useAuth();
    const processed = useRef(false);

    useEffect(() => {
        if (processed.current) return;
        processed.current = true;

        const hash = window.location.hash || "";
        const params = new URLSearchParams(hash.replace(/^#/, ""));
        const sessionId = params.get("session_id");
        if (!sessionId) {
            nav("/login", { replace: true });
            return;
        }
        (async () => {
            try {
                const { data } = await api.post("/auth/google/session", { session_id: sessionId });
                setUser(data);
                window.history.replaceState(null, "", window.location.pathname);
                toast.success(`Welcome, ${data.name || data.email}`);
                nav("/dashboard", { replace: true });
            } catch (e) {
                console.warn("Google session exchange failed:", e?.message || e);
                toast.error("Google sign-in failed");
                nav("/login", { replace: true });
            }
        })();
    // one-shot effect at mount — external deps (api, setUser, nav) are stable
    }, []);

    return (
        <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--af-bg)" }}>
            <div className="flex flex-col items-center gap-4">
                <div className="w-10 h-10 rounded-lg animate-pulse" style={{ background: "linear-gradient(135deg,#00FF94,#00E5FF)" }} />
                <p className="text-sm text-white/50 tracking-wide">Completing sign in…</p>
            </div>
        </div>
    );
}
