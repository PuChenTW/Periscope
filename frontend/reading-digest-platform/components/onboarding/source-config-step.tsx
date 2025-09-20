"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Switch } from "@/components/ui/switch"
import { Badge } from "@/components/ui/badge"
import { Plus, Globe, Rss, ArrowLeft } from "lucide-react"

interface SourceConfigStepProps {
  onNext: (data: any) => void
  onBack: () => void
  canGoBack: boolean
  data: any
}

const POPULAR_SOURCES = [
  { name: "TechCrunch", url: "https://techcrunch.com/feed/", category: "Technology" },
  { name: "BBC News", url: "https://feeds.bbci.co.uk/news/rss.xml", category: "News" },
  { name: "Harvard Business Review", url: "https://hbr.org/feed", category: "Business" },
  { name: "Wired", url: "https://www.wired.com/feed/rss", category: "Technology" },
  { name: "The Verge", url: "https://www.theverge.com/rss/index.xml", category: "Technology" },
  { name: "MIT Technology Review", url: "https://www.technologyreview.com/feed/", category: "Technology" },
  { name: "Fast Company", url: "https://www.fastcompany.com/rss.xml", category: "Business" },
  { name: "Ars Technica", url: "https://feeds.arstechnica.com/arstechnica/index", category: "Technology" },
]

export function SourceConfigStep({ onNext, onBack, canGoBack, data }: SourceConfigStepProps) {
  const [selectedSources, setSelectedSources] = useState<string[]>(data.sources || [])
  const [customUrl, setCustomUrl] = useState("")
  const [customSources, setCustomSources] = useState<any[]>([])

  const toggleSource = (sourceUrl: string) => {
    setSelectedSources((prev) =>
      prev.includes(sourceUrl) ? prev.filter((url) => url !== sourceUrl) : [...prev, sourceUrl],
    )
  }

  const addCustomSource = () => {
    if (customUrl && !selectedSources.includes(customUrl)) {
      const newSource = { name: "Custom Source", url: customUrl, category: "Custom" }
      setCustomSources((prev) => [...prev, newSource])
      setSelectedSources((prev) => [...prev, customUrl])
      setCustomUrl("")
    }
  }

  const handleNext = () => {
    onNext({ sources: selectedSources })
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Choose Your News Sources</CardTitle>
        <CardDescription>
          Select from popular sources or add your own RSS feeds. You can add up to 20 sources.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Popular Sources */}
        <div>
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-4 h-4" />
            Popular Sources
          </h3>
          <div className="grid gap-3">
            {POPULAR_SOURCES.map((source) => (
              <div
                key={source.url}
                className="flex items-center justify-between p-3 border border-border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary/10 rounded flex items-center justify-center">
                    <Rss className="w-4 h-4 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium">{source.name}</p>
                    <p className="text-sm text-muted-foreground">{source.category}</p>
                  </div>
                </div>
                <Switch
                  checked={selectedSources.includes(source.url)}
                  onCheckedChange={() => toggleSource(source.url)}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Custom Sources */}
        <div>
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Custom Source
          </h3>
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder="Enter RSS feed URL or blog URL"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && addCustomSource()}
              />
            </div>
            <Button onClick={addCustomSource} variant="outline">
              Add
            </Button>
          </div>
          {customSources.length > 0 && (
            <div className="mt-4 space-y-2">
              {customSources.map((source, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-muted/50 rounded">
                  <Rss className="w-4 h-4 text-primary" />
                  <span className="text-sm">{source.url}</span>
                  <Badge variant="secondary">Custom</Badge>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Selected Count */}
        <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
          <span className="text-sm text-muted-foreground">Selected sources: {selectedSources.length}/20</span>
          {selectedSources.length > 0 && <Badge variant="secondary">{selectedSources.length} sources selected</Badge>}
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-4">
          {canGoBack && (
            <Button variant="outline" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          )}
          <Button onClick={handleNext} disabled={selectedSources.length === 0} className={!canGoBack ? "ml-auto" : ""}>
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
