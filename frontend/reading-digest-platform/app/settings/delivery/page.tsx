import { AuthGuard } from "@/components/auth-guard"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DeliverySettings } from "@/components/settings/delivery-settings"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function DeliverySettingsPage() {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-background">
        <DashboardHeader />

        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center gap-4 mb-8">
              <Button variant="ghost" size="sm" asChild>
                <Link href="/settings">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Settings
                </Link>
              </Button>
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">Delivery Settings</h1>
                <p className="text-muted-foreground">Configure when and how you receive your daily digest</p>
              </div>
            </div>

            <DeliverySettings />
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
