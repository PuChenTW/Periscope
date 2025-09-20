import { AuthGuard } from "@/components/auth-guard"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { AddSourceForm } from "@/components/sources/add-source-form"
import { PopularSources } from "@/components/sources/popular-sources"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function AddSourcePage() {
  return (
    <AuthGuard requireAuth={true}>
      <div className="min-h-screen bg-background">
        <DashboardHeader />

        <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" asChild>
                <Link href="/sources">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to Sources
                </Link>
              </Button>
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-2">Add New Source</h1>
                <p className="text-muted-foreground">Add RSS feeds, blogs, or choose from popular sources</p>
              </div>
            </div>

            {/* Content */}
            <div className="grid lg:grid-cols-2 gap-8">
              <AddSourceForm />
              <PopularSources />
            </div>
          </div>
        </main>
      </div>
    </AuthGuard>
  )
}
