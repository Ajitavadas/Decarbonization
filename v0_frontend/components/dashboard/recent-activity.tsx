"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { fetchRecentActivity } from "@/lib/api"

export function RecentActivity() {
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchRecentActivity()
        setActivities(data)
      } catch (err) {
        console.error("Failed to load activity:", err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Card className="border-border bg-card">
      <CardHeader>
        <CardTitle className="text-base font-medium">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading activity...</p>
          ) : activities.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent activity detected.</p>
          ) : (
            activities.map((activity) => (
              <div key={activity.id} className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium text-foreground">{activity.description}</p>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-[10px] uppercase">
                      {activity.scope}
                    </Badge>
                    <span className="text-xs text-muted-foreground">{activity.category}</span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-foreground">{(activity.amount || 0).toFixed(2)} t</p>
                  <p className="text-[10px] text-muted-foreground">
                    {new Date(activity.date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
