"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight, FileQuestion, Zap } from "lucide-react"
import { cn } from "@/lib/utils"

const gaps = [
  {
    id: 1,
    type: "missing",
    severity: "high",
    title: "Missing Heating Data",
    facility: "NYC Headquarters",
    description: "Scope 1 natural gas consumption data missing for Oct-Dec 2024",
    icon: FileQuestion,
  },
  {
    id: 2,
    type: "anomaly",
    severity: "medium",
    title: "Electricity Spike Detected",
    facility: "LA Distribution Center",
    description: "2.3σ deviation from baseline - 40% increase in consumption",
    icon: Zap,
  },
  {
    id: 3,
    type: "missing",
    severity: "low",
    title: "Incomplete Travel Records",
    facility: "Global",
    description: "Business travel data partially missing for Q4 2024",
    icon: FileQuestion,
  },
]

export function DataGaps() {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-base font-medium">Data Gaps & Anomalies</CardTitle>
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs font-medium text-destructive-foreground">
              {gaps.length}
            </span>
          </div>
          <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
            View all
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {gaps.map((gap) => (
          <div
            key={gap.id}
            className="group flex items-start gap-3 rounded-lg border border-border bg-secondary/50 p-3 transition-colors hover:bg-secondary"
          >
            <div
              className={cn(
                "mt-0.5 rounded-md p-1.5",
                gap.severity === "high" && "bg-destructive/10 text-destructive",
                gap.severity === "medium" && "bg-warning/10 text-warning",
                gap.severity === "low" && "bg-muted text-muted-foreground",
              )}
            >
              <gap.icon className="h-4 w-4" />
            </div>
            <div className="flex-1 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-foreground">{gap.title}</span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[10px] font-medium uppercase",
                    gap.severity === "high" && "bg-destructive/10 text-destructive",
                    gap.severity === "medium" && "bg-warning/10 text-warning",
                    gap.severity === "low" && "bg-muted text-muted-foreground",
                  )}
                >
                  {gap.severity}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">{gap.facility}</p>
              <p className="text-xs text-muted-foreground">{gap.description}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
