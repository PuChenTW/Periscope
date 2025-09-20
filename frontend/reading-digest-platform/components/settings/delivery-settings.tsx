"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Switch } from "@/components/ui/switch"
import { Clock, Save } from "lucide-react"

export function DeliverySettings() {
  const [deliveryTime, setDeliveryTime] = useState("08:00")
  const [timezone, setTimezone] = useState("america/new_york")
  const [summaryStyle, setSummaryStyle] = useState("brief")
  const [emailFormat, setEmailFormat] = useState("html")
  const [weekendDelivery, setWeekendDelivery] = useState(false)

  const handleSave = () => {
    // Save settings logic here
    console.log("Saving delivery settings...")
  }

  return (
    <Card id="delivery">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Delivery Settings
        </CardTitle>
        <CardDescription>Configure when and how you receive your daily digest</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Delivery Time */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label>Delivery Time</Label>
            <Select value={deliveryTime} onValueChange={setDeliveryTime}>
              <SelectTrigger>
                <SelectValue />
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
          </div>

          <div className="space-y-2">
            <Label>Timezone</Label>
            <Select value={timezone} onValueChange={setTimezone}>
              <SelectTrigger>
                <SelectValue />
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
        </div>

        {/* Summary Style */}
        <div className="space-y-4">
          <Label>Summary Style</Label>
          <RadioGroup value={summaryStyle} onValueChange={setSummaryStyle}>
            <div className="space-y-3">
              <div className="flex items-start space-x-3 p-3 border border-border rounded-lg">
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

              <div className="flex items-start space-x-3 p-3 border border-border rounded-lg">
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

              <div className="flex items-start space-x-3 p-3 border border-border rounded-lg">
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

        {/* Email Format */}
        <div className="space-y-4">
          <Label>Email Format</Label>
          <RadioGroup value={emailFormat} onValueChange={setEmailFormat}>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="html" id="html" />
              <Label htmlFor="html">HTML (Rich formatting with images and styling)</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="plain" id="plain" />
              <Label htmlFor="plain">Plain Text (Simple text format)</Label>
            </div>
          </RadioGroup>
        </div>

        {/* Weekend Delivery */}
        <div className="flex items-center justify-between p-4 border border-border rounded-lg">
          <div>
            <Label htmlFor="weekend-delivery" className="font-medium">
              Weekend Delivery
            </Label>
            <p className="text-sm text-muted-foreground">Receive digests on Saturday and Sunday</p>
          </div>
          <Switch id="weekend-delivery" checked={weekendDelivery} onCheckedChange={setWeekendDelivery} />
        </div>

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
