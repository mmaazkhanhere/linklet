import React, { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { Navbar } from "@/components/Navbar"
import { AnalyticsCard } from "@/components/AnalyticsCard"
import { CreateLinkModal } from "@/components/CreateLinkModal"
import { LinkTable } from "@/components/LinkTable"
import {
  LinkItem,
  User,
  authTokenStorageKey,
  getApiErrorMessage,
  getCurrentUser,
  listLinks,
} from "@/lib/api"

export const Dashboard: React.FC = () => {
  const [user, setUser] = useState<User | null>(null)
  const [links, setLinks] = useState<LinkItem[]>([])
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  const loadDashboard = async () => {
    setError("")

    try {
      const [currentUser, linkList] = await Promise.all([getCurrentUser(), listLinks()])
      setUser(currentUser)
      setLinks(linkList.items)
    } catch (err) {
      localStorage.removeItem(authTokenStorageKey)
      navigate("/login", { replace: true })
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    void loadDashboard()
  }, [])

  const handleLinkCreated = (link: LinkItem) => {
    setLinks((currentLinks) => [link, ...currentLinks])
  }

  const handleLinkError = (err: unknown) => {
    setError(getApiErrorMessage(err, "Unable to create link."))
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar user={user} />
      <main className="container py-8 space-y-8 flex-1">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Link Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your shortened URLs and inspect real-time click metrics.
          </p>
        </div>

        {isLoading ? (
          <div className="rounded-lg border border-border bg-card p-6 text-sm text-muted-foreground">
            Loading dashboard...
          </div>
        ) : (
          <>
            {error ? <p className="text-sm text-destructive">{error}</p> : null}
            <AnalyticsCard
              totalLinks={links.length}
              totalClicks={links.reduce((total, link) => total + link.total_clicks, 0)}
            />
            <CreateLinkModal onCreated={handleLinkCreated} onError={handleLinkError} />
            <LinkTable links={links} />
          </>
        )}
      </main>
    </div>
  )
}
