import React from "react";

// Status → styles map. Uses inline styles for exact neon control.
const STATUS_MAP = {
    available:         { text: "#00FF94", bg: "rgba(0, 255, 148, 0.10)", border: "rgba(0, 255, 148, 0.25)", label: "Available" },
    allocated:         { text: "#00E5FF", bg: "rgba(0, 229, 255, 0.10)", border: "rgba(0, 229, 255, 0.25)", label: "Allocated" },
    reserved:          { text: "#E0FF00", bg: "rgba(224, 255, 0, 0.10)", border: "rgba(224, 255, 0, 0.25)", label: "Reserved" },
    under_maintenance: { text: "#FFB800", bg: "rgba(255, 184, 0, 0.10)", border: "rgba(255, 184, 0, 0.25)", label: "Maintenance" },
    lost:              { text: "#9CA3AF", bg: "rgba(156, 163, 175, 0.10)", border: "rgba(156, 163, 175, 0.25)", label: "Lost" },
    retired:           { text: "#71717A", bg: "rgba(113, 113, 122, 0.10)", border: "rgba(113, 113, 122, 0.25)", label: "Retired" },
    disposed:          { text: "#52525B", bg: "rgba(82, 82, 91, 0.10)", border: "rgba(82, 82, 91, 0.25)", label: "Disposed" },
    overdue:           { text: "#FF3366", bg: "rgba(255, 51, 102, 0.10)", border: "rgba(255, 51, 102, 0.25)", label: "Overdue" },
    // maintenance kanban / transfers / bookings
    pending:           { text: "#FFB800", bg: "rgba(255, 184, 0, 0.10)", border: "rgba(255, 184, 0, 0.25)", label: "Pending" },
    approved:          { text: "#00E5FF", bg: "rgba(0, 229, 255, 0.10)", border: "rgba(0, 229, 255, 0.25)", label: "Approved" },
    assigned:          { text: "#A78BFA", bg: "rgba(167, 139, 250, 0.10)", border: "rgba(167, 139, 250, 0.25)", label: "Assigned" },
    in_progress:       { text: "#00E5FF", bg: "rgba(0, 229, 255, 0.10)", border: "rgba(0, 229, 255, 0.25)", label: "In Progress" },
    resolved:          { text: "#00FF94", bg: "rgba(0, 255, 148, 0.10)", border: "rgba(0, 255, 148, 0.25)", label: "Resolved" },
    rejected:          { text: "#FF3366", bg: "rgba(255, 51, 102, 0.10)", border: "rgba(255, 51, 102, 0.25)", label: "Rejected" },
    requested:         { text: "#FFB800", bg: "rgba(255, 184, 0, 0.10)", border: "rgba(255, 184, 0, 0.25)", label: "Requested" },
    completed:         { text: "#00FF94", bg: "rgba(0, 255, 148, 0.10)", border: "rgba(0, 255, 148, 0.25)", label: "Completed" },
    cancelled:         { text: "#71717A", bg: "rgba(113, 113, 122, 0.10)", border: "rgba(113, 113, 122, 0.25)", label: "Cancelled" },
    upcoming:          { text: "#00E5FF", bg: "rgba(0, 229, 255, 0.10)", border: "rgba(0, 229, 255, 0.25)", label: "Upcoming" },
    ongoing:           { text: "#00FF94", bg: "rgba(0, 255, 148, 0.10)", border: "rgba(0, 255, 148, 0.25)", label: "Ongoing" },
    active:            { text: "#00FF94", bg: "rgba(0, 255, 148, 0.10)", border: "rgba(0, 255, 148, 0.25)", label: "Active" },
    returned:          { text: "#71717A", bg: "rgba(113, 113, 122, 0.10)", border: "rgba(113, 113, 122, 0.25)", label: "Returned" },
    transferred:       { text: "#A78BFA", bg: "rgba(167, 139, 250, 0.10)", border: "rgba(167, 139, 250, 0.25)", label: "Transferred" },
};

export default function StatusPill({ status, label, testId }) {
    const s = STATUS_MAP[status] || STATUS_MAP.pending;
    return (
        <span
            data-testid={testId || `status-pill-${status}`}
            className="inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[11px] font-medium tracking-wide"
            style={{
                color: s.text,
                background: s.bg,
                border: `1px solid ${s.border}`,
            }}
        >
            <span
                className="dot-glow"
                style={{ background: s.text, color: s.text }}
            />
            {label || s.label}
        </span>
    );
}
