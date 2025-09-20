"use client"

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { CheckCircle, AlertCircle, Clock, ExternalLink, Rss } from "lucide-react"

interface SourceDetailsModalProps {
  source: any
  isOpen: boolean
  onClose: () => void
}

export function SourceDetailsModal({ source, isOpen, onClose }: SourceDetailsModalProps) {
  if (!source) return null

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

  const mockRecentArticles = [
    {
      title: "The Future of Artificial Intelligence in 2024",
      publishedAt: "2 hours ago",
      summary: "Exploring the latest developments in AI technology and their implications for various industries.",
    },
    {
      title: "Breakthrough in Quantum Computing Research",
      publishedAt: "5 hours ago",
      summary:
        "Scientists achieve new milestone in quantum error correction, bringing practical quantum computers closer to reality.",
    },
    {
      title: "Sustainable Technology Trends to Watch",
      publishedAt: "1 day ago",
      summary: "How green technology is reshaping industries and creating new opportunities for innovation.",
    },
  ]

  const mockFetchHistory = [
    { date: "2024-12-19 14:30", status: "success", articles: 12 },
    { date: "2024-12-19 08:00", status: "success", articles: 8 },
    { date: "2024-12-18 20:15", status: "success", articles: 15 },
    { date: "2024-12-18 14:30", status: "error", articles: 0 },
    { date: "2024-12-18 08:00", status: "success", articles: 10 },
  ]

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStatusIcon(source.status)}
            {source.name}
          </DialogTitle>
          <DialogDescription>{source.url}</DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Source Info */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">Status</h3>
              <Badge variant={source.status === "active" ? "secondary" : "destructive"}>{source.status}</Badge>
            </div>
            <div>
              <h3 className="font-medium mb-2">Category</h3>
              <Badge variant="outline">{source.category}</Badge>
            </div>
            <div>
              <h3 className="font-medium mb-2">Success Rate</h3>
              <p className="text-2xl font-bold">{source.successRate}%</p>
            </div>
            <div>
              <h3 className="font-medium mb-2">Articles Today</h3>
              <p className="text-2xl font-bold">{source.articleCount}</p>
            </div>
          </div>

          <Separator />

          {/* Recent Articles */}
          <div>
            <h3 className="font-medium mb-4">Recent Articles</h3>
            <div className="space-y-3">
              {mockRecentArticles.map((article, index) => (
                <div key={index} className="p-3 border border-border rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium text-sm line-clamp-2">{article.title}</h4>
                    <Button variant="ghost" size="sm">
                      <ExternalLink className="w-3 h-3" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{article.summary}</p>
                  <p className="text-xs text-muted-foreground">{article.publishedAt}</p>
                </div>
              ))}
            </div>
          </div>

          <Separator />

          {/* Fetch History */}
          <div>
            <h3 className="font-medium mb-4">Fetch History</h3>
            <div className="space-y-2">
              {mockFetchHistory.map((fetch, index) => (
                <div key={index} className="flex items-center justify-between p-2 text-sm">
                  <span className="text-muted-foreground">{fetch.date}</span>
                  <div className="flex items-center gap-2">
                    <span>{fetch.articles} articles</span>
                    {fetch.status === "success" ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
