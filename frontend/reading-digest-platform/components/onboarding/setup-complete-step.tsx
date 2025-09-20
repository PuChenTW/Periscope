import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, Mail, Clock, Brain, Rss, ArrowRight } from "lucide-react"
import Link from "next/link"

interface SetupCompleteStepProps {
  onNext: () => void
  onBack: () => void
  canGoBack: boolean
  data: any
}

export function SetupCompleteStep({ data }: SetupCompleteStepProps) {
  const formatTime = (time: string) => {
    const [hours, minutes] = time.split(":")
    const hour = Number.parseInt(hours)
    const ampm = hour >= 12 ? "PM" : "AM"
    const displayHour = hour % 12 || 12
    return `${displayHour}:${minutes} ${ampm}`
  }

  return (
    <Card className="border-0 shadow-sm">
      <CardHeader className="text-center pb-6">
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle className="w-8 h-8 text-primary" />
        </div>
        <CardTitle className="text-3xl mb-2">Setup Complete!</CardTitle>
        <CardDescription className="text-lg">Your personalized daily reading digest is ready to go</CardDescription>
      </CardHeader>
      <CardContent className="space-y-8">
        {/* Configuration Summary */}
        <div className="space-y-6">
          <h3 className="font-semibold text-lg">Your Configuration Summary</h3>

          <div className="grid gap-4">
            <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-lg">
              <Rss className="w-5 h-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">News Sources</p>
                <p className="text-sm text-muted-foreground">{data.sources?.length || 0} sources selected</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-lg">
              <Clock className="w-5 h-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">Delivery Schedule</p>
                <p className="text-sm text-muted-foreground">
                  Daily at {data.deliveryTime ? formatTime(data.deliveryTime) : "Not set"} •{" "}
                  {data.summaryStyle || "Not set"} summaries
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-muted/30 rounded-lg">
              <Brain className="w-5 h-5 text-primary mt-0.5" />
              <div>
                <p className="font-medium">Interest Keywords</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  {data.keywords?.slice(0, 5).map((keyword: string) => (
                    <Badge key={keyword} variant="secondary" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                  {data.keywords?.length > 5 && (
                    <Badge variant="outline" className="text-xs">
                      +{data.keywords.length - 5} more
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* What Happens Next */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">What Happens Next?</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary-foreground">1</span>
              </div>
              <div>
                <p className="font-medium">We're preparing your first digest</p>
                <p className="text-sm text-muted-foreground">Our AI is analyzing your selected sources and interests</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary-foreground">2</span>
              </div>
              <div>
                <p className="font-medium">First digest delivery</p>
                <p className="text-sm text-muted-foreground">
                  You'll receive your first digest tomorrow at{" "}
                  {data.deliveryTime ? formatTime(data.deliveryTime) : "your scheduled time"}
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs font-bold text-primary-foreground">3</span>
              </div>
              <div>
                <p className="font-medium">Manage your preferences</p>
                <p className="text-sm text-muted-foreground">
                  Use your dashboard to adjust sources, timing, and interests anytime
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center pt-4">
          <Button size="lg" className="px-8" asChild>
            <Link href="/dashboard">
              Go to Dashboard
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </Button>
          <p className="text-sm text-muted-foreground mt-4">
            <Mail className="w-4 h-4 inline mr-1" />
            Check your email for a confirmation and setup summary
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
