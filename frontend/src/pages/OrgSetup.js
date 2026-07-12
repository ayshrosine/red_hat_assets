import React, { useEffect, useState } from "react";
import { api, formatApiError } from "@/lib/api";
import { ORG } from "@/constants/testIds";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Trash2, Building2, Tags, Users, Shield, ChevronRight } from "lucide-react";
import { roleLabel } from "@/context/AuthContext";

export default function OrgSetup() {
    const [tab, setTab] = useState("departments");

    return (
        <div className="space-y-8">
            <div>
                <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Organization</p>
                <h1 className="font-display text-4xl font-medium tracking-tighter">Organization setup</h1>
                <p className="mt-2 text-white/50 text-sm">Departments, categories and team roles.</p>
            </div>

            <Tabs value={tab} onValueChange={setTab} className="w-full">
                <TabsList className="bg-white/[0.03] border border-white/10 p-1">
                    <TabsTrigger data-testid={ORG.tabDepartments} value="departments" className="data-[state=active]:bg-white data-[state=active]:text-black">
                        <Building2 size={13} className="mr-1.5" /> Departments
                    </TabsTrigger>
                    <TabsTrigger data-testid={ORG.tabCategories} value="categories" className="data-[state=active]:bg-white data-[state=active]:text-black">
                        <Tags size={13} className="mr-1.5" /> Categories
                    </TabsTrigger>
                    <TabsTrigger data-testid={ORG.tabEmployees} value="employees" className="data-[state=active]:bg-white data-[state=active]:text-black">
                        <Users size={13} className="mr-1.5" /> Employees
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="departments" className="mt-6"><Departments /></TabsContent>
                <TabsContent value="categories" className="mt-6"><Categories /></TabsContent>
                <TabsContent value="employees" className="mt-6"><Employees /></TabsContent>
            </Tabs>
        </div>
    );
}

