"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter, useParams } from "next/navigation"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
    ArrowLeft, Upload, Loader2, FileUp, CheckCircle2, XCircle,
    Cloud, Flame, Factory, Truck, Trash2
} from "lucide-react"
import { api } from "@/lib/api"
import type { Project, User, Activity, ProjectSummary, BatchJob } from "@/types"
import { formatDate, formatNumber } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function ProjectDetailPage() {
    const router = useRouter()
    const params = useParams()
    const projectId = params.id as string

    const [user, setUser] = useState<User | null>(null)
    const [project, setProject] = useState<Project | null>(null)
    const [activities, setActivities] = useState<Activity[]>([])
    const [summary, setSummary] = useState<ProjectSummary | null>(null)
    const [batchJobs, setBatchJobs] = useState<BatchJob[]>([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [uploadError, setUploadError] = useState("")

    const fetchData = useCallback(async () => {
        if (!api.isAuthenticated()) {
            router.push("/login")
            return
        }

        try {
            const [userData, projectData, activitiesData, batchJobsData] = await Promise.all([
                api.getMe(),
                api.getProject(projectId),
                api.getActivities(projectId),
                api.getBatchJobs(),
            ])
            setUser(userData)
            setProject(projectData)
            setActivities(activitiesData)
            setBatchJobs(batchJobsData.filter(job => job.file_name))

            // Get summary if there are activities
            if (activitiesData.length > 0) {
                const summaryData = await api.getProjectSummary(projectId)
                setSummary(summaryData)
            }
        } catch {
            router.push("/projects")
        } finally {
            setLoading(false)
        }
    }, [projectId, router])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        setUploading(true)
        setUploadError("")

        try {
            await api.uploadCSV(projectId, file)
            // Poll for job completion
            setTimeout(() => {
                fetchData()
            }, 2000)
        } catch (err) {
            setUploadError(err instanceof Error ? err.message : "Upload failed")
        } finally {
            setUploading(false)
        }
    }

    const handleDeleteActivity = async (activityId: string) => {
        try {
            await api.deleteActivity(activityId)
            setActivities(activities.filter(a => a.id !== activityId))
        } catch (err) {
            console.error("Failed to delete activity:", err)
        }
    }

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

    if (!project) {
        return null
    }

    return (
        <DashboardShell userName={user?.full_name} organizationName={user?.organization?.name}>
            <div className="space-y-6 p-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link href="/projects">
                            <Button variant="ghost" size="icon">
                                <ArrowLeft className="h-4 w-4" />
                            </Button>
                        </Link>
                        <div>
                            <div className="flex items-center gap-2">
                                <h1 className="text-2xl font-semibold text-foreground">{project.name}</h1>
                                <Badge variant="secondary">{project.reporting_year}</Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                                {project.description || "No description"} • Created {formatDate(project.created_at)}
                            </p>
                        </div>
                    </div>
                    <div>
                        <input
                            type="file"
                            id="csv-upload"
                            accept=".csv"
                            onChange={handleFileUpload}
                            className="hidden"
                            disabled={uploading}
                        />
                        <label htmlFor="csv-upload">
                            <Button asChild disabled={uploading}>
                                <span>
                                    {uploading ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Uploading...
                                        </>
                                    ) : (
                                        <>
                                            <Upload className="mr-2 h-4 w-4" />
                                            Upload CSV
                                        </>
                                    )}
                                </span>
                            </Button>
                        </label>
                    </div>
                </div>

                {uploadError && (
                    <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                        {uploadError}
                    </div>
                )}

                {/* Summary Cards */}
                {summary && (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                        <Card className="border-border bg-card">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-muted-foreground">Total Emissions</p>
                                        <p className="text-2xl font-bold text-foreground">
                                            {formatNumber(Math.round(summary.total_co2e_kg))}
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
                                            {formatNumber(Math.round(summary.scope_breakdown["Scope 1"] || 0))}
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
                                            {formatNumber(Math.round(summary.scope_breakdown["Scope 2"] || 0))}
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
                                            {formatNumber(Math.round(summary.scope_breakdown["Scope 3"] || 0))}
                                        </p>
                                        <p className="text-xs text-muted-foreground">kg CO₂e</p>
                                    </div>
                                    <Truck className="h-8 w-8 text-chart-3" />
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Recent Batch Jobs */}
                {batchJobs.length > 0 && (
                    <Card className="border-border bg-card">
                        <CardHeader>
                            <CardTitle className="text-base">Recent Uploads</CardTitle>
                            <CardDescription>Status of your recent CSV uploads</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {batchJobs.slice(0, 3).map((job) => (
                                    <div key={job.id} className="flex items-center gap-4 rounded-lg border border-border p-3">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary">
                                            {job.status === "completed" ? (
                                                <CheckCircle2 className="h-5 w-5 text-primary" />
                                            ) : job.status === "failed" ? (
                                                <XCircle className="h-5 w-5 text-destructive" />
                                            ) : (
                                                <FileUp className="h-5 w-5 text-muted-foreground" />
                                            )}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-medium">{job.file_name}</p>
                                                <Badge
                                                    variant={job.status === "completed" ? "default" : job.status === "failed" ? "destructive" : "secondary"}
                                                >
                                                    {job.status}
                                                </Badge>
                                            </div>
                                            {job.status === "processing" && (
                                                <Progress value={(job.processed_records / job.total_records) * 100} className="mt-2" />
                                            )}
                                            <p className="text-xs text-muted-foreground">
                                                {job.successful_records}/{job.total_records} records processed
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Activities Table */}
                <Card className="border-border bg-card">
                    <CardHeader>
                        <CardTitle className="text-base">Activities</CardTitle>
                        <CardDescription>
                            {activities.length} activities in this project
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {activities.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8">
                                <FileUp className="h-10 w-10 text-muted-foreground mb-3" />
                                <p className="text-sm text-muted-foreground">No activities yet</p>
                                <p className="text-xs text-muted-foreground">Upload a CSV to add emission data</p>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow className="border-border">
                                        <TableHead>Description</TableHead>
                                        <TableHead>Type</TableHead>
                                        <TableHead>Scope</TableHead>
                                        <TableHead className="text-right">Emissions</TableHead>
                                        <TableHead>Date</TableHead>
                                        <TableHead></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {activities.map((activity) => (
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
                                                {formatNumber(Math.round(Number(activity.co2e_kg)))} kg
                                            </TableCell>
                                            <TableCell className="text-muted-foreground">
                                                {activity.activity_date ? formatDate(activity.activity_date) : "-"}
                                            </TableCell>
                                            <TableCell>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => handleDeleteActivity(activity.id)}
                                                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardShell>
    )
}
