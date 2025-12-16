"use client"

import { MetricCards } from "@/components/dashboard/metric-cards"
import { EmissionsChart } from "@/components/dashboard/emissions-chart"
import { ScopeBreakdown } from "@/components/dashboard/scope-breakdown"
import { FacilitiesTable } from "@/components/dashboard/facilities-table"
import { RecentActivity } from "@/components/dashboard/recent-activity"
import { DataGaps } from "@/components/dashboard/data-gaps"

export function DashboardContent() {
  return (
    <div className="space-y-6 p-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Monitor your organization's carbon footprint in real-time</p>
        </div>
        <div className="flex items-center gap-2">
          <select className="rounded-md border border-border bg-secondary px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
            <option>Last 12 months</option>
            <option>Last 6 months</option>
            <option>Last 30 days</option>
            <option>This year</option>
          </select>
        </div>
      </div>

      {/* Metric Cards */}
      <MetricCards />

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <EmissionsChart />
        </div>
        <ScopeBreakdown />
      </div>

      {/* Data Gaps & Activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DataGaps />
        <RecentActivity />
      </div>

      {/* Facilities Table */}
      <FacilitiesTable />
    </div>
  )
}
