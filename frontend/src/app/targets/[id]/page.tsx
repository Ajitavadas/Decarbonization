"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter, useParams } from "next/navigation"
import { api, ReductionTarget, ReductionStrategy } from "@/lib/api"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Target,
    ArrowLeft,
    RefreshCw,
    TrendingUp,
    TrendingDown,
    CheckCircle2,
    AlertTriangle,
    Sparkles,
    Lightbulb,
    Zap,
    Clock,
    DollarSign,
    Leaf,
} from "lucide-react"
import { cn } from "@/lib/utils"

// Status config
const statusConfig: Record<string, { icon: typeof TrendingUp; color: string; bgColor: string; label: string }> = {
    on_track: { icon: TrendingUp, color: "text-primary", bgColor: "bg-primary/10", label: "On Track" },
    at_risk: { icon: AlertTriangle, color: "text-warning", bgColor: "bg-warning/10", label: "At Risk" },
    off_track: { icon: TrendingDown, color: "text-destructive", bgColor: "bg-destructive/10", label: "Off Track" },
    achieved: { icon: CheckCircle2, color: "text-primary", bgColor: "bg-primary/10", label: "Achieved" },
}

// Difficulty config
const difficultyConfig: Record<string, { color: string; label: string }> = {
    easy: { color: "bg-primary/10 text-primary", label: "Easy" },
    medium: { color: "bg-warning/10 text-warning", label: "Medium" },
    hard: { color: "bg-destructive/10 text-destructive", label: "Hard" },
}

// Category icons
const categoryIcons: Record<string, typeof Zap> = {
    energy: Zap,
    travel: Target,
    procurement: DollarSign,
    operations: Target,
    facility: Leaf,
}

