"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { CheckCircle, Clock, AlertCircle, Eye, Search, Download, Calendar } from "lucide-react"
import Link from "next/link"

const MOCK_DIGESTS = [
  {
    id: "1",
    date: "2024-12-19",
    displayDate: "Today, Dec 19",
    status: "delivered",
    articleCount: 47,
    deliveryTime: "8:00 AM",
    readTime: "12 min",
    topTopics: ["AI", "Climate", "Startups"],
    preview: "AI breakthrough at OpenAI, Climate summit updates, New startup funding trends...",
  },
  {
    id: "2",
    date: "2024-12-18",
    displayDate: "Yesterday, Dec 18",
    status: "delivered",
    articleCount: 52,
    deliveryTime: "8:00 AM",
    readTime: "15 min",
    topTopics: ["Tech", "Business", "Health"],
    preview: "Market volatility continues, Healthcare innovation breakthrough, Remote work productivity study...",
  },
  {
    id: "3",
    date: "2024-12-17",
    displayDate: "Dec 17, 2024",
    status: "delivered",
    articleCount: 38,
    deliveryTime: "8:00 AM",
    readTime: "10 min",
    topTopics: ["Climate", "Energy", "Policy"],
    preview: "Sustainable energy progress, New environmental policies, Green technology investments...",
  },
  {
    id: "4",
    date: "2024-12-16",
    displayDate: "Dec 16, 2024",
    status: "delivered",
    articleCount: 44,
    deliveryTime: "8:00 AM",
    readTime: "13 min",
    topTopics: ["Crypto", "Finance", "Tech"],
    preview: "Cryptocurrency regulations update, Financial market analysis, Tech sector developments...",
  },
  {
    id: "5",
    date: "2024-12-15",
    displayDate: "Dec 15, 2024",
    status: "failed",
    articleCount: 0,
    deliveryTime: "8:00 AM",
    readTime: "0 min",
    topTopics: [],
    preview: "Delivery failed due to source connectivity issues",
  },
  {
    id: "6",
    date: "2024-12-14",
    displayDate: "Dec 14, 2024",
    status: "delivered",
    articleCount: 41,
    deliveryTime: "8:00 AM",
    readTime: "11 min",
    topTopics: ["Space", "Science", "Innovation"],
    preview: "Space exploration milestones, Scientific breakthroughs, Innovation in biotechnology...",
  },
]

export function DigestHistory() {
  const [searchQuery, setSearchQuery] = useState("")
  const [filteredDigests, setFilteredDigests] = useState(MOCK_DIGESTS)

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (!query) {
      setFilteredDigests(MOCK_DIGESTS)
    } else {
      const filtered = MOCK_DIGESTS.filter(
        (digest) =>
          digest.preview.toLowerCase().includes(query.toLowerCase()) ||
          digest.topTopics.some((topic) => topic.toLowerCase().includes(query.toLowerCase())),
      )
      setFilteredDigests(filtered)
    }
  }

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
            <CardTitle>Your Digest History</CardTitle>
            <CardDescription>Browse through your past daily reading digests</CardDescription>
          </div>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
          <Input
            placeholder="Search digests by content or topics..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Digest List */}
        <div className="space-y-4">
          {filteredDigests.map((digest) => (
            <div
              key={digest.id}
              className="flex items-start gap-4 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="flex-shrink-0 mt-1">{getStatusIcon(digest.status)}</div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <h3 className="font-medium">{digest.displayDate}</h3>
                    {getStatusBadge(digest.status)}
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    {digest.deliveryTime}
                  </div>
                </div>

                <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{digest.preview}</p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>{digest.articleCount} articles</span>
                    <span>{digest.readTime} read time</span>
                    {digest.topTopics.length > 0 && (
                      <div className="flex items-center gap-1">
                        <span>Topics:</span>
                        <div className="flex gap-1">
                          {digest.topTopics.slice(0, 3).map((topic) => (
                            <Badge key={topic} variant="outline" className="text-xs px-1 py-0">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
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

        {filteredDigests.length === 0 && (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No digests found matching your search.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
