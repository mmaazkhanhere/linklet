import React, { useState } from "react"
import { Plus } from "lucide-react"

export const CreateLinkModal: React.FC = () => {
  const [url, setUrl] = useState("")

  return (
    <div className="flex flex-col gap-4 p-6 rounded-xl border border-border bg-card">
      <h2 className="text-lg font-semibold">Shorten a new link</h2>
      <form onSubmit={(e) => e.preventDefault()} className="flex gap-3">
        <input
          type="url"
          placeholder="Paste long URL here (e.g. https://example.com/very-long-path)"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="flex-1 px-4 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          required
        />
        <button
          type="submit"
          className="flex items-center gap-2 px-5 py-2 bg-primary text-primary-foreground font-medium rounded-lg text-sm hover:opacity-90 transition-opacity"
        >
          <Plus className="h-4 w-4" />
          <span>Shorten</span>
        </button>
      </form>
    </div>
  )
}
