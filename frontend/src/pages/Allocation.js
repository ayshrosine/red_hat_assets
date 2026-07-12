import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, formatApiError, extractDetail } from "@/lib/api";
import { ALLOC } from "@/constants/testIds";
import StatusPill from "@/components/StatusPill";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";
import { useAuth, hasRole } from "@/context/AuthContext";
import { ArrowRightLeft, CheckCircle2, XCircle, AlertOctagon, Undo2 } from "lucide-react";

export default function Allocation() {
    const { user } = useAuth();
    const [params] = useSearchParams();
    const canApprove = hasRole(user, "admin", "asset_manager", "department_head");

    const [assets, setAssets] = useState([]);
    const [users, setUsers] = useState([]);
    const [allocs, setAllocs] = useState([]);
    const [transfers, setTransfers] = useState([]);

    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ asset_id: params.get("asset") || "", assignee_user_id: "", expected_return: "", notes: "" });
    const [conflict, setConflict] = useState(null); // { current_holder, asset_id }

    const [tOpen, setTOpen] = useState(false);
    const [tForm, setTForm] = useState({ asset_id: "", to_user_id: "", reason: "" });

    const load = async () => {
        const [a, u, al, tr] = await Promise.all([
            api.get("/assets"),
            api.get("/users"),
            api.get("/allocations"),
            api.get("/transfers"),
        ]);
        setAssets(a.data); setUsers(u.data); setAllocs(al.data); setTransfers(tr.data);
    };

    useEffect(() => { load(); }, []);

    const allocate = async () => {
        setConflict(null);
        try {
            await api.post("/allocations", {
                asset_id: form.asset_id,
                assignee_user_id: form.assignee_user_id,
                expected_return: form.expected_return ? new Date(form.expected_return + "T23:59:59").toISOString() : null,
                notes: form.notes,
            });
            toast.success("Asset allocated");
            setOpen(false);
            setForm({ asset_id: "", assignee_user_id: "", expected_return: "", notes: "" });
            load();
        } catch (e) {
            const detail = extractDetail(e);
            if (e?.response?.status === 409 && detail?.current_holder) {
                setConflict({ ...detail, asset_id: form.asset_id });
                toast.error("Asset already allocated — try a transfer.");
            } else {
                toast.error(formatApiError(e));
            }
        }
    };

    const requestTransfer = async () => {
        try {
            await api.post("/transfers", tForm);
            toast.success("Transfer requested");
            setTOpen(false);
            setTForm({ asset_id: "", to_user_id: "", reason: "" });
            load();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const approveT = async (id) => {
        try { await api.post(`/transfers/${id}/approve`); toast.success("Transfer approved"); load(); }
        catch (e) { toast.error(formatApiError(e)); }
    };
    const rejectT = async (id) => {
        try { await api.post(`/transfers/${id}/reject`); toast.success("Rejected"); load(); }
        catch (e) { toast.error(formatApiError(e)); }
    };
    const returnA = async (id) => {
        if (!window.confirm("Confirm asset return?")) return;
        try { await api.post("/allocations/return", { allocation_id: id, condition_notes: "" }); toast.success("Returned"); load(); }
        catch (e) { toast.error(formatApiError(e)); }
    };

    const activeAllocs = allocs.filter((a) => a.state === "active");
    const overdueList = activeAllocs.filter((a) => a.expected_return && new Date(a.expected_return) < new Date());
    const pendingTransfers = transfers.filter((t) => t.status === "requested");

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Allocation</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Allocation & Transfer</h1>
                    <p className="mt-2 text-white/50 text-sm">Assign assets to people. Move them safely between hands.</p>
                </div>
                <div className="flex gap-2">
                    {canApprove && (
                        <Button data-testid={ALLOC.allocateButton} onClick={() => setOpen(true)} className="bg-white text-black hover:bg-white/90 h-10">
                            Allocate asset
                        </Button>
                    )}
                    <Button data-testid={ALLOC.transferButton} variant="secondary" onClick={() => setTOpen(true)} className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] h-10">
                        <ArrowRightLeft size={14} className="mr-1.5" /> Request transfer
                    </Button>
                </div>
            </div>

            {conflict && (
                <div className="rounded-xl border p-4 flex items-start gap-3" style={{ background: "rgba(255,184,0,0.06)", borderColor: "rgba(255,184,0,0.25)" }} data-testid="double-alloc-warning">
                    <AlertOctagon size={18} className="text-[#FFB800] mt-0.5" />
                    <div className="flex-1">
                        <p className="text-sm text-white">Asset is currently held by <span className="font-medium">{conflict.current_holder?.name}</span>.</p>
                        <p className="text-xs text-white/50 mt-0.5">Direct re-allocation is blocked. Initiate a transfer instead.</p>
                    </div>
                    <Button size="sm" onClick={() => { setTForm((f) => ({ ...f, asset_id: conflict.asset_id })); setTOpen(true); setConflict(null); }} className="bg-white text-black hover:bg-white/90 h-8">
                        Start transfer
                    </Button>
                </div>
            )}

            <Tabs defaultValue="active">
                <div className="-mx-1 overflow-x-auto scrollbar-none">
                    <TabsList className="bg-white/[0.03] border border-white/10 p-1 w-max">
                        <TabsTrigger value="active" className="data-[state=active]:bg-white data-[state=active]:text-black">Active ({activeAllocs.length})</TabsTrigger>
                        <TabsTrigger value="overdue" className="data-[state=active]:bg-white data-[state=active]:text-black">Overdue ({overdueList.length})</TabsTrigger>
                        <TabsTrigger value="transfers" className="data-[state=active]:bg-white data-[state=active]:text-black">Transfers ({pendingTransfers.length})</TabsTrigger>
                        <TabsTrigger value="all" className="data-[state=active]:bg-white data-[state=active]:text-black">All history</TabsTrigger>
                    </TabsList>
                </div>

                <TabsContent value="active" className="mt-6">
                    <AllocTable list={activeAllocs} onReturn={returnA} />
                </TabsContent>
                <TabsContent value="overdue" className="mt-6">
                    <AllocTable list={overdueList} highlightOverdue onReturn={returnA} />
                </TabsContent>
                <TabsContent value="transfers" className="mt-6">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] divide-y divide-white/5">
                        {transfers.length === 0 && <div className="p-8 text-center text-sm text-white/40">No transfer activity.</div>}
                        {transfers.map((t) => (
                            <div key={t.transfer_id} className="p-4 flex items-center justify-between">
                                <div>
                                    <p className="text-sm">{t.asset_name} → <span className="text-white">{t.to_user_name}</span></p>
                                    <p className="text-[11px] text-white/40 mt-0.5">{t.reason || "No reason provided"} · {new Date(t.created_at).toLocaleString()}</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <StatusPill status={t.status} />
                                    {t.status === "requested" && canApprove && (
                                        <>
                                            <Button size="sm" data-testid={ALLOC.approveTransfer} onClick={() => approveT(t.transfer_id)} className="h-8 bg-[#00FF94]/10 text-[#00FF94] border border-[#00FF94]/20 hover:bg-[#00FF94]/20"><CheckCircle2 size={12} className="mr-1" />Approve</Button>
                                            <Button size="sm" data-testid={ALLOC.rejectTransfer} onClick={() => rejectT(t.transfer_id)} className="h-8 bg-[#FF3366]/10 text-[#FF3366] border border-[#FF3366]/20 hover:bg-[#FF3366]/20"><XCircle size={12} className="mr-1" />Reject</Button>
                                        </>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </TabsContent>
                <TabsContent value="all" className="mt-6">
                    <AllocTable list={allocs} onReturn={returnA} />
                </TabsContent>
            </Tabs>

            {/* Allocate dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
                <DialogContent className="bg-[#0e0e0e] border-white/10">
                    <DialogHeader>
                        <DialogTitle>Allocate asset</DialogTitle>
                        <DialogDescription className="text-white/50">Assign to a team member with an expected return date.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div className="space-y-1.5">
                            <Label className="text-xs">Asset</Label>
                            <Select value={form.asset_id} onValueChange={(v) => setForm((f) => ({ ...f, asset_id: v }))}>
                                <SelectTrigger data-testid={ALLOC.selectAsset} className="bg-white/[0.03] border-white/10"><SelectValue placeholder="Select asset" /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    {assets.map((a) => <SelectItem key={a.asset_id} value={a.asset_id}>{a.tag} · {a.name} ({a.status})</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Assignee</Label>
                            <Select value={form.assignee_user_id} onValueChange={(v) => setForm((f) => ({ ...f, assignee_user_id: v }))}>
                                <SelectTrigger data-testid={ALLOC.selectAssignee} className="bg-white/[0.03] border-white/10"><SelectValue placeholder="Select person" /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    {users.map((u) => <SelectItem key={u.user_id} value={u.user_id}>{u.name} · {u.email}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Expected return</Label>
                            <Input data-testid={ALLOC.expectedReturn} type="date" value={form.expected_return} onChange={(e) => setForm((f) => ({ ...f, expected_return: e.target.value }))} />
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Notes</Label>
                            <Textarea value={form.notes} onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))} rows={2} />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button data-testid={ALLOC.submit} onClick={allocate} disabled={!form.asset_id || !form.assignee_user_id} className="bg-white text-black hover:bg-white/90">Allocate</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

            {/* Transfer dialog */}
            <Dialog open={tOpen} onOpenChange={setTOpen}>
                <DialogContent className="bg-[#0e0e0e] border-white/10">
                    <DialogHeader>
                        <DialogTitle>Request transfer</DialogTitle>
                        <DialogDescription className="text-white/50">Move an already-allocated asset to a new holder. Needs approval.</DialogDescription>
                    </DialogHeader>
                    <div className="space-y-3">
                        <div className="space-y-1.5">
                            <Label className="text-xs">Asset</Label>
                            <Select value={tForm.asset_id} onValueChange={(v) => setTForm((f) => ({ ...f, asset_id: v }))}>
                                <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue placeholder="Select asset" /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    {assets.map((a) => <SelectItem key={a.asset_id} value={a.asset_id}>{a.tag} · {a.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Transfer to</Label>
                            <Select value={tForm.to_user_id} onValueChange={(v) => setTForm((f) => ({ ...f, to_user_id: v }))}>
                                <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue placeholder="New holder" /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    {users.map((u) => <SelectItem key={u.user_id} value={u.user_id}>{u.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Reason</Label>
                            <Textarea value={tForm.reason} onChange={(e) => setTForm((f) => ({ ...f, reason: e.target.value }))} rows={2} />
                        </div>
                    </div>
                    <DialogFooter>
                        <Button onClick={requestTransfer} disabled={!tForm.asset_id || !tForm.to_user_id} className="bg-white text-black hover:bg-white/90">Request</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}

function AllocTable({ list, highlightOverdue, onReturn }) {
    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e] overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="text-[10px] uppercase tracking-[0.16em] text-white/40 border-b border-white/5">
                        <th className="text-left px-5 py-3 font-normal">Asset</th>
                        <th className="text-left px-5 py-3 font-normal">Assignee</th>
                        <th className="text-left px-5 py-3 font-normal">Allocated</th>
                        <th className="text-left px-5 py-3 font-normal">Expected return</th>
                        <th className="text-left px-5 py-3 font-normal">State</th>
                        <th className="text-right px-5 py-3 font-normal">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {list.map((a) => {
                        const overdue = highlightOverdue || (a.expected_return && a.state === "active" && new Date(a.expected_return) < new Date());
                        return (
                            <tr key={a.allocation_id} className="border-b border-white/5 hover:bg-white/[0.02]">
                                <td className="px-5 py-3 text-white">{a.asset_name}</td>
                                <td className="px-5 py-3 text-white/70">{a.assignee_name}</td>
                                <td className="px-5 py-3 text-white/50 tabular-nums">{new Date(a.created_at).toLocaleDateString()}</td>
                                <td className={"px-5 py-3 tabular-nums " + (overdue && a.state === "active" ? "text-[#FF3366]" : "text-white/50")}>
                                    {a.expected_return ? new Date(a.expected_return).toLocaleDateString() : "—"}
                                </td>
                                <td className="px-5 py-3">
                                    {overdue && a.state === "active" ? <StatusPill status="overdue" /> : <StatusPill status={a.state} />}
                                </td>
                                <td className="px-5 py-3 text-right">
                                    {a.state === "active" && (
                                        <Button size="sm" data-testid={`alloc-return-${a.allocation_id}`} onClick={() => onReturn(a.allocation_id)} className="h-8 bg-white/[0.04] border border-white/10 hover:bg-white/[0.08]">
                                            <Undo2 size={12} className="mr-1" /> Return
                                        </Button>
                                    )}
                                </td>
                            </tr>
                        );
                    })}
                    {list.length === 0 && (
                        <tr><td colSpan={6} className="text-center py-16 text-sm text-white/40">Nothing here.</td></tr>
                    )}
                </tbody>
            </table>
        </div>
    );
}
