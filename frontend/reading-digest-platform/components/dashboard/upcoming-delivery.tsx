import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Clock, CheckCircle, Settings } from "lucide-react"
import Link from "next/link"

export function UpcomingDelivery() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-5 h-5 text-primary" />
          Next Delivery
        </CardTitle>
        <CardDescription>Your upcoming digest information</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="text-center p-6 bg-muted/30 rounded-lg">
          <div className="text-2xl font-bold mb-1">Tomorrow</div>
          <div className="text-lg text-muted-foreground mb-2">8:00 AM EST</div>
          <Badge variant="secondary" className="mb-4">
            <CheckCircle className="w-3 h-3 mr-1" />
            On Schedule
          </Badge>

          <div className="space-y-2 text-sm text-muted-foreground">
            <div className="flex justify-between">
              <span>Sources:</span>
              <span className="font-medium">12 active</span>
            </div>
            <div className="flex justify-between">
              <span>Summary Style:</span>
              <span className="font-medium">Brief</span>
            </div>
            <div className="flex justify-between">
              <span>Keywords:</span>
              <span className="font-medium">25 topics</span>
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="font-medium text-sm">Recent Activity</h4>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span>47 new articles collected</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>AI summarization in progress</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
              <span>Personalization applied</span>
            </div>
          </div>
        </div>

        <Button variant="outline" size="sm" className="w-full bg-transparent" asChild>
          <Link href="/settings/delivery">
            <Settings className="w-4 h-4 mr-2" />
            Adjust Schedule
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}
