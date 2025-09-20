import { AuthGuard } from "@/components/auth-guard"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { StatusOverview } from "@/components/dashboard/status-overview"
import { RecentDigests } from "@/components/dashboard/recent-digests"
import { QuickActions } from "@/components/dashboard/quick-actions"
import { UpcomingDelivery } from "@/components/dashboard/upcoming-delivery"

export default function DashboardPage() {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-background">
        <DashboardHeader />

        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Welcome Section */}
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back!</h1>
              <p className="text-muted-foreground">Here's your daily reading digest overview</p>
            </div>

            {/* Status Overview */}
            <StatusOverview />

            {/* Main Content Grid */}
            <div className="grid lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2 space-y-8">
                <RecentDigests />
              </div>
              <div className="space-y-8">
                <UpcomingDelivery />
                <QuickActions />
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
