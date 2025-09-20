"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { X, Plus, ArrowLeft, Brain } from "lucide-react"

interface InterestProfileStepProps {
  onNext: (data: any) => void
  onBack: () => void
  canGoBack: boolean
  data: any
}

const SUGGESTED_KEYWORDS = [
  "Technology",
  "Artificial Intelligence",
  "Machine Learning",
  "Startups",
  "Business",
  "Finance",
  "Marketing",
  "Design",
  "Programming",
  "Data Science",
  "Cybersecurity",
  "Cloud Computing",
  "Mobile Development",
  "Web Development",
  "Product Management",
  "Leadership",
  "Innovation",
  "Entrepreneurship",
  "Investment",
  "Cryptocurrency",
  "Healthcare",
  "Science",
  "Climate Change",
  "Sustainability",
  "Remote Work",
]

export function InterestProfileStep({ onNext, onBack, canGoBack, data }: InterestProfileStepProps) {
  const [keywords, setKeywords] = useState<string[]>(data.keywords || [])
  const [newKeyword, setNewKeyword] = useState("")

  const addKeyword = (keyword: string) => {
    if (keyword && !keywords.includes(keyword) && keywords.length < 50) {
      setKeywords((prev) => [...prev, keyword])
    }
  }

  const removeKeyword = (keyword: string) => {
    setKeywords((prev) => prev.filter((k) => k !== keyword))
  }

  const handleAddCustomKeyword = () => {
    if (newKeyword.trim()) {
      addKeyword(newKeyword.trim())
      setNewKeyword("")
    }
  }

  const handleNext = () => {
    onNext({ keywords })
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Interest Profile</CardTitle>
        <CardDescription>
          Add keywords and topics that interest you to get more relevant content in your digest
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Keywords */}
        {keywords.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-base font-semibold">Your Keywords</Label>
              <span className="text-sm text-muted-foreground">{keywords.length}/50</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword) => (
                <Badge key={keyword} variant="secondary" className="px-3 py-1">
                  {keyword}
                  <button onClick={() => removeKeyword(keyword)} className="ml-2 hover:text-destructive">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Add Custom Keyword */}
        <div className="space-y-3">
          <Label className="text-base font-semibold flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Add Custom Keyword
          </Label>
          <div className="flex gap-2">
            <Input
              placeholder="Enter a keyword or topic"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleAddCustomKeyword()}
              disabled={keywords.length >= 50}
            />
            <Button
              onClick={handleAddCustomKeyword}
              variant="outline"
              disabled={!newKeyword.trim() || keywords.length >= 50}
            >
              Add
            </Button>
          </div>
        </div>

        {/* Suggested Keywords */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary" />
            <Label className="text-base font-semibold">Suggested Keywords</Label>
          </div>
          <p className="text-sm text-muted-foreground">Click on any keyword below to add it to your profile</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_KEYWORDS.filter((keyword) => !keywords.includes(keyword)).map((keyword) => (
              <Button
                key={keyword}
                variant="outline"
                size="sm"
                onClick={() => addKeyword(keyword)}
                disabled={keywords.length >= 50}
                className="h-8 px-3 text-xs"
              >
                {keyword}
              </Button>
            ))}
          </div>
        </div>

        {/* Keyword Limit Warning */}
        {keywords.length >= 45 && (
          <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-sm text-amber-800">
              {keywords.length >= 50
                ? "You've reached the maximum of 50 keywords."
                : `You're approaching the limit of 50 keywords (${keywords.length}/50).`}
            </p>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between pt-4">
          {canGoBack && (
            <Button variant="outline" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          )}
          <Button onClick={handleNext} className={!canGoBack ? "ml-auto" : ""}>
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
