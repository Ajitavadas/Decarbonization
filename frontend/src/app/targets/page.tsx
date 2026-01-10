"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { api, ReductionTarget, CreateTargetData } from "@/lib/api"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
    Target,
    Plus,
    RefreshCw,
    TrendingUp,
    TrendingDown,
    CheckCircle2,
    AlertTriangle,
    Sparkles,
    ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"

// Status config
const statusConfig: Record<string, { icon: typeof TrendingUp; color: string; label: string }> = {
    on_track: { icon: TrendingUp, color: "text-primary", label: "On Track" },
    at_risk: { icon: AlertTriangle, color: "text-warning", label: "At Risk" },
    off_track: { icon: TrendingDown, color: "text-destructive", label: "Off Track" },
    achieved: { icon: CheckCircle2, color: "text-primary", label: "Achieved" },
}

export default function TargetsPage() {
    const router = useRouter()
    const [targets, setTargets] = useState<ReductionTarget[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [showCreateDialog, setShowCreateDialog] = useState(false)
    const [creating, setCreating] = useState(false)

    // Form state
    const [formData, setFormData] = useState<CreateTargetData>({
        name: "",
        target_type: "percentage",
        scope: "all",
        baseline_year: new Date().getFullYear().toString(),
        baseline_value: 0,
        target_year: (new Date().getFullYear() + 5).toString(),
        target_value: 20,
        milestones: [],
    })

    const fetchTargets = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)
            const data = await api.getTargets()
            setTargets(data)
        } catch (err) {
            console.error("Failed to fetch targets:", err)
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
    }, [router])

    useEffect(() => {
        if (typeof window !== "undefined") {
            if (!api.isAuthenticated()) {
                router.push("/login")
                return
            }
            fetchTargets()
        }
    }, [fetchTargets, router])

    const handleCreateTarget = async () => {
        try {
            setCreating(true)
            setError(null)
            await api.createTarget(formData)
            setShowCreateDialog(false)
            setFormData({
                name: "",
                target_type: "percentage",
                scope: "all",
                baseline_year: new Date().getFullYear().toString(),
                baseline_value: 0,
                target_year: (new Date().getFullYear() + 5).toString(),
                target_value: 20,
                milestones: [],
            })
            await fetchTargets()
        } catch (err) {
            console.error("Failed to create target:", err)
            setError(err instanceof Error ? err.message : "Failed to create target")
        } finally {
            setCreating(false)
        }
    }

    const getProgressColor = (progress: number | null) => {
        if (progress === null) return "bg-muted"
        if (progress >= 75) return "bg-primary"
        if (progress >= 50) return "bg-primary/70"
        if (progress >= 25) return "bg-warning"
        return "bg-destructive"
    }

    return (
        <DashboardShell>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">Reduction Targets</h1>
                        <p className="text-muted-foreground">
                            Set and track emission reduction goals with AI-powered strategies
                        </p>
                    </div>
                    <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                        <DialogTrigger asChild>
                            <Button className="gap-2">
                                <Plus className="h-4 w-4" />
                                Add Target
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[500px]">
                            <DialogHeader>
                                <DialogTitle>Create Reduction Target</DialogTitle>
                                <DialogDescription>
                                    Set a new emission reduction goal for your organization
                                </DialogDescription>
                            </DialogHeader>
                            <div className="grid gap-4 py-4">
                                <div className="grid gap-2">
                                    <Label htmlFor="name">Target Name</Label>
                                    <Input
                                        id="name"
                                        placeholder="e.g., Net Zero by 2030"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="grid gap-2">
                                        <Label>Target Type</Label>
                                        <Select
                                            value={formData.target_type}
                                            onValueChange={(v) => setFormData({ ...formData, target_type: v as "absolute" | "percentage" })}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="percentage">Percentage Reduction</SelectItem>
                                                <SelectItem value="absolute">Absolute Target</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="grid gap-2">
                                        <Label>Scope</Label>
                                        <Select
                                            value={formData.scope || "all"}
                                            onValueChange={(v) => setFormData({ ...formData, scope: v })}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="all">All Scopes</SelectItem>
                                                <SelectItem value="Scope 1">Scope 1</SelectItem>
                                                <SelectItem value="Scope 2">Scope 2</SelectItem>
                                                <SelectItem value="Scope 3">Scope 3</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="baseline_year">Baseline Year</Label>
                                        <Input
                                            id="baseline_year"
                                            type="number"
                                            value={formData.baseline_year}
                                            onChange={(e) => setFormData({ ...formData, baseline_year: e.target.value })}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="baseline_value">Baseline Emissions (kg CO₂e)</Label>
                                        <Input
                                            id="baseline_value"
                                            type="number"
                                            value={formData.baseline_value}
                                            onChange={(e) => setFormData({ ...formData, baseline_value: parseFloat(e.target.value) || 0 })}
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="target_year">Target Year</Label>
                                        <Input
                                            id="target_year"
                                            type="number"
                                            value={formData.target_year}
                                            onChange={(e) => setFormData({ ...formData, target_year: e.target.value })}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="target_value">
                                            {formData.target_type === "percentage" ? "Target Reduction (%)" : "Target Emissions (kg CO₂e)"}
                                        </Label>
                                        <Input
                                            id="target_value"
                                            type="number"
                                            value={formData.target_value}
                                            onChange={(e) => setFormData({ ...formData, target_value: parseFloat(e.target.value) || 0 })}
                                        />
                                    </div>
                                </div>
                            </div>
                            <DialogFooter>
                                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                                    Cancel
                                </Button>
                                <Button onClick={handleCreateTarget} disabled={creating || !formData.name}>
                                    {creating ? (
                                        <>
                                            <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                            Creating...
                                        </>
                                    ) : (
                                        "Create Target"
                                    )}
                                </Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                </div>

                {/* Error Alert */}
                {error && (
                    <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
                        {error}
                    </div>
                )}

                {/* Summary Cards */}
                <div className="grid gap-4 md:grid-cols-4">
                    <Card className="border-border bg-card">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">
                                Total Targets
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold">{targets.length}</div>
                        </CardContent>
                    </Card>
                    <Card className="border-border bg-card">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">
                                On Track
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-primary">
                                {targets.filter((t) => t.status === "on_track" || t.status === "achieved").length}
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="border-border bg-card">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">
                                At Risk
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-warning">
                                {targets.filter((t) => t.status === "at_risk").length}
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="border-border bg-card">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm font-medium text-muted-foreground">
                                Achieved
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="text-2xl font-bold text-primary">
                                {targets.filter((t) => t.status === "achieved").length}
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Targets List */}
                <Card className="border-border bg-card">
                    <CardHeader>
                        <CardTitle>Your Targets</CardTitle>
                        <CardDescription>
                            {loading ? "Loading..." : `${targets.length} reduction targets`}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : targets.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-center">
                                <Target className="h-12 w-12 text-muted-foreground/50 mb-4" />
                                <h3 className="text-lg font-medium">No targets yet</h3>
                                <p className="text-muted-foreground text-sm mt-1 mb-4">
                                    Create your first reduction target to get started
                                </p>
                                <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
                                    <Plus className="h-4 w-4" />
                                    Add Target
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {targets.map((target) => {
                                    const StatusIcon = statusConfig[target.status]?.icon || Target
                                    const statusColor = statusConfig[target.status]?.color || ""
                                    const statusLabel = statusConfig[target.status]?.label || target.status

                                    return (
                                        <div
                                            key={target.id}
                                            className="group flex items-center gap-4 rounded-lg border border-border p-4 cursor-pointer hover:bg-accent/50 transition-colors"
                                            onClick={() => router.push(`/targets/${target.id}`)}
                                        >
                                            <div className={cn("rounded-md bg-accent p-2", statusColor)}>
                                                <StatusIcon className="h-5 w-5" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <h4 className="font-medium truncate">{target.name}</h4>
                                                    <Badge variant="outline" className="text-xs">
                                                        {target.scope || "All Scopes"}
                                                    </Badge>
                                                    <Badge variant="secondary" className="text-xs">
                                                        {target.target_type === "percentage"
                                                            ? `${target.target_value}% reduction`
                                                            : `${target.target_value.toLocaleString()} kg CO₂e`}
                                                    </Badge>
                                                </div>
                                                <div className="flex items-center gap-4 mt-2">
                                                    <span className="text-sm text-muted-foreground">
                                                        {target.baseline_year} → {target.target_year}
                                                    </span>
                                                    <div className="flex-1 max-w-xs">
                                                        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
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
                                                    </div>
                                                    <span className="text-sm font-medium">
                                                        {target.progress_percentage?.toFixed(0) || 0}%
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <Badge
                                                    variant="outline"
                                                    className={cn("text-xs", statusColor)}
                                                >
                                                    {statusLabel}
                                                </Badge>
                                                <ChevronRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
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
