import React from "react"
import { ExternalLink } from "lucide-react"
import { LinkItem } from "@/lib/api"

const redirectBaseUrl =
  import.meta.env.VITE_REDIRECT_BASE_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : window.location.origin)

const redirectUrl = (shortCode: string) => `${redirectBaseUrl}/${shortCode}`

interface LinkTableProps {
  links: LinkItem[]
}

export const LinkTable: React.FC<LinkTableProps> = ({ links }) => {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-border bg-card">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-border bg-muted/50 text-muted-foreground uppercase text-xs">
          <tr>
            <th className="px-4 py-3">Short Link</th>
            <th className="px-4 py-3">Destination URL</th>
            <th className="px-4 py-3">Clicks</th>
            <th className="px-4 py-3">Created</th>
            <th className="px-4 py-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {links.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                No links created yet.
              </td>
            </tr>
          ) : (
            links.map((link) => (
              <tr key={link.link_id}>
                <td className="px-4 py-3">
                  <a
                    href={redirectUrl(link.short_code)}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-primary hover:underline"
                  >
                    {link.short_code}
                  </a>
                </td>
                <td className="max-w-md truncate px-4 py-3 text-muted-foreground">
                  {link.destination_url}
                </td>
                <td className="px-4 py-3">{link.total_clicks}</td>
                <td className="px-4 py-3 text-muted-foreground">
                  {new Date(link.created_on).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <a
                    href={redirectUrl(link.short_code)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:text-foreground"
                    aria-label={`Open ${link.short_code}`}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