function Departments() {
    const [list, setList] = useState([]);
    const [users, setUsers] = useState([]);
    const [open, setOpen] = useState(false);
    const [name, setName] = useState("");
    const [headId, setHeadId] = useState("");

    const load = async () => {
        const [d, u] = await Promise.all([api.get("/departments"), api.get("/users")]);
        setList(d.data); setUsers(u.data);
    };
    useEffect(() => { load(); }, []);

    const save = async () => {
        try {
            await api.post("/departments", { name, head_user_id: headId || null, active: true });
            toast.success("Department created");
            setOpen(false); setName(""); setHeadId("");
            load();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const remove = async (id) => {
        if (!window.confirm("Delete this department?")) return;
        await api.delete(`/departments/${id}`);
        load();
    };

    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
            <div className="p-5 flex items-center justify-between border-b border-white/5">
                <div>
                    <h3 className="font-display text-lg font-medium">Departments</h3>
                    <p className="text-xs text-white/50 mt-0.5">{list.length} in organization</p>
                </div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button data-testid={ORG.addDeptButton} className="bg-white text-black hover:bg-white/90 h-9">
                            <Plus size={14} className="mr-1.5" /> Add department
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-[#0e0e0e] border-white/10">
                        <DialogHeader>
                            <DialogTitle>New department</DialogTitle>
                            <DialogDescription className="text-white/50">Group your assets and people.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-2">
                            <div className="space-y-1.5">
                                <Label className="text-xs">Name</Label>
                                <Input data-testid={ORG.deptNameInput} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Engineering" />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">Head</Label>
                                <Select value={headId || "none"} onValueChange={(v) => setHeadId(v === "none" ? "" : v)}>
                                    <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue placeholder="Assign later" /></SelectTrigger>
                                    <SelectContent className="bg-[#0e0e0e] border-white/10">
                                        <SelectItem value="none">Assign later</SelectItem>
                                        {users.map((u) => (
                                            <SelectItem key={u.user_id} value={u.user_id}>{u.name} · {roleLabel(u.role)}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button data-testid={ORG.deptSaveButton} onClick={save} disabled={!name.trim()} className="bg-white text-black hover:bg-white/90">Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
            <div className="divide-y divide-white/5">
                {list.map((d) => {
                    const head = users.find((u) => u.user_id === d.head_user_id);
                    return (
                        <div key={d.department_id} className="p-4 flex items-center justify-between hover:bg-white/[0.02]">
                            <div className="flex items-center gap-4">
                                <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center"><Building2 size={16} strokeWidth={1.5} /></div>
                                <div>
                                    <p className="text-sm text-white">{d.name}</p>
                                    <p className="text-xs text-white/40">{head ? `Head: ${head.name}` : "No head assigned"}</p>
                                </div>
                            </div>
                            <button onClick={() => remove(d.department_id)} className="text-white/40 hover:text-[#FF3366] p-2"><Trash2 size={14} /></button>
                        </div>
                    );
                })}
                {list.length === 0 && <div className="p-8 text-center text-sm text-white/40">No departments yet.</div>}
            </div>
        </div>
    );
}

function Categories() {
    const [list, setList] = useState([]);
    const [open, setOpen] = useState(false);
    const [name, setName] = useState("");
    const [fields, setFields] = useState("");

    const load = async () => { const d = await api.get("/categories"); setList(d.data); };
    useEffect(() => { load(); }, []);

    const save = async () => {
        try {
            const custom_fields = fields.split(",").map((s) => s.trim()).filter(Boolean);
            await api.post("/categories", { name, custom_fields });
            toast.success("Category created");
            setOpen(false); setName(""); setFields("");
            load();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const remove = async (id) => {
        if (!window.confirm("Delete this category?")) return;
        await api.delete(`/categories/${id}`);
        load();
    };

    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
            <div className="p-5 flex items-center justify-between border-b border-white/5">
                <div>
                    <h3 className="font-display text-lg font-medium">Categories</h3>
                    <p className="text-xs text-white/50 mt-0.5">{list.length} defined</p>
                </div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button data-testid={ORG.addCatButton} className="bg-white text-black hover:bg-white/90 h-9">
                            <Plus size={14} className="mr-1.5" /> Add category
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-[#0e0e0e] border-white/10">
                        <DialogHeader>
                            <DialogTitle>New category</DialogTitle>
                            <DialogDescription className="text-white/50">Categories drive the asset form.</DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div className="space-y-1.5">
                                <Label className="text-xs">Name</Label>
                                <Input data-testid={ORG.catNameInput} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Laptops" />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs">Custom fields (comma separated)</Label>
                                <Input value={fields} onChange={(e) => setFields(e.target.value)} placeholder="cpu, ram, storage" />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button data-testid={ORG.catSaveButton} onClick={save} disabled={!name.trim()} className="bg-white text-black hover:bg-white/90">Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-5">
                {list.map((c) => (
                    <div key={c.category_id} className="rounded-lg border border-white/10 bg-white/[0.02] p-4 hover:border-white/20 transition-colors">
                        <div className="flex items-start justify-between">
                            <div>
                                <p className="text-white font-medium text-sm">{c.name}</p>
                                <p className="text-xs text-white/40 mt-1 truncate">{(c.custom_fields || []).join(" · ") || "No custom fields"}</p>
                            </div>
                            <button onClick={() => remove(c.category_id)} className="text-white/40 hover:text-[#FF3366] p-1"><Trash2 size={14} /></button>
                        </div>
                    </div>
                ))}
                {list.length === 0 && <div className="col-span-full p-8 text-center text-sm text-white/40">No categories yet.</div>}
            </div>
        </div>
    );
}

function Employees() {
    const [list, setList] = useState([]);
    const [depts, setDepts] = useState([]);
    const [dialog, setDialog] = useState(null); // user id
    const [newRole, setNewRole] = useState("employee");
    const [newDept, setNewDept] = useState("");

    const load = async () => {
        const [u, d] = await Promise.all([api.get("/users"), api.get("/departments")]);
        setList(u.data); setDepts(d.data);
    };
    useEffect(() => { load(); }, []);

    const promote = async () => {
        try {
            await api.post("/users/promote", { user_id: dialog, role: newRole, department_id: newDept || null });
            toast.success("Role updated");
            setDialog(null);
            load();
        } catch (e) { toast.error(formatApiError(e)); }
    };

    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
            <div className="p-5 border-b border-white/5">
                <h3 className="font-display text-lg font-medium">Employees</h3>
                <p className="text-xs text-white/50 mt-0.5">{list.length} accounts · promote roles here</p>
            </div>
            <div className="divide-y divide-white/5">
                {list.map((u) => {
                    const dept = depts.find((d) => d.department_id === u.department_id);
                    return (
                        <div key={u.user_id} className="p-4 flex items-center justify-between hover:bg-white/[0.02]">
                            <div className="flex items-center gap-4">
                                <div className="w-9 h-9 rounded-full bg-white/5 flex items-center justify-center text-xs">
                                    {u.name.split(" ").map((s) => s[0]).slice(0, 2).join("")}
                                </div>
                                <div>
                                    <p className="text-sm text-white">{u.name}</p>
                                    <p className="text-xs text-white/40">{u.email}{dept ? ` · ${dept.name}` : ""}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-white/70 bg-white/5 border border-white/10 px-2.5 py-1 rounded-full">
                                    {roleLabel(u.role)}
                                </span>
                                <Button data-testid={ORG.promoteButton} variant="secondary" className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08] h-8" onClick={() => { setDialog(u.user_id); setNewRole(u.role); setNewDept(u.department_id || ""); }}>
                                    <Shield size={13} className="mr-1.5" /> Change role
                                </Button>
                            </div>
                        </div>
                    );
                })}
            </div>
            <Dialog open={!!dialog} onOpenChange={(o) => !o && setDialog(null)}>
                <DialogContent className="bg-[#0e0e0e] border-white/10">
                    <DialogHeader>
                        <DialogTitle>Change role</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                        <div className="space-y-1.5">
                            <Label className="text-xs">Role</Label>
                            <Select value={newRole} onValueChange={setNewRole}>
                                <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    <SelectItem value="admin">Admin</SelectItem>
                                    <SelectItem value="asset_manager">Asset Manager</SelectItem>
                                    <SelectItem value="department_head">Department Head</SelectItem>
                                    <SelectItem value="employee">Employee</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs">Department</Label>
                            <Select value={newDept || "none"} onValueChange={(v) => setNewDept(v === "none" ? "" : v)}>
                                <SelectTrigger className="bg-white/[0.03] border-white/10"><SelectValue /></SelectTrigger>
                                <SelectContent className="bg-[#0e0e0e] border-white/10">
                                    <SelectItem value="none">None</SelectItem>
                                    {depts.map((d) => <SelectItem key={d.department_id} value={d.department_id}>{d.name}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                    <DialogFooter>
                        <Button onClick={promote} className="bg-white text-black hover:bg-white/90">Save</Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
