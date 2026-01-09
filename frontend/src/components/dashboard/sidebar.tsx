"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
    LayoutDashboard,
    FileBarChart,
    Settings,
    Zap,
    Globe,
    Leaf,
    ChevronLeft,
    ChevronRight,
    Upload,
    AlertTriangle,
    Target,
    Sparkles,
    FolderKanban,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface SidebarProps {
    collapsed: boolean
    onToggle: () => void
    onToggleCopilot: () => void
    copilotOpen: boolean
}

const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: FolderKanban, label: "Projects", href: "/projects" },
    { icon: Upload, label: "Activity Data Upload", href: "/upload" },
    { icon: Zap, label: "Emissions", href: "/emissions" },
    { icon: Globe, label: "Scope Analysis", href: "/scope-analysis" },
    { icon: Target, label: "Reduction Targets", href: "/targets" },
    { icon: AlertTriangle, label: "Anomalies", href: "/anomalies" },
    { icon: FileBarChart, label: "Reports", href: "/reports", disabled: true },
]

const bottomNavItems = [{ icon: Settings, label: "Settings", href: "/settings", disabled: true }]

export function Sidebar({ collapsed, onToggle, onToggleCopilot, copilotOpen }: SidebarProps) {
    const pathname = usePathname()

    return (
        <TooltipProvider delayDuration={0}>
            <aside
                className={cn(
                    "relative flex flex-col border-r border-border bg-sidebar transition-all duration-300",
                    collapsed ? "w-16" : "w-64",
                )}
            >
                {/* Logo */}
                <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4">
                    {!collapsed && (
                        <div className="flex items-center gap-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                                <Leaf className="h-5 w-5 text-primary-foreground" />
                            </div>
                            <span className="font-semibold text-foreground">Decarbonization</span>
                        </div>
                    )}
                    {collapsed && (
                        <div className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                            <Leaf className="h-5 w-5 text-primary-foreground" />
                        </div>
                    )}
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-1 p-2">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))

                        const NavButton = (
                            <Button
                                variant={isActive ? "secondary" : "ghost"}
                                className={cn(
                                    "w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                                    isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
                                    collapsed && "justify-center px-2",
                                    item.disabled && "opacity-50 cursor-not-allowed",
                                )}
                                disabled={item.disabled}
                            >
                                <item.icon className="h-5 w-5 shrink-0" />
                                {!collapsed && <span>{item.label}</span>}
                                {!collapsed && item.badge && (
                                    <span className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground">
                                        {item.badge}
                                    </span>
                                )}
                            </Button>
                        )

                        const NavContent = item.disabled ? (
                            <div key={item.label}>{NavButton}</div>
                        ) : (
                            <Link key={item.label} href={item.href}>
                                {NavButton}
                            </Link>
                        )

                        if (collapsed) {
                            return (
                                <Tooltip key={item.label}>
                                    <TooltipTrigger asChild>{NavContent}</TooltipTrigger>
                                    <TooltipContent side="right" className="flex items-center gap-2">
                                        {item.label}
                                        {item.badge && (
                                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground">
                                                {item.badge}
                                            </span>
                                        )}
                                        {item.disabled && <span className="text-xs text-muted-foreground">(Coming soon)</span>}
                                    </TooltipContent>
                                </Tooltip>
                            )
                        }

                        return NavContent
                    })}

                    {/* Copilot Button in Sidebar */}
                    <div className="pt-2 border-t border-sidebar-border mt-2">
                        {(() => {
                            const CopilotButton = (
                                <Button
                                    variant={copilotOpen ? "secondary" : "ghost"}
                                    onClick={onToggleCopilot}
                                    className={cn(
                                        "w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                                        copilotOpen && "bg-sidebar-accent text-sidebar-accent-foreground",
                                        collapsed && "justify-center px-2",
                                    )}
                                >
                                    <div className={cn("flex h-5 w-5 items-center justify-center rounded", copilotOpen && "ai-gradient rounded-md")}>
                                        <Sparkles className={cn("h-4 w-4 shrink-0", copilotOpen && "text-primary-foreground")} />
                                    </div>
                                    {!collapsed && <span>Carbon Copilot</span>}
                                    {!collapsed && copilotOpen && (
                                        <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-primary/20 text-primary">Active</span>
                                    )}
                                </Button>
                            )

                            if (collapsed) {
                                return (
                                    <Tooltip>
                                        <TooltipTrigger asChild>{CopilotButton}</TooltipTrigger>
                                        <TooltipContent side="right" className="flex items-center gap-2">
                                            Carbon Copilot
                                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">Coming soon</span>
                                        </TooltipContent>
                                    </Tooltip>
                                )
                            }

                            return CopilotButton
                        })()}
                    </div>
                </nav>

                {/* Bottom Navigation */}
                <div className="border-t border-sidebar-border p-2">
                    {bottomNavItems.map((item) => {
                        const NavButton = (
                            <Button
                                variant="ghost"
                                className={cn(
                                    "w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                                    collapsed && "justify-center px-2",
                                    item.disabled && "opacity-50 cursor-not-allowed",
                                )}
                                disabled={item.disabled}
                            >
                                <item.icon className="h-5 w-5 shrink-0" />
                                {!collapsed && <span>{item.label}</span>}
                            </Button>
                        )

                        const NavContent = item.disabled ? (
                            <div key={item.label}>{NavButton}</div>
                        ) : (
                            <Link key={item.label} href={item.href}>
                                {NavButton}
                            </Link>
                        )

                        if (collapsed) {
                            return (
                                <Tooltip key={item.label}>
                                    <TooltipTrigger asChild>{NavContent}</TooltipTrigger>
                                    <TooltipContent side="right">
                                        {item.label}
                                        {item.disabled && <span className="text-xs text-muted-foreground"> (Coming soon)</span>}
                                    </TooltipContent>
                                </Tooltip>
                            )
                        }

                        return NavContent
                    })}
                </div>

                {/* Collapse Toggle */}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onToggle}
                    className="absolute -right-3 top-20 z-10 h-6 w-6 rounded-full border border-border bg-background shadow-sm hover:bg-accent"
                >
                    {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
                </Button>
            </aside>
        </TooltipProvider>
    )
}
