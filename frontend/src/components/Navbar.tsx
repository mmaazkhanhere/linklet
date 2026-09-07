import React from "react"
import { Link2, LogOut } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { ThemeToggle } from "@/components/ThemeToggle"
import { User, authTokenStorageKey } from "@/lib/api"

interface NavbarProps {
  user: User | null
}

export const Navbar: React.FC<NavbarProps> = ({ user }) => {
  const navigate = useNavigate()

  const handleSignOut = () => {
    localStorage.removeItem(authTokenStorageKey)
    navigate("/login", { replace: true })
  }

  return (
    <nav className="border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-2 font-bold text-xl tracking-tight text-primary">
          <Link2 className="h-6 w-6" />
          <span>Linklet</span>
        </div>
        <div className="flex items-center gap-4">
          {user ? (
            <span className="hidden text-sm text-muted-foreground sm:inline">{user.name}</span>
          ) : null}
          <ThemeToggle />
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    </nav>
  )
}
