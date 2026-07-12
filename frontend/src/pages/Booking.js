import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, formatApiError, extractDetail } from "@/lib/api";
import { BOOK } from "@/constants/testIds";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import StatusPill from "@/components/StatusPill";
import { XCircle, CalendarDays } from "lucide-react";

function fmtDT(dt) {
    const d = new Date(dt);
    return d.toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function localInputValue(dt) {
    // returns yyyy-MM-ddTHH:mm for datetime-local
    const d = new Date(dt);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function Booking() {
    const [params] = useSearchParams();
    const [assets, setAssets] = useState([]);
    const [selected, setSelected] = useState(params.get("asset") || "");
    const [bookings, setBookings] = useState([]);
    const [form, setForm] = useState(() => {
        const start = new Date();
        start.setMinutes(0, 0, 0); start.setHours(start.getHours() + 1);
        const end = new Date(start); end.setHours(end.getHours() + 1);
        return { start: localInputValue(start), end: localInputValue(end), purpose: "" };
    });
    const [conflict, setConflict] = useState(null);

    useEffect(() => {
        (async () => {
            const { data } = await api.get("/assets", { params: { bookable: true } });
            setAssets(data);
            if (!selected && data.length) setSelected(data[0].asset_id);
        })();
    // one-shot mount load; `selected` is only used to skip auto-select
    }, []);

    useEffect(() => {
        if (!selected) return;
        (async () => {
            const { data } = await api.get("/bookings", { params: { asset_id: selected } });
            setBookings(data);
        })();
    }, [selected]);

    const submit = async () => {
        setConflict(null);
        try {
            await api.post("/bookings", {
                asset_id: selected,
                start_at: new Date(form.start).toISOString(),
                end_at: new Date(form.end).toISOString(),
                purpose: form.purpose,
            });
            toast.success("Booking confirmed");
            const { data } = await api.get("/bookings", { params: { asset_id: selected } });
            setBookings(data);
        } catch (e) {
            const detail = extractDetail(e);
            if (e?.response?.status === 409 && detail?.conflict) {
                setConflict(detail.conflict);
                toast.error("Time slot conflicts with existing booking");
            } else {
                toast.error(formatApiError(e));
            }
        }
    };

    const cancel = async (id) => {
        try {
            await api.post(`/bookings/${id}/cancel`);
            const { data } = await api.get("/bookings", { params: { asset_id: selected } });
            setBookings(data);
            toast.success("Booking cancelled");
        } catch (e) { toast.error(formatApiError(e)); }
    };

    const upcoming = useMemo(() => bookings.filter((b) => b.status !== "cancelled").sort((a, b) => new Date(a.start_at) - new Date(b.start_at)), [bookings]);
    const selectedAsset = assets.find((a) => a.asset_id === selected);

    // Simple timeline: next 7 days
    const timeline = useMemo(() => {
        const days = [];
        for (let i = 0; i < 7; i++) {
            const d = new Date(); d.setHours(0, 0, 0, 0); d.setDate(d.getDate() + i);
            const dayBookings = upcoming.filter((b) => {
                const s = new Date(b.start_at); return s.getFullYear() === d.getFullYear() && s.getMonth() === d.getMonth() && s.getDate() === d.getDate();
            });
            days.push({ date: d, bookings: dayBookings });
        }
        return days;
    }, [upcoming]);

    return (
        <div className="space-y-8">
            <div>
                <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Booking</p>
                <h1 className="font-display text-4xl font-medium tracking-tighter">Resource booking</h1>
                <p className="mt-2 text-white/50 text-sm">Reserve rooms, projectors and vehicles by time-slot.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Resource selector + timeline */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5">
                        <Label className="text-xs text-white/60">Resource</Label>
                        <Select value={selected} onValueChange={setSelected}>
                            <SelectTrigger data-testid={BOOK.selectResource} className="mt-1.5 bg-white/[0.03] border-white/10">
                                <SelectValue placeholder="Choose bookable asset" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#0e0e0e] border-white/10">
                                {assets.map((a) => <SelectItem key={a.asset_id} value={a.asset_id}>{a.tag} · {a.name}</SelectItem>)}
                            </SelectContent>
                        </Select>
                        {selectedAsset && (
                            <div className="mt-4 flex items-center gap-3 text-sm text-white/60">
                                <CalendarDays size={14} />
                                <span>{selectedAsset.location || "No location set"}</span>
                            </div>
                        )}
                    </div>

                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5">
                        <h3 className="font-display text-lg font-medium mb-4">Next 7 days</h3>
                        <div className="space-y-2">
                            {timeline.map((day) => (
                                <div key={day.date.toISOString()} className="flex gap-4 py-2 border-b border-white/5 last:border-b-0">
                                    <div className="w-24 flex-shrink-0">
                                        <p className="text-[10px] uppercase tracking-[0.18em] text-white/40">
                                            {day.date.toLocaleDateString(undefined, { weekday: "short" })}
                                        </p>
                                        <p className="font-display text-xl tabular-nums">{day.date.getDate()}</p>
                                    </div>
                                    <div className="flex-1 space-y-1.5">
                                        {day.bookings.length === 0 && (
                                            <p className="text-xs text-white/30 italic pt-2">Nothing booked</p>
                                        )}
                                        {day.bookings.map((b) => (
                                            <div key={b.booking_id} className="rounded-lg px-3 py-2 flex items-center justify-between" style={{ background: "rgba(0, 229, 255, 0.06)", border: "1px solid rgba(0, 229, 255, 0.2)" }}>
                                                <div>
                                                    <p className="text-sm">{b.purpose || "Booking"}</p>
                                                    <p className="text-[11px] text-white/50 tabular-nums">
                                                        {new Date(b.start_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} —{" "}
                                                        {new Date(b.end_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} · {b.user_name}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <StatusPill status={b.status} />
                                                    <button data-testid={BOOK.cancelButton + "-" + b.booking_id} onClick={() => cancel(b.booking_id)} className="p-1 text-white/40 hover:text-[#FF3366]"><XCircle size={14} /></button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Booking form */}
                <div className="space-y-4">
                    <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-5 space-y-4">
                        <h3 className="font-display text-lg font-medium">New booking</h3>
                        <div className="space-y-1.5">
                            <Label className="text-xs text-white/60">Start</Label>
                            <Input data-testid={BOOK.startInput} type="datetime-local" value={form.start} onChange={(e) => setForm((f) => ({ ...f, start: e.target.value }))} />
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs text-white/60">End</Label>
                            <Input data-testid={BOOK.endInput} type="datetime-local" value={form.end} onChange={(e) => setForm((f) => ({ ...f, end: e.target.value }))} />
                        </div>
                        <div className="space-y-1.5">
                            <Label className="text-xs text-white/60">Purpose</Label>
                            <Textarea data-testid={BOOK.purposeInput} rows={2} value={form.purpose} onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))} placeholder="Team retrospective" />
                        </div>

                        {conflict && (
                            <div className="rounded-lg p-3 text-sm" style={{ background: "rgba(255,184,0,0.08)", border: "1px solid rgba(255,184,0,0.25)" }} data-testid="booking-conflict">
                                <p className="text-white">Slot overlaps existing booking</p>
                                <p className="text-xs text-white/60 mt-1 tabular-nums">
                                    {fmtDT(conflict.start)} — {fmtDT(conflict.end)}
                                    {conflict.user && <> · by {conflict.user}</>}
                                </p>
                            </div>
                        )}

                        <Button data-testid={BOOK.submit} onClick={submit} disabled={!selected} className="w-full bg-white text-black hover:bg-white/90">
                            Confirm booking
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
