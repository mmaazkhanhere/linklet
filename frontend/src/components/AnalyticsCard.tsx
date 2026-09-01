import React from "react"
import { Link as LinkIcon, MousePointerClick } from "lucide-react"

interface AnalyticsCardProps {
  totalLinks: number
  totalClicks: number
}

export const AnalyticsCard: React.FC<AnalyticsCardProps> = ({ totalLinks, totalClicks }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div className="flex items-center gap-4 p-5 rounded-xl border border-border bg-card">
        <div className="p-3 rounded-lg bg-primary/10 text-primary">
          <LinkIcon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase">Total Active Links</p>
          <p className="text-2xl font-bold">{totalLinks}</p>
        </div>
      </div>

      <div className="flex items-center gap-4 p-5 rounded-xl border border-border bg-card">
        <div className="p-3 rounded-lg bg-primary/10 text-primary">
          <MousePointerClick className="h-6 w-6" />
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase">Total Click Analytics</p>
          <p className="text-2xl font-bold">{totalClicks}</p>
        </div>
      </div>
    </div>
  )
}
