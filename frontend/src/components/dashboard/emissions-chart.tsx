"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"

const data = [
    { month: "Jan", scope1: 320, scope2: 580, scope3: 210 },
    { month: "Feb", scope1: 300, scope2: 560, scope3: 195 },
    { month: "Mar", scope1: 340, scope2: 620, scope3: 230 },
    { month: "Apr", scope1: 280, scope2: 540, scope3: 180 },
    { month: "May", scope1: 290, scope2: 550, scope3: 200 },
    { month: "Jun", scope1: 310, scope2: 590, scope3: 220 },
    { month: "Jul", scope1: 330, scope2: 610, scope3: 240 },
    { month: "Aug", scope1: 300, scope2: 570, scope3: 210 },
    { month: "Sep", scope1: 270, scope2: 520, scope3: 190 },
    { month: "Oct", scope1: 260, scope2: 500, scope3: 180 },
    { month: "Nov", scope1: 250, scope2: 480, scope3: 170 },
    { month: "Dec", scope1: 240, scope2: 470, scope3: 165 },
]

export function EmissionsChart() {
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
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="scope1Gradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#f97316" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#f97316" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="scope2Gradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="scope3Gradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#eab308" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#eab308" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333347" vertical={false} />
                            <XAxis
                                dataKey="month"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: "#8c8c8c", fontSize: 12 }}
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: "#8c8c8c", fontSize: 12 }}
                                tickFormatter={(value) => `${value}`}
                            />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: "#1a1a2e",
                                    border: "1px solid #333347",
                                    borderRadius: "8px",
                                    color: "#f2f2f2",
                                }}
                                labelStyle={{ color: "#f2f2f2" }}
                            />
                            <Area
                                type="monotone"
                                dataKey="scope1"
                                stackId="1"
                                stroke="#f97316"
                                fill="url(#scope1Gradient)"
                                strokeWidth={2}
                            />
                            <Area
                                type="monotone"
                                dataKey="scope2"
                                stackId="1"
                                stroke="#3b82f6"
                                fill="url(#scope2Gradient)"
                                strokeWidth={2}
                            />
                            <Area
                                type="monotone"
                                dataKey="scope3"
                                stackId="1"
                                stroke="#eab308"
                                fill="url(#scope3Gradient)"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </CardContent>
        </Card>
    )
}
