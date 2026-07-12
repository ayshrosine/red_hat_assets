import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, formatApiError } from "@/lib/api";
import StatusPill from "@/components/StatusPill";
import { ASSETS } from "@/constants/testIds";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { useAuth, hasRole } from "@/context/AuthContext";
import { Plus, Search, ChevronRight } from "lucide-react";

const STATUS_OPTIONS = ["available", "allocated", "reserved", "under_maintenance", "lost", "retired", "disposed"];

export default function Assets() {
    const { user } = useAuth();
    const nav = useNavigate();
    const [params] = useSearchParams();

    const [assets, setAssets] = useState([]);
    const [cats, setCats] = useState([]);
    const [depts, setDepts] = useState([]);
    const [q, setQ] = useState(params.get("q") || "");
    const [fCat, setFCat] = useState("");
    const [fStatus, setFStatus] = useState("");
    const [fDept, setFDept] = useState("");

    const [open, setOpen] = useState(params.get("new") === "1");
    const canManage = hasRole(user, "admin", "asset_manager");

    const load = async () => {
        const query = {};
        if (q) query.q = q;
        if (fCat) query.category_id = fCat;
        if (fStatus) query.status = fStatus;
        if (fDept) query.department_id = fDept;
        const { data } = await api.get("/assets", { params: query });
        setAssets(data);
    };

    useEffect(() => {
        (async () => {
            const [c, d] = await Promise.all([api.get("/categories"), api.get("/departments")]);
            setCats(c.data); setDepts(d.data);
        })();
    }, []);

    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(() => { load(); }, [q, fCat, fStatus, fDept]);

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Assets</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Registry</h1>
                    <p className="mt-2 text-white/50 text-sm">Every asset, tagged and tracked.</p>
                </div>
                {canManage && (
                    <Button data-testid={ASSETS.registerButton} onClick={() => setOpen(true)} className="bg-white text-black hover:bg-white/90 h-10">
                        <Plus size={14} className="mr-1.5" /> Register asset
                    </Button>
                )}
            </div>

            <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
                <div className="p-4 border-b border-white/5 grid grid-cols-1 md:grid-cols-4 gap-3">
                    <div className="relative md:col-span-2">
                        <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                        <Input data-testid={ASSETS.searchInput} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search by tag, name, serial…" className="pl-9 bg-white/[0.03] border-white/10" />
                    </div>
                    <Select value={fCat || "all"} onValueChange={(v) => setFCat(v === "all" ? "" : v)}>
                        <SelectTrigger data-testid={ASSETS.filterCategory} className="bg-white/[0.03] border-white/10"><SelectValue placeholder="All categories" /></SelectTrigger>
                        <SelectContent className="bg-[#0e0e0e] border-white/10">
                            <SelectItem value="all">All categories</SelectItem>
                            {cats.map((c) => <SelectItem key={c.category_id} value={c.category_id}>{c.name}</SelectItem>)}
                        </SelectContent>
                    </Select>
                    <Select value={fStatus || "all"} onValueChange={(v) => setFStatus(v === "all" ? "" : v)}>
                        <SelectTrigger data-testid={ASSETS.filterStatus} className="bg-white/[0.03] border-white/10"><SelectValue placeholder="All statuses" /></SelectTrigger>
                        <SelectContent className="bg-[#0e0e0e] border-white/10">
                            <SelectItem value="all">All statuses</SelectItem>
                            {STATUS_OPTIONS.map((s) => <SelectItem key={s} value={s}>{s.replace(/_/g, " ")}</SelectItem>)}
                        </SelectContent>
                    </Select>
                </div>

                <div className="overflow-x-auto" data-testid={ASSETS.listTable}>
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="text-[10px] uppercase tracking-[0.16em] text-white/40 border-b border-white/5">
                                <th className="text-left px-5 py-3 font-normal">Tag</th>
                                <th className="text-left px-5 py-3 font-normal">Name</th>
                                <th className="text-left px-5 py-3 font-normal">Category</th>
                                <th className="text-left px-5 py-3 font-normal">Location</th>
                                <th className="text-left px-5 py-3 font-normal">Status</th>
                                <th className="w-8"></th>
                            </tr>
                        </thead>
                        <tbody>
                            {assets.map((a) => {
                                const cat = cats.find((c) => c.category_id === a.category_id);
                                return (
                                    <tr
                                        key={a.asset_id}
                                        className="border-b border-white/5 hover:bg-white/[0.02] cursor-pointer transition-colors"
                                        onClick={() => nav(`/assets/${a.asset_id}`)}
                                        data-testid={`asset-row-${a.tag}`}
                                    >
                                        <td className="px-5 py-3.5 font-mono-af text-xs text-white/70">{a.tag}</td>
                                        <td className="px-5 py-3.5 text-white">{a.name}</td>
                                        <td className="px-5 py-3.5 text-white/60">{cat?.name || "—"}</td>
                                        <td className="px-5 py-3.5 text-white/60">{a.location || "—"}</td>
                                        <td className="px-5 py-3.5"><StatusPill status={a.status} /></td>
                                        <td className="px-5 py-3.5 text-white/40"><ChevronRight size={14} /></td>
                                    </tr>
                                );
                            })}
                            {assets.length === 0 && (
                                <tr><td colSpan={6} className="text-center py-16 text-sm text-white/40">No assets match your filters.</td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            <RegisterDialog open={open} onOpenChange={setOpen} cats={cats} depts={depts} onCreated={load} />
        </div>
    );
}

function RegisterDialog({ open, onOpenChange, cats, depts, onCreated }) {
    const [form, setForm] = useState({
        name: "", tag: "", serial: "", category_id: "", department_id: "",
        location: "", condition: "good", acquisition_cost: 0, acquisition_date: "",
        bookable: false, photo_url: "", notes: "",
    });
    const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

    const submit = async () => {
        try {
            await api.post("/assets", {
                ...form,
                category_id: form.category_id,
                department_id: form.department_id || null,
                acquisition_cost: Number(form.acquisition_cost) || 0,
                acquisition_date: form.acquisition_date || null,
                custom_data: {},
            });
            toast.success("Asset registered");
            onOpenChange(false);
            setForm({ name: "", tag: "", serial: "", category_id: "", department_id: "", location: "", condition: "good", acquisition_cost: 0, acquisition_date: "", bookable: false, photo_url: "", notes: "" });
            onCreated();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="bg-[#0e0e0e] border-white/10 max-w-lg">
                <DialogHeader>
                    <DialogTitle>Register asset</DialogTitle>
                    <DialogDescription className="text-white/50">Give it a tag, category, and where it lives.</DialogDescription>
                </DialogHeader>
                <div className="space-y-3">
                    <Field label="Name">
                        <Input data-testid={ASSETS.createName} value={form.name} onChange={(e) => set("name", e.target.value)} placeholder="MacBook Pro 16" />
                    </Field>
                    <div className="grid grid-cols-2 gap-3">
                        <Field label="Tag">
                            <Input data-testid={ASSETS.createTag} value={form.tag} onChange={(e) => set("tag", e.target.value)} placeholder="AF-LP-042" />
                        </Field>
                        <Field label="Serial">
                            <Input data-testid={ASSETS.createSerial} value={form.serial} onChange={(e) => set("serial", e.target.value)} />
                        </Field>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                        <Field label="Category">
                            <Select value={form.category_id} onValueChange={(v) => set("category_id", v)}>
                                <SelectTrigger data-testid={ASSETS.createCategory} className="bg-white/[0.03] border-white/10"><SelectValue placeholder="Select…" /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    {cats.map((c) => <SelectItem key={c.category_id} value={c.category_id}>{c.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </Field>
                        <Field label="Department">
                            <Select value={form.department_id || "none"} onValueChange={(v) => set("department_id", v === "none" ? "" : v)}>
                                <SelectTrigger data-testid={ASSETS.createDepartment} className="bg-white/[0.03] border-white/10"><SelectValue /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    <SelectItem value="none">None</SelectItem>
                                    {depts.map((d) => <SelectItem key={d.department_id} value={d.department_id}>{d.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </Field>
                    </div>
                    <Field label="Location">
                        <Input data-testid={ASSETS.createLocation} value={form.location} onChange={(e) => set("location", e.target.value)} placeholder="HQ / Floor 3" />
                    </Field>
                    <div className="grid grid-cols-2 gap-3">
                        <Field label="Condition">
                            <Select value={form.condition} onValueChange={(v) => set("condition", v)}>
                                <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    <SelectItem value="new">New</SelectItem>
                                    <SelectItem value="good">Good</SelectItem>
                                    <SelectItem value="fair">Fair</SelectItem>
                                    <SelectItem value="poor">Poor</SelectItem>
                                </SelectContent>
                            </Select>
                        </Field>
                        <Field label="Acquisition cost">
                            <Input type="number" value={form.acquisition_cost} onChange={(e) => set("acquisition_cost", e.target.value)} />
                        </Field>
                    </div>
                    <Field label="Photo URL (optional)">
                        <Input value={form.photo_url} onChange={(e) => set("photo_url", e.target.value)} placeholder="https://…" />
                    </Field>
                    <Field label="Notes">
                        <Textarea value={form.notes} onChange={(e) => set("notes", e.target.value)} rows={2} />
                    </Field>
                    <div className="flex items-center justify-between rounded-lg border border-white/10 bg-white/[0.02] px-4 py-3">
                        <div>
                            <p className="text-sm text-white">Bookable resource</p>
                            <p className="text-xs text-white/40">Enable time-slot booking (rooms, projectors, vehicles).</p>
                        </div>
                        <Switch data-testid={ASSETS.createBookable} checked={form.bookable} onCheckedChange={(v) => set("bookable", v)} />
                    </div>
                </div>
                <DialogFooter>
                    <Button data-testid={ASSETS.createSubmit} onClick={submit} disabled={!form.name || !form.tag || !form.category_id} className="bg-white text-black hover:bg-white/90">
                        Register
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

function Field({ label, children }) {
    return (
        <div className="space-y-1.5">
            <Label className="text-xs text-white/60">{label}</Label>
            {children}
        </div>
    );
}
