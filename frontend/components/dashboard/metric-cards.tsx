"use client"

import { Card, CardContent } from "@/components/ui/card"
import { ArrowDown, ArrowUp, Flame, Factory, Truck, Cloud } from "lucide-react"
import { cn } from "@/lib/utils"

const metrics = [
  {
    title: "Total Emissions",
    value: "12,847",
    unit: "tCO₂e",
    change: -8.2,
    changeLabel: "vs last year",
    icon: Cloud,
    iconColor: "text-chart-1",
    iconBg: "bg-chart-1/10",
  },
  {
    title: "Scope 1",
    value: "3,421",
    unit: "tCO₂e",
    change: -12.5,
    changeLabel: "vs last year",
    icon: Flame,
    iconColor: "text-chart-5",
    iconBg: "bg-chart-5/10",
  },
  {
    title: "Scope 2",
    value: "6,892",
    unit: "tCO₂e",
    change: -5.3,
    changeLabel: "vs last year",
    icon: Factory,
    iconColor: "text-chart-2",
    iconBg: "bg-chart-2/10",
  },
  {
    title: "Scope 3",
    value: "2,534",
    unit: "tCO₂e",
    change: 2.1,
    changeLabel: "vs last year",
    icon: Truck,
    iconColor: "text-chart-3",
    iconBg: "bg-chart-3/10",
  },
]

export function MetricCards() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <Card key={metric.title} className="border-border bg-card">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold text-foreground">{metric.value}</span>
                  <span className="text-sm text-muted-foreground">{metric.unit}</span>
                </div>
              </div>
              <div className={cn("rounded-lg p-2", metric.iconBg)}>
                <metric.icon className={cn("h-5 w-5", metric.iconColor)} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-1">
              {metric.change < 0 ? (
                <ArrowDown className="h-4 w-4 text-primary" />
              ) : (
                <ArrowUp className="h-4 w-4 text-destructive" />
              )}
              <span className={cn("text-sm font-medium", metric.change < 0 ? "text-primary" : "text-destructive")}>
                {Math.abs(metric.change)}%
              </span>
              <span className="text-sm text-muted-foreground">{metric.changeLabel}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
