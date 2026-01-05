"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { api } from "@/lib/api"
import type { User } from "@/types"

export default function Home() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const checkAuth = async () => {
            if (!api.isAuthenticated()) {
                router.push("/login")
                return
            }

            try {
                const userData = await api.getMe()
                setUser(userData)
            } catch {
                router.push("/login")
            } finally {
                setLoading(false)
            }
        }

        checkAuth()
    }, [router])

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-4">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                    <p className="text-sm text-muted-foreground">Loading...</p>
                </div>
            </div>
        )
    }

    return (
        <DashboardShell
            userName={user?.full_name}
            organizationName={user?.organization?.name}
        />
    )
}
