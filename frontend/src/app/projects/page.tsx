"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, FolderKanban, Calendar, ArrowRight, Loader2 } from "lucide-react"
import { api } from "@/lib/api"
import type { Project, User } from "@/types"
import { formatDate } from "@/lib/utils"

export default function ProjectsPage() {
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

    return (
        <DashboardShell userName={user?.full_name} organizationName={user?.organization?.name}>
            <div className="space-y-6 p-6">
                {/* Page Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-semibold text-foreground">Projects</h1>
                        <p className="text-sm text-muted-foreground">
                            Manage your emission tracking projects
                        </p>
                    </div>
                    <Link href="/projects/new">
                        <Button>
                            <Plus className="mr-2 h-4 w-4" />
                            New Project
                        </Button>
                    </Link>
                </div>

                {/* Projects Grid */}
                {projects.length === 0 ? (
                    <Card className="border-border bg-card">
                        <CardContent className="flex flex-col items-center justify-center py-12">
                            <FolderKanban className="h-12 w-12 text-muted-foreground mb-4" />
                            <h3 className="text-lg font-medium text-foreground mb-2">No projects yet</h3>
                            <p className="text-sm text-muted-foreground mb-4">
                                Create your first project to start tracking emissions
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
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {projects.map((project) => (
                            <Card key={project.id} className="border-border bg-card hover:border-primary/50 transition-colors">
                                <CardHeader>
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                                                <FolderKanban className="h-5 w-5 text-primary" />
                                            </div>
                                            <div>
                                                <CardTitle className="text-base">{project.name}</CardTitle>
                                                <CardDescription className="text-xs">
                                                    {project.description || "No description"}
                                                </CardDescription>
                                            </div>
                                        </div>
                                        <Badge variant="secondary">{project.reporting_year}</Badge>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4">
                                        <div className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            <span>Created {formatDate(project.created_at)}</span>
                                        </div>
                                    </div>
                                    <Link href={`/projects/${project.id}`}>
                                        <Button variant="outline" size="sm" className="w-full">
                                            View Project
                                            <ArrowRight className="ml-2 h-3 w-3" />
                                        </Button>
                                    </Link>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}
            </div>
        </DashboardShell>
    )
}
