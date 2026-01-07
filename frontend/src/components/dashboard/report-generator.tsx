"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { FileText, Download, Loader2, FileJson } from "lucide-react"
import { api } from "@/lib/api"

interface ReportGeneratorProps {
    projectId: string
    projectName: string
    hasActivities: boolean
}

export function ReportGenerator({ projectId, projectName, hasActivities }: ReportGeneratorProps) {
    const [loadingPDF, setLoadingPDF] = useState(false)
    const [loadingHTML, setLoadingHTML] = useState(false)
    const [error, setError] = useState("")

    const handleDownloadReport = async (format: 'pdf' | 'html') => {
        if (!hasActivities) {
            setError("Please add activities before generating a report")
            return
        }

        const isHTML = format === 'html'
        if (isHTML) {
            setLoadingHTML(true)
        } else {
            setLoadingPDF(true)
        }
        setError("")

        try {
            const blob = await api.generateReport(projectId, format)
            
            // Create download link
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement("a")
            link.href = url
            link.download = `${projectName.replace(/\s+/g, "_")}_report.${format === 'pdf' ? 'pdf' : 'html'}`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to generate report")
        } finally {
            if (isHTML) {
                setLoadingHTML(false)
            } else {
                setLoadingPDF(false)
            }
        }
    }

    return (
        <Card className="border-border bg-card">
            <CardHeader>
                <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    <div>
                        <CardTitle>Generate Report</CardTitle>
                        <CardDescription>
                            Download comprehensive carbon footprint reports
                        </CardDescription>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {error && (
                    <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                        {error}
                    </div>
                )}

                {!hasActivities && (
                    <div className="rounded-md bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-400">
                        Add emission activities to your project before generating a report
                    </div>
                )}

                <div className="grid gap-3 sm:grid-cols-2">
                    {/* PDF Report Button */}
                    <Button
                        onClick={() => handleDownloadReport('pdf')}
                        disabled={loadingPDF || !hasActivities}
                        className="w-full"
                        variant="default"
                    >
                        {loadingPDF ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Generating PDF...
                            </>
                        ) : (
                            <>
                                <Download className="mr-2 h-4 w-4" />
                                Download PDF Report
                            </>
                        )}
                    </Button>

                    {/* HTML Report Button */}
                    <Button
                        onClick={() => handleDownloadReport('html')}
                        disabled={loadingHTML || !hasActivities}
                        className="w-full"
                        variant="outline"
                    >
                        {loadingHTML ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Generating HTML...
                            </>
                        ) : (
                            <>
                                <FileJson className="mr-2 h-4 w-4" />
                                Download HTML Report
                            </>
                        )}
                    </Button>
                </div>

                <div className="grid gap-2 text-xs text-muted-foreground">
                    <div className="flex items-start gap-2">
                        <span className="mt-1">📊</span>
                        <span>
                            <strong>PDF Format:</strong> Professional PDF with visualizations, charts, and formatted tables
                        </span>
                    </div>
                    <div className="flex items-start gap-2">
                        <span className="mt-1">🌐</span>
                        <span>
                            <strong>HTML Format:</strong> Interactive HTML report with embedded charts and sortable tables
                        </span>
                    </div>
                </div>

                <div className="rounded-md bg-secondary/30 p-3 text-xs text-muted-foreground space-y-1">
                    <p><strong>Report includes:</strong></p>
                    <ul className="list-inside space-y-1 ml-2">
                        <li>✓ Executive summary with total emissions</li>
                        <li>✓ Scope breakdown (1, 2, 3) with percentages</li>
                        <li>✓ Activity type analysis</li>
                        <li>✓ Visualizations and charts</li>
                        <li>✓ Detailed activity list with all emissions data</li>
                    </ul>
                </div>
            </CardContent>
        </Card>
    )
}
