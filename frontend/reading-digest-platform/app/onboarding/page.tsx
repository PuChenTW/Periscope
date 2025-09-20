"use client"

import { useState } from "react"
import { Progress } from "@/components/ui/progress"
import { Newspaper } from "lucide-react"
import { WelcomeStep } from "@/components/onboarding/welcome-step"
import { SourceConfigStep } from "@/components/onboarding/source-config-step"
import { DeliveryPrefsStep } from "@/components/onboarding/delivery-prefs-step"
import { InterestProfileStep } from "@/components/onboarding/interest-profile-step"
import { SetupCompleteStep } from "@/components/onboarding/setup-complete-step"

const STEPS = [
  { id: "welcome", title: "Welcome", component: WelcomeStep },
  { id: "sources", title: "Sources", component: SourceConfigStep },
  { id: "delivery", title: "Delivery", component: DeliveryPrefsStep },
  { id: "interests", title: "Interests", component: InterestProfileStep },
  { id: "complete", title: "Complete", component: SetupCompleteStep },
]

export default function OnboardingPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [onboardingData, setOnboardingData] = useState({
    sources: [],
    deliveryTime: "",
    timezone: "",
    summaryStyle: "",
    keywords: [],
  })

  const progress = ((currentStep + 1) / STEPS.length) * 100
  const CurrentStepComponent = STEPS[currentStep].component

  const handleNext = (stepData?: any) => {
    if (stepData) {
      setOnboardingData((prev) => ({ ...prev, ...stepData }))
    }
    if (currentStep < STEPS.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-background/95 backdrop-blur">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Newspaper className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold text-foreground">Daily Digest</span>
            </div>
            <div className="text-sm text-muted-foreground">
              Step {currentStep + 1} of {STEPS.length}
            </div>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="border-b border-border bg-muted/30">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="max-w-2xl mx-auto">
            <Progress value={progress} className="h-2" />
            <div className="flex justify-between mt-2 text-xs text-muted-foreground">
              {STEPS.map((step, index) => (
                <span key={step.id} className={index <= currentStep ? "text-primary font-medium" : ""}>
                  {step.title}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-2xl mx-auto">
          <CurrentStepComponent
            onNext={handleNext}
            onBack={handleBack}
            data={onboardingData}
            canGoBack={currentStep > 0}
            isLastStep={currentStep === STEPS.length - 1}
          />
        </div>
      </main>
    </div>
  )
}
