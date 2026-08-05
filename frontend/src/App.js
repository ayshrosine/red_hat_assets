import React, { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { Toaster } from "sonner";
import Layout from "@/components/Layout";
import LoginPage from "@/pages/Login";
import LandingPage from "@/pages/LandingPage";
import Dashboard from "@/pages/Dashboard";
import OrgSetup from "@/pages/OrgSetup";
import Assets from "@/pages/Assets";
import AssetDetail from "@/pages/AssetDetail";
import Allocation from "@/pages/Allocation";
import Booking from "@/pages/Booking";
import Maintenance from "@/pages/Maintenance";
import Audit from "@/pages/Audit";
import Reports from "@/pages/Reports";
import Notifications from "@/pages/Notifications";

function Protected({ children, roles }) {
    const { user, loading } = useAuth();
    if (loading) return <LoadingSplash />;
    if (!user) return <Navigate to="/login" replace />;
    if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
    return <Layout>{children}</Layout>;
}

function LoadingSplash() {
    return (
        <div className="min-h-screen flex items-center justify-center" style={{ background: "var(--af-bg)" }}>
            <div className="flex flex-col items-center gap-4">
                <div className="w-10 h-10 rounded-lg animate-pulse" style={{ background: "linear-gradient(135deg,#00FF94,#00E5FF)" }} />
                <p className="text-sm text-white/40 tracking-wide">Loading AssetFlow…</p>
            </div>
        </div>
    );
}

function AppRouter() {
    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<Navigate to="/login" replace />} />
            <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
            <Route path="/organization" element={<Protected roles={["admin"]}><OrgSetup /></Protected>} />
            <Route path="/assets" element={<Protected><Assets /></Protected>} />
            <Route path="/assets/:assetId" element={<Protected><AssetDetail /></Protected>} />
            <Route path="/allocation" element={<Protected><Allocation /></Protected>} />
            <Route path="/booking" element={<Protected><Booking /></Protected>} />
            <Route path="/maintenance" element={<Protected><Maintenance /></Protected>} />
            <Route path="/audit" element={<Protected roles={["admin", "asset_manager"]}><Audit /></Protected>} />
            <Route path="/reports" element={<Protected roles={["admin", "asset_manager"]}><Reports /></Protected>} />
            <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
            <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
    );
}

export default function App() {
    return (
        <div className="App">
            <BrowserRouter>
                <AuthProvider>
                    <AppRouter />
                    <Toaster
                        theme="dark"
                        position="top-right"
                        toastOptions={{
                            style: {
                                background: "#0e0e0e",
                                border: "1px solid rgba(255,255,255,0.1)",
                                color: "#fff",
                            },
                        }}
                    />
                </AuthProvider>
            </BrowserRouter>
        </div>
    );
}
