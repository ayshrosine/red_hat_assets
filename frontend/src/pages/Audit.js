import React, { useEffect, useMemo, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { useAuth, hasRole } from "@/context/AuthContext";
import { Plus, ClipboardCheck, CheckCircle2, XCircle, AlertTriangle, ArrowLeft } from "lucide-react";

export default function Audit() {
    const { user } = useAuth();
    const canManage = hasRole(user, "admin", "asset_manager");
    const [cycles, setCycles] = useState([]);
    const [detail, setDetail] = useState(null); // { cycle, items }
    const [depts, setDepts] = useState([]);
    const [users, setUsers] = useState([]);
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ name: "", department_id: "", location: "", start_date: "", end_date: "", auditor_ids: [] });

    const loadCycles = async () => {
        const { data } = await api.get("/audit/cycles");
        setCycles(data);
    };
    const loadRefs = async () => {
        const [d, u] = await Promise.all([api.get("/departments"), api.get("/users")]);
        setDepts(d.data); setUsers(u.data);
    };
    useEffect(() => { loadCycles(); loadRefs(); }, []);

    const openDetail = async (cycleId) => {
        const { data } = await api.get(`/audit/cycles/${cycleId}`);
        setDetail(data);
    };

    const createCycle = async () => {
        try {
            await api.post("/audit/cycles", {
                name: form.name,
                department_id: form.department_id || null,
                location: form.location,
                start_date: form.start_date,
                end_date: form.end_date,
                auditor_ids: form.auditor_ids,
            });
            toast.success("Audit cycle created");
            setOpen(false);
            setForm({ name: "", department_id: "", location: "", start_date: "", end_date: "", auditor_ids: [] });
            loadCycles();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    if (detail) return <AuditDetail data={detail} onClose={() => { setDetail(null); loadCycles(); }} canManage={canManage} />;

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Audit</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Audit cycles</h1>
                    <p className="mt-2 text-white/50 text-sm">Scheduled discovery — verify, flag missing, mark damaged, close.</p>
                </div>
                {canManage && (
                    <Button data-testid="audit-new-cycle" onClick={() => setOpen(true)} className="bg-white text-black hover:bg-white/90 h-10">
                        <Plus size={14} className="mr-1.5" /> New audit cycle
                    </Button>
                )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cycles.length === 0 && (
                    <div className="col-span-full rounded-xl border border-dashed border-white/10 bg-[#0e0e0e] p-12 text-center">
                        <ClipboardCheck size={22} className="mx-auto text-white/30 mb-3" />
                        <p className="text-sm text-white/50">No audit cycles yet. Kick one off to inventory a department or location.</p>
                    </div>
                )}
                {cycles.map((c) => {
                    const total = c.asset_count || 0;
                    const c_ = c.counts || {};
                    const done = (c_.verified || 0) + (c_.missing || 0) + (c_.damaged || 0);
                    const pct = total ? Math.round((done / total) * 100) : 0;
                    return (
                        <button
                            key={c.cycle_id}
                            onClick={() => openDetail(c.cycle_id)}
                            data-testid={`audit-card-${c.cycle_id}`}
                            className="text-left rounded-xl border border-white/10 bg-[#0e0e0e] p-5 hover:border-white/20 hover:-translate-y-[2px] transition-all"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <p className="text-[10px] uppercase tracking-[0.18em] text-white/40">{c.status.replace("_", " ")}</p>
                                <span className={`text-[10px] px-2 py-0.5 rounded-full border ${c.status === "closed" ? "border-white/10 text-white/50 bg-white/[0.02]" : "border-[#00FF94]/25 text-[#00FF94] bg-[#00FF94]/10"}`}>
                                    {c.status === "closed" ? "Closed" : "Open"}
                                </span>
                            </div>
                            <h3 className="font-display text-lg font-medium mb-1">{c.name}</h3>
                            <p className="text-xs text-white/40 mb-4 tabular-nums">
                                {c.start_date} → {c.end_date}
                            </p>
                            <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden mb-3">
                                <div className="h-full bg-[#00FF94]" style={{ width: `${pct}%` }} />
                            </div>
                            <div className="grid grid-cols-4 gap-2 text-[11px]">
                                <Metric label="Assets" value={total} color="#fff" />
                                <Metric label="Verified" value={c_.verified || 0} color="#00FF94" />
                                <Metric label="Missing" value={c_.missing || 0} color="#FF3366" />
                                <Metric label="Damaged" value={c_.damaged || 0} color="#FFB800" />
                            </div>
                        </button>
                    );
                })}
            </div>

            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="bg-[#0e0e0e] border-white/10">
                    <DialogHeader>
                        <DialogTitle>New audit cycle</DialogTitle>
                        <DialogDescription className="text-white/50">Snapshots eligible assets right now.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div className="space-y-1.5">
                            <Label className="text-xs">Name</Label>
                            <Input data-testid="audit-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Q1 Sweep" />
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <Label className="text-xs">Department (optional)</Label>
                                <Select value={form.department_id || "all"} onValueChange={(v) => setForm({ ...form, department_id: v === "all" ? "" : v })}>
                                    <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue placeholder="All" /></SelectTrigger>
                                    <SelectContent className="bg-[#0e0e0e] border-white/10">
                                        <SelectItem value="all">All departments</SelectItem>
                                        {depts.map((d) => <SelectItem key={d.department_id} value={d.department_id}>{d.name}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">Location filter (optional)</Label>
                                <Input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} placeholder="HQ / Floor 3" />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <Label className="text-xs">Start date</Label>
                                <Input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">End date</Label>
                                <Input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
                            </div>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Assign auditors (optional)</Label>
                            <div className="rounded-lg border border-white/10 bg-white/[0.02] max-h-40 overflow-y-auto p-2 space-y-1">
                                {users.map((u) => {
                                    const checked = form.auditor_ids.includes(u.user_id);
                                    return (
                                        <label key={u.user_id} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/[0.03] cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={checked}
                                                onChange={(e) => {
                                                    if (e.target.checked) setForm({ ...form, auditor_ids: [...form.auditor_ids, u.user_id] });
                                                    else setForm({ ...form, auditor_ids: form.auditor_ids.filter((id) => id !== u.user_id) });
                                                }}
                                                className="accent-white"
                                            />
                                            <span className="text-sm">{u.name}</span>
                                            <span className="text-xs text-white/40 ml-auto">{u.role.replace("_", " ")}</span>
                                        </label>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button data-testid="audit-create" onClick={createCycle} disabled={!form.name || !form.start_date || !form.end_date} className="bg-white text-black hover:bg-white/90">
                            Create
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

function Metric({ label, value, color }) {
    return (
        <div>
            <p className="text-[9px] uppercase tracking-[0.14em] text-white/40">{label}</p>
            <p className="font-display text-base tabular-nums" style={{ color }}>{value}</p>
        </div>
    );
}

function AuditDetail({ data, onClose, canManage }) {
    const { cycle, items: initial } = data;
    const [items, setItems] = useState(initial);
    const [notes, setNotes] = useState({}); // item_id -> note

    const mark = async (item, result) => {
        try {
            await api.post(`/audit/items/${item.item_id}/mark`, { result, notes: notes[item.item_id] || "" });
            setItems((prev) => prev.map((it) => it.item_id === item.item_id ? { ...it, result, notes: notes[item.item_id] || "" } : it));
            toast.success(`Marked ${result}`);
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const close = async () => {
        if (!window.confirm("Close this cycle? Missing → Lost, Damaged → Under Maintenance. Cannot be undone.")) return;
        try {
            const { data } = await api.post(`/audit/cycles/${cycle.cycle_id}/close`);
            toast.success(`Closed. ${data.missing_updated} lost · ${data.damaged_updated} to maintenance.`);
            onClose();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const counts = useMemo(() => {
        const c = { verified: 0, missing: 0, damaged: 0, pending: 0 };
        items.forEach((it) => { c[it.result || "pending"]++; });
        return c;
    }, [items]);
    const discrepancies = items.filter((it) => it.result === "missing" || it.result === "damaged");

    return (
        <div className="space-y-8">
            <button onClick={onClose} className="text-xs text-white/50 hover:text-white flex items-center gap-1"><ArrowLeft size={12} /> Back to cycles</button>

            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Audit · {cycle.status.replace("_", " ")}</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">{cycle.name}</h1>
                    <p className="mt-2 text-white/50 text-sm tabular-nums">{cycle.start_date} → {cycle.end_date} · {cycle.asset_count} assets</p>
                </div>
                {canManage && cycle.status !== "closed" && (
                    <Button data-testid="audit-close-cycle" onClick={close} className="bg-[#FF3366]/10 border border-[#FF3366]/25 text-[#FF3366] hover:bg-[#FF3366]/20 h-10">
                        Close cycle
                    </Button>
                )}
            </div>

            <div className="grid grid-cols-4 gap-4">
                <Card label="Verified" value={counts.verified} color="#00FF94" />
                <Card label="Missing" value={counts.missing} color="#FF3366" />
                <Card label="Damaged" value={counts.damaged} color="#FFB800" />
                <Card label="Pending" value={counts.pending} color="#71717A" />
            </div>

            {discrepancies.length > 0 && (
                <div className="rounded-xl border border-[#FF3366]/20 bg-[#FF3366]/[0.05] p-5">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle size={16} className="text-[#FF3366]" />
                        <h3 className="font-display text-lg font-medium">Discrepancy report</h3>
                        <span className="text-xs text-white/40">{discrepancies.length} item{discrepancies.length !== 1 ? "s" : ""}</span>
                    </div>
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-[10px] uppercase tracking-[0.14em] text-white/40 border-b border-white/5">
                                <th className="text-left py-2 font-normal">Tag</th>
                                <th className="text-left py-2 font-normal">Asset</th>
                                <th className="text-left py-2 font-normal">Result</th>
                                <th className="text-left py-2 font-normal">Notes</th>
                            </tr>
                        </thead>
                        <tbody>
                            {discrepancies.map((it) => (
                                <tr key={it.item_id} className="border-b border-white/5 last:border-b-0">
                                    <td className="py-2 font-mono-af text-xs">{it.asset_tag}</td>
                                    <td className="py-2">{it.asset_name}</td>
                                    <td className="py-2" style={{ color: it.result === "missing" ? "#FF3366" : "#FFB800" }}>{it.result}</td>
                                    <td className="py-2 text-white/60">{it.notes || "—"}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
                <div className="p-5 border-b border-white/5"><h3 className="font-display text-lg font-medium">Checklist</h3></div>
                <div className="divide-y divide-white/5">
                    {items.map((it) => (
                        <div key={it.item_id} className="p-4 flex items-start gap-4">
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3">
                                    <span className="font-mono-af text-xs text-white/50">{it.asset_tag}</span>
                                    <p className="text-sm">{it.asset_name}</p>
                                    {it.result && (
                                        <span className="text-[10px] px-2 py-0.5 rounded-full" style={{
                                            color: it.result === "verified" ? "#00FF94" : it.result === "missing" ? "#FF3366" : "#FFB800",
                                            background: it.result === "verified" ? "rgba(0,255,148,0.1)" : it.result === "missing" ? "rgba(255,51,102,0.1)" : "rgba(255,184,0,0.1)",
                                            border: "1px solid",
                                            borderColor: it.result === "verified" ? "rgba(0,255,148,0.25)" : it.result === "missing" ? "rgba(255,51,102,0.25)" : "rgba(255,184,0,0.25)",
                                        }}>
                                            {it.result}
                                        </span>
                                    )}
                                </div>
                                <p className="text-[11px] text-white/40 mt-1">Expected: {it.expected_location || "—"}</p>
                                {cycle.status !== "closed" && (
                                    <Input placeholder="Note (optional)" className="mt-2 h-8 text-xs" value={notes[it.item_id] ?? it.notes ?? ""} onChange={(e) => setNotes({ ...notes, [it.item_id]: e.target.value })} />
                                )}
                            </div>
                            {cycle.status !== "closed" && (
                                <div className="flex gap-1.5 flex-shrink-0">
                                    <IconButton data-testid={`audit-verify-${it.item_id}`} onClick={() => mark(it, "verified")} color="#00FF94" icon={CheckCircle2} title="Verified" />
                                    <IconButton data-testid={`audit-missing-${it.item_id}`} onClick={() => mark(it, "missing")} color="#FF3366" icon={XCircle} title="Missing" />
                                    <IconButton data-testid={`audit-damaged-${it.item_id}`} onClick={() => mark(it, "damaged")} color="#FFB800" icon={AlertTriangle} title="Damaged" />
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

function IconButton({ onClick, color, icon: Icon, title, ...rest }) {
    return (
        <button
            onClick={onClick}
            title={title}
            className="w-8 h-8 rounded-lg border flex items-center justify-center transition-colors"
            style={{ color, borderColor: `${color}33`, background: `${color}10` }}
            {...rest}
        >
            <Icon size={14} />
        </button>
    );
}

function Card({ label, value, color }) {
    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-4">
            <p className="text-[10px] uppercase tracking-[0.18em] text-white/40 mb-2">{label}</p>
            <p className="font-display text-3xl tabular-nums" style={{ color }}>{value}</p>
        </div>
    );
}
