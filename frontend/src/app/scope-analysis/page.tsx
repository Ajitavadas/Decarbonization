"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Loader2, Flame, Factory, Truck, Plus, FolderKanban
} from "lucide-react"
import { api } from "@/lib/api"
import type { User, Project, ProjectSummary } from "@/types"
import { formatNumber } from "@/lib/utils"
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from "recharts"

interface ProjectWithSummary extends Project {
    summary?: ProjectSummary | null
}

export default function ScopeAnalysisPage() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [projectsWithData, setProjectsWithData] = useState<ProjectWithSummary[]>([])
    const [loading, setLoading] = useState(true)
    const [selectedProject, setSelectedProject] = useState<string | null>(null)

    const fetchData = useCallback(async () => {
        if (!api.isAuthenticated()) {
            router.push("/login")
            return
        }

        try {
            const [userData, projectsData] = await Promise.all([
                api.getMe(),
                api.getProjects(),
            ])
            setUser(userData)

            // Fetch summaries for each project
            const projectsWithSummaries = await Promise.all(
                projectsData.map(async (project) => {
                    try {
                        const summary = await api.getProjectSummary(project.id)
                        return { ...project, summary }
                    } catch {
                        return { ...project, summary: null }
                    }
                })
            )
            setProjectsWithData(projectsWithSummaries)
            if (projectsWithSummaries.length > 0) {
                setSelectedProject(projectsWithSummaries[0].id)
            }
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
            <div className="flex h-screen items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    const currentProject = projectsWithData.find(p => p.id === selectedProject)
    const summary = currentProject?.summary

    // Prepare chart data - parse values as Numbers since backend returns strings
    const pieData = summary ? [
        { name: "Scope 1", value: Number(summary.scope_breakdown["Scope 1"]) || 0, color: "#f97316" },
        { name: "Scope 2", value: Number(summary.scope_breakdown["Scope 2"]) || 0, color: "#3b82f6" },
        { name: "Scope 3", value: Number(summary.scope_breakdown["Scope 3"]) || 0, color: "#eab308" },
    ].filter(d => d.value > 0) : []

    const barData = summary ? [
        {
            name: "Scope 1",
            value: Number(summary.scope_breakdown["Scope 1"]) || 0,
            fill: "#f97316",
            icon: Flame,
            description: "Direct emissions"
        },
        {
            name: "Scope 2",
            value: Number(summary.scope_breakdown["Scope 2"]) || 0,
            fill: "#3b82f6",
            icon: Factory,
            description: "Indirect (electricity)"
        },
        {
            name: "Scope 3",
            value: Number(summary.scope_breakdown["Scope 3"]) || 0,
            fill: "#eab308",
            icon: Truck,
            description: "Value chain"
        },
    ] : []

    const total = pieData.reduce((acc, d) => acc + d.value, 0)

    return (
        <DashboardShell userName={user?.full_name} organizationName={user?.organization?.name}>
            <div className="space-y-6 p-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-semibold text-foreground">Scope Analysis</h1>
                        <p className="text-sm text-muted-foreground">
                            Breakdown of emissions by GHG Protocol scope
                        </p>
                    </div>
                    {projectsWithData.length > 0 && (
                        <select
                            value={selectedProject || ""}
                            onChange={(e) => setSelectedProject(e.target.value)}
                            className="rounded-md border border-border bg-secondary px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                        >
                            {projectsWithData.map((project) => (
                                <option key={project.id} value={project.id}>
                                    {project.name} ({project.reporting_year})
                                </option>
                            ))}
                        </select>
                    )}
                </div>

                {projectsWithData.length === 0 ? (
                    <Card className="border-border bg-card">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <FolderKanban className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-medium text-foreground mb-2">No projects yet</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Create a project and upload activity data to analyze scope breakdown
                            </p>
                            <Link href="/projects/new">
                                <Button>
                                    <Plus className="mr-2 h-4 w-4" />
                                    Create Project
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : !summary || total === 0 ? (
                    <Card className="border-border bg-card">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <Factory className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-medium text-foreground mb-2">No emission data</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Upload activity data to this project to see scope analysis
                            </p>
                            <Link href="/upload">
                                <Button>Upload Data</Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : (
                    <>
                        {/* Scope Cards */}
                        <div className="grid gap-4 md:grid-cols-3">
                            {barData.map((scope) => {
                                const percentage = total > 0 ? ((scope.value / total) * 100).toFixed(1) : "0"
                                const IconComponent = scope.icon
                                return (
                                    <Card key={scope.name} className="border-border bg-card">
                                        <CardContent className="p-6">
                                            <div className="flex items-center gap-4">
                                                <div
                                                    className="flex h-12 w-12 items-center justify-center rounded-lg"
                                                    style={{ backgroundColor: `${scope.fill}20` }}
                                                >
                                                    <IconComponent className="h-6 w-6" style={{ color: scope.fill }} />
                                                </div>
                                                <div className="flex-1">
                                                    <div className="flex items-center justify-between">
                                                        <p className="text-sm font-medium text-muted-foreground">{scope.name}</p>
                                                        <Badge variant="secondary">{percentage}%</Badge>
                                                    </div>
                                                    <p className="text-2xl font-bold text-foreground">
                                                        {formatNumber(Math.round(scope.value))}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground">{scope.description}</p>
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )
                            })}
                        </div>

                        {/* Charts */}
                        <div className="grid gap-6 lg:grid-cols-2">
                            {/* Pie Chart */}
                            <Card className="border-border bg-card">
                                <CardHeader>
                                    <CardTitle className="text-base">Scope Distribution</CardTitle>
                                    <CardDescription>Percentage breakdown by scope</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <PieChart>
                                                <Pie
                                                    data={pieData}
                                                    cx="50%"
                                                    cy="50%"
                                                    innerRadius={60}
                                                    outerRadius={100}
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
                                                    formatter={(value: number) => [`${formatNumber(Math.round(value))} kg CO₂e`, ""]}
                                                />
                                                <Legend
                                                    verticalAlign="bottom"
                                                    height={36}
                                                    formatter={(value) => <span className="text-foreground">{value}</span>}
                                                />
                                            </PieChart>
                                        </ResponsiveContainer>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Bar Chart */}
                            <Card className="border-border bg-card">
                                <CardHeader>
                                    <CardTitle className="text-base">Emissions by Scope</CardTitle>
                                    <CardDescription>Total kg CO₂e per scope</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-[300px]">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <BarChart data={barData} layout="vertical" margin={{ left: 0, right: 20 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="#333347" horizontal={false} />
                                                <XAxis
                                                    type="number"
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: "#8c8c8c", fontSize: 12 }}
                                                    tickFormatter={(value) => formatNumber(value)}
                                                />
                                                <YAxis
                                                    type="category"
                                                    dataKey="name"
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fill: "#8c8c8c", fontSize: 12 }}
                                                    width={60}
                                                />
                                                <Tooltip
                                                    contentStyle={{
                                                        backgroundColor: "#1a1a2e",
                                                        border: "1px solid #333347",
                                                        borderRadius: "8px",
                                                        color: "#f2f2f2",
                                                    }}
                                                    formatter={(value: number) => [`${formatNumber(Math.round(value))} kg CO₂e`, "Emissions"]}
                                                />
                                                <Bar
                                                    dataKey="value"
                                                    radius={[0, 4, 4, 0]}
                                                >
                                                    {barData.map((entry, index) => (
                                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                                    ))}
                                                </Bar>
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Scope Descriptions */}
                        <Card className="border-border bg-card">
                            <CardHeader>
                                <CardTitle className="text-base">Understanding GHG Protocol Scopes</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-4 md:grid-cols-3">
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <Flame className="h-5 w-5 text-chart-5" />
                                            <h4 className="font-medium text-foreground">Scope 1 - Direct</h4>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            Direct GHG emissions from sources owned or controlled by your organization,
                                            such as company vehicles, on-site fuel combustion, and fugitive emissions.
                                        </p>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <Factory className="h-5 w-5 text-chart-2" />
                                            <h4 className="font-medium text-foreground">Scope 2 - Indirect</h4>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            Indirect GHG emissions from the generation of purchased electricity,
                                            steam, heating, and cooling consumed by your organization.
                                        </p>
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <Truck className="h-5 w-5 text-chart-3" />
                                            <h4 className="font-medium text-foreground">Scope 3 - Value Chain</h4>
                                        </div>
                                        <p className="text-sm text-muted-foreground">
                                            All other indirect emissions in the value chain, including business travel,
                                            employee commuting, purchased goods, and downstream transportation.
                                        </p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>
        </DashboardShell>
    )
}
