"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { ArchetypeOnboarding } from "@/components/copilot/archetype-onboarding"
import { api } from "@/lib/api"
import type { User } from "@/types"

export default function Home() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)
    const [showOnboarding, setShowOnboarding] = useState(false)
    const [organizationName, setOrganizationName] = useState<string>("")

    useEffect(() => {
        const checkAuth = async () => {
            if (!api.isAuthenticated()) {
                router.push("/login")
                return
            }

            try {
                const userData = await api.getMe()
                setUser(userData)

                // Check if organization has archetype set
                const org = await api.getMyOrganization()
                setOrganizationName(org.name)

                if (!org.emission_archetype) {
                    // Show onboarding for new organizations
                    setShowOnboarding(true)
                }
            } catch {
                router.push("/login")
            } finally {
                setLoading(false)
            }
        }

        checkAuth()
    }, [router])

    const handleOnboardingComplete = () => {
        setShowOnboarding(false)
    }

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
        <>
            <DashboardShell
                userName={user?.full_name}
                organizationName={user?.organization?.name}
            />

            <ArchetypeOnboarding
                open={showOnboarding}
                onComplete={handleOnboardingComplete}
                organizationName={organizationName}
            />
        </>
    )
}

