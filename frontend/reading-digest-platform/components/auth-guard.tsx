"use client"

import type React from "react"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

interface AuthGuardProps {
  children: React.ReactNode
  requireAuth?: boolean
}

export function AuthGuard({ children, requireAuth = true }: AuthGuardProps) {
  return <>{children}</>

  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const router = useRouter()

  useEffect(() => {
    // Simulate auth check - replace with actual auth logic
    const checkAuth = () => {
      const token = localStorage.getItem("auth_token")
      setIsAuthenticated(!!token)
    }

    checkAuth()
  }, [])

  useEffect(() => {
    if (isAuthenticated === null) return // Still loading

    if (requireAuth && !isAuthenticated) {
      router.push("/login")
    } else if (!requireAuth && isAuthenticated) {
      router.push("/dashboard")
    }
  }, [isAuthenticated, requireAuth, router])

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (requireAuth && !isAuthenticated) {
    return null // Will redirect to login
  }

  if (!requireAuth && isAuthenticated) {
    return null // Will redirect to dashboard
  }

  return <>{children}</>
}
