import React from "react"
import { AlertCircle } from "lucide-react"

export const NotFound: React.FC = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 text-center">
      <div className="p-4 rounded-full bg-destructive/10 text-destructive mb-4">
        <AlertCircle className="h-10 w-10" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight">404 - Page Not Found</h1>
      <p className="text-muted-foreground mt-2 max-w-sm">
        The link or page you are looking for does not exist or has been removed.
      </p>
    </div>
  )
}
