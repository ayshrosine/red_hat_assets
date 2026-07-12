import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import { MAINT } from "@/constants/testIds";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { toast } from "sonner";
import { useAuth, hasRole } from "@/context/AuthContext";
import { Plus, Flag } from "lucide-react";

const COLUMNS = [
    { key: "pending",    label: "Pending",     accent: "#FFB800" },
    { key: "approved",   label: "Approved",    accent: "#00E5FF" },
    { key: "assigned",   label: "Assigned",    accent: "#A78BFA" },
    { key: "in_progress",label: "In Progress", accent: "#00E5FF" },
    { key: "resolved",   label: "Resolved",    accent: "#00FF94" },
];

const PRIORITY_COLOR = { urgent: "#FF3366", high: "#FFB800", medium: "#00E5FF", low: "#71717A" };

export default function Maintenance() {
    const { user } = useAuth();
    const [params] = useSearchParams();
    const canManage = hasRole(user, "admin", "asset_manager", "department_head");

    const [items, setItems] = useState([]);
    const [assets, setAssets] = useState([]);
    const [open, setOpen] = useState(params.get("raise") === "1");
    const [form, setForm] = useState({ asset_id: params.get("asset") || "", issue: "", priority: "medium", photo_url: "" });

    const load = async () => {
        const [m, a] = await Promise.all([api.get("/maintenance"), api.get("/assets")]);
        setItems(m.data); setAssets(a.data);
    };

    useEffect(() => { load(); }, []);

    const create = async () => {
        try {
            await api.post("/maintenance", form);
            toast.success("Request raised");
            setOpen(false); setForm({ asset_id: "", issue: "", priority: "medium", photo_url: "" });
            load();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const move = async (request_id, to_status, technician = "") => {
        try {
            await api.post("/maintenance/move", { request_id, to_status, technician });
            toast.success(`Moved to ${to_status.replace(/_/g, " ")}`);
            load();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const rejected = items.filter((i) => i.status === "rejected");

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Maintenance</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Maintenance board</h1>
                    <p className="mt-2 text-white/50 text-sm">Approve, assign and resolve — asset status stays in sync.</p>
                </div>
                <Button data-testid={MAINT.raiseButton} onClick={() => setOpen(true)} className="bg-white text-black hover:bg-white/90 h-10">
                    <Plus size={14} className="mr-1.5" /> Raise request
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4">
                {COLUMNS.map((col) => {
                    const cards = items.filter((i) => i.status === col.key);
                    return (
                        <div
                            key={col.key}
                            className="rounded-xl border border-white/5 bg-white/[0.02] p-3 kanban-col-glow"
                            style={{ "--tw-shadow-color": `${col.accent}12` }}
                            data-testid={`kanban-column-${col.key}`}
                        >
                            <div className="flex items-center justify-between px-1 py-2 mb-2">
                                <div className="flex items-center gap-2">
                                    <span className="dot-glow" style={{ background: col.accent, color: col.accent }} />
                                    <p className="text-[11px] uppercase tracking-[0.16em] text-white/60">{col.label}</p>
                                </div>
                                <span className="text-[11px] text-white/40 tabular-nums">{cards.length}</span>
                            </div>
                            <div className="space-y-2 min-h-[100px]">
                                {cards.map((c) => (
                                    <Card key={c.request_id} card={c} canManage={canManage} onMove={move} />
                                ))}
                                {cards.length === 0 && (
                                    <div className="text-[11px] text-white/25 text-center py-6 border border-dashed border-white/5 rounded-lg">Empty</div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {rejected.length > 0 && (
                <div className="rounded-xl border border-[#FF3366]/20 bg-[#FF3366]/5 p-4">
                    <p className="text-[10px] uppercase tracking-[0.18em] text-[#FF3366] mb-2">Rejected</p>
                    <ul className="text-sm space-y-1">
                        {rejected.map((r) => <li key={r.request_id} className="text-white/70">{r.asset_name} — {r.issue}</li>)}
                    </ul>
                </div>
            )}

            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="bg-[#0e0e0e] border-white/10">
                    <DialogHeader>
                        <DialogTitle>Raise maintenance request</DialogTitle>
                        <DialogDescription className="text-white/50">Describe the issue and its urgency.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div className="space-y-1.5">
                            <Label className="text-xs">Asset</Label>
                            <Select value={form.asset_id} onValueChange={(v) => setForm((f) => ({ ...f, asset_id: v }))}>
                                <SelectTrigger data-testid={MAINT.selectAsset} className="bg-white/[0.03] border-white/10"><SelectValue placeholder="Select asset" /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    {assets.map((a) => <SelectItem key={a.asset_id} value={a.asset_id}>{a.tag} · {a.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Issue</Label>
                            <Textarea data-testid={MAINT.issueInput} rows={3} value={form.issue} onChange={(e) => setForm((f) => ({ ...f, issue: e.target.value }))} placeholder="Describe what's wrong…" />
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Priority</Label>
                            <Select value={form.priority} onValueChange={(v) => setForm((f) => ({ ...f, priority: v }))}>
                                <SelectTrigger data-testid={MAINT.prioritySelect} className="bg-white/[0.03] border-white/10"><SelectValue /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    <SelectItem value="low">Low</SelectItem>
                                    <SelectItem value="medium">Medium</SelectItem>
                                    <SelectItem value="high">High</SelectItem>
                                    <SelectItem value="urgent">Urgent</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button data-testid={MAINT.submit} onClick={create} disabled={!form.asset_id || !form.issue.trim()} className="bg-white text-black hover:bg-white/90">Raise</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

function Card({ card, canManage, onMove }) {
    const pc = PRIORITY_COLOR[card.priority] || "#71717A";
    return (
        <div className="rounded-lg border border-white/10 bg-[#181818] p-3 space-y-2 hover:border-white/20 transition-colors" data-testid={`maint-card-${card.request_id}`}>
            <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-white leading-snug">{card.asset_name}</p>
                <span className="text-[10px] flex items-center gap-1 px-1.5 py-0.5 rounded" style={{ background: `${pc}18`, color: pc, border: `1px solid ${pc}33` }}>
                    <Flag size={9} /> {card.priority}
                </span>
            </div>
            <p className="text-xs text-white/60 leading-snug line-clamp-2">{card.issue}</p>
            <p className="text-[10px] text-white/30 tabular-nums">by {card.raised_by_name} · {new Date(card.created_at).toLocaleDateString()}</p>
            {canManage && (
                <div className="flex flex-wrap gap-1 pt-1 border-t border-white/5">
                    {card.status === "pending" && (
                        <>
                            <button data-testid={MAINT.approveButton} onClick={() => onMove(card.request_id, "approved")} className="text-[10px] px-2 py-1 rounded bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20 hover:bg-[#00E5FF]/20">Approve</button>
                            <button data-testid={MAINT.rejectButton} onClick={() => onMove(card.request_id, "rejected")} className="text-[10px] px-2 py-1 rounded bg-[#FF3366]/10 text-[#FF3366] border border-[#FF3366]/20 hover:bg-[#FF3366]/20">Reject</button>
                        </>
                    )}
                    {card.status === "approved" && (
                        <button data-testid={MAINT.assignButton} onClick={() => onMove(card.request_id, "assigned", "In-house")} className="text-[10px] px-2 py-1 rounded bg-[#A78BFA]/10 text-[#A78BFA] border border-[#A78BFA]/20 hover:bg-[#A78BFA]/20">Assign</button>
                    )}
                    {card.status === "assigned" && (
                        <button data-testid={MAINT.inProgressButton} onClick={() => onMove(card.request_id, "in_progress")} className="text-[10px] px-2 py-1 rounded bg-[#00E5FF]/10 text-[#00E5FF] border border-[#00E5FF]/20 hover:bg-[#00E5FF]/20">Start</button>
                    )}
                    {card.status === "in_progress" && (
                        <button data-testid={MAINT.resolveButton} onClick={() => onMove(card.request_id, "resolved")} className="text-[10px] px-2 py-1 rounded bg-[#00FF94]/10 text-[#00FF94] border border-[#00FF94]/20 hover:bg-[#00FF94]/20">Resolve</button>
                    )}
                </div>
            )}
        </div>
    );
}
