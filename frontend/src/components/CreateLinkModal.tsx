import React, { useState } from "react"
import { Plus } from "lucide-react"
import { LinkItem, createLink } from "@/lib/api"

interface CreateLinkModalProps {
  onCreated: (link: LinkItem) => void
  onError: (error: unknown) => void
}

export const CreateLinkModal: React.FC<CreateLinkModalProps> = ({ onCreated, onError }) => {
  const [url, setUrl] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)

    try {
      const link = await createLink(url)
      setUrl("")
      onCreated(link)
    } catch (err) {
      onError(err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-4 p-6 rounded-xl border border-border bg-card">
      <h2 className="text-lg font-semibold">Shorten a new link</h2>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row">
        <input
          type="url"
          placeholder="Paste long URL here"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 px-4 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          required
        />
        <button
          type="submit"
          disabled={isSubmitting}
          className="flex items-center justify-center gap-2 px-5 py-2 bg-primary text-primary-foreground font-medium rounded-lg text-sm hover:opacity-90 transition-opacity disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Plus className="h-4 w-4" />
          <span>{isSubmitting ? "Shortening..." : "Shorten"}</span>
        </button>
      </form>
    </div>
  )
}
