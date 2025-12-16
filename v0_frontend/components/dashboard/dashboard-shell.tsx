"use client"

import { useState } from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { Header } from "@/components/dashboard/header"
import { DashboardContent } from "@/components/dashboard/dashboard-content"
import { CarbonCopilot } from "@/components/copilot/carbon-copilot"

export function DashboardShell() {
  const [copilotOpen, setCopilotOpen] = useState(true)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Left Sidebar Navigation */}
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onToggleCopilot={() => setCopilotOpen(!copilotOpen)} copilotOpen={copilotOpen} />
        <main className="flex-1 overflow-auto">
          <DashboardContent />
        </main>
      </div>

      {/* Carbon Copilot Side Panel */}
      <CarbonCopilot open={copilotOpen} onClose={() => setCopilotOpen(false)} />
    </div>
  )
}
