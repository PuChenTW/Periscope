import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Newspaper, Mail, CheckCircle, RefreshCw } from "lucide-react"
import Link from "next/link"

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="border-0 shadow-lg">
          <CardHeader className="text-center pb-6">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Mail className="w-6 h-6 text-primary" />
            </div>
            <CardTitle className="text-2xl">Check Your Email</CardTitle>
            <CardDescription>{"We've sent a verification link to your email address"}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center space-y-4">
              <div className="p-4 bg-muted/50 rounded-lg">
                <CheckCircle className="w-8 h-8 text-primary mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">
                  Click the link in your email to verify your account and complete your registration.
                </p>
              </div>

              <div className="text-sm text-muted-foreground">
                <p>{"Didn't receive the email? Check your spam folder or"}</p>
              </div>

              <Button variant="outline" className="w-full bg-transparent">
                <RefreshCw className="w-4 h-4 mr-2" />
                Resend Verification Email
              </Button>
            </div>

            <Separator />

            <div className="text-center">
              <p className="text-sm text-muted-foreground">
                Wrong email address?{" "}
                <Link href="/signup" className="text-primary hover:underline font-medium">
                  Sign up again
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 text-center">
          <Link
            href="/"
            className="flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <Newspaper className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-medium">Daily Digest</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
