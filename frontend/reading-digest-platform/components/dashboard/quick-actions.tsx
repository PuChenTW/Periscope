import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Settings, Rss, Clock } from "lucide-react"
import Link from "next/link"

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
        <CardDescription>Manage your digest preferences</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
          <Link href="/sources/add">
            <Plus className="w-4 h-4 mr-2" />
            Add New Source
          </Link>
        </Button>

        <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
          <Link href="/sources">
            <Rss className="w-4 h-4 mr-2" />
            Manage Sources
          </Link>
        </Button>

        <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
          <Link href="/settings/delivery">
            <Clock className="w-4 h-4 mr-2" />
            Update Schedule
          </Link>
        </Button>

        <Button variant="outline" className="w-full justify-start bg-transparent" asChild>
          <Link href="/settings">
            <Settings className="w-4 h-4 mr-2" />
            All Settings
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}
