"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts"

interface ScopeBreakdownProps {
    scope1?: number
    scope2?: number
    scope3?: number
}

export function ScopeBreakdown({ scope1, scope2, scope3 }: ScopeBreakdownProps) {
    const data = [
        { name: "Scope 1 - Direct", value: scope1 || 3421, color: "#f97316" },
        { name: "Scope 2 - Indirect", value: scope2 || 6892, color: "#3b82f6" },
        { name: "Scope 3 - Value Chain", value: scope3 || 2534, color: "#eab308" },
    ]

    const total = data.reduce((acc, item) => acc + item.value, 0)

    return (
        <Card className="border-border bg-card">
            <CardHeader className="pb-2">
                <CardTitle className="text-base font-medium">Scope Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="flex flex-col items-center">
                    <div className="relative h-[200px] w-[200px]">
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
                                        backgroundColor: "#1a1a2e",
                                        border: "1px solid #333347",
                                        borderRadius: "8px",
                                        color: "#f2f2f2",
                                    }}
                                    formatter={(value: number) => [`${value.toLocaleString()} tCO₂e`, ""]}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                        {/* Center Text */}
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-2xl font-bold text-foreground">{(total / 1000).toFixed(1)}k</span>
                            <span className="text-xs text-muted-foreground">tCO₂e</span>
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="mt-4 space-y-2 w-full">
                        {data.map((item) => (
                            <div key={item.name} className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                                    <span className="text-sm text-muted-foreground">{item.name}</span>
                                </div>
                                <span className="text-sm font-medium text-foreground">{((item.value / total) * 100).toFixed(1)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
