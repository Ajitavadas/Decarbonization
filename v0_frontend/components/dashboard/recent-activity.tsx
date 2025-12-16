"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight, Check, FileUp, MessageSquare, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"

const activities = [
  {
    id: 1,
    type: "upload",
    title: "Invoice Processed",
    description: "Electricity invoice for SF Office automatically processed",
    time: "2 min ago",
    icon: FileUp,
    iconColor: "text-primary",
  },
  {
    id: 2,
    type: "calculation",
    title: "Emissions Calculated",
    description: "Q4 2024 Scope 2 emissions updated for all facilities",
    time: "15 min ago",
    icon: RefreshCw,
    iconColor: "text-chart-2",
  },
  {
    id: 3,
    type: "copilot",
    title: "Copilot Response",
    description: "Estimated missing fleet data using industry benchmarks",
    time: "1 hour ago",
    icon: MessageSquare,
    iconColor: "text-chart-4",
  },
  {
    id: 4,
    type: "verification",
    title: "Data Verified",
    description: "User confirmed heating data for NYC HQ",
    time: "3 hours ago",
    icon: Check,
    iconColor: "text-primary",
  },
]

export function RecentActivity() {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">Recent Activity</CardTitle>
          <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
            View all
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="relative space-y-4">
          {/* Timeline line */}
          <div className="absolute left-[15px] top-2 h-[calc(100%-16px)] w-px bg-border" />

          {activities.map((activity) => (
            <div key={activity.id} className="relative flex items-start gap-3 pl-8">
              {/* Timeline dot */}
              <div className="absolute left-0 top-1 flex h-[30px] w-[30px] items-center justify-center rounded-full border border-border bg-card">
                <activity.icon className={cn("h-4 w-4", activity.iconColor)} />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">{activity.title}</span>
                  <span className="text-xs text-muted-foreground">{activity.time}</span>
                </div>
                <p className="text-xs text-muted-foreground">{activity.description}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
