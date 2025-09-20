"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { X, Plus, Brain, Save } from "lucide-react"

const SUGGESTED_KEYWORDS = [
  "Artificial Intelligence",
  "Machine Learning",
  "Blockchain",
  "Cybersecurity",
  "Climate Change",
  "Renewable Energy",
  "Space Technology",
  "Biotechnology",
  "Quantum Computing",
  "Robotics",
  "Virtual Reality",
  "Augmented Reality",
  "Internet of Things",
  "5G Technology",
  "Electric Vehicles",
]

export function InterestSettings() {
  const [keywords, setKeywords] = useState([
    "Technology",
    "Artificial Intelligence",
    "Startups",
    "Business",
    "Climate Change",
  ])
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

  const handleSave = () => {
    // Save settings logic here
    console.log("Saving interest settings...")
  }

  return (
    <Card id="interests">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Interest Profile
        </CardTitle>
        <CardDescription>Manage your keywords and topics to personalize your digest content</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Keywords */}
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
          <Label className="text-base font-semibold">Suggested Keywords</Label>
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

        {/* Save Button */}
        <div className="flex justify-end pt-4">
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
