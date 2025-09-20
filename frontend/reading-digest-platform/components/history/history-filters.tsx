"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { CalendarIcon, Filter, X } from "lucide-react"
import { format } from "date-fns"

export function HistoryFilters() {
  const [dateRange, setDateRange] = useState<{ from?: Date; to?: Date }>({})
  const [status, setStatus] = useState("all")
  const [topics, setTopics] = useState<string[]>([])

  const availableTopics = [
    "Technology",
    "Business",
    "Science",
    "Health",
    "Climate",
    "AI",
    "Startups",
    "Finance",
    "Space",
    "Energy",
  ]

  const toggleTopic = (topic: string) => {
    setTopics((prev) => (prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]))
  }

  const clearFilters = () => {
    setDateRange({})
    setStatus("all")
    setTopics([])
  }

  const hasActiveFilters = dateRange.from || dateRange.to || status !== "all" || topics.length > 0

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Filters
            </CardTitle>
            <CardDescription>Filter your digest history</CardDescription>
          </div>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              <X className="w-4 h-4 mr-1" />
              Clear
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Date Range */}
        <div className="space-y-2">
          <Label>Date Range</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full justify-start text-left font-normal bg-transparent">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {dateRange.from ? (
                  dateRange.to ? (
                    <>
                      {format(dateRange.from, "LLL dd, y")} - {format(dateRange.to, "LLL dd, y")}
                    </>
                  ) : (
                    format(dateRange.from, "LLL dd, y")
                  )
                ) : (
                  <span>Pick a date range</span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="start">
              <Calendar
                initialFocus
                mode="range"
                defaultMonth={dateRange.from}
                selected={dateRange}
                onSelect={setDateRange}
                numberOfMonths={2}
              />
            </PopoverContent>
          </Popover>
        </div>

        {/* Status Filter */}
        <div className="space-y-2">
          <Label>Status</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="delivered">Delivered</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="processing">Processing</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Topics Filter */}
        <div className="space-y-3">
          <Label>Topics</Label>
          <div className="space-y-2">
            {availableTopics.map((topic) => (
              <div key={topic} className="flex items-center space-x-2">
                <Checkbox id={topic} checked={topics.includes(topic)} onCheckedChange={() => toggleTopic(topic)} />
                <Label htmlFor={topic} className="text-sm font-normal cursor-pointer">
                  {topic}
                </Label>
              </div>
            ))}
          </div>
        </div>

        {/* Active Filters Summary */}
        {hasActiveFilters && (
          <div className="pt-4 border-t border-border">
            <Label className="text-xs text-muted-foreground">Active Filters:</Label>
            <div className="mt-2 space-y-1 text-xs">
              {dateRange.from && <div>Date: {format(dateRange.from, "MMM dd")} onwards</div>}
              {status !== "all" && <div>Status: {status}</div>}
              {topics.length > 0 && <div>Topics: {topics.join(", ")}</div>}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
