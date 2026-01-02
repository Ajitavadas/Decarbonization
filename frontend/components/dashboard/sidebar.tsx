"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Building2,
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
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
}

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/", active: true },
  { icon: Upload, label: "Upload Data", href: "/upload" },
  { icon: Building2, label: "Facilities", href: "#" },
  { icon: Zap, label: "Emissions", href: "#" },
  { icon: Globe, label: "Scope Analysis", href: "#" },
  { icon: Target, label: "Reduction Targets", href: "#" },
  { icon: AlertTriangle, label: "Anomalies", href: "#", badge: 3 },
  { icon: FileBarChart, label: "Reports", href: "#" },
]

const bottomNavItems = [{ icon: Settings, label: "Settings", href: "#" }]

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
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
            <Link href="/" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Leaf className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="font-semibold text-foreground">Decarbonization</span>
            </Link>
          )}
          {collapsed && (
            <Link href="/" className="mx-auto flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Leaf className="h-5 w-5 text-primary-foreground" />
            </Link>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href === "/" && pathname === "/")
            const NavItem = (
              <Link href={item.href} key={item.label}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={cn(
                    "w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                    isActive && "bg-sidebar-accent text-sidebar-accent-foreground",
                    collapsed && "justify-center px-2",
                  )}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                  {!collapsed && item.badge && (
                    <span className="ml-auto flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground">
                      {item.badge}
                    </span>
                  )}
                </Button>
              </Link>
            )

            if (collapsed) {
              return (
                <Tooltip key={item.label}>
                  <TooltipTrigger asChild>{NavItem}</TooltipTrigger>
                  <TooltipContent side="right" className="flex items-center gap-2">
                    {item.label}
                    {item.badge && (
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs text-destructive-foreground">
                        {item.badge}
                      </span>
                    )}
                  </TooltipContent>
                </Tooltip>
              )
            }

            return NavItem
          })}
        </nav>

        {/* Bottom Navigation */}
        <div className="border-t border-sidebar-border p-2">
          {bottomNavItems.map((item) => {
            const NavItem = (
              <Button
                key={item.label}
                variant="ghost"
                className={cn(
                  "w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  collapsed && "justify-center px-2",
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </Button>
            )

            if (collapsed) {
              return (
                <Tooltip key={item.label}>
                  <TooltipTrigger asChild>{NavItem}</TooltipTrigger>
                  <TooltipContent side="right">{item.label}</TooltipContent>
                </Tooltip>
              )
            }

            return NavItem
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
