import React, { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Download, Sparkles, FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, LineChart, Line, CartesianGrid, PieChart, Pie, Cell } from "recharts";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { toast } from "sonner";

const HOURS = Array.from({ length: 12 }, (_, i) => 8 + i); // 8:00 → 19:00
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function Reports() {
    const [assets, setAssets] = useState([]);
    const [allocs, setAllocs] = useState([]);
    const [depts, setDepts] = useState([]);
    const [maint, setMaint] = useState([]);
    const [bookings, setBookings] = useState([]);
    const containerRef = useRef(null);

    useEffect(() => {
        (async () => {
            const [a, al, d, m, b] = await Promise.all([
                api.get("/assets"), api.get("/allocations"), api.get("/departments"), api.get("/maintenance"), api.get("/bookings"),
            ]);
            setAssets(a.data); setAllocs(al.data); setDepts(d.data); setMaint(m.data); setBookings(b.data);
        })();
    }, []);

    const utilization = useMemo(() => depts.map((d) => {
        const inDept = assets.filter((a) => a.department_id === d.department_id);
        const used = inDept.filter((a) => a.status === "allocated").length;
        return { name: d.name, total: inDept.length, allocated: used };
    }), [depts, assets]);

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

    // Booking heatmap: day-of-week × hour buckets
    const heatmap = useMemo(() => {
        // Initialize matrix
        const matrix = Array.from({ length: 7 }, () => Array(HOURS.length).fill(0));
        bookings.filter((b) => b.status !== "cancelled").forEach((b) => {
            const start = new Date(b.start_at);
            const end = new Date(b.end_at);
            // JS getDay(): 0=Sun. Convert to Mon-based
            const jsDay = start.getDay();
            const day = jsDay === 0 ? 6 : jsDay - 1;
            const startHour = Math.max(HOURS[0], start.getHours());
            const endHour = Math.min(HOURS[HOURS.length - 1] + 1, Math.max(startHour + 1, end.getHours() + (end.getMinutes() > 0 ? 1 : 0)));
            for (let h = startHour; h < endHour; h++) {
                const idx = HOURS.indexOf(h);
                if (idx >= 0) matrix[day][idx] += 1;
            }
        });
        return matrix;
    }, [bookings]);

    const maxHeat = useMemo(() => Math.max(1, ...heatmap.flat()), [heatmap]);

    // Most-used vs idle
    const usage = useMemo(() => {
        const useCount = {};
        allocs.forEach((al) => { useCount[al.asset_id] = (useCount[al.asset_id] || 0) + 1; });
        const enriched = assets.map((a) => ({ ...a, uses: useCount[a.asset_id] || 0 }));
        return {
            mostUsed: [...enriched].sort((a, b) => b.uses - a.uses).slice(0, 5),
            idle: enriched.filter((a) => a.uses === 0 && a.status === "available").slice(0, 5),
        };
    }, [assets, allocs]);

    const COLORS = ["#00FF94", "#00E5FF", "#FFB800", "#FF3366", "#A78BFA", "#E0FF00", "#71717A"];

    const csv = () => {
        const rows = [["Tag", "Name", "Status", "Location"], ...assets.map((a) => [a.tag, a.name, a.status, a.location || ""])];
        const csvText = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n");
        const blob = new Blob([csvText], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a"); a.href = url; a.download = "assetflow-report.csv"; a.click();
    };

    const pdf = async () => {
        toast.info("Rendering PDF…");
        try {
            const node = containerRef.current;
            const canvas = await html2canvas(node, {
                backgroundColor: "#050505",
                scale: 1.5,
                useCORS: true,
                windowWidth: node.scrollWidth,
                windowHeight: node.scrollHeight,
            });
            const imgData = canvas.toDataURL("image/jpeg", 0.85);
            const pdfDoc = new jsPDF({ orientation: "portrait", unit: "px", format: [canvas.width, canvas.height] });
            pdfDoc.addImage(imgData, "JPEG", 0, 0, canvas.width, canvas.height);
            pdfDoc.save(`assetflow-report-${new Date().toISOString().slice(0, 10)}.pdf`);
            toast.success("PDF downloaded");
        } catch (e) {
            toast.error("PDF export failed: " + (e?.message || "unknown"));
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Reports</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Reports & analytics</h1>
                    <p className="mt-2 text-white/50 text-sm">Utilization, maintenance frequency, booking heatmap and inventory health.</p>
                </div>
                <div className="flex gap-2">
                    <Button data-testid="reports-export-csv" onClick={csv} variant="secondary" className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08]">
                        <Download size={14} className="mr-1.5" /> CSV
                    </Button>
                    <Button data-testid="reports-export-pdf" onClick={pdf} className="bg-white text-black hover:bg-white/90">
                        <FileDown size={14} className="mr-1.5" /> Export PDF
                    </Button>
                </div>
            </div>

            <div ref={containerRef} className="space-y-6" style={{ background: "#050505" }}>
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

                    <ChartCard title="Allocation velocity" subtitle="Demo trend">
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

                {/* Booking heatmap */}
                <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h3 className="font-display text-lg font-medium">Booking heatmap</h3>
                            <p className="text-xs text-white/40">Hour × day usage · brighter = more concurrent bookings</p>
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-white/50">
                            <span>less</span>
                            <div className="flex gap-1">
                                {[0.15, 0.35, 0.55, 0.75, 1].map((op) => (
                                    <span key={op} className="w-3 h-3 rounded" style={{ background: `rgba(0, 255, 148, ${op})` }} />
                                ))}
                            </div>
                            <span>more</span>
                        </div>
                    </div>
                    <div className="overflow-x-auto">
                        <div className="inline-grid gap-1" style={{ gridTemplateColumns: `48px repeat(${HOURS.length}, minmax(28px, 1fr))` }}>
                            <div />
                            {HOURS.map((h) => (
                                <div key={h} className="text-[10px] text-white/40 text-center tabular-nums">{h}</div>
                            ))}
                            {DAYS.map((day, di) => (
                                <React.Fragment key={day}>
                                    <div className="text-[10px] uppercase tracking-[0.14em] text-white/40 flex items-center">{day}</div>
                                    {HOURS.map((h, hi) => {
                                        const v = heatmap[di][hi];
                                        const intensity = v / maxHeat;
                                        return (
                                            <div
                                                key={hi}
                                                className="aspect-square rounded"
                                                style={{
                                                    background: v > 0 ? `rgba(0, 255, 148, ${0.15 + intensity * 0.75})` : "rgba(255, 255, 255, 0.02)",
                                                    border: "1px solid rgba(255, 255, 255, 0.04)",
                                                }}
                                                title={`${day} ${h}:00 — ${v} booking${v === 1 ? "" : "s"}`}
                                            />
                                        );
                                    })}
                                </React.Fragment>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Most used vs idle */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <ChartCard title="Most-used assets">
                        <ul className="divide-y divide-white/5">
                            {usage.mostUsed.map((a) => (
                                <li key={a.asset_id} className="py-2.5 flex items-center justify-between">
                                    <div>
                                        <p className="text-sm">{a.name}</p>
                                        <p className="text-[11px] text-white/40 font-mono-af">{a.tag}</p>
                                    </div>
                                    <span className="text-sm text-white/70 tabular-nums">{a.uses} allocation{a.uses === 1 ? "" : "s"}</span>
                                </li>
                            ))}
                            {usage.mostUsed.length === 0 && <p className="text-sm text-white/40 py-4 text-center">No allocations yet.</p>}
                        </ul>
                    </ChartCard>
                    <ChartCard title="Idle assets" subtitle="Available and never allocated">
                        <ul className="divide-y divide-white/5">
                            {usage.idle.map((a) => (
                                <li key={a.asset_id} className="py-2.5 flex items-center justify-between">
                                    <div>
                                        <p className="text-sm">{a.name}</p>
                                        <p className="text-[11px] text-white/40 font-mono-af">{a.tag}</p>
                                    </div>
                                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-white/50">idle</span>
                                </li>
                            ))}
                            {usage.idle.length === 0 && <p className="text-sm text-white/40 py-4 text-center">Every asset has been used.</p>}
                        </ul>
                    </ChartCard>
                </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-6 flex items-start gap-3">
                <Sparkles size={16} className="text-[#00FF94] mt-0.5" />
                <p className="text-sm text-white/70">
                    Reports refresh live from your data. Export a snapshot to PDF for stakeholder reviews, or pipe the CSV into your BI tool.
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
