import { AuthGuard } from "@/components/auth-guard"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { SourcesGrid } from "@/components/sources/sources-grid"
import { AddSourceForm } from "@/components/sources/add-source-form"
import { SourcesStats } from "@/components/sources/sources-stats"

export default function SourcesPage() {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-background">
        <DashboardHeader />

        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Header */}
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Manage Sources</h1>
              <p className="text-muted-foreground">Add, remove, and configure your news sources and RSS feeds</p>
            </div>

            {/* Stats */}
            <SourcesStats />

            {/* Main Content */}
            <div className="grid lg:grid-cols-3 gap-8">
              <div className="lg:col-span-2">
                <SourcesGrid />
              </div>
              <div>
                <AddSourceForm />
              </div>
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
