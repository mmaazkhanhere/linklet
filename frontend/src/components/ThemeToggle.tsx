import React from "react"
import { Moon, Sun, Laptop } from "lucide-react"
import { useTheme } from "@/context/ThemeProvider"

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex items-center gap-1 p-1 bg-muted rounded-lg border border-border">
      <button
        onClick={() => setTheme("light")}
        className={`p-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
          theme === "light"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        title="Light Mode"
      >
        <Sun className="h-4 w-4" />
        <span className="sr-only sm:not-sr-only">Light</span>
      </button>

      <button
        onClick={() => setTheme("dark")}
        className={`p-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
          theme === "dark"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        title="Dark Mode"
      >
        <Moon className="h-4 w-4" />
        <span className="sr-only sm:not-sr-only">Dark</span>
      </button>

      <button
        onClick={() => setTheme("system")}
        className={`p-1.5 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
          theme === "system"
            ? "bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        }`}
        title="System Preference"
      >
        <Laptop className="h-4 w-4" />
        <span className="sr-only sm:not-sr-only">System</span>
      </button>
    </div>
  )
}
