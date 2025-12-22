"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"
import { fetchDashboardData } from "@/lib/api"

export function ScopeBreakdown() {
  const [data, setData] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const result = await fetchDashboardData()
        const breakdown = [
          { name: "Scope 1 - Direct", value: result.scope_breakdown?.["Scope 1"] ?? 0, color: "oklch(0.70 0.15 30)" },
          { name: "Scope 2 - Indirect", value: result.scope_breakdown?.["Scope 2"] ?? 0, color: "oklch(0.65 0.15 200)" },
          { name: "Scope 3 - Value Chain", value: result.scope_breakdown?.["Scope 3"] ?? 0, color: "oklch(0.75 0.12 85)" },
        ]
        setData(breakdown)
        setTotal(breakdown.reduce((acc, item) => acc + item.value, 0))
      } catch (err) {
        console.error("Failed to load scope breakdown:", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">Scope Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center">
          <div className="relative h-[200px] w-[200px]">
            {loading ? (
              <div className="flex h-full w-full items-center justify-center">
                <span className="text-muted-foreground">Loading...</span>
              </div>
            ) : (
              <>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                      strokeWidth={0}
                    >
                      {data.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "oklch(0.16 0.005 240)",
                        border: "1px solid oklch(0.28 0.008 240)",
                        borderRadius: "8px",
                        color: "oklch(0.95 0 0)",
                      }}
                      formatter={(value: number) => [`${value.toLocaleString()} tCO₂e`, ""]}
                    />
                  </PieChart>
                </ResponsiveContainer>
                {/* Center Text */}
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-foreground">
                    {total > 1000 ? `${(total / 1000).toFixed(1)}k` : total.toFixed(0)}
                  </span>
                  <span className="text-xs text-muted-foreground">tCO₂e</span>
                </div>
              </>
            )}
          </div>

          {/* Legend */}
          <div className="mt-4 space-y-2 w-full">
            {data.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-muted-foreground">{item.name}</span>
                </div>
                <span className="text-sm font-medium text-foreground">
                  {total > 0 ? `${((item.value / total) * 100).toFixed(1)}%` : "0%"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
