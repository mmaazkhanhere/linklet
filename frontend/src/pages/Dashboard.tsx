import React from "react"
import { Navbar } from "@/components/Navbar"
import { AnalyticsCard } from "@/components/AnalyticsCard"
import { CreateLinkModal } from "@/components/CreateLinkModal"
import { LinkTable } from "@/components/LinkTable"

export const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <main className="container py-8 space-y-8 flex-1">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Link Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your shortened URLs and inspect real-time click metrics.
          </p>
        </div>

        <AnalyticsCard totalLinks={0} totalClicks={0} />
        <CreateLinkModal />
        <LinkTable />
      </main>
    </div>
  )
}
