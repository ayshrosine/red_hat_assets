import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Bell, CheckCheck, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

const KIND_LABEL = {
    asset: "Asset", user: "User", department: "Dept", category: "Category",
    booking: "Booking", maintenance: "Maintenance", transfer: "Transfer",
};

export default function Notifications() {
    const [notifs, setNotifs] = useState([]);
    const [activity, setActivity] = useState([]);

    const load = async () => {
        const [n, a] = await Promise.all([api.get("/notifications"), api.get("/activity", { params: { limit: 100 } })]);
        setNotifs(n.data); setActivity(a.data);
    };

    useEffect(() => { load(); }, []);

    const markAll = async () => {
        await api.post("/notifications/read-all");
        load();
    };

    return (
        <div className="space-y-8">
            <div className="flex items-end justify-between gap-4 flex-wrap">
                <div>
                    <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Notifications</p>
                    <h1 className="font-display text-4xl font-medium tracking-tighter">Inbox</h1>
                    <p className="mt-2 text-white/50 text-sm">Everything that happened, and what needs your attention.</p>
                </div>
                <Button onClick={markAll} variant="secondary" className="bg-white/[0.04] border border-white/10 hover:bg-white/[0.08]">
                    <CheckCheck size={14} className="mr-1.5" /> Mark all read
                </Button>
            </div>

            <Tabs defaultValue="notifications">
                <TabsList className="bg-white/[0.03] border border-white/10 p-1">
                    <TabsTrigger value="notifications" className="data-[state=active]:bg-white data-[state=active]:text-black">
                        <Bell size={13} className="mr-1.5" /> Notifications
                    </TabsTrigger>
                    <TabsTrigger value="activity" className="data-[state=active]:bg-white data-[state=active]:text-black">
                        <Filter size={13} className="mr-1.5" /> Activity log
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="notifications" className="mt-6">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
                        {notifs.length === 0 && (
                            <div className="p-12 text-center">
                                <Bell size={24} className="mx-auto text-white/20 mb-3" />
                                <p className="text-sm text-white/40">You&apos;re all caught up.</p>
                            </div>
                        )}
                        <ul className="divide-y divide-white/5">
                            {notifs.map((n) => (
                                <li key={n.notif_id} className={"p-4 flex items-start gap-3 " + (n.read ? "opacity-60" : "")}>
                                    <span className="w-2 h-2 rounded-full mt-1.5" style={{ background: n.read ? "#3f3f46" : "#00FF94", boxShadow: n.read ? "none" : "0 0 8px #00FF94" }} />
                                    <div className="flex-1">
                                        <p className="text-sm text-white">{n.title}</p>
                                        {n.body && <p className="text-xs text-white/50 mt-0.5">{n.body}</p>}
                                        <p className="text-[11px] text-white/30 mt-1 tabular-nums">{new Date(n.created_at).toLocaleString()}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </TabsContent>

                <TabsContent value="activity" className="mt-6">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e]">
                        {activity.length === 0 && <div className="p-12 text-center text-sm text-white/40">No activity.</div>}
                        <ul className="divide-y divide-white/5">
                            {activity.map((a) => (
                                <li key={a.activity_id} className="p-4 flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-[10px]">
                                        {(a.actor_name || "?").split(" ").map((s) => s[0]).slice(0, 2).join("")}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-white">
                                            <span className="font-medium">{a.actor_name}</span> <span className="text-white/50">{a.action.replace(/_/g, " ")}</span> {a.target_name}
                                        </p>
                                        <p className="text-[11px] text-white/40 tabular-nums">
                                            {KIND_LABEL[a.kind] || a.kind} · {new Date(a.created_at).toLocaleString()}
                                        </p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
