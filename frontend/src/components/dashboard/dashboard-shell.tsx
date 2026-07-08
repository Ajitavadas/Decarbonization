"use client"

import { useState, useEffect } from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { DashboardContent } from "@/components/dashboard/dashboard-content"
import { CarbonCopilot } from "@/components/copilot/carbon-copilot"
import { ArchetypeOnboarding } from "@/components/copilot/archetype-onboarding"

interface DashboardShellProps {
    children?: React.ReactNode
    userName?: string
    organizationName?: string
    showArchetypeOnboarding?: boolean
}

export function DashboardShell({ children, userName, organizationName, showArchetypeOnboarding = false }: DashboardShellProps) {
    const [copilotOpen, setCopilotOpen] = useState(false)
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
    const [showOnboarding, setShowOnboarding] = useState(showArchetypeOnboarding)

    // Handle onboarding completion
    const handleOnboardingComplete = () => {
        setShowOnboarding(false)
    }

    return (
        <div className="flex h-screen overflow-hidden bg-background">
            {/* Left Sidebar Navigation */}
            <Sidebar
                collapsed={sidebarCollapsed}
                onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
                onToggleCopilot={() => setCopilotOpen(!copilotOpen)}
                copilotOpen={copilotOpen}
            />

            {/* Main Content Area */}
            <div className="flex flex-1 flex-col overflow-hidden">
                <Header userName={userName} organizationName={organizationName} />
                <main className="flex-1 overflow-auto">
                    {children || <DashboardContent />}
                </main>
            </div>

            {/* Carbon Copilot Side Panel */}
            <CarbonCopilot open={copilotOpen} onClose={() => setCopilotOpen(false)} />

            {/* Archetype Onboarding Modal */}
            {showOnboarding && (
                <ArchetypeOnboarding
                    open={showOnboarding}
                    onComplete={handleOnboardingComplete}
                    organizationName={organizationName || "Your Organization"}
                />
            )}
        </div>
    )
}