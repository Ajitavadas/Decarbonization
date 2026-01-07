"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight, FileQuestion, Zap, TrendingDown, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import type { AuditFinding, FlagType } from "@/types"

// Icon mapping for finding types
const typeIcons: Record<FlagType, typeof FileQuestion> = {
    gap: FileQuestion,
    anomaly: Zap,
    archetype_mismatch: TrendingDown,
}

export function DataGaps() {
    const router = useRouter()
    const [findings, setFindings] = useState<AuditFinding[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        const fetchFindings = async () => {
            try {
                setLoading(true)
                const response = await api.getAuditFindings({ status: "open", limit: 3 })
                setFindings(response.findings)
            } catch (err) {
                console.error("Failed to fetch findings:", err)
                // Don't redirect on error, just show empty state
                setError(err instanceof Error ? err.message : "Failed to load")
            } finally {
                setLoading(false)
            }
        }

        if (api.isAuthenticated()) {
            fetchFindings()
        }
    }, [])

    const getSeverityStyle = (severity: string) => {
        switch (severity) {
            case "critical":
                return "bg-destructive/10 text-destructive"
            case "warning":
                return "bg-warning/10 text-warning"
            default:
                return "bg-muted text-muted-foreground"
        }
    }

    const getTypeLabel = (type: FlagType) => {
        switch (type) {
            case "gap":
                return "Data Gap"
            case "anomaly":
                return "Anomaly"
            case "archetype_mismatch":
                return "Mismatch"
        }
    }

    return (
        <Card className="border-border bg-card">
            <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <CardTitle className="text-base font-medium">Data Gaps & Anomalies</CardTitle>
                        {findings.length > 0 && (
                            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs font-medium text-destructive-foreground">
                                {findings.length}
                            </span>
                        )}
                    </div>
                    <Link href="/anomalies">
                        <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
                            View all
                            <ArrowRight className="ml-1 h-3 w-3" />
                        </Button>
                    </Link>
                </div>
            </CardHeader>
            <CardContent className="space-y-3">
                {loading ? (
                    <div className="flex items-center justify-center py-6">
                        <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
                    </div>
                ) : error ? (
                    <div className="text-center py-6 text-sm text-muted-foreground">
                        <p>Unable to load findings</p>
                        <p className="text-xs mt-1">{error}</p>
                    </div>
                ) : findings.length === 0 ? (
                    <div className="text-center py-6 text-sm text-muted-foreground">
                        <FileQuestion className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p>No open issues detected</p>
                        <Link href="/anomalies">
                            <Button variant="outline" size="sm" className="mt-3">
                                Run Audit
                            </Button>
                        </Link>
                    </div>
                ) : (
                    findings.map((finding) => {
                        const Icon = typeIcons[finding.flag_type] || FileQuestion
                        return (
                            <div
                                key={finding.id}
                                className="group flex items-start gap-3 rounded-lg border border-border bg-secondary/50 p-3 transition-colors hover:bg-secondary"
                            >
                                <div
                                    className={cn(
                                        "mt-0.5 rounded-md p-1.5",
                                        getSeverityStyle(finding.severity)
                                    )}
                                >
                                    <Icon className="h-4 w-4" />
                                </div>
                                <div className="flex-1 space-y-1">
                                    <div className="flex items-center justify-between">
                                        <span className="text-sm font-medium text-foreground">{finding.title}</span>
                                        <span
                                            className={cn(
                                                "rounded-full px-2 py-0.5 text-[10px] font-medium uppercase",
                                                getSeverityStyle(finding.severity)
                                            )}
                                        >
                                            {finding.severity}
                                        </span>
                                    </div>
                                    <p className="text-xs text-muted-foreground">
                                        {getTypeLabel(finding.flag_type)}
                                    </p>
                                    {finding.description && (
                                        <p className="text-xs text-muted-foreground line-clamp-2">
                                            {finding.description}
                                        </p>
                                    )}
                                </div>
                            </div>
                        )
                    })
                )}
            </CardContent>
        </Card>
    )
}
