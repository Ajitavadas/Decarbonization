"use client"

import { useEffect, useState } from "react"
import { ArrowDownRight, ArrowUpRight, BarChart3, Cloud, Factory, Zap } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { fetchDashboardData } from "@/lib/api"

export function MetricCards() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchDashboardData()
        setData(result)
      } catch (err) {
        console.error("Failed to load metrics:", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const metrics = [
    {
      title: "Total Emissions",
      value: loading ? "..." : `${data?.total_emissions_tonnes ?? 0} tCO2e`,
      change: "-4.5%",
      trend: "down",
      icon: Cloud,
      description: "YTD vs previous year",
    },
    {
      title: "Scope 1",
      value: loading ? "..." : `${data?.scope_breakdown?.["Scope 1"] ?? 0} tCO2e`,
      change: "+2.1%",
      trend: "up",
      icon: Factory,
      description: "Direct emissions",
    },
    {
      title: "Scope 2",
      value: loading ? "..." : `${data?.scope_breakdown?.["Scope 2"] ?? 0} tCO2e`,
      change: "-12.4%",
      trend: "down",
      icon: Zap,
      description: "Indirect energy",
    },
    {
      title: "Scope 3",
      value: loading ? "..." : `${data?.scope_breakdown?.["Scope 3"] ?? 0} tCO2e`,
      change: "-0.8%",
      trend: "down",
      icon: BarChart3,
      description: "Value chain emissions",
    },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <Card key={metric.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
            <metric.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metric.value}</div>
            <div className="flex items-center pt-1">
              {metric.trend === "up" ? (
                <ArrowUpRight className="mr-1 h-4 w-4 text-destructive" />
              ) : (
                <ArrowDownRight className="mr-1 h-4 w-4 text-emerald-500" />
              )}
              <span className={metric.trend === "up" ? "text-destructive" : "text-emerald-500"}>{metric.change}</span>
              <span className="ml-1 text-xs text-muted-foreground">{metric.description}</span>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
