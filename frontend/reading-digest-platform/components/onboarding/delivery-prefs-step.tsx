"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Clock, ArrowLeft, Mail } from "lucide-react"

interface DeliveryPrefsStepProps {
  onNext: (data: any) => void
  onBack: () => void
  canGoBack: boolean
  data: any
}

export function DeliveryPrefsStep({ onNext, onBack, canGoBack, data }: DeliveryPrefsStepProps) {
  const [deliveryTime, setDeliveryTime] = useState(data.deliveryTime || "")
  const [timezone, setTimezone] = useState(data.timezone || "")
  const [summaryStyle, setSummaryStyle] = useState(data.summaryStyle || "")

  const handleNext = () => {
    onNext({ deliveryTime, timezone, summaryStyle })
  }

  const canContinue = deliveryTime && timezone && summaryStyle

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader>
        <CardTitle className="text-2xl">Delivery Preferences</CardTitle>
        <CardDescription>Choose when and how you want to receive your daily digest</CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Delivery Time */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-primary" />
            <Label className="text-base font-semibold">Delivery Time</Label>
          </div>
          <Select value={deliveryTime} onValueChange={setDeliveryTime}>
            <SelectTrigger>
              <SelectValue placeholder="Choose your preferred delivery time" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="06:00">6:00 AM</SelectItem>
              <SelectItem value="07:00">7:00 AM</SelectItem>
              <SelectItem value="08:00">8:00 AM</SelectItem>
              <SelectItem value="09:00">9:00 AM</SelectItem>
              <SelectItem value="10:00">10:00 AM</SelectItem>
              <SelectItem value="12:00">12:00 PM</SelectItem>
              <SelectItem value="18:00">6:00 PM</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            Your digest will be delivered at this time every day in your timezone
          </p>
        </div>

        {/* Timezone */}
        <div className="space-y-4">
          <Label className="text-base font-semibold">Timezone</Label>
          <Select value={timezone} onValueChange={setTimezone}>
            <SelectTrigger>
              <SelectValue placeholder="Select your timezone" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="america/new_york">Eastern Time (ET)</SelectItem>
              <SelectItem value="america/chicago">Central Time (CT)</SelectItem>
              <SelectItem value="america/denver">Mountain Time (MT)</SelectItem>
              <SelectItem value="america/los_angeles">Pacific Time (PT)</SelectItem>
              <SelectItem value="europe/london">London (GMT)</SelectItem>
              <SelectItem value="europe/paris">Paris (CET)</SelectItem>
              <SelectItem value="asia/tokyo">Tokyo (JST)</SelectItem>
              <SelectItem value="australia/sydney">Sydney (AEDT)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Summary Style */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-primary" />
            <Label className="text-base font-semibold">Summary Style</Label>
          </div>
          <RadioGroup value={summaryStyle} onValueChange={setSummaryStyle}>
            <div className="space-y-4">
              <div className="flex items-start space-x-3 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
                <RadioGroupItem value="brief" id="brief" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="brief" className="font-medium cursor-pointer">
                    Brief Summaries
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Short, concise summaries focusing on key points. Perfect for quick reading.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
                <RadioGroupItem value="detailed" id="detailed" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="detailed" className="font-medium cursor-pointer">
                    Detailed Summaries
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Comprehensive summaries with more context and background information.
                  </p>
                </div>
              </div>

              <div className="flex items-start space-x-3 p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors">
                <RadioGroupItem value="headlines" id="headlines" className="mt-1" />
                <div className="flex-1">
                  <Label htmlFor="headlines" className="font-medium cursor-pointer">
                    Headlines Only
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Just the headlines with links to full articles. Minimal reading time.
                  </p>
                </div>
              </div>
            </div>
          </RadioGroup>
        </div>

        {/* Navigation */}
        <div className="flex justify-between pt-4">
          {canGoBack && (
            <Button variant="outline" onClick={onBack}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
          )}
          <Button onClick={handleNext} disabled={!canContinue} className={!canGoBack ? "ml-auto" : ""}>
            Continue
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
