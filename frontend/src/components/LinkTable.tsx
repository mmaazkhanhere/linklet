import React from "react"

export interface LinkItem {
  id: string
  target_url: string
  short_code: string
  short_url: string
  clicks: number
  created_at: string
}

export const LinkTable: React.FC = () => {
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
          <tr>
            <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
              No links created yet.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}
