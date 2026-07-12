import React from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
    LayoutDashboard, Building2, Boxes, ArrowLeftRight, CalendarDays,
    Wrench, ClipboardCheck, BarChart3, Bell, LogOut, Search, ChevronDown, User,
} from "lucide-react";
import { useAuth, roleLabel, hasRole } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import {
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
    DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";

const NAV = [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: null, testId: "nav-dashboard" },
    { to: "/organization", label: "Organization", icon: Building2, roles: ["admin"], testId: "nav-organization" },
    { to: "/assets", label: "Assets", icon: Boxes, roles: null, testId: "nav-assets" },
    { to: "/allocation", label: "Allocation & Transfer", icon: ArrowLeftRight, roles: null, testId: "nav-allocation" },
    { to: "/booking", label: "Resource Booking", icon: CalendarDays, roles: null, testId: "nav-booking" },
    { to: "/maintenance", label: "Maintenance", icon: Wrench, roles: null, testId: "nav-maintenance" },
    { to: "/audit", label: "Asset Audit", icon: ClipboardCheck, roles: ["admin", "asset_manager"], testId: "nav-audit" },
    { to: "/reports", label: "Reports", icon: BarChart3, roles: ["admin", "asset_manager"], testId: "nav-reports" },
    { to: "/notifications", label: "Notifications", icon: Bell, roles: null, testId: "nav-notifications" },
];

export default function Layout({ children }) {
    const { user, logout } = useAuth();
    const nav = useNavigate();
    const loc = useLocation();

    const initials = (user?.name || user?.email || "?")
        .split(" ")
        .map((s) => s[0])
        .join("")
        .slice(0, 2)
        .toUpperCase();

    return (
        <div className="min-h-screen grain flex" style={{ background: "var(--af-bg)" }}>
            {/* Sidebar */}
            <aside
                className="fixed inset-y-0 left-0 w-64 border-r flex-col hidden md:flex z-30"
                style={{ background: "var(--af-sidebar)", borderColor: "var(--af-border)" }}
                data-testid="app-sidebar"
            >
                <div className="h-16 px-6 flex items-center border-b" style={{ borderColor: "var(--af-border)" }}>
                    <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-md" style={{ background: "linear-gradient(135deg,#00FF94,#00E5FF)" }} />
                        <span className="font-display text-lg font-medium tracking-tight">AssetFlow</span>
                    </div>
                </div>

                <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
                    <p className="px-3 pt-2 pb-2 text-[10px] uppercase tracking-[0.18em] text-white/40">Workspace</p>
                    {NAV.map((n) => {
                        if (n.roles && !hasRole(user, ...n.roles)) return null;
                        const Icon = n.icon;
                        return (
                            <NavLink
                                key={n.to}
                                to={n.to}
                                data-testid={n.testId}
                                className={({ isActive }) =>
                                    `group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors duration-150 ${
                                        isActive
                                            ? "bg-white/[0.04] text-white"
                                            : "text-white/60 hover:text-white hover:bg-white/[0.03]"
                                    }`
                                }
                            >
                                {({ isActive }) => (
                                    <>
                                        {isActive && (
                                            <span
                                                className="absolute left-0 top-1.5 bottom-1.5 w-[2px] rounded-r"
                                                style={{ background: "#00FF94", boxShadow: "0 0 8px #00FF94" }}
                                            />
                                        )}
                                        <Icon size={16} strokeWidth={1.5} />
                                        <span>{n.label}</span>
                                    </>
                                )}
                            </NavLink>
                        );
                    })}
                </nav>

                <div className="p-3 border-t" style={{ borderColor: "var(--af-border)" }}>
                    <div className="rounded-lg p-3 bg-white/[0.03] border border-white/5">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-white/40 mb-1">Signed in</p>
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-xs font-medium">
                                {initials}
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm truncate">{user?.name}</p>
                                <p className="text-xs text-white/40">{roleLabel(user?.role)}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main */}
            <div className="flex-1 md:ml-64 flex flex-col min-h-screen relative">
                {/* Topbar */}
                <header
                    className="sticky top-0 z-20 h-16 border-b flex items-center gap-4 px-6 backdrop-blur-xl"
                    style={{ background: "rgba(5,5,5,0.65)", borderColor: "var(--af-border)" }}
                >
                    <div className="flex-1 max-w-md">
                        <div className="relative">
                            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" />
                            <Input
                                data-testid="global-search-input"
                                placeholder="Search assets, tags, people…"
                                className="pl-9 h-10 bg-white/[0.03] border-white/10 focus-visible:ring-white/20 focus-visible:ring-1"
                                onKeyDown={(e) => {
                                    if (e.key === "Enter" && e.currentTarget.value) {
                                        nav(`/assets?q=${encodeURIComponent(e.currentTarget.value)}`);
                                    }
                                }}
                            />
                            <kbd className="hidden md:flex absolute right-3 top-1/2 -translate-y-1/2 items-center gap-1 rounded border border-white/10 bg-white/5 px-1.5 py-0.5 text-[10px] text-white/50">⌘K</kbd>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            className="relative w-9 h-9 rounded-full border border-white/10 bg-white/[0.03] hover:bg-white/[0.08] flex items-center justify-center transition-colors"
                            onClick={() => nav("/notifications")}
                            data-testid="notifications-bell"
                        >
                            <Bell size={16} strokeWidth={1.5} />
                        </button>
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <button
                                    data-testid="user-menu-trigger"
                                    className="flex items-center gap-2 rounded-full pl-2 pr-3 py-1.5 border border-white/10 bg-white/[0.03] hover:bg-white/[0.08] transition-colors"
                                >
                                    <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[10px]">{initials}</div>
                                    <span className="text-sm max-w-[140px] truncate">{user?.name}</span>
                                    <ChevronDown size={14} className="text-white/50" />
                                </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56 bg-[#0e0e0e] border-white/10">
                                <DropdownMenuLabel className="text-white/60 text-xs">
                                    {user?.email}
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator className="bg-white/10" />
                                <DropdownMenuItem className="text-sm">
                                    <User size={14} className="mr-2" /> {roleLabel(user?.role)}
                                </DropdownMenuItem>
                                <DropdownMenuSeparator className="bg-white/10" />
                                <DropdownMenuItem
                                    data-testid="logout-button"
                                    onClick={async () => { await logout(); nav("/login"); }}
                                    className="text-sm cursor-pointer"
                                >
                                    <LogOut size={14} className="mr-2" /> Sign out
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </header>

                <main key={loc.pathname} className="flex-1 p-6 lg:p-8 max-w-[1600px] w-full mx-auto af-fade-in">
                    {children}
                </main>
            </div>
        </div>
    );
}