export default function TargetDetailPage() {
    const router = useRouter()
    const params = useParams()
    const targetId = params.id as string

    const [target, setTarget] = useState<ReductionTarget | null>(null)
    const [strategies, setStrategies] = useState<ReductionStrategy[]>([])
    const [loading, setLoading] = useState(true)
    const [generatingStrategies, setGeneratingStrategies] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)
            const [targetData, strategiesData] = await Promise.all([
                api.getTarget(targetId),
                api.getStrategies(targetId),
            ])
            setTarget(targetData)
            setStrategies(strategiesData)
        } catch (err) {
            console.error("Failed to fetch target:", err)
            if (err instanceof Error) {
                if (err.message === "Unauthorized") {
                    router.push("/login")
                    return
                }
                setError(err.message)
            }
        } finally {
            setLoading(false)
        }
    }, [targetId, router])

    useEffect(() => {
        if (typeof window !== "undefined") {
            if (!api.isAuthenticated()) {
                router.push("/login")
                return
            }
            fetchData()
        }
    }, [fetchData, router])

    const handleGenerateStrategies = async () => {
        try {
            setGeneratingStrategies(true)
            setError(null)
            const newStrategies = await api.generateStrategies(targetId, strategies.length > 0)
            setStrategies(newStrategies)
        } catch (err) {
            console.error("Failed to generate strategies:", err)
            setError(err instanceof Error ? err.message : "Failed to generate strategies")
        } finally {
            setGeneratingStrategies(false)
        }
    }

    const handleRecalculateProgress = async () => {
        try {
            setLoading(true)
            const updatedTarget = await api.calculateTargetProgress(targetId)
            setTarget(updatedTarget)
        } catch (err) {
            console.error("Failed to recalculate progress:", err)
            setError(err instanceof Error ? err.message : "Failed to recalculate")
        } finally {
            setLoading(false)
        }
    }

    const getProgressColor = (progress: number | null) => {
        if (progress === null) return "bg-muted"
        if (progress >= 75) return "bg-primary"
        if (progress >= 50) return "bg-primary/70"
        if (progress >= 25) return "bg-warning"
        return "bg-destructive"
    }

    if (loading && !target) {
        return (
            <DashboardShell>
                <div className="flex items-center justify-center py-12">
                    <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </DashboardShell>
        )
    }

    if (!target) {
        return (
            <DashboardShell>
                <div className="flex flex-col items-center justify-center py-12">
                    <Target className="h-12 w-12 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium">Target not found</h3>
                    <Button variant="outline" onClick={() => router.push("/targets")} className="mt-4">
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Targets
                    </Button>
                </div>
            </DashboardShell>
        )
    }

    const StatusIcon = statusConfig[target.status]?.icon || Target
    const statusColor = statusConfig[target.status]?.color || ""
    const statusBgColor = statusConfig[target.status]?.bgColor || ""

    return (
        <DashboardShell>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="icon" onClick={() => router.push("/targets")}>
                            <ArrowLeft className="h-5 w-5" />
                        </Button>
                        <div>
                            <h1 className="text-2xl font-bold text-foreground">{target.name}</h1>
                            <div className="flex items-center gap-2 mt-1">
                                <Badge variant="outline">{target.scope || "All Scopes"}</Badge>
                                <Badge variant="secondary">
                                    {target.target_type === "percentage"
                                        ? `${target.target_value}% reduction`
                                        : `${target.target_value.toLocaleString()} kg CO₂e`}
                                </Badge>
                                <Badge className={cn(statusBgColor, statusColor, "border-0")}>
                                    <StatusIcon className="h-3 w-3 mr-1" />
                                    {statusConfig[target.status]?.label}
                                </Badge>
                            </div>
                        </div>
                    </div>
                    <Button variant="outline" onClick={handleRecalculateProgress} disabled={loading}>
                        <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                        Recalculate Progress
                    </Button>
                </div>

                {/* Error Alert */}
                {error && (
                    <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
                        {error}
                    </div>
                )}

                {/* Progress Overview */}
                <div className="grid gap-4 md:grid-cols-2">
                    <Card className="border-border bg-card">
                        <CardHeader>
                            <CardTitle>Progress</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="relative h-4 w-full rounded-full bg-muted overflow-hidden">
                                <div
                                    className={cn(
                                        "h-full transition-all",
                                        getProgressColor(target.progress_percentage)
                                    )}
                                    style={{
                                        width: `${Math.min(target.progress_percentage || 0, 100)}%`,
                                    }}
                                />
                            </div>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">
                                    {target.progress_percentage?.toFixed(1) || 0}% toward target
                                </span>
                                <span className="font-medium">
                                    {target.current_reduction_pct?.toFixed(1) || 0}% reduced so far
                                </span>
                            </div>

                            {/* Milestones */}
                            {target.milestones.length > 0 && (
                                <div className="pt-4 border-t">
                                    <h4 className="text-sm font-medium mb-2">Milestones</h4>
                                    <div className="space-y-2">
                                        {target.milestones.map((milestone, idx) => (
                                            <div key={idx} className="flex items-center justify-between text-sm">
                                                <span className="text-muted-foreground">
                                                    {milestone.year}: {milestone.value}% reduction
                                                </span>
                                                {milestone.achieved ? (
                                                    <Badge variant="default" className="gap-1">
                                                        <CheckCircle2 className="h-3 w-3" />
                                                        Achieved
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="outline">Pending</Badge>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    <Card className="border-border bg-card">
                        <CardHeader>
                            <CardTitle>Details</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <dl className="space-y-3 text-sm">
                                <div className="flex justify-between">
                                    <dt className="text-muted-foreground">Baseline Year</dt>
                                    <dd className="font-medium">{target.baseline_year}</dd>
                                </div>
                                <div className="flex justify-between">
                                    <dt className="text-muted-foreground">Baseline Emissions</dt>
                                    <dd className="font-medium">{target.baseline_value.toLocaleString()} kg CO₂e</dd>
                                </div>
                                <div className="flex justify-between">
                                    <dt className="text-muted-foreground">Target Year</dt>
                                    <dd className="font-medium">{target.target_year}</dd>
                                </div>
                                <div className="flex justify-between">
                                    <dt className="text-muted-foreground">Current Emissions</dt>
                                    <dd className="font-medium">
                                        {target.current_value?.toLocaleString() || "Not calculated"} kg CO₂e
                                    </dd>
                                </div>
                                {target.last_calculated_at && (
                                    <div className="flex justify-between pt-2 border-t text-xs">
                                        <dt className="text-muted-foreground">Last Updated</dt>
                                        <dd>{new Date(target.last_calculated_at).toLocaleString()}</dd>
                                    </div>
                                )}
                            </dl>
                        </CardContent>
                    </Card>
                </div>

                {/* AI Strategies */}
                <Card className="border-border bg-card">
                    <CardHeader className="flex flex-row items-center justify-between">
                        <div>
                            <CardTitle className="flex items-center gap-2">
                                <Sparkles className="h-5 w-5 text-primary" />
                                Reduction Strategies
                            </CardTitle>
                            <CardDescription>
                                AI-generated strategies tailored to your organization
                            </CardDescription>
                        </div>
                        <Button
                            onClick={handleGenerateStrategies}
                            disabled={generatingStrategies}
                            className="gap-2"
                        >
                            {generatingStrategies ? (
                                <>
                                    <RefreshCw className="h-4 w-4 animate-spin" />
                                    Generating...
                                </>
                            ) : strategies.length > 0 ? (
                                <>
                                    <RefreshCw className="h-4 w-4" />
                                    Regenerate
                                </>
                            ) : (
                                <>
                                    <Sparkles className="h-4 w-4" />
                                    Generate Strategies
                                </>
                            )}
                        </Button>
                    </CardHeader>
                    <CardContent>
                        {strategies.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-center">
                                <Lightbulb className="h-12 w-12 text-muted-foreground/50 mb-4" />
                                <h3 className="text-lg font-medium">No strategies yet</h3>
                                <p className="text-muted-foreground text-sm mt-1 max-w-md">
                                    Generate AI-powered reduction strategies tailored to your organization&apos;s archetype and emission profile
                                </p>
                            </div>
                        ) : (
                            <div className="grid gap-4 md:grid-cols-2">
                                {strategies.map((strategy) => {
                                    const CategoryIcon = categoryIcons[strategy.category] || Lightbulb
                                    const diffConfig = difficultyConfig[strategy.difficulty || "medium"]

                                    return (
                                        <div
                                            key={strategy.id}
                                            className="rounded-lg border border-border p-4 space-y-3"
                                        >
                                            <div className="flex items-start justify-between gap-2">
                                                <div className="flex items-center gap-2">
                                                    <div className="rounded-md bg-accent p-2">
                                                        <CategoryIcon className="h-4 w-4" />
                                                    </div>
                                                    <div>
                                                        <h4 className="font-medium">{strategy.title}</h4>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            {strategy.is_ai_generated ? (
                                                                <Badge variant="outline" className="text-xs gap-1">
                                                                    <Sparkles className="h-3 w-3" />
                                                                    AI Generated
                                                                </Badge>
                                                            ) : (
                                                                <Badge variant="outline" className="text-xs">
                                                                    📊 Manual
                                                                </Badge>
                                                            )}
                                                            <Badge
                                                                variant="outline"
                                                                className={cn("text-xs", diffConfig?.color)}
                                                            >
                                                                {diffConfig?.label || "Medium"}
                                                            </Badge>
                                                        </div>
                                                    </div>
                                                </div>
                                                <Badge variant="secondary" className="text-xs">
                                                    #{strategy.priority}
                                                </Badge>
                                            </div>
                                            <p className="text-sm text-muted-foreground">
                                                {strategy.description}
                                            </p>
                                            <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
                                                {strategy.estimated_reduction_pct && (
                                                    <span className="flex items-center gap-1">
                                                        <TrendingDown className="h-3 w-3" />
                                                        ~{strategy.estimated_reduction_pct}% reduction
                                                    </span>
                                                )}
                                                {strategy.implementation_timeframe && (
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        {strategy.implementation_timeframe}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </DashboardShell>
    )
}
