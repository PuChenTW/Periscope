import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Clock, AlertCircle, Eye, ExternalLink } from "lucide-react"
import Link from "next/link"

const RECENT_DIGESTS = [
  {
    id: "1",
    date: "Today, Dec 19",
    status: "processing",
    articleCount: 47,
    deliveryTime: "8:00 AM",
    preview: "Processing articles from TechCrunch, BBC News, Harvard Business Review...",
  },
  {
    id: "2",
    date: "Yesterday, Dec 18",
    status: "delivered",
    articleCount: 52,
    deliveryTime: "8:00 AM",
    preview: "AI breakthrough at OpenAI, Market volatility continues, New startup funding trends...",
  },
  {
    id: "3",
    date: "Dec 17, 2024",
    status: "delivered",
    articleCount: 38,
    deliveryTime: "8:00 AM",
    preview: "Climate summit updates, Tech layoffs analysis, Remote work productivity study...",
  },
  {
    id: "4",
    date: "Dec 16, 2024",
    status: "delivered",
    articleCount: 44,
    deliveryTime: "8:00 AM",
    preview: "Cryptocurrency regulations, Healthcare innovation, Sustainable energy progress...",
  },
  {
    id: "5",
    date: "Dec 15, 2024",
    status: "failed",
    articleCount: 0,
    deliveryTime: "8:00 AM",
    preview: "Delivery failed due to source connectivity issues",
  },
]

export function RecentDigests() {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "delivered":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "processing":
        return <Clock className="w-4 h-4 text-blue-500" />
      case "failed":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      default:
        return <Clock className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "delivered":
        return (
          <Badge variant="secondary" className="text-green-700 bg-green-50">
            Delivered
          </Badge>
        )
      case "processing":
        return (
          <Badge variant="secondary" className="text-blue-700 bg-blue-50">
            Processing
          </Badge>
        )
      case "failed":
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Digests</CardTitle>
            <CardDescription>Your last 7 daily reading digests</CardDescription>
          </div>
          <Button variant="outline" asChild>
            <Link href="/history">
              View All
              <ExternalLink className="w-4 h-4 ml-2" />
            </Link>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {RECENT_DIGESTS.map((digest) => (
            <div
              key={digest.id}
              className="flex items-start gap-4 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex-shrink-0 mt-1">{getStatusIcon(digest.status)}</div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium">{digest.date}</h3>
                    {getStatusBadge(digest.status)}
                  </div>
                  <div className="text-sm text-muted-foreground">{digest.deliveryTime}</div>
                </div>

                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{digest.preview}</p>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">{digest.articleCount} articles</span>
                  {digest.status === "delivered" && (
                    <Button variant="ghost" size="sm" asChild>
                      <Link href={`/digest/${digest.id}`}>
                        <Eye className="w-4 h-4 mr-2" />
                        View Digest
                      </Link>
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
