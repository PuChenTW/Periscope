"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Plus, Globe, CheckCircle, AlertCircle, Loader2 } from "lucide-react"

export function AddSourceForm() {
  const [url, setUrl] = useState("")
  const [sourceName, setSourceName] = useState("")
  const [isValidating, setIsValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<any>(null)

  const validateSource = async () => {
    if (!url) return

    setIsValidating(true)
    setValidationResult(null)

    // Simulate API call
    setTimeout(() => {
      const isValid = url.includes("feed") || url.includes("rss") || url.includes("xml")
      setValidationResult({
        isValid,
        name: isValid ? "Example Blog" : null,
        description: isValid ? "A technology blog with daily updates" : "Invalid RSS feed URL",
        articleCount: isValid ? 15 : 0,
      })
      if (isValid && !sourceName) {
        setSourceName("Example Blog")
      }
      setIsValidating(false)
    }, 2000)
  }

  const addSource = () => {
    if (validationResult?.isValid) {
      // Add source logic here
      setUrl("")
      setSourceName("")
      setValidationResult(null)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="w-5 h-5" />
          Add New Source
        </CardTitle>
        <CardDescription>Add RSS feeds, blogs, or news sources to your digest</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="source-url">RSS Feed or Blog URL</Label>
          <div className="flex gap-2">
            <Input
              id="source-url"
              placeholder="https://example.com/feed"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
            <Button onClick={validateSource} disabled={!url || isValidating} variant="outline">
              {isValidating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Test"}
            </Button>
          </div>
        </div>

        {validationResult && (
          <div
            className={`p-3 rounded-lg border ${
              validationResult.isValid ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              {validationResult.isValid ? (
                <CheckCircle className="w-4 h-4 text-green-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600" />
              )}
              <span className={`font-medium ${validationResult.isValid ? "text-green-800" : "text-red-800"}`}>
                {validationResult.isValid ? "Valid RSS Feed" : "Invalid Source"}
              </span>
            </div>
            <p className={`text-sm ${validationResult.isValid ? "text-green-700" : "text-red-700"}`}>
              {validationResult.description}
            </p>
            {validationResult.isValid && (
              <div className="mt-2">
                <Badge variant="secondary">{validationResult.articleCount} recent articles</Badge>
              </div>
            )}
          </div>
        )}

        {validationResult?.isValid && (
          <div className="space-y-2">
            <Label htmlFor="source-name">Source Name (Optional)</Label>
            <Input
              id="source-name"
              placeholder="Custom name for this source"
              value={sourceName}
              onChange={(e) => setSourceName(e.target.value)}
            />
          </div>
        )}

        <Button onClick={addSource} disabled={!validationResult?.isValid} className="w-full">
          <Globe className="w-4 h-4 mr-2" />
          Add Source
        </Button>

        <div className="text-xs text-muted-foreground">
          <p>Supported formats: RSS, Atom, JSON Feed</p>
          <p>Maximum 20 sources per account</p>
        </div>
      </CardContent>
    </Card>
  )
}
