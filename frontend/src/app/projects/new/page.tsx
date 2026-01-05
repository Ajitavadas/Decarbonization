"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ArrowLeft, Loader2 } from "lucide-react"
import { api } from "@/lib/api"
import type { User } from "@/types"

export default function NewProjectPage() {
    const router = useRouter()
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState("")
    const currentYear = new Date().getFullYear()
    const [formData, setFormData] = useState({
        name: "",
        description: "",
        start_date: `${currentYear}-01-01`,
        end_date: `${currentYear}-12-31`,
        reporting_year: String(currentYear),
    })

    useEffect(() => {
        const checkAuth = async () => {
            if (!api.isAuthenticated()) {
                router.push("/login")
                return
            }

            try {
                const userData = await api.getMe()
                setUser(userData)
            } catch {
                router.push("/login")
            } finally {
                setLoading(false)
            }
        }

        checkAuth()
    }, [router])

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setFormData((prev) => ({
            ...prev,
            [e.target.name]: e.target.value,
        }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        setSubmitting(true)

        try {
            const project = await api.createProject({
                name: formData.name,
                description: formData.description || undefined,
                start_date: formData.start_date,
                end_date: formData.end_date,
                reporting_year: formData.reporting_year,
            })
            router.push(`/projects/${project.id}`)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to create project")
        } finally {
            setSubmitting(false)
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
                <div className="flex items-center gap-4">
                    <Link href="/projects">
                        <Button variant="ghost" size="icon">
                            <ArrowLeft className="h-4 w-4" />
                        </Button>
                    </Link>
                    <div>
                        <h1 className="text-2xl font-semibold text-foreground">Create Project</h1>
                        <p className="text-sm text-muted-foreground">
                            Set up a new emission tracking project
                        </p>
                    </div>
                </div>

                {/* Form */}
                <Card className="max-w-2xl border-border bg-card">
                    <CardHeader>
                        <CardTitle>Project Details</CardTitle>
                        <CardDescription>
                            Enter the details for your new project
                        </CardDescription>
                    </CardHeader>
                    <form onSubmit={handleSubmit}>
                        <CardContent className="space-y-4">
                            {error && (
                                <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                                    {error}
                                </div>
                            )}

                            <div className="space-y-2">
                                <Label htmlFor="name">Project Name *</Label>
                                <Input
                                    id="name"
                                    name="name"
                                    type="text"
                                    placeholder="2025 Q1 Emissions"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required
                                    className="bg-secondary"
                                />
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="description">Description</Label>
                                <Input
                                    id="description"
                                    name="description"
                                    type="text"
                                    placeholder="Quarterly emissions report for Q1 2025"
                                    value={formData.description}
                                    onChange={handleChange}
                                    className="bg-secondary"
                                />
                            </div>

                            <div className="grid gap-4 sm:grid-cols-2">
                                <div className="space-y-2">
                                    <Label htmlFor="start_date">Start Date *</Label>
                                    <Input
                                        id="start_date"
                                        name="start_date"
                                        type="date"
                                        value={formData.start_date}
                                        onChange={handleChange}
                                        required
                                        className="bg-secondary"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <Label htmlFor="end_date">End Date *</Label>
                                    <Input
                                        id="end_date"
                                        name="end_date"
                                        type="date"
                                        value={formData.end_date}
                                        onChange={handleChange}
                                        required
                                        className="bg-secondary"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="reporting_year">Reporting Year *</Label>
                                <Input
                                    id="reporting_year"
                                    name="reporting_year"
                                    type="text"
                                    pattern="[0-9]{4}"
                                    maxLength={4}
                                    placeholder="2024"
                                    value={formData.reporting_year}
                                    onChange={handleChange}
                                    required
                                    className="bg-secondary"
                                />
                            </div>

                            <div className="flex gap-4 pt-4">
                                <Link href="/projects">
                                    <Button type="button" variant="outline">
                                        Cancel
                                    </Button>
                                </Link>
                                <Button type="submit" disabled={submitting}>
                                    {submitting ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Creating...
                                        </>
                                    ) : (
                                        "Create Project"
                                    )}
                                </Button>
                            </div>
                        </CardContent>
                    </form>
                </Card>
            </div>
        </DashboardShell>
    )
}
