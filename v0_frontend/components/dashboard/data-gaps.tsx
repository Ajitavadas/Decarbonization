"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle, Calendar, MapPin } from "lucide-react"
import { fetchGaps } from "@/lib/api"

export function DataGaps() {
  const [gaps, setGaps] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchGaps()
        setGaps(data)
      } catch (err) {
        console.error("Failed to load gaps:", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-base font-medium">Data Quality Gaps</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {loading ? (
            <p className="text-sm text-muted-foreground">Analyzing data for gaps...</p>
          ) : gaps.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center">
              <div className="rounded-full bg-emerald-500/10 p-3">
                <AlertCircle className="h-6 w-6 text-emerald-500" />
              </div>
              <h3 className="mt-2 text-sm font-medium">No gaps detected</h3>
              <p className="max-w-[150px] text-xs text-muted-foreground">Your data coverage looks complete for the past year.</p>
            </div>
          ) : (
            gaps.map((gap, index) => (
              <div key={index} className="flex items-start gap-3 rounded-lg border border-border bg-secondary/30 p-3">
                <AlertCircle className={`mt-0.5 h-4 w-4 ${gap.severity === 'high' ? 'text-destructive' : 'text-amber-500'}`} />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-foreground">{gap.description}</p>
                  <div className="flex flex-wrap gap-2 text-[10px] text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      {(gap.details?.missing_months || []).join(", ")}
                    </span>
                    {gap.details?.category && (
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {gap.details.category}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
