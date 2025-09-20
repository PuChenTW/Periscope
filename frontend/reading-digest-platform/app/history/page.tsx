import { AuthGuard } from "@/components/auth-guard"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DigestHistory } from "@/components/history/digest-history"
import { HistoryStats } from "@/components/history/history-stats"
import { HistoryFilters } from "@/components/history/history-filters"

export default function HistoryPage() {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-background">
        <DashboardHeader />

        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Digest History</h1>
              <p className="text-muted-foreground">View and search through your past daily reading digests</p>
            </div>

            {/* Stats */}
            <HistoryStats />

            {/* Main Content */}
            <div className="grid lg:grid-cols-4 gap-8">
              <div className="lg:col-span-1">
                <HistoryFilters />
              </div>
              <div className="lg:col-span-3">
                <DigestHistory />
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
