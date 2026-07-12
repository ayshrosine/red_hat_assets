import React from "react";
import { ClipboardCheck, Sparkles } from "lucide-react";

export default function Audit() {
    return (
        <div className="space-y-8">
            <div>
                <p className="text-[10px] uppercase tracking-[0.24em] text-white/40 mb-2">Audit</p>
                <h1 className="font-display text-4xl font-medium tracking-tighter">Asset audit</h1>
                <p className="mt-2 text-white/50 text-sm">Scheduled discovery of what&apos;s really where.</p>
            </div>

            <div className="rounded-xl border border-white/10 bg-[#0e0e0e] p-12 text-center relative overflow-hidden">
                <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse at top, rgba(0, 255, 148, 0.06), transparent 60%)" }} />
                <div className="relative">
                    <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 mx-auto mb-4 flex items-center justify-center">
                        <ClipboardCheck size={22} className="text-white/60" />
                    </div>
                    <h2 className="font-display text-2xl font-medium mb-2">Audit cycles arrive next.</h2>
                    <p className="text-sm text-white/50 max-w-md mx-auto">
                        Create cycles, assign auditors, run verified/missing/damaged checklists, and auto-generate discrepancy reports. Coming in Phase 6.
                    </p>
                    <div className="mt-6 inline-flex items-center gap-2 text-xs text-white/60 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5">
                        <Sparkles size={12} className="text-[#00FF94]" />
                        Reach out to prioritize this in your workspace
                    </div>
                </div>
            </div>
        </div>
    );
}
