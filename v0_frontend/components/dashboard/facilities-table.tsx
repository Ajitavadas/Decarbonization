"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ArrowRight, ArrowUpRight, Building2, MapPin } from "lucide-react"
import { cn } from "@/lib/utils"

const facilities = [
  {
    id: 1,
    name: "NYC Headquarters",
    location: "New York, USA",
    type: "Office",
    emissions: 2840,
    trend: -12.3,
    status: "complete",
  },
  {
    id: 2,
    name: "LA Distribution Center",
    location: "Los Angeles, USA",
    type: "Warehouse",
    emissions: 4120,
    trend: 5.2,
    status: "anomaly",
  },
  {
    id: 3,
    name: "SF Innovation Hub",
    location: "San Francisco, USA",
    type: "Office",
    emissions: 1560,
    trend: -8.7,
    status: "complete",
  },
  {
    id: 4,
    name: "London Office",
    location: "London, UK",
    type: "Office",
    emissions: 2180,
    trend: -3.1,
    status: "incomplete",
  },
  {
    id: 5,
    name: "Berlin Manufacturing",
    location: "Berlin, Germany",
    type: "Factory",
    emissions: 5640,
    trend: -15.8,
    status: "complete",
  },
]

export function FacilitiesTable() {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium">Facilities Overview</CardTitle>
          <Button variant="ghost" size="sm" className="text-xs text-muted-foreground hover:text-foreground">
            Manage facilities
            <ArrowRight className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-muted-foreground">Facility</TableHead>
              <TableHead className="text-muted-foreground">Type</TableHead>
              <TableHead className="text-right text-muted-foreground">Emissions (tCO₂e)</TableHead>
              <TableHead className="text-right text-muted-foreground">YoY Change</TableHead>
              <TableHead className="text-muted-foreground">Status</TableHead>
              <TableHead className="text-right text-muted-foreground"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {facilities.map((facility) => (
              <TableRow key={facility.id} className="border-border">
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-secondary">
                      <Building2 className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="font-medium text-foreground">{facility.name}</p>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        {facility.location}
                      </div>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="secondary" className="font-normal">
                    {facility.type}
                  </Badge>
                </TableCell>
                <TableCell className="text-right font-medium text-foreground">
                  {facility.emissions.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <span className={cn("font-medium", facility.trend < 0 ? "text-primary" : "text-destructive")}>
                    {facility.trend > 0 ? "+" : ""}
                    {facility.trend}%
                  </span>
                </TableCell>
                <TableCell>
                  <Badge
                    variant="outline"
                    className={cn(
                      "font-normal",
                      facility.status === "complete" && "border-primary/50 bg-primary/10 text-primary",
                      facility.status === "incomplete" && "border-warning/50 bg-warning/10 text-warning",
                      facility.status === "anomaly" && "border-destructive/50 bg-destructive/10 text-destructive",
                    )}
                  >
                    {facility.status === "complete" && "Complete"}
                    {facility.status === "incomplete" && "Incomplete"}
                    {facility.status === "anomaly" && "Anomaly"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <ArrowUpRight className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
