"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Cloud, Flame, Factory, Truck, Upload, FolderKanban, FileUp,
    CheckCircle2, Loader2
} from "lucide-react"
import { api } from "@/lib/api"
import type { Project, Activity, BatchJob, ProjectSummary } from "@/types"
import { formatNumber, formatDate } from "@/lib/utils"
import {
    Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
    Cell, Pie, PieChart, Legend
} from "recharts"

interface DashboardData {
    projects: Project[]
    allActivities: Activity[]
    batchJobs: BatchJob[]
    summaries: Record<string, ProjectSummary>
    totalEmissions: number
    scope1: number
    scope2: number
    scope3: number
}

export function DashboardContent() {
    const router = useRouter()
    const [loading, setLoading] = useState(true)
    const [data, setData] = useState<DashboardData | null>(null)

    const fetchData = useCallback(async () => {
        if (!api.isAuthenticated()) {
            router.push("/login")
            return
        }

        try {
            const [projects, batchJobs] = await Promise.all([
                api.getProjects(),
                api.getBatchJobs(),
            ])

            // Fetch activities and summaries for each project
            let allActivities: Activity[] = []
            const summaries: Record<string, ProjectSummary> = {}
            let totalEmissions = 0
            let scope1 = 0
            let scope2 = 0
            let scope3 = 0

            for (const project of projects) {
                try {
                    const activities = await api.getActivities(project.id)
                    allActivities = [...allActivities, ...activities]

                    if (activities.length > 0) {
                        const summary = await api.getProjectSummary(project.id)
                        summaries[project.id] = summary
                        totalEmissions += Number(summary.total_co2e_kg) || 0
                        scope1 += Number(summary.scope_breakdown["Scope 1"]) || 0
                        scope2 += Number(summary.scope_breakdown["Scope 2"]) || 0
                        scope3 += Number(summary.scope_breakdown["Scope 3"]) || 0
                    }
                } catch {
                    // Skip project if can't fetch data
                }
            }

            setData({
                projects,
                allActivities,
                batchJobs,
                summaries,
                totalEmissions,
                scope1,
                scope2,
                scope3,
            })
        } catch {
            router.push("/login")
        } finally {
            setLoading(false)
        }
    }, [router])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    if (loading) {
        return (
            <div className="flex h-full items-center justify-center p-6">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    const hasData = data && data.allActivities.length > 0
    const hasProjects = data && data.projects.length > 0

    // Prepare emissions by month from actual activity dates
    const emissionsByMonth: Record<string, { scope1: number; scope2: number; scope3: number }> = {}

    if (data) {
        data.allActivities.forEach((activity) => {
            const date = activity.activity_date ? new Date(activity.activity_date) : new Date(activity.created_at)
            const monthKey = date.toLocaleDateString("en-US", { month: "short", year: "2-digit" })

            if (!emissionsByMonth[monthKey]) {
                emissionsByMonth[monthKey] = { scope1: 0, scope2: 0, scope3: 0 }
            }

            const emissions = Number(activity.co2e_kg) || 0
            if (activity.scope === "Scope 1") {
                emissionsByMonth[monthKey].scope1 += emissions
            } else if (activity.scope === "Scope 2") {
                emissionsByMonth[monthKey].scope2 += emissions
            } else if (activity.scope === "Scope 3") {
                emissionsByMonth[monthKey].scope3 += emissions
            }
        })
    }

    const chartData = Object.entries(emissionsByMonth)
        .map(([month, values]) => ({
            month,
            scope1: Math.round(values.scope1),
            scope2: Math.round(values.scope2),
            scope3: Math.round(values.scope3),
        }))
        .sort((a, b) => {
            const dateA = new Date(a.month)
            const dateB = new Date(b.month)
            return dateA.getTime() - dateB.getTime()
        })

    // Prepare pie chart data
    const pieData = data ? [
        { name: "Scope 1", value: Math.round(data.scope1), color: "#f97316" },
        { name: "Scope 2", value: Math.round(data.scope2), color: "#3b82f6" },
        { name: "Scope 3", value: Math.round(data.scope3), color: "#eab308" },
    ].filter(d => d.value > 0) : []

    // Recent batch jobs - sorted by date descending
    const recentJobs = data?.batchJobs
        .filter(j => j.file_name)
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 5) || []

    return (
        <div className="space-y-6 p-6">
            {/* Page Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-semibold text-foreground">Dashboard</h1>
                    <p className="text-sm text-muted-foreground">
                        Monitor your organization&apos;s carbon footprint in real-time
                    </p>
                </div>
            </div>

            {/* Empty State - No Projects */}
            {!hasProjects && (
                <Card className="border-border bg-card">
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <FolderKanban className="h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-medium text-foreground mb-2">Welcome! Get started</h3>
                        <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                            Create your first project and upload activity data to start tracking your carbon emissions.
                        </p>
                        <div className="flex gap-3">
                            <Link href="/projects/new">
                                <Button>
                                    <FolderKanban className="mr-2 h-4 w-4" />
                                    Create Project
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Empty State - Has Projects but No Data */}
            {hasProjects && !hasData && (
                <Card className="border-border bg-card">
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <Upload className="h-12 w-12 text-muted-foreground mb-4" />
                        <h3 className="text-lg font-medium text-foreground mb-2">Upload your first data</h3>
                        <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                            You have {data?.projects.length} project(s). Upload a CSV file with your activity data to see emission calculations.
                        </p>
                        <Link href="/upload">
                            <Button>
                                <FileUp className="mr-2 h-4 w-4" />
                                Upload Activity Data
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            )}

            {/* Dashboard with Real Data */}
            {hasData && (
                <>
                    {/* Metric Cards */}
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <Card className="border-border bg-card">
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-muted-foreground">Total Emissions</p>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-2xl font-bold text-foreground">
                                                {formatNumber(Math.round(data.totalEmissions))}
                                            </span>
                                            <span className="text-sm text-muted-foreground">kg CO₂e</span>
                                        </div>
                                    </div>
                                    <div className="rounded-lg p-2 bg-primary/10">
                                        <Cloud className="h-5 w-5 text-primary" />
                                    </div>
                                </div>
                                <p className="mt-4 text-xs text-muted-foreground">
                                    From {data.allActivities.length} activities
                                </p>
                            </CardContent>
                        </Card>

                        <Card className="border-border bg-card">
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-muted-foreground">Scope 1</p>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-2xl font-bold text-foreground">
                                                {formatNumber(Math.round(data.scope1))}
                                            </span>
                                            <span className="text-sm text-muted-foreground">kg CO₂e</span>
                                        </div>
                                    </div>
                                    <div className="rounded-lg p-2 bg-chart-5/10">
                                        <Flame className="h-5 w-5 text-chart-5" />
                                    </div>
                                </div>
                                <p className="mt-4 text-xs text-muted-foreground">Direct emissions</p>
                            </CardContent>
                        </Card>

                        <Card className="border-border bg-card">
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-muted-foreground">Scope 2</p>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-2xl font-bold text-foreground">
                                                {formatNumber(Math.round(data.scope2))}
                                            </span>
                                            <span className="text-sm text-muted-foreground">kg CO₂e</span>
                                        </div>
                                    </div>
                                    <div className="rounded-lg p-2 bg-chart-2/10">
                                        <Factory className="h-5 w-5 text-chart-2" />
                                    </div>
                                </div>
                                <p className="mt-4 text-xs text-muted-foreground">Indirect (electricity)</p>
                            </CardContent>
                        </Card>

                        <Card className="border-border bg-card">
                            <CardContent className="p-6">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-1">
                                        <p className="text-sm font-medium text-muted-foreground">Scope 3</p>
                                        <div className="flex items-baseline gap-1">
                                            <span className="text-2xl font-bold text-foreground">
                                                {formatNumber(Math.round(data.scope3))}
                                            </span>
                                            <span className="text-sm text-muted-foreground">kg CO₂e</span>
                                        </div>
                                    </div>
                                    <div className="rounded-lg p-2 bg-chart-3/10">
                                        <Truck className="h-5 w-5 text-chart-3" />
                                    </div>
                                </div>
                                <p className="mt-4 text-xs text-muted-foreground">Value chain</p>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Charts Row */}
                    <div className="grid gap-6 lg:grid-cols-3">
                        {/* Emissions Over Time - Real Data */}
                        <Card className="border-border bg-card lg:col-span-2">
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-base font-medium">Emissions Over Time</CardTitle>
                                    <div className="flex items-center gap-4 text-xs">
                                        <div className="flex items-center gap-1.5">
                                            <span className="h-2.5 w-2.5 rounded-full bg-chart-5" />
                                            <span className="text-muted-foreground">Scope 1</span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <span className="h-2.5 w-2.5 rounded-full bg-chart-2" />
                                            <span className="text-muted-foreground">Scope 2</span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <span className="h-2.5 w-2.5 rounded-full bg-chart-3" />
                                            <span className="text-muted-foreground">Scope 3</span>
                                        </div>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent>
                                {chartData.length > 0 ? (
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                <defs>
                                                    <linearGradient id="scope1Gradient" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="0%" stopColor="#f97316" stopOpacity={0.3} />
                                                        <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
                                                    </linearGradient>
                                                    <linearGradient id="scope2Gradient" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                                        <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                                                    </linearGradient>
                                                    <linearGradient id="scope3Gradient" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="0%" stopColor="#eab308" stopOpacity={0.3} />
                                                        <stop offset="100%" stopColor="#eab308" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#333347" vertical={false} />
                                                <XAxis
                                                    dataKey="month"
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: "#8c8c8c", fontSize: 12 }}
                                                />
                                                <YAxis
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: "#8c8c8c", fontSize: 12 }}
                                                    tickFormatter={(value) => formatNumber(value)}
                                                />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: "#1a1a2e",
                                                        border: "1px solid #333347",
                                                        borderRadius: "8px",
                                                        color: "#f2f2f2",
                                                    }}
                                                    formatter={(value: number, name: string) => [
                                                        `${formatNumber(value)} kg CO₂e`,
                                                        name === "scope1" ? "Scope 1" : name === "scope2" ? "Scope 2" : "Scope 3"
                                                    ]}
                                                />
                                                <Area type="monotone" dataKey="scope1" stackId="1" stroke="#f97316" fill="url(#scope1Gradient)" strokeWidth={2} />
                                                <Area type="monotone" dataKey="scope2" stackId="1" stroke="#3b82f6" fill="url(#scope2Gradient)" strokeWidth={2} />
                                                <Area type="monotone" dataKey="scope3" stackId="1" stroke="#eab308" fill="url(#scope3Gradient)" strokeWidth={2} />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    <div className="flex h-[300px] items-center justify-center text-muted-foreground">
                                        No emission data to display
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Scope Breakdown - Real Data */}
                        <Card className="border-border bg-card">
                            <CardHeader>
                                <CardTitle className="text-base font-medium">Scope Breakdown</CardTitle>
                                <CardDescription>Emissions by GHG Protocol scope</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {pieData.length > 0 ? (
                                    <div className="h-[250px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={pieData}
                                                    cx="50%"
                                                    cy="50%"
                                                    innerRadius={50}
                                                    outerRadius={80}
                                                    paddingAngle={4}
                                                    dataKey="value"
                                                    strokeWidth={0}
                                                >
                                                    {pieData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.color} />
                                                    ))}
                                                </Pie>
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: "#1a1a2e",
                                                        border: "1px solid #333347",
                                                        borderRadius: "8px",
                                                        color: "#f2f2f2",
                                                    }}
                                                    formatter={(value: number) => [`${formatNumber(value)} kg CO₂e`, ""]}
                                                />
                                                <Legend
                                                    verticalAlign="bottom"
                                                    height={36}
                                                    formatter={(value) => <span className="text-foreground text-sm">{value}</span>}
                                                />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                ) : (
                                    <div className="flex h-[250px] items-center justify-center text-muted-foreground">
                                        No scope data
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    {/* Recent Uploads & Projects */}
                    <div className="grid gap-6 lg:grid-cols-2">
                        {/* Recent Uploads */}
                        <Card className="border-border bg-card">
                            <CardHeader>
                                <CardTitle className="text-base font-medium">Recent Uploads</CardTitle>
                                <CardDescription>Your latest activity data uploads</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {recentJobs.length > 0 ? (
                                    <div className="space-y-3">
                                        {recentJobs.map((job) => (
                                            <div key={job.id} className="flex items-center gap-3 rounded-lg border border-border p-3">
                                                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
                                                    <CheckCircle2 className="h-4 w-4 text-primary" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium truncate">{job.file_name}</p>
                                                    <p className="text-xs text-muted-foreground">
                                                        {job.successful_records} records • {formatDate(job.created_at)}
                                                    </p>
                                                </div>
                                                <Badge variant={job.status === "completed" ? "default" : "secondary"}>
                                                    {job.status}
                                                </Badge>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="flex flex-col items-center justify-center py-8 text-center">
                                        <FileUp className="h-8 w-8 text-muted-foreground mb-2" />
                                        <p className="text-sm text-muted-foreground">No uploads yet</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Projects Overview */}
                        <Card className="border-border bg-card">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base font-medium">Projects</CardTitle>
                                        <CardDescription>Your emission tracking projects</CardDescription>
                                    </div>
                                    <Link href="/projects/new">
                                        <Button variant="outline" size="sm">
                                            <FolderKanban className="mr-2 h-4 w-4" />
                                            New
                                        </Button>
                                    </Link>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {data.projects.slice(0, 5).map((project) => {
                                        const summary = data.summaries[project.id]
                                        return (
                                            <Link key={project.id} href={`/projects/${project.id}`}>
                                                <div className="flex items-center gap-3 rounded-lg border border-border p-3 hover:bg-secondary/50 transition-colors cursor-pointer">
                                                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                                                        <FolderKanban className="h-4 w-4 text-primary" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium truncate">{project.name}</p>
                                                        <p className="text-xs text-muted-foreground">
                                                            {summary ? `${formatNumber(Math.round(Number(summary.total_co2e_kg)))} kg CO₂e` : "No data"}
                                                        </p>
                                                    </div>
                                                    <Badge variant="secondary">{project.reporting_year}</Badge>
                                                </div>
                                            </Link>
                                        )
                                    })}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </>
            )}
        </div>
    )
}
