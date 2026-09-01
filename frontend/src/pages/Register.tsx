import React, { useState } from "react"
import { Link2 } from "lucide-react"
import { ThemeToggle } from "@/components/ThemeToggle"

export const Register: React.FC = () => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-background transition-colors duration-200">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-6 p-8 rounded-2xl border border-border bg-card shadow-lg">
        <div className="flex flex-col items-center text-center gap-2">
          <div className="p-3 rounded-full bg-primary/10 text-primary">
            <Link2 className="h-8 w-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Create your Account</h1>
          <p className="text-sm text-muted-foreground">
            Get started with Linklet URL management
          </p>
        </div>

        <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
              placeholder="you@example.com"
              required
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-input bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-colors"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full py-2.5 bg-primary text-primary-foreground font-medium rounded-lg text-sm hover:opacity-90 transition-opacity"
          >
            Create Account
          </button>
        </form>
      </div>
    </div>
  )
}
