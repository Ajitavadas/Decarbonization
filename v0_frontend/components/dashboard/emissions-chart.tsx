"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { fetchDashboardData } from "@/lib/api"

export function EmissionsChart() {
  const [chartData, setChartData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchDashboardData()
        if (result.monthly_trend) {
          setChartData(result.monthly_trend)
        }
      } catch (err) {
        console.error("Failed to load trend data:", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">Emissions Over Time</CardTitle>
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-chart-5" />
              <span className="text-muted-foreground">Scope 1</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-chart-2" />
              <span className="text-muted-foreground">Scope 2</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-chart-3" />
              <span className="text-muted-foreground">Scope 3</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          {loading ? (
            <div className="flex h-full w-full items-center justify-center">
              <span className="text-muted-foreground">Loading...</span>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="scope1Gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.70 0.15 30)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="oklch(0.70 0.15 30)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="scope2Gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.65 0.15 200)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="oklch(0.65 0.15 200)" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="scope3Gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="oklch(0.75 0.12 85)" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="oklch(0.75 0.12 85)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="oklch(0.28 0.008 240)" vertical={false} />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "oklch(0.65 0 0)", fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "oklch(0.65 0 0)", fontSize: 12 }}
                  tickFormatter={(value) => `${value}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "oklch(0.16 0.005 240)",
                    border: "1px solid oklch(0.28 0.008 240)",
                    borderRadius: "8px",
                    color: "oklch(0.95 0 0)",
                  }}
                  labelStyle={{ color: "oklch(0.95 0 0)" }}
                />
                <Area
                  type="monotone"
                  dataKey="Scope 1"
                  stackId="1"
                  stroke="oklch(0.70 0.15 30)"
                  fill="url(#scope1Gradient)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="Scope 2"
                  stackId="1"
                  stroke="oklch(0.65 0.15 200)"
                  fill="url(#scope2Gradient)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="Scope 3"
                  stackId="1"
                  stroke="oklch(0.75 0.12 85)"
                  fill="url(#scope3Gradient)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
