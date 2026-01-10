"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { DashboardShell } from "@/components/dashboard/dashboard-shell"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    AlertTriangle,
    FileQuestion,
    Zap,
    TrendingDown,
    RefreshCw,
    CheckCircle2,
    XCircle,
    Clock,
    Sparkles,
    Filter,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { AuditFinding, AuditSummary, Severity, FlagType, FindingStatus } from "@/types"

// Icon mapping for finding types
const typeIcons: Record<FlagType, typeof AlertTriangle> = {
    gap: FileQuestion,
    anomaly: Zap,
    archetype_mismatch: TrendingDown,
}

// Status icons
const statusIcons: Record<FindingStatus, typeof Clock> = {
    open: Clock,
    acknowledged: AlertTriangle,
    resolved: CheckCircle2,
    false_positive: XCircle,
}

export default function AnomaliesPage() {
    const router = useRouter()
    const [findings, setFindings] = useState<AuditFinding[]>([])
    const [summary, setSummary] = useState<AuditSummary | null>(null)
    const [loading, setLoading] = useState(true)
    const [runningAudit, setRunningAudit] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [statusFilter, setStatusFilter] = useState<string>("open")
    const [typeFilter, setTypeFilter] = useState<string>("")
    const [severityFilter, setSeverityFilter] = useState<string>("")

    const fetchData = useCallback(async () => {
        try {
            setLoading(true)
            setError(null)

            // Fetch findings with filters
            const params: Record<string, string> = {}
            if (statusFilter) params.status = statusFilter
            if (typeFilter) params.flag_type = typeFilter
            if (severityFilter) params.severity = severityFilter

            const [findingsRes, summaryRes] = await Promise.all([
                api.getAuditFindings(params),
                api.getAuditSummary(),
            ])

            setFindings(findingsRes.findings)
            setSummary(summaryRes)
        } catch (err) {
            console.error("Failed to fetch audit data:", err)
            if (err instanceof Error) {
                if (err.message === "Unauthorized") {
                    router.push("/login")
                    return
                }
                // Handle network errors more gracefully
                if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
                    setError("Unable to connect to server. Please check if the backend is running.")
                } else {
                    setError(err.message)
                }
            } else {
                setError("Failed to load audit data")
            }
        } finally {
            setLoading(false)
        }
    }, [router, statusFilter, typeFilter, severityFilter])

    useEffect(() => {
        // Check auth first before making any API calls
        if (typeof window !== "undefined") {
            if (!api.isAuthenticated()) {
                router.push("/login")
                return
            }
            // Only fetch data if authenticated
            fetchData()
        }
    }, [fetchData, router])

    const handleRunAudit = async () => {
        try {
            setRunningAudit(true)
            setError(null)
            await api.runAudit({ include_ai_analysis: true })
            await fetchData()
        } catch (err) {
            console.error("Audit failed:", err)
            setError(err instanceof Error ? err.message : "Audit failed")
        } finally {
            setRunningAudit(false)
        }
    }

    const handleResolveFinding = async (findingId: string, status: "resolved" | "false_positive") => {
        try {
            await api.resolveFinding(findingId, status)
            await fetchData()
        } catch (err) {
            console.error("Failed to resolve finding:", err)
            setError(err instanceof Error ? err.message : "Failed to resolve")
        }
    }

    const getSeverityColor = (severity: Severity) => {
        switch (severity) {
            case "critical":
                return "bg-destructive/10 text-destructive border-destructive/20"
            case "warning":
                return "bg-warning/10 text-warning border-warning/20"
            case "info":
                return "bg-muted text-muted-foreground border-border"
        }
    }

    const getTypeLabel = (type: FlagType) => {
        switch (type) {
            case "gap":
                return "Data Gap"
            case "anomaly":
                return "Anomaly"
            case "archetype_mismatch":
                return "Archetype Mismatch"
        }
    }

    return (
        <DashboardShell>
            <div className="space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-foreground">Anomalies & Data Gaps</h1>
                        <p className="text-muted-foreground">
                            AI-powered anomaly detection and data quality auditing
                        </p>
                    </div>
                    <Button
                        onClick={handleRunAudit}
                        disabled={runningAudit}
                        className="gap-2"
                    >
                        {runningAudit ? (
                            <>
                                <RefreshCw className="h-4 w-4 animate-spin" />
                                Running Audit...
                            </>
                        ) : (
                            <>
                                <Sparkles className="h-4 w-4" />
                                Run AI Audit
                            </>
                        )}
                    </Button>
                </div>

                {/* Error Alert */}
                {error && (
                    <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive">
                        {error}
                    </div>
                )}

                {/* Summary Cards */}
                {summary && (
                    <div className="grid gap-4 md:grid-cols-4">
                        <Card className="border-border bg-card">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Total Findings
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{summary.total_findings}</div>
                            </CardContent>
                        </Card>
                        <Card className="border-border bg-card">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    Open Critical
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className={cn(
                                    "text-2xl font-bold",
                                    summary.open_critical > 0 && "text-destructive"
                                )}>
                                    {summary.open_critical}
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-border bg-card">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    By Status
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex gap-2 text-sm">
                                    <span className="text-muted-foreground">Open:</span>
                                    <span className="font-medium">{summary.by_status?.open || 0}</span>
                                    <span className="text-muted-foreground ml-2">Resolved:</span>
                                    <span className="font-medium">{summary.by_status?.resolved || 0}</span>
                                </div>
                            </CardContent>
                        </Card>
                        <Card className="border-border bg-card">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    By Type
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="flex gap-2 text-sm">
                                    <span className="text-muted-foreground">Gaps:</span>
                                    <span className="font-medium">{summary.by_type?.gap || 0}</span>
                                    <span className="text-muted-foreground ml-2">Anomalies:</span>
                                    <span className="font-medium">{summary.by_type?.anomaly || 0}</span>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {/* Filters */}
                <Card className="border-border bg-card">
                    <CardHeader className="pb-3">
                        <div className="flex items-center gap-2">
                            <Filter className="h-4 w-4 text-muted-foreground" />
                            <CardTitle className="text-sm font-medium">Filters</CardTitle>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap gap-4">
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-muted-foreground">Status:</span>
                                <div className="flex gap-1">
                                    {["", "open", "resolved", "false_positive"].map((status) => (
                                        <Button
                                            key={status || "all"}
                                            variant={statusFilter === status ? "secondary" : "ghost"}
                                            size="sm"
                                            onClick={() => setStatusFilter(status)}
                                        >
                                            {status || "All"}
                                        </Button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-muted-foreground">Type:</span>
                                <div className="flex gap-1">
                                    {["", "gap", "anomaly", "archetype_mismatch"].map((type) => (
                                        <Button
                                            key={type || "all"}
                                            variant={typeFilter === type ? "secondary" : "ghost"}
                                            size="sm"
                                            onClick={() => setTypeFilter(type)}
                                        >
                                            {type ? getTypeLabel(type as FlagType) : "All"}
                                        </Button>
                                    ))}
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-muted-foreground">Severity:</span>
                                <div className="flex gap-1">
                                    {["", "critical", "warning", "info"].map((sev) => (
                                        <Button
                                            key={sev || "all"}
                                            variant={severityFilter === sev ? "secondary" : "ghost"}
                                            size="sm"
                                            onClick={() => setSeverityFilter(sev)}
                                        >
                                            {sev || "All"}
                                        </Button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Findings List */}
                <Card className="border-border bg-card">
                    <CardHeader>
                        <CardTitle>Findings</CardTitle>
                        <CardDescription>
                            {loading ? "Loading..." : `${findings.length} findings found`}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {loading ? (
                            <div className="flex items-center justify-center py-8">
                                <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : findings.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center">
                                <CheckCircle2 className="h-12 w-12 text-primary/50 mb-4" />
                                <h3 className="text-lg font-medium">No findings</h3>
                                <p className="text-muted-foreground text-sm mt-1">
                                    {statusFilter === "open"
                                        ? "No open issues found. Run an audit to check for new anomalies."
                                        : "No findings match the current filters."}
                                </p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {findings.map((finding) => {
                                    const TypeIcon = typeIcons[finding.flag_type] || AlertTriangle
                                    const StatusIcon = statusIcons[finding.status] || Clock

                                    return (
                                        <div
                                            key={finding.id}
                                            className={cn(
                                                "group flex items-start gap-4 rounded-lg border p-4 transition-colors",
                                                getSeverityColor(finding.severity),
                                                finding.status === "resolved" && "opacity-60"
                                            )}
                                        >
                                            <div className="mt-0.5 rounded-md bg-background/50 p-2">
                                                <TypeIcon className="h-4 w-4" />
                                            </div>
                                            <div className="flex-1 space-y-2">
                                                <div className="flex items-start justify-between gap-2">
                                                    <div>
                                                        <h4 className="font-medium">{finding.title}</h4>
                                                        <div className="flex items-center gap-2 mt-1">
                                                            <Badge variant="outline" className="text-xs">
                                                                {getTypeLabel(finding.flag_type)}
                                                            </Badge>
                                                            <Badge
                                                                variant="outline"
                                                                className={cn(
                                                                    "text-xs uppercase",
                                                                    finding.severity === "critical" && "border-destructive text-destructive",
                                                                    finding.severity === "warning" && "border-warning text-warning"
                                                                )}
                                                            >
                                                                {finding.severity}
                                                            </Badge>
                                                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                                                <StatusIcon className="h-3 w-3" />
                                                                {finding.status}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    {finding.status === "open" && (
                                                        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                onClick={() => handleResolveFinding(finding.id, "resolved")}
                                                            >
                                                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                                                Resolve
                                                            </Button>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                onClick={() => handleResolveFinding(finding.id, "false_positive")}
                                                            >
                                                                <XCircle className="h-3 w-3 mr-1" />
                                                                False Positive
                                                            </Button>
                                                        </div>
                                                    )}
                                                </div>
                                                {finding.description && (
                                                    <p className="text-sm text-muted-foreground">
                                                        {finding.description}
                                                    </p>
                                                )}
                                                {finding.recommendation && (
                                                    <div className="rounded-md bg-background/50 p-3 text-sm">
                                                        <span className="font-medium">Recommendation: </span>
                                                        {finding.recommendation}
                                                    </div>
                                                )}
                                                {finding.created_at && (
                                                    <p className="text-xs text-muted-foreground">
                                                        Detected: {new Date(finding.created_at).toLocaleString()}
                                                    </p>
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
