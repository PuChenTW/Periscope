"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Clock, Brain, Bell, User, Shield, CreditCard } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const SETTINGS_ITEMS = [
  {
    id: "delivery",
    label: "Delivery Settings",
    icon: Clock,
    href: "#delivery",
    description: "Schedule and format",
  },
  {
    id: "interests",
    label: "Interest Profile",
    icon: Brain,
    href: "#interests",
    description: "Keywords and topics",
  },
  {
    id: "notifications",
    label: "Notifications",
    icon: Bell,
    href: "#notifications",
    description: "Email preferences",
  },
  {
    id: "account",
    label: "Account Settings",
    icon: User,
    href: "#account",
    description: "Profile and security",
  },
  {
    id: "privacy",
    label: "Privacy & Data",
    icon: Shield,
    href: "#privacy",
    description: "Data management",
  },
  {
    id: "billing",
    label: "Billing",
    icon: CreditCard,
    href: "#billing",
    description: "Subscription and payments",
  },
]

export function SettingsNav() {
  const pathname = usePathname()

  return (
    <Card>
      <CardContent className="p-0">
        <nav className="space-y-1">
          {SETTINGS_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = pathname.includes(item.id)

            return (
              <Link
                key={item.id}
                href={item.href}
                className={cn(
                  "flex items-start gap-3 px-4 py-3 text-sm transition-colors hover:bg-muted/50",
                  isActive && "bg-primary/10 text-primary border-r-2 border-primary",
                )}
              >
                <Icon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium">{item.label}</div>
                  <div className="text-xs text-muted-foreground">{item.description}</div>
                </div>
              </Link>
            )
          })}
        </nav>
      </CardContent>
    </Card>
  )
}
