import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import StatusPill from "@/components/StatusPill";
import { ArrowLeft, MapPin, Tag as TagIcon, Package, ExternalLink } from "lucide-react";

export default function AssetDetail() {
    const { assetId } = useParams();
    const nav = useNavigate();
    const [data, setData] = useState(null);

    useEffect(() => {
        (async () => {
            try {
                const { data } = await api.get(`/assets/${assetId}`);
                setData(data);
            } catch { nav("/assets"); }
        })();
    }, [assetId, nav]);

    if (!data) return <div className="text-white/40 text-sm">Loading…</div>;
    const { asset, allocations, maintenance } = data;

    return (
        <div className="space-y-6">
            <button onClick={() => nav("/assets")} className="text-xs text-white/50 hover:text-white flex items-center gap-1">
                <ArrowLeft size={12} /> Back to registry
            </button>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-6">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-6">
                        <div className="flex items-start gap-6">
                            {asset.photo_url ? (
                                <img src={asset.photo_url} alt={asset.name} className="w-32 h-32 object-cover rounded-lg border border-white/10" />
                            ) : (
                                <div className="w-32 h-32 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                                    <Package size={32} className="text-white/30" />
                                </div>
                            )}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-3 text-xs text-white/50 mb-2">
                                    <TagIcon size={12} />
                                    <span className="font-mono-af">{asset.tag}</span>
                                    {asset.serial && (<><span>·</span><span className="font-mono-af">{asset.serial}</span></>)}
                                </div>
                                <h1 className="font-display text-3xl font-medium tracking-tighter mb-3">{asset.name}</h1>
                                <div className="flex items-center gap-2 flex-wrap">
                                    <StatusPill status={asset.status} />
                                    {asset.bookable && <span className="text-[11px] px-2 py-0.5 rounded-full border border-white/10 text-white/70">Bookable</span>}
                                    {asset.location && (
                                        <span className="text-[11px] text-white/50 inline-flex items-center gap-1"><MapPin size={11} /> {asset.location}</span>
                                    )}
                                </div>
                                {asset.notes && <p className="mt-4 text-sm text-white/60">{asset.notes}</p>}
                            </div>
                        </div>
                    </div>

                    <Section title="Allocation history">
                        {allocations.length === 0 && <Empty label="No allocations yet." />}
                        {allocations.map((a) => (
                            <div key={a.allocation_id} className="flex items-center justify-between py-3 border-b border-white/5 last:border-b-0">
                                <div>
                                    <p className="text-sm">{a.assignee_name}</p>
                                    <p className="text-[11px] text-white/40 tabular-nums">
                                        Allocated {new Date(a.created_at).toLocaleDateString()}
                                        {a.returned_at ? ` · Returned ${new Date(a.returned_at).toLocaleDateString()}` : ""}
                                    </p>
                                </div>
                                <StatusPill status={a.state} />
                            </div>
                        ))}
                    </Section>

                    <Section title="Maintenance history">
                        {maintenance.length === 0 && <Empty label="No maintenance requests." />}
                        {maintenance.map((m) => (
                            <div key={m.request_id} className="py-3 border-b border-white/5 last:border-b-0">
                                <div className="flex items-center justify-between">
                                    <p className="text-sm">{m.issue}</p>
                                    <StatusPill status={m.status} />
                                </div>
                                <p className="text-[11px] text-white/40 mt-1">
                                    Raised by {m.raised_by_name} · {new Date(m.created_at).toLocaleDateString()} · Priority {m.priority}
                                </p>
                            </div>
                        ))}
                    </Section>
                </div>

                <div className="space-y-4">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5 space-y-3">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-white/40">Metadata</p>
                        <Row k="Condition" v={asset.condition} />
                        <Row k="Cost" v={asset.acquisition_cost ? `$${Number(asset.acquisition_cost).toLocaleString()}` : "—"} />
                        <Row k="Acquired" v={asset.acquisition_date || "—"} />
                        <Row k="Department" v={asset.department_id || "—"} />
                        {Object.entries(asset.custom_data || {}).map(([k, v]) => (
                            <Row key={k} k={k} v={String(v)} />
                        ))}
                    </div>

                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-white/40 mb-2">Actions</p>
                        <div className="space-y-2">
                            <button onClick={() => nav("/allocation?asset=" + asset.asset_id)} className="w-full text-left text-sm rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 hover:bg-white/[0.05] flex items-center justify-between">
                                Allocate <ExternalLink size={12} className="text-white/40" />
                            </button>
                            {asset.bookable && (
                                <button onClick={() => nav("/booking?asset=" + asset.asset_id)} className="w-full text-left text-sm rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 hover:bg-white/[0.05] flex items-center justify-between">
                                    Book time slot <ExternalLink size={12} className="text-white/40" />
                                </button>
                            )}
                            <button onClick={() => nav("/maintenance?asset=" + asset.asset_id + "&raise=1")} className="w-full text-left text-sm rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2 hover:bg-white/[0.05] flex items-center justify-between">
                                Raise maintenance <ExternalLink size={12} className="text-white/40" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function Section({ title, children }) {
    return (
        <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5">
            <h3 className="font-display text-lg font-medium mb-3">{title}</h3>
            <div>{children}</div>
        </div>
    );
}

function Row({ k, v }) {
    return (
        <div className="flex items-center justify-between text-sm">
            <span className="text-white/40 capitalize">{k}</span>
            <span className="text-white/80">{v}</span>
        </div>
    );
}

function Empty({ label }) {
    return <p className="text-sm text-white/40 py-4 text-center">{label}</p>;
}
