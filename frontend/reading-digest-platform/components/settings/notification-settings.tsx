"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Bell, Save } from "lucide-react"

export function NotificationSettings() {
  const [digestDelivery, setDigestDelivery] = useState(true)
  const [sourceErrors, setSourceErrors] = useState(true)
  const [weeklyReport, setWeeklyReport] = useState(false)
  const [productUpdates, setProductUpdates] = useState(true)
  const [marketingEmails, setMarketingEmails] = useState(false)

  const handleSave = () => {
    // Save settings logic here
    console.log("Saving notification settings...")
  }

  return (
    <Card id="notifications">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="w-5 h-5" />
          Notification Settings
        </CardTitle>
        <CardDescription>Choose which emails you want to receive from us</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 border border-border rounded-lg">
            <div>
              <Label htmlFor="digest-delivery" className="font-medium">
                Daily Digest Delivery
              </Label>
              <p className="text-sm text-muted-foreground">Your personalized daily reading digest</p>
            </div>
            <Switch id="digest-delivery" checked={digestDelivery} onCheckedChange={setDigestDelivery} />
          </div>

          <div className="flex items-center justify-between p-4 border border-border rounded-lg">
            <div>
              <Label htmlFor="source-errors" className="font-medium">
                Source Error Alerts
              </Label>
              <p className="text-sm text-muted-foreground">Get notified when sources fail to fetch content</p>
            </div>
            <Switch id="source-errors" checked={sourceErrors} onCheckedChange={setSourceErrors} />
          </div>

          <div className="flex items-center justify-between p-4 border border-border rounded-lg">
            <div>
              <Label htmlFor="weekly-report" className="font-medium">
                Weekly Reading Report
              </Label>
              <p className="text-sm text-muted-foreground">Summary of your reading activity and top articles</p>
            </div>
            <Switch id="weekly-report" checked={weeklyReport} onCheckedChange={setWeeklyReport} />
          </div>

          <div className="flex items-center justify-between p-4 border border-border rounded-lg">
            <div>
              <Label htmlFor="product-updates" className="font-medium">
                Product Updates
              </Label>
              <p className="text-sm text-muted-foreground">New features, improvements, and important announcements</p>
            </div>
            <Switch id="product-updates" checked={productUpdates} onCheckedChange={setProductUpdates} />
          </div>

          <div className="flex items-center justify-between p-4 border border-border rounded-lg">
            <div>
              <Label htmlFor="marketing-emails" className="font-medium">
                Marketing Emails
              </Label>
              <p className="text-sm text-muted-foreground">Tips, best practices, and promotional content</p>
            </div>
            <Switch id="marketing-emails" checked={marketingEmails} onCheckedChange={setMarketingEmails} />
          </div>
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
