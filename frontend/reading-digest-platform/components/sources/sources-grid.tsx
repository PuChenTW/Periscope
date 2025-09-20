"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Rss, Globe, MoreVertical, Eye, Trash2, AlertCircle, CheckCircle, Clock } from "lucide-react"
import { SourceDetailsModal } from "./source-details-modal"

const MOCK_SOURCES = [
  {
    id: "1",
    name: "TechCrunch",
    url: "https://techcrunch.com/feed/",
    category: "Technology",
    status: "active",
    lastFetch: "2 hours ago",
    articleCount: 12,
    successRate: 98.5,
    isEnabled: true,
  },
  {
    id: "2",
    name: "BBC News",
    url: "https://feeds.bbci.co.uk/news/rss.xml",
    category: "News",
    status: "active",
    lastFetch: "1 hour ago",
    articleCount: 8,
    successRate: 99.2,
    isEnabled: true,
  },
  {
    id: "3",
    name: "Harvard Business Review",
    url: "https://hbr.org/feed",
    category: "Business",
    status: "active",
    lastFetch: "3 hours ago",
    articleCount: 5,
    successRate: 97.8,
    isEnabled: true,
  },
  {
    id: "4",
    name: "The Verge",
    url: "https://www.theverge.com/rss/index.xml",
    category: "Technology",
    status: "error",
    lastFetch: "Failed",
    articleCount: 0,
    successRate: 85.2,
    isEnabled: false,
  },
  {
    id: "5",
    name: "Custom Tech Blog",
    url: "https://example-blog.com/feed",
    category: "Custom",
    status: "active",
    lastFetch: "30 minutes ago",
    articleCount: 3,
    successRate: 94.1,
    isEnabled: true,
  },
  {
    id: "6",
    name: "Wired",
    url: "https://www.wired.com/feed/rss",
    category: "Technology",
    status: "pending",
    lastFetch: "Processing...",
    articleCount: 0,
    successRate: 0,
    isEnabled: true,
  },
]

export function SourcesGrid() {
  const [sources, setSources] = useState(MOCK_SOURCES)
  const [selectedSource, setSelectedSource] = useState<any>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const toggleSource = (sourceId: string) => {
    setSources((prev) =>
      prev.map((source) => (source.id === sourceId ? { ...source, isEnabled: !source.isEnabled } : source)),
    )
  }

  const removeSource = (sourceId: string) => {
    setSources((prev) => prev.filter((source) => source.id !== sourceId))
  }

  const viewSourceDetails = (source: any) => {
    setSelectedSource(source)
    setIsModalOpen(true)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case "pending":
        return <Clock className="w-4 h-4 text-blue-500" />
      default:
        return <Rss className="w-4 h-4 text-muted-foreground" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <Badge variant="secondary" className="text-green-700 bg-green-50">
            Active
          </Badge>
        )
      case "error":
        return <Badge variant="destructive">Error</Badge>
      case "pending":
        return (
          <Badge variant="secondary" className="text-blue-700 bg-blue-50">
            Pending
          </Badge>
        )
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Your Sources</CardTitle>
          <CardDescription>Manage your active news sources and RSS feeds</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {sources.map((source) => (
              <div
                key={source.id}
                className="flex items-center gap-4 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex-shrink-0">
                  {source.category === "Custom" ? (
                    <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                      <Globe className="w-5 h-5 text-muted-foreground" />
                    </div>
                  ) : (
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                      <Rss className="w-5 h-5 text-primary" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium truncate">{source.name}</h3>
                    {getStatusIcon(source.status)}
                    {getStatusBadge(source.status)}
                  </div>
                  <p className="text-sm text-muted-foreground truncate mb-2">{source.url}</p>
                  <div className="flex items-center gap-4 text-xs text-muted-foreground">
                    <span>Last fetch: {source.lastFetch}</span>
                    <span>Articles: {source.articleCount}</span>
                    <span>Success: {source.successRate}%</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Switch checked={source.isEnabled} onCheckedChange={() => toggleSource(source.id)} />

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => viewSourceDetails(source)}>
                        <Eye className="w-4 h-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => removeSource(source.id)} className="text-destructive">
                        <Trash2 className="w-4 h-4 mr-2" />
                        Remove Source
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <SourceDetailsModal source={selectedSource} isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  )
}
