import React from "react"
import { ThemeProvider } from "@/context/ThemeProvider"
import { Dashboard } from "@/pages/Dashboard"

export const App: React.FC = () => {
  return (
    <ThemeProvider defaultTheme="system" storageKey="linklet-ui-theme">
      <Dashboard />
    </ThemeProvider>
  )
}

export default App
