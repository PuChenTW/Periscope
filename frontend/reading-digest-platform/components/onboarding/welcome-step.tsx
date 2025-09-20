"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckCircle, Clock, Brain, Mail } from "lucide-react"

interface WelcomeStepProps {
  onNext: () => void
  onBack: () => void
  canGoBack: boolean
}

export function WelcomeStep({ onNext }: WelcomeStepProps) {
  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="text-center pb-6">
        <CardTitle className="text-3xl mb-2">Welcome to Daily Digest!</CardTitle>
        <CardDescription className="text-lg">
          {"Let's set up your personalized reading experience in just a few steps"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        <div className="grid gap-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <Mail className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Choose Your Sources</h3>
              <p className="text-muted-foreground text-sm">
                Select from popular news sources or add your own RSS feeds and blogs
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <Clock className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Set Delivery Preferences</h3>
              <p className="text-muted-foreground text-sm">
                Choose when you want to receive your digest and how detailed you want the summaries
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <Brain className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Personalize Your Interests</h3>
              <p className="text-muted-foreground text-sm">
                Add keywords and topics that matter to you for more relevant content
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <CheckCircle className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Start Receiving Digests</h3>
              <p className="text-muted-foreground text-sm">
                Get your first personalized digest delivered to your inbox tomorrow morning
              </p>
            </div>
          </div>
        </div>

        <div className="text-center pt-4">
          <p className="text-sm text-muted-foreground mb-6">This setup will take about 3-5 minutes to complete</p>
          <Button onClick={onNext} size="lg" className="px-8">
            {"Let's Get Started"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
