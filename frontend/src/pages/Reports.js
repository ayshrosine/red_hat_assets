import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { BarChart3, Download, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, LineChart, Line, CartesianGrid, PieChart, Pie, Cell } from "recharts";

export default function Reports() {
    const [assets, setAssets] = useState([]);
    const [allocs, setAllocs] = useState([]);
    const [depts, setDepts] = useState([]);
    const [maint, setMaint] = useState([]);

    useEffect(() => {
        (async () => {
            const [a, al, d, m] = await Promise.all([
                api.get("/assets"), api.get("/allocations"), api.get("/departments"), api.get("/maintenance"),
            ]);
            setAssets(a.data); setAllocs(al.data); setDepts(d.data); setMaint(m.data);
        })();
    }, []);

    const utilization = useMemo(() => {
        return depts.map((d) => {
            const inDept = assets.filter((a) => a.department_id === d.department_id);
            const used = inDept.filter((a) => a.status === "allocated").length;
            return { name: d.name, total: inDept.length, allocated: used };
        });
    }, [depts, assets]);

    const statusDist = useMemo(() => {
        const map = {};
        assets.forEach((a) => { map[a.status] = (map[a.status] || 0) + 1; });
        return Object.entries(map).map(([status, count]) => ({ status: status.replace(/_/g, " "), count }));
    }, [assets]);

    const maintByPriority = useMemo(() => {
        const map = { low: 0, medium: 0, high: 0, urgent: 0 };
        maint.forEach((m) => { map[m.priority] = (map[m.priority] || 0) + 1; });
        return Object.entries(map).map(([priority, count]) => ({ priority, count }));
    }, [maint]);

    const csv = () => {
        const rows = [["Tag", "Name", "Status", "Location"], ...assets.map((a) => [a.tag, a.name, a.status, a.location || ""])];
        const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = "assets.csv"; a.click();
    };

    const COLORS = ["#00FF94", "#00E5FF", "#FFB800", "#FF3366", "#A78BFA", "#E0FF00", "#71717A"];

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Reports</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Reports & analytics</h1>
                    <p className="mt-2 text-white/50 text-sm">Utilization, maintenance frequency and inventory health.</p>
                </div>
                <Button onClick={csv} variant="secondary" className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08]">
                    <Download size={14} className="mr-1.5" /> Export CSV
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ChartCard title="Utilization by department">
                    <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={utilization} margin={{ left: -20, right: 8 }}>
                            <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="name" tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip cursor={{ fill: "rgba(255,255,255,0.03)" }} contentStyle={{ background: "#0e0e0e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
                            <Bar dataKey="total" fill="#3f3f46" radius={[4, 4, 0, 0]} />
                            <Bar dataKey="allocated" fill="#00FF94" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Status distribution">
                    <ResponsiveContainer width="100%" height={260}>
                        <PieChart>
                            <Pie data={statusDist} dataKey="count" nameKey="status" innerRadius={60} outerRadius={100} paddingAngle={2}>
                                {statusDist.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="#0e0e0e" strokeWidth={2} />)}
                            </Pie>
                            <Tooltip contentStyle={{ background: "#0e0e0e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
                        </PieChart>
                    </ResponsiveContainer>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                        {statusDist.map((s, i) => (
                            <div key={s.status} className="flex items-center gap-2 text-white/60">
                                <span className="w-2 h-2 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
                                <span className="capitalize">{s.status}</span>
                                <span className="ml-auto tabular-nums">{s.count}</span>
                            </div>
                        ))}
                    </div>
                </ChartCard>

                <ChartCard title="Maintenance by priority">
                    <ResponsiveContainer width="100%" height={260}>
                        <BarChart data={maintByPriority} margin={{ left: -20, right: 8 }}>
                            <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="priority" tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip cursor={{ fill: "rgba(255,255,255,0.03)" }} contentStyle={{ background: "#0e0e0e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
                            <Bar dataKey="count" fill="#FFB800" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </ChartCard>

                <ChartCard title="Allocation velocity" subtitle="Placeholder demo trend">
                    <ResponsiveContainer width="100%" height={260}>
                        <LineChart data={[{ w: "W1", v: 2 }, { w: "W2", v: 5 }, { w: "W3", v: 4 }, { w: "W4", v: 7 }, { w: "W5", v: 6 }, { w: "W6", v: 9 }]} margin={{ left: -20, right: 8 }}>
                            <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="w" tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                            <YAxis tick={{ fill: "#a1a1aa", fontSize: 11 }} axisLine={false} tickLine={false} />
                            <Tooltip contentStyle={{ background: "#0e0e0e", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
                            <Line type="monotone" dataKey="v" stroke="#00E5FF" strokeWidth={2} dot={{ fill: "#00E5FF", r: 3 }} />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>
            </div>

            <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-6 flex items-start gap-3">
                <Sparkles size={16} className="text-[#00FF94] mt-0.5" />
                <p className="text-sm text-white/70">
                    More reports coming in Phase 7: booking heatmap, PDF export, most-used vs idle assets, and assets nearing retirement.
                </p>
            </div>
        </div>
    );
}

function ChartCard({ title, subtitle, children }) {
    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5">
            <div className="mb-4">
                <h3 className="font-display text-lg font-medium">{title}</h3>
                {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
            </div>
            {children}
        </div>
    );
}
