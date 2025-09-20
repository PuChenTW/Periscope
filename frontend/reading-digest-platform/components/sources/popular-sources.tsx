"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Rss, Plus } from "lucide-react"

const POPULAR_SOURCES = [
  {
    name: "MIT Technology Review",
    url: "https://www.technologyreview.com/feed/",
    category: "Technology",
    description: "In-depth analysis of emerging technologies",
    subscribers: "2.1M",
  },
  {
    name: "Fast Company",
    url: "https://www.fastcompany.com/rss.xml",
    category: "Business",
    description: "Innovation, leadership, and design",
    subscribers: "1.8M",
  },
  {
    name: "Ars Technica",
    url: "https://feeds.arstechnica.com/arstechnica/index",
    category: "Technology",
    description: "Technology news and analysis",
    subscribers: "1.5M",
  },
  {
    name: "The Next Web",
    url: "https://thenextweb.com/feed/",
    category: "Technology",
    description: "Technology news and startup coverage",
    subscribers: "1.2M",
  },
  {
    name: "Entrepreneur",
    url: "https://www.entrepreneur.com/latest.rss",
    category: "Business",
    description: "Entrepreneurship and business advice",
    subscribers: "980K",
  },
  {
    name: "VentureBeat",
    url: "https://venturebeat.com/feed/",
    category: "Technology",
    description: "Technology news and venture capital",
    subscribers: "850K",
  },
]

export function PopularSources() {
  const addPopularSource = (source: any) => {
    // Add source logic here
    console.log("Adding source:", source)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Popular Sources</CardTitle>
        <CardDescription>Choose from curated, high-quality news sources</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {POPULAR_SOURCES.map((source, index) => (
            <div
              key={index}
              className="flex items-start gap-3 p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors"
            >
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                <Rss className="w-5 h-5 text-primary" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-medium">{source.name}</h3>
                  <Badge variant="outline" className="text-xs">
                    {source.category}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground mb-2">{source.description}</p>
                <p className="text-xs text-muted-foreground">{source.subscribers} subscribers</p>
              </div>

              <Button size="sm" variant="outline" onClick={() => addPopularSource(source)}>
                <Plus className="w-4 h-4 mr-1" />
                Add
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
