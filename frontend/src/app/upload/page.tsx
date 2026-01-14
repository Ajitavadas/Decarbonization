"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
    Upload, Loader2, FileUp, CheckCircle2, XCircle, Clock,
    AlertCircle, FolderKanban
} from "lucide-react"
import { api } from "@/lib/api"
import type { User, Project, BatchJob } from "@/types"
import { formatDateTime } from "@/lib/utils"
import Link from "next/link"

export default function UploadPage() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [projects, setProjects] = useState<Project[]>([])
    const [batchJobs, setBatchJobs] = useState<BatchJob[]>([])
    const [loading, setLoading] = useState(true)
    const [uploading, setUploading] = useState(false)
    const [uploadError, setUploadError] = useState("")
    const [selectedProject, setSelectedProject] = useState<string>("")

    const fetchData = useCallback(async () => {
        if (!api.isAuthenticated()) {
            router.push("/login")
            return
        }

        try {
            const [userData, projectsData, jobsData] = await Promise.all([
                api.getMe(),
                api.getProjects(),
                api.getBatchJobs(),
            ])
            setUser(userData)
            setProjects(projectsData)
            setBatchJobs(jobsData)
            if (projectsData.length > 0 && !selectedProject) {
                setSelectedProject(projectsData[0].id)
            }
        } catch {
            router.push("/login")
        } finally {
            setLoading(false)
        }
    }, [router, selectedProject])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    // Poll for job updates
    useEffect(() => {
        const hasActiveJobs = batchJobs.some(job => job.status === "processing" || job.status === "pending")
        if (hasActiveJobs) {
            const interval = setInterval(() => {
                api.getBatchJobs().then(setBatchJobs).catch(console.error)
            }, 3000)
            return () => clearInterval(interval)
        }
    }, [batchJobs])

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file || !selectedProject) return

        setUploading(true)
        setUploadError("")

        try {
            await api.uploadCSV(selectedProject, file)
            // Refresh batch jobs
            const jobs = await api.getBatchJobs()
            setBatchJobs(jobs)
        } catch (err) {
            setUploadError(err instanceof Error ? err.message : "Upload failed")
        } finally {
            setUploading(false)
        }
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed":
                return <CheckCircle2 className="h-5 w-5 text-primary" />
            case "failed":
                return <XCircle className="h-5 w-5 text-destructive" />
            case "processing":
                return <Loader2 className="h-5 w-5 text-warning animate-spin" />
            default:
                return <Clock className="h-5 w-5 text-muted-foreground" />
        }
    }

    const getStatusBadge = (status: string) => {
        switch (status) {
            case "completed":
                return <Badge variant="default">Completed</Badge>
            case "failed":
                return <Badge variant="destructive">Failed</Badge>
            case "processing":
                return <Badge variant="secondary" className="bg-warning/20 text-warning">Processing</Badge>
            default:
                return <Badge variant="secondary">Pending</Badge>
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
                    <h1 className="text-2xl font-semibold text-foreground">Activity Data Upload</h1>
                    <p className="text-sm text-muted-foreground">
                        Upload CSV files with your activity data to calculate emissions
                    </p>
                </div>

                {/* Upload Section */}
                <Card className="border-border bg-card">
                    <CardHeader>
                        <CardTitle className="text-base">Upload Activity Data</CardTitle>
                        <CardDescription>
                            Select a project and upload your activity data file
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* File Format Information Panel */}
                        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
                            <h4 className="font-medium text-sm mb-3 flex items-center gap-2">
                                <FileUp className="h-4 w-4 text-primary" />
                                Supported File Formats
                            </h4>
                            <div className="flex gap-2 text-xs mb-4">
                                <div className="bg-primary/10 text-primary rounded px-3 py-1.5 font-medium">CSV</div>
                                <div className="bg-primary/10 text-primary rounded px-3 py-1.5 font-medium">XLSX</div>
                                <div className="bg-primary/10 text-primary rounded px-3 py-1.5 font-medium">PDF</div>
                            </div>
                            <div className="text-xs space-y-2">
                                <p className="font-medium text-foreground">Required Fields:</p>
                                <div className="bg-background/50 rounded p-2">
                                    <div className="grid grid-cols-4 gap-2 text-muted-foreground">
                                        <span>• description</span>
                                        <span>• amount</span>
                                        <span>• unit</span>
                                        <span>• region</span>
                                        <span>• activity_date</span>
                                        <span>• year</span>
                                        <span>• category</span>
                                    </div>
                                </div>
                                <p className="text-muted-foreground/80">
                                    <span className="font-medium">Optional:</span> supplier_name
                                </p>
                                <p className="text-muted-foreground/70 text-[10px] mt-2">
                                    PDFs will be processed using AI to extract data from tables. Regions like &quot;Karnataka&quot; will be normalized to ISO codes (IN, US, GB, etc).
                                </p>
                            </div>
                        </div>

                        {projects.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <FolderKanban className="h-10 w-10 text-muted-foreground mb-3" />
                                <p className="text-sm text-muted-foreground mb-4">
                                    You need to create a project first before uploading data
                                </p>
                                <Link href="/projects/new">
                                    <Button>Create Project</Button>
                                </Link>
                            </div>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Select Project</label>
                                    <select
                                        value={selectedProject}
                                        onChange={(e) => setSelectedProject(e.target.value)}
                                        className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                                    >
                                        {projects.map((project) => (
                                            <option key={project.id} value={project.id}>
                                                {project.name} ({project.reporting_year})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                {uploadError && (
                                    <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                                        <AlertCircle className="h-4 w-4" />
                                        {uploadError}
                                    </div>
                                )}

                                <div className="flex items-center gap-4">
                                    <input
                                        type="file"
                                        id="file-upload"
                                        accept=".csv,.xlsx,.xls,.pdf"
                                        onChange={handleFileUpload}
                                        className="hidden"
                                        disabled={uploading || !selectedProject}
                                    />
                                    <label htmlFor="file-upload">
                                        <Button asChild disabled={uploading || !selectedProject}>
                                            <span>
                                                {uploading ? (
                                                    <>
                                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                        Uploading...
                                                    </>
                                                ) : (
                                                    <>
                                                        <Upload className="mr-2 h-4 w-4" />
                                                        Select File
                                                    </>
                                                )}
                                            </span>
                                        </Button>
                                    </label>
                                    <span className="text-xs text-muted-foreground">
                                        CSV, XLSX, or PDF
                                    </span>
                                </div>
                            </>
                        )}
                    </CardContent>
                </Card>

                {/* Recent Uploads */}
                <Card className="border-border bg-card">
                    <CardHeader>
                        <CardTitle className="text-base">Recent Uploads</CardTitle>
                        <CardDescription>
                            Status of your uploaded activity data files
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {batchJobs.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <FileUp className="h-10 w-10 text-muted-foreground mb-3" />
                                <p className="text-sm text-muted-foreground">No uploads yet</p>
                                <p className="text-xs text-muted-foreground">Upload a CSV file to get started</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {batchJobs.map((job) => (
                                    <div key={job.id} className="flex items-center gap-4 rounded-lg border border-border bg-secondary/50 p-4">
                                        <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-background">
                                            {getStatusIcon(job.status)}
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center justify-between mb-1">
                                                <p className="text-sm font-medium">{job.file_name || "Uploaded file"}</p>
                                                {getStatusBadge(job.status)}
                                            </div>
                                            {job.status === "processing" && (
                                                <Progress
                                                    value={(job.processed_records / Math.max(job.total_records, 1)) * 100}
                                                    className="h-2 mt-2"
                                                />
                                            )}
                                            <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                                                <span>{job.successful_records} of {job.total_records} records</span>
                                                {job.failed_records > 0 && (
                                                    <span className="text-destructive">{job.failed_records} failed</span>
                                                )}
                                                <span>{formatDateTime(job.created_at)}</span>
                                            </div>
                                            {job.error_message && (
                                                <p className="text-xs text-destructive mt-1">{job.error_message}</p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardShell>
    )
}
