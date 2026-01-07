"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { ReportGenerator } from "@/components/dashboard/report-generator"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { FileText, FolderKanban, Loader2, ArrowRight, ExternalLink } from "lucide-react"
import { api } from "@/lib/api"
import type { Project, User } from "@/types"
import { formatDate, formatNumber } from "@/lib/utils"

export default function ReportsPage() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [projects, setProjects] = useState<Project[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
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
                setProjects(projectsData)
            } catch {
                router.push("/login")
            } finally {
                setLoading(false)
            }
        }

        fetchData()
    }, [router])

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

    const projectsWithActivities = projects.filter(p => p.emission_activities_count > 0)

    return (
        <DashboardShell userName={user?.full_name} organizationName={user?.organization?.name}>
            <div className="space-y-6 p-6">
                {/* Page Header */}
                <div>
                    <h1 className="text-2xl font-semibold text-foreground">Reports</h1>
                    <p className="text-sm text-muted-foreground">
                        Generate and download carbon footprint reports for your projects
                    </p>
                </div>

                {/* Info Card */}
                <Card className="border-border bg-card">
                    <CardContent className="pt-6">
                        <div className="flex items-start gap-3">
                            <FileText className="h-5 w-5 text-primary mt-0.5" />
                            <div className="flex-1">
                                <p className="text-sm font-medium text-foreground">Generate Reports</p>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Open any project with emission activities to generate professional PDF or HTML reports. 
                                    Reports include visualizations, scope breakdown, activity analysis, and detailed data tables.
                                </p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Projects Grid */}
                {projectsWithActivities.length === 0 ? (
                    <Card className="border-border bg-card">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <FolderKanban className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-medium text-foreground mb-2">No projects with data</h3>
                            <p className="text-sm text-muted-foreground mb-4 text-center">
                                Create a project and upload emission activities to generate reports
                            </p>
                            <Link href="/projects">
                                <Button>
                                    Go to Projects
                                    <ArrowRight className="ml-2 h-4 w-4" />
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-1">
                        {projectsWithActivities.map((project) => (
                            <Card key={project.id} className="border-border bg-card">
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                                <FileText className="h-5 w-5 text-primary" />
                                            </div>
                                            <div>
                                                <CardTitle className="text-base">{project.name}</CardTitle>
                                                <CardDescription className="text-xs">
                                                    {project.emission_activities_count} activities • Created {formatDate(project.created_at)}
                                                </CardDescription>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <Badge variant="secondary">{project.reporting_year}</Badge>
                                            <Link href={`/projects/${project.id}`}>
                                                <Button variant="ghost" size="icon" title="View project details">
                                                    <ExternalLink className="h-4 w-4" />
                                                </Button>
                                            </Link>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <ReportGenerator
                                        projectId={project.id}
                                        projectName={project.name}
                                        hasActivities={project.emission_activities_count > 0}
                                    />
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* All Projects Section */}
                {projects.length > projectsWithActivities.length && (
                    <div className="mt-8">
                        <h2 className="text-lg font-semibold text-foreground mb-4">Projects Without Data</h2>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {projects.filter(p => p.emission_activities_count === 0).map((project) => (
                                <Card key={project.id} className="border-border bg-card opacity-60">
                                    <CardHeader>
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                                                    <FolderKanban className="h-5 w-5 text-muted-foreground" />
                                                </div>
                                                <div>
                                                    <CardTitle className="text-base">{project.name}</CardTitle>
                                                    <CardDescription className="text-xs">
                                                        No activities yet
                                                    </CardDescription>
                                                </div>
                                            </div>
                                            <Badge variant="secondary">{project.reporting_year}</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="text-xs text-muted-foreground mb-4">
                                            <p>Created {formatDate(project.created_at)}</p>
                                            <p className="text-amber-500 mt-2">Upload emission activities to generate reports</p>
                                        </div>
                                        <Link href={`/projects/${project.id}`}>
                                            <Button variant="outline" size="sm" className="w-full">
                                                Go to Project
                                                <ArrowRight className="ml-2 h-3 w-3" />
                                            </Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </DashboardShell>
    )
}
