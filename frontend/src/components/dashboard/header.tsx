"use client"

import { Bell, Search, User, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { api } from "@/lib/api"

interface HeaderProps {
    userName?: string
    organizationName?: string
}

export function Header({ userName, organizationName }: HeaderProps) {
    const handleLogout = () => {
        api.logout()
    }

    return (
        <header className="flex h-16 items-center justify-between border-b border-border bg-background px-6">
            {/* Search */}
            <div className="relative w-96">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                    placeholder="Search projects, emissions, reports..."
                    className="pl-9 bg-secondary border-0 focus-visible:ring-1 focus-visible:ring-primary"
                />
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-2">
                {/* Organization Badge */}
                {organizationName && (
                    <Badge variant="secondary" className="hidden md:flex">
                        {organizationName}
                    </Badge>
                )}

                {/* Notifications */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="relative">
                            <Bell className="h-5 w-5" />
                            <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-medium text-primary-foreground">
                                5
                            </span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-80">
                        <DropdownMenuLabel className="flex items-center justify-between">
                            Notifications
                            <Badge variant="secondary" className="text-xs">
                                5 new
                            </Badge>
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="flex flex-col items-start gap-1 p-3">
                            <div className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-warning" />
                                <span className="font-medium">Missing Scope 1 Data</span>
                            </div>
                            <span className="text-xs text-muted-foreground">Facility is missing heating data for Q4 2024</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem className="flex flex-col items-start gap-1 p-3">
                            <div className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-destructive" />
                                <span className="font-medium">Anomaly Detected</span>
                            </div>
                            <span className="text-xs text-muted-foreground">Electricity usage spike detected</span>
                        </DropdownMenuItem>
                        <DropdownMenuItem className="flex flex-col items-start gap-1 p-3">
                            <div className="flex items-center gap-2">
                                <span className="h-2 w-2 rounded-full bg-primary" />
                                <span className="font-medium">Report Ready</span>
                            </div>
                            <span className="text-xs text-muted-foreground">Your Q3 2024 carbon report is ready for review</span>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>

                {/* User Menu */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="rounded-full">
                            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                                <User className="h-4 w-4 text-primary" />
                            </div>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>
                            <div className="flex flex-col">
                                <span>{userName || "User"}</span>
                                {organizationName && (
                                    <span className="text-xs font-normal text-muted-foreground">{organizationName}</span>
                                )}
                            </div>
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>Profile</DropdownMenuItem>
                        <DropdownMenuItem>Organization</DropdownMenuItem>
                        <DropdownMenuItem>API Keys</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                            <LogOut className="mr-2 h-4 w-4" />
                            Log out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </header>
    )
}
