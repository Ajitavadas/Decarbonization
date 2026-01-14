"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, Loader2, FolderKanban, Calendar, FileDown, Sparkles } from "lucide-react"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { api } from "@/lib/api"
import type { Project, User, Activity } from "@/types"
import { formatDate } from "@/lib/utils"

interface ProjectWithActivities extends Project {
    activity_count: number
}

export default function ReportsPage() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [projects, setProjects] = useState<ProjectWithActivities[]>([])
    const [loading, setLoading] = useState(true)
    const [downloadingPdf, setDownloadingPdf] = useState<string | null>(null)

    useEffect(() => {
        fetchData()
    }, [])

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

            // Fetch activity counts for each project
            const projectsWithCounts = await Promise.all(
                projectsData.map(async (project) => {
                    try {
                        const activities = await api.getActivities(project.id)
                        return {
                            ...project,
                            activity_count: activities.length,
                        }
                    } catch {
                        return {
                            ...project,
                            activity_count: 0,
                        }
                    }
                })
            )

            // Filter projects with activities
            const projectsWithData = projectsWithCounts.filter((p) => p.activity_count > 0)
            setProjects(projectsWithData)
        } catch (error) {
            console.error("Failed to fetch data:", error)
        } finally {
            setLoading(false)
        }
    }

    const handleDownloadPdf = async (projectId: string, projectName: string) => {
        setDownloadingPdf(projectId)
        try {
            const blob = await api.downloadReport(projectId, { format_type: 'standard', output_format: 'pdf' })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${projectName.replace(/\s+/g, '_')}_carbon_report.pdf`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (error: any) {
            alert(`Failed to download PDF: ${error.message}`)
        } finally {
            setDownloadingPdf(null)
        }
    }

    const handleDownloadDocx = async (projectId: string, projectName: string) => {
        setDownloadingPdf(projectId)
        try {
            const blob = await api.downloadReport(projectId, { format_type: 'standard', output_format: 'docx' })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${projectName.replace(/\s+/g, '_')}_carbon_report.docx`
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (error: any) {
            alert(`Failed to download DOCX: ${error.message}`)
        } finally {
            setDownloadingPdf(null)
        }
    }

    if (loading) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        )
    }

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
                    <CardHeader>
                        <div className="flex items-start gap-4">
                            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                                <FileText className="h-6 w-6 text-primary" />
                            </div>
                            <div className="flex-1">
                                <CardTitle className="text-base font-medium">Report Options</CardTitle>
                                <CardDescription className="mt-1">
                                    <strong>Standard Format:</strong> Professional PDF reports with all sections, visualizations, and comprehensive data tables.<br/>
                                    <strong>Custom Format:</strong> Build your own report by selecting specific tables and columns to include.
                                </CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                </Card>

                {/* Projects with Data */}
                {projects.length === 0 ? (
                    <Card className="border-border bg-card">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <FolderKanban className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-medium text-foreground mb-2">No projects with data</h3>
                            <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                                Create a project and upload emission activities to generate reports
                            </p>
                            <Link href="/projects">
                                <Button>
                                    Go to Projects
                                    <FolderKanban className="ml-2 h-4 w-4" />
                                </Button>
                            </Link>
                        </CardContent>
                    </Card>
                ) : (
                    <>
                        <div>
                            <h2 className="text-lg font-medium text-foreground mb-4">
                                Projects with Data ({projects.length})
                            </h2>
                        </div>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {projects.map((project) => (
                                <Card key={project.id} className="border-border bg-card hover:border-primary/50 transition-colors">
                                    <CardHeader>
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <FolderKanban className="h-4 w-4 text-primary" />
                                                    <CardTitle className="text-base">{project.name}</CardTitle>
                                                </div>
                                                <CardDescription className="text-xs">
                                                    {project.description || "No description"}
                                                </CardDescription>
                                            </div>
                                            <Badge variant="secondary">{project.reporting_year}</Badge>
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                            <div className="flex items-center gap-1">
                                                <Calendar className="h-3 w-3" />
                                                <span>Created {formatDate(project.created_at)}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs">
                                            <FileDown className="h-3 w-3 text-muted-foreground" />
                                            <span className="text-muted-foreground">
                                                {project.activity_count} {project.activity_count === 1 ? 'activity' : 'activities'}
                                            </span>
                                        </div>
                                        <div className="flex gap-2">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button
                                                        variant="default"
                                                        size="sm"
                                                        className="flex-1"
                                                        disabled={downloadingPdf === project.id}
                                                    >
                                                        {downloadingPdf === project.id ? (
                                                            <>
                                                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                                                Generating...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Download className="mr-2 h-3 w-3" />
                                                                Standard
                                                            </>
                                                        )}
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem
                                                        onClick={() => handleDownloadPdf(project.id, project.name)}
                                                    >
                                                        <FileText className="mr-2 h-4 w-4" />
                                                        Download as PDF
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem
                                                        onClick={() => handleDownloadDocx(project.id, project.name)}
                                                    >
                                                        <FileText className="mr-2 h-4 w-4" />
                                                        Download as DOCX
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                            <Link href={`/reports/custom?project=${project.id}`} className="flex-1">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="w-full"
                                                >
                                                    <Sparkles className="mr-2 h-3 w-3" />
                                                    Custom
                                                </Button>
                                            </Link>
                                        </div>
                                        <Link href={`/projects/${project.id}`}>
                                            <Button variant="ghost" size="sm" className="w-full">
                                                View Project Details
                                            </Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </>
                )}
            </div>
        </DashboardShell>
    )
}
