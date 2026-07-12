import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "@/lib/api";

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null); // null = checking, false = anon, obj = user
    const [loading, setLoading] = useState(true);

    const checkAuth = useCallback(async () => {
        try {
            const { data } = await api.get("/auth/me");
            setUser(data);
        } catch {
            setUser(false);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        // If returning from OAuth callback, let AuthCallback handle it first
        if (window.location.hash?.includes("session_id=")) {
            setLoading(false);
            return;
        }
        checkAuth();
    }, [checkAuth]);

    const login = async (email, password) => {
        try {
            const { data } = await api.post("/auth/login", { email, password });
            setUser(data);
            return { ok: true };
        } catch (e) {
            return { ok: false, error: formatApiError(e) };
        }
    };

    const register = async (name, email, password) => {
        try {
            const { data } = await api.post("/auth/register", { name, email, password });
            setUser(data);
            return { ok: true };
        } catch (e) {
            return { ok: false, error: formatApiError(e) };
        }
    };

    const logout = async () => {
        try { await api.post("/auth/logout"); } catch (e) {
            console.warn("Logout API call failed:", e?.message || e);
        }
        setUser(false);
    };

    const refresh = async () => {
        try {
            const { data } = await api.get("/auth/me");
            setUser(data);
        } catch {
            setUser(false);
        }
    };

    return (
        <AuthCtx.Provider value={{ user, loading, login, register, logout, checkAuth, refresh, setUser }}>
            {children}
        </AuthCtx.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthCtx);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
}

export function roleLabel(r) {
    if (!r) return "";
    return r.split("_").map((s) => s[0].toUpperCase() + s.slice(1)).join(" ");
}

export function hasRole(user, ...roles) {
    return !!user && roles.includes(user.role);
}
