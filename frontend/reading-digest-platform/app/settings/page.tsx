import { AuthGuard } from "@/components/auth-guard"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { SettingsNav } from "@/components/settings/settings-nav"
import { DeliverySettings } from "@/components/settings/delivery-settings"
import { InterestSettings } from "@/components/settings/interest-settings"
import { AccountSettings } from "@/components/settings/account-settings"
import { NotificationSettings } from "@/components/settings/notification-settings"

export default function SettingsPage() {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-background">
        <DashboardHeader />

        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
              <p className="text-muted-foreground">Manage your digest preferences and account settings</p>
            </div>

            {/* Settings Content */}
            <div className="grid lg:grid-cols-4 gap-8">
              <div className="lg:col-span-1">
                <SettingsNav />
              </div>
              <div className="lg:col-span-3 space-y-8">
                <DeliverySettings />
                <InterestSettings />
                <NotificationSettings />
                <AccountSettings />
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
