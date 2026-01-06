"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
    Loader2, Cloud, Flame, Factory, Truck, Plus, ArrowRight,
    FolderKanban
} from "lucide-react"
import { api } from "@/lib/api"
import type { User, Project, Activity, ProjectSummary } from "@/types"
import { formatNumber, formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"

interface ProjectWithSummary extends Project {
    summary?: ProjectSummary
    activities?: Activity[]
}

export default function EmissionsPage() {
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

            // Fetch activities and summaries for each project
            const projectsWithSummaries = await Promise.all(
                projectsData.map(async (project) => {
                    try {
                        const [activities, summary] = await Promise.all([
                            api.getActivities(project.id),
                            api.getProjectSummary(project.id).catch(() => null),
                        ])
                        return { ...project, activities, summary: summary || undefined }
                    } catch {
                        return { ...project, activities: [], summary: undefined }
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

    const getScopeIcon = (scope: string) => {
        switch (scope) {
            case "Scope 1":
                return <Flame className="h-4 w-4 text-chart-5" />
            case "Scope 2":
                return <Factory className="h-4 w-4 text-chart-2" />
            case "Scope 3":
                return <Truck className="h-4 w-4 text-chart-3" />
            default:
                return <Cloud className="h-4 w-4 text-muted-foreground" />
        }
    }

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    const currentProject = projectsWithData.find(p => p.id === selectedProject)

    return (
        <DashboardShell userName={user?.full_name} organizationName={user?.organization?.name}>
            <div className="space-y-6 p-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-semibold text-foreground">Emissions</h1>
                        <p className="text-sm text-muted-foreground">
                            View calculated emissions from your uploaded activity data
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
                                Create a project and upload activity data to see emissions
                            </p>
                            <Link href="/projects/new">
                                <Button>
                                    <Plus className="mr-2 h-4 w-4" />
                                    Create Project
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : (
                    <>
                        {/* Summary Cards */}
                        {currentProject?.summary && (
                            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                                <Card className="border-border bg-card">
                                    <CardContent className="p-6">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-sm text-muted-foreground">Total Emissions</p>
                                                <p className="text-2xl font-bold text-foreground">
                                                    {formatNumber(Math.round(currentProject.summary.total_co2e_kg))}
                                                </p>
                                                <p className="text-xs text-muted-foreground">kg CO₂e</p>
                                            </div>
                                            <Cloud className="h-8 w-8 text-primary" />
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card className="border-border bg-card">
                                    <CardContent className="p-6">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-sm text-muted-foreground">Scope 1</p>
                                                <p className="text-2xl font-bold text-foreground">
                                                    {formatNumber(Math.round(currentProject.summary.scope_breakdown["Scope 1"] || 0))}
                                                </p>
                                                <p className="text-xs text-muted-foreground">kg CO₂e</p>
                                            </div>
                                            <Flame className="h-8 w-8 text-chart-5" />
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card className="border-border bg-card">
                                    <CardContent className="p-6">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-sm text-muted-foreground">Scope 2</p>
                                                <p className="text-2xl font-bold text-foreground">
                                                    {formatNumber(Math.round(currentProject.summary.scope_breakdown["Scope 2"] || 0))}
                                                </p>
                                                <p className="text-xs text-muted-foreground">kg CO₂e</p>
                                            </div>
                                            <Factory className="h-8 w-8 text-chart-2" />
                                        </div>
                                    </CardContent>
                                </Card>
                                <Card className="border-border bg-card">
                                    <CardContent className="p-6">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <p className="text-sm text-muted-foreground">Scope 3</p>
                                                <p className="text-2xl font-bold text-foreground">
                                                    {formatNumber(Math.round(currentProject.summary.scope_breakdown["Scope 3"] || 0))}
                                                </p>
                                                <p className="text-xs text-muted-foreground">kg CO₂e</p>
                                            </div>
                                            <Truck className="h-8 w-8 text-chart-3" />
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>
                        )}

                        {/* Activities Table */}
                        <Card className="border-border bg-card">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="text-base">Emission Activities</CardTitle>
                                        <CardDescription>
                                            {currentProject?.activities?.length || 0} activities with calculated emissions
                                        </CardDescription>
                                    </div>
                                    {currentProject && (
                                        <Link href={`/projects/${currentProject.id}`}>
                                            <Button variant="outline" size="sm">
                                                View Project
                                                <ArrowRight className="ml-2 h-4 w-4" />
                                            </Button>
                                        </Link>
                                    )}
                                </div>
                            </CardHeader>
                            <CardContent>
                                {!currentProject?.activities?.length ? (
                                    <div className="flex flex-col items-center justify-center py-8">
                                        <Cloud className="h-10 w-10 text-muted-foreground mb-3" />
                                        <p className="text-sm text-muted-foreground">No activities in this project</p>
                                        <p className="text-xs text-muted-foreground">Upload a CSV to add emission data</p>
                                        <Link href="/upload" className="mt-4">
                                            <Button variant="outline" size="sm">
                                                Upload Data
                                            </Button>
                                        </Link>
                                    </div>
                                ) : (
                                    <Table>
                                        <TableHeader>
                                            <TableRow className="border-border">
                                                <TableHead>Description</TableHead>
                                                <TableHead>Type</TableHead>
                                                <TableHead>Scope</TableHead>
                                                <TableHead className="text-right">Emissions (kg CO₂e)</TableHead>
                                                <TableHead>Date</TableHead>
                                            </TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {currentProject.activities.map((activity) => (
                                                <TableRow key={activity.id} className="border-border">
                                                    <TableCell className="font-medium">
                                                        {activity.description || activity.activity_type.replace(/_/g, " ")}
                                                    </TableCell>
                                                    <TableCell>
                                                        <Badge variant="secondary" className="font-normal">
                                                            {activity.activity_type.replace(/_/g, " ")}
                                                        </Badge>
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2">
                                                            {getScopeIcon(activity.scope)}
                                                            <span className={cn(
                                                                "text-sm",
                                                                activity.scope === "Scope 1" && "text-chart-5",
                                                                activity.scope === "Scope 2" && "text-chart-2",
                                                                activity.scope === "Scope 3" && "text-chart-3",
                                                            )}>
                                                                {activity.scope}
                                                            </span>
                                                        </div>
                                                    </TableCell>
                                                    <TableCell className="text-right font-medium">
                                                        {formatNumber(Math.round(Number(activity.co2e_kg)))}
                                                    </TableCell>
                                                    <TableCell className="text-muted-foreground">
                                                        {activity.activity_date ? formatDate(activity.activity_date) : "-"}
                                                    </TableCell>
                                                </TableRow>
                                            ))}
                                        </TableBody>
                                    </Table>
                                )}
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>
        </DashboardShell>
    )
}
