import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import StatusPill from "@/components/StatusPill";
import { DASH } from "@/constants/testIds";
import { Button } from "@/components/ui/button";
import {
    Boxes, TrendingUp, ArrowUpRight, Plus, CalendarPlus, Wrench,
    AlertTriangle, Clock, ArrowRightLeft,
} from "lucide-react";

export default function Dashboard() {
    const { user } = useAuth();
    const nav = useNavigate();
    const [stats, setStats] = useState(null);
    const [activity, setActivity] = useState([]);

    useEffect(() => {
        (async () => {
            const [s, a] = await Promise.all([
                api.get("/dashboard/stats"),
                api.get("/activity", { params: { limit: 8 } }),
            ]);
            setStats(s.data);
            setActivity(a.data);
        })();
    }, []);

    if (!stats) return <SkeletonDash />;

    const hour = new Date().getHours();
    const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Dashboard</p>
                    <h1 className="font-display text-4xl md:text-5xl font-medium tracking-tighter">
                        {greet}, <span style={{ background: "linear-gradient(90deg,#fff,#a1a1aa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{user?.name?.split(" ")[0] || "there"}</span>.
                    </h1>
                    <p className="mt-2 text-white/50 text-sm">Here&apos;s what&apos;s moving across your workspace today.</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                    <Button data-testid={DASH.quickRegister} onClick={() => nav("/assets?new=1")} className="bg-white text-black hover:bg-white/90 h-10">
                        <Plus size={14} className="mr-1.5" /> Register asset
                    </Button>
                    <Button data-testid={DASH.quickBook} variant="secondary" onClick={() => nav("/booking")} className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] h-10">
                        <CalendarPlus size={14} className="mr-1.5" /> Book resource
                    </Button>
                    <Button data-testid={DASH.quickMaintenance} variant="secondary" onClick={() => nav("/maintenance?raise=1")} className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] h-10">
                        <Wrench size={14} className="mr-1.5" /> Raise request
                    </Button>
                </div>
            </div>

            {/* Overdue banner */}
            {stats.overdue > 0 && (
                <div
                    data-testid={DASH.overdueBanner}
                    className="rounded-xl border p-4 flex items-center gap-3 justify-between"
                    style={{ background: "rgba(255,51,102,0.06)", borderColor: "rgba(255,51,102,0.25)" }}
                >
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: "rgba(255,51,102,0.12)" }}>
                            <AlertTriangle size={16} className="text-[#FF3366]" />
                        </div>
                        <div>
                            <p className="text-sm text-white">
                                <span className="font-medium">{stats.overdue}</span> overdue return{stats.overdue > 1 ? "s" : ""} require attention.
                            </p>
                            <p className="text-xs text-white/50">Take action to avoid escalation.</p>
                        </div>
                    </div>
                    <Button onClick={() => nav("/allocation")} variant="ghost" className="hover:bg-white/5 text-[#FF3366]">
                        Review <ArrowUpRight size={14} className="ml-1" />
                    </Button>
                </div>
            )}

            {/* Stats grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <StatCard tid={DASH.cardTotal} label="Total assets" value={stats.total} icon={Boxes} accent="#fff" />
                <StatCard tid={DASH.cardAvailable} label="Available" value={stats.available} accent="#00FF94" />
                <StatCard tid={DASH.cardAllocated} label="Allocated" value={stats.allocated} accent="#00E5FF" />
                <StatCard tid={DASH.cardMaintenance} label="Maintenance" value={stats.under_maintenance} accent="#FFB800" />
                <StatCard tid={DASH.cardBookings} label="Active bookings" value={stats.active_bookings} icon={Clock} accent="#E0FF00" />
                <StatCard tid={DASH.cardTransfers} label="Pending transfers" value={stats.pending_transfers} icon={ArrowRightLeft} accent="#A78BFA" />
            </div>

            {/* Activity + snapshots */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 rounded-xl border border-white/10 bg-[#0e0e0e] p-6" data-testid={DASH.activityFeed}>
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-display text-lg font-medium tracking-tight">Recent activity</h3>
                        <button onClick={() => nav("/notifications")} className="text-xs text-white/50 hover:text-white">
                            View all <ArrowUpRight size={12} className="inline" />
                        </button>
                    </div>
                    <ul className="space-y-1">
                        {activity.length === 0 && (
                            <li className="text-sm text-white/40 py-8 text-center">No activity yet.</li>
                        )}
                        {activity.map((a) => (
                            <li key={a.activity_id} className="flex items-start gap-3 py-2.5 border-b border-white/5 last:border-b-0">
                                <div className="w-7 h-7 rounded-full bg-white/5 flex items-center justify-center text-[10px] font-medium mt-0.5">
                                    {(a.actor_name || "?").split(" ").map((s) => s[0]).slice(0, 2).join("")}
                                </div>
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm text-white/80">
                                        <span className="text-white">{a.actor_name}</span>{" "}
                                        <span className="text-white/50">{a.action.replace(/_/g, " ")}</span>{" "}
                                        <span className="text-white">{a.target_name}</span>
                                    </p>
                                    <p className="text-[11px] text-white/40 mt-0.5 tabular-nums">
                                        {new Date(a.created_at).toLocaleString()}
                                    </p>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>

                <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-6">
                    <h3 className="font-display text-lg font-medium tracking-tight mb-4">Distribution</h3>
                    <DistributionBar available={stats.available} allocated={stats.allocated} maintenance={stats.under_maintenance} total={stats.total} />
                    <div className="mt-6 space-y-2.5">
                        {[
                            { label: "Available", val: stats.available, k: "available" },
                            { label: "Allocated", val: stats.allocated, k: "allocated" },
                            { label: "Maintenance", val: stats.under_maintenance, k: "under_maintenance" },
                        ].map((r) => (
                            <div key={r.label} className="flex items-center justify-between text-sm">
                                <StatusPill status={r.k} label={r.label} />
                                <span className="font-mono-af tabular-nums text-white/80">{r.val}</span>
                            </div>
                        ))}
                    </div>
                    <div className="mt-6 pt-6 border-t border-white/5">
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-white/60">Upcoming returns</span>
                            <span className="font-mono-af tabular-nums">{stats.upcoming_returns}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ label, value, icon: Icon, accent, tid }) {
    return (
        <div
            data-testid={tid}
            className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5 hover:-translate-y-[2px] hover:border-white/20 transition-all duration-200"
        >
            <div className="flex items-start justify-between mb-4">
                <p className="text-[10px] uppercase tracking-[0.18em] text-white/40">{label}</p>
                {Icon && <Icon size={14} strokeWidth={1.5} className="text-white/40" />}
            </div>
            <p className="font-display font-medium text-3xl tracking-tighter tabular-nums" style={{ color: accent }}>
                {value}
            </p>
        </div>
    );
}

function DistributionBar({ available, allocated, maintenance, total }) {
    const t = total || 1;
    const a = (available / t) * 100;
    const al = (allocated / t) * 100;
    const m = (maintenance / t) * 100;
    return (
        <div className="h-3 w-full rounded-full overflow-hidden flex bg-white/5">
            <div style={{ width: `${a}%`, background: "#00FF94" }} />
            <div style={{ width: `${al}%`, background: "#00E5FF" }} />
            <div style={{ width: `${m}%`, background: "#FFB800" }} />
        </div>
    );
}

function SkeletonDash() {
    return (
        <div className="space-y-6 animate-pulse">
            <div className="h-10 w-64 bg-white/5 rounded" />
            <div className="grid grid-cols-6 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div key={i} className="h-24 rounded-xl bg-white/5" />
                ))}
            </div>
            <div className="h-64 rounded-xl bg-white/5" />
        </div>
    );
}
