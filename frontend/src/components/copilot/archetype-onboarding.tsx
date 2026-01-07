"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Sparkles, Check, ArrowRight, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

interface Archetype {
    id: string
    name: string
    icon: string
    tagline: string
    description: string
    examples: string[]
    dominant_scope: string
}

interface ArchetypeOnboardingProps {
    open: boolean
    onComplete: () => void
    organizationName: string
}

export function ArchetypeOnboarding({ open, onComplete, organizationName }: ArchetypeOnboardingProps) {
    const [archetypes, setArchetypes] = useState<Archetype[]>([])
    const [selectedArchetype, setSelectedArchetype] = useState<string | null>(null)
    const [step, setStep] = useState<"welcome" | "selection" | "confirm">("welcome")
    const [isLoading, setIsLoading] = useState(false)
    const [isSaving, setIsSaving] = useState(false)

    useEffect(() => {
        if (open) {
            loadArchetypes()
        }
    }, [open])

    const loadArchetypes = async () => {
        setIsLoading(true)
        try {
            const response = await api.getArchetypes()
            setArchetypes(response.archetypes)
        } catch (error) {
            console.error("Failed to load archetypes:", error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleConfirm = async () => {
        if (!selectedArchetype) return

        setIsSaving(true)
        try {
            await api.setOrganizationArchetype(selectedArchetype)
            onComplete()
        } catch (error) {
            console.error("Failed to set archetype:", error)
        } finally {
            setIsSaving(false)
        }
    }

    const getSelectedArchetypeData = () => {
        return archetypes.find(a => a.id === selectedArchetype)
    }

    if (!open) return null

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="relative w-full max-w-4xl mx-4 max-h-[90vh] bg-background rounded-2xl shadow-2xl border border-border flex flex-col">
                {/* Header */}
                <div className="px-8 py-6 border-b border-border bg-gradient-to-r from-primary/10 to-info/10 flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="relative flex h-12 w-12 items-center justify-center rounded-xl ai-gradient">
                            <Sparkles className="h-6 w-6 text-primary-foreground" />
                            <span className="pulse-ring absolute inset-0 rounded-xl" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold text-foreground">Carbon Copilot</h1>
                            <p className="text-sm text-muted-foreground">Let's personalize your experience</p>
                        </div>
                    </div>
                </div>

                {/* Content - Scrollable */}
                <div className="flex-1 overflow-y-auto p-8">
                    {step === "welcome" && (
                        <div className="text-center space-y-6 py-8">
                            <div className="text-6xl mb-6">👋</div>
                            <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-info bg-clip-text text-transparent">
                                Welcome to {organizationName}!
                            </h2>
                            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
                                I'm your Carbon Copilot, here to help you track and reduce your carbon footprint.
                                Before we start, I'd love to learn more about your organization so I can provide
                                <strong className="text-foreground"> personalized insights and anomaly detection</strong>.
                            </p>
                            <p className="text-muted-foreground">
                                This will only take a moment! 🌱
                            </p>
                            <Button
                                size="lg"
                                className="ai-gradient mt-4"
                                onClick={() => setStep("selection")}
                            >
                                Let's Get Started
                                <ArrowRight className="ml-2 h-5 w-5" />
                            </Button>
                        </div>
                    )}

                    {step === "selection" && (
                        <div className="space-y-6">
                            <div className="text-center mb-8">
                                <h2 className="text-2xl font-bold text-foreground mb-2">
                                    What best describes your organization?
                                </h2>
                                <p className="text-muted-foreground">
                                    Select the archetype that fits your business. This helps me understand your emission patterns.
                                </p>
                            </div>

                            {isLoading ? (
                                <div className="flex justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {archetypes.map((archetype) => (
                                        <button
                                            key={archetype.id}
                                            onClick={() => setSelectedArchetype(archetype.id)}
                                            className={cn(
                                                "relative p-5 rounded-xl border-2 text-left transition-all duration-200 hover:shadow-lg",
                                                selectedArchetype === archetype.id
                                                    ? "border-primary bg-primary/5 shadow-md"
                                                    : "border-border hover:border-primary/50 bg-card"
                                            )}
                                        >
                                            {selectedArchetype === archetype.id && (
                                                <div className="absolute top-3 right-3 h-6 w-6 rounded-full bg-primary flex items-center justify-center">
                                                    <Check className="h-4 w-4 text-primary-foreground" />
                                                </div>
                                            )}

                                            <div className="flex items-start gap-4">
                                                <span className="text-3xl">{archetype.icon}</span>
                                                <div className="flex-1 min-w-0">
                                                    <h3 className="font-semibold text-foreground text-lg">
                                                        {archetype.name}
                                                    </h3>
                                                    <p className="text-sm text-primary font-medium mb-2">
                                                        "{archetype.tagline}"
                                                    </p>
                                                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                                                        {archetype.description}
                                                    </p>
                                                    <div className="flex flex-wrap gap-1.5">
                                                        {archetype.examples.slice(0, 3).map((example, i) => (
                                                            <span
                                                                key={i}
                                                                className="text-xs px-2 py-0.5 rounded-full bg-secondary text-secondary-foreground"
                                                            >
                                                                {example}
                                                            </span>
                                                        ))}
                                                    </div>
                                                    <p className="text-xs text-info mt-2 font-medium">
                                                        📊 Expected: {archetype.dominant_scope}
                                                    </p>
                                                </div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {step === "confirm" && (
                        <div className="text-center space-y-6 py-8">
                            {getSelectedArchetypeData() && (
                                <>
                                    <span className="text-6xl">{getSelectedArchetypeData()?.icon}</span>
                                    <h2 className="text-2xl font-bold text-foreground">
                                        Great choice! You're <span className="text-primary">{getSelectedArchetypeData()?.name}</span>
                                    </h2>
                                    <p className="text-muted-foreground max-w-xl mx-auto">
                                        {getSelectedArchetypeData()?.description}
                                    </p>
                                    <div className="bg-info/10 border border-info/30 rounded-lg p-4 max-w-md mx-auto">
                                        <p className="text-sm text-info">
                                            <strong>What this means:</strong> I'll use industry-specific benchmarks to identify
                                            anomalies and gaps in your emission data. Your expected scope distribution is{" "}
                                            <strong>{getSelectedArchetypeData()?.dominant_scope}</strong>.
                                        </p>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-8 py-4 border-t border-border bg-muted/30 flex justify-between items-center flex-shrink-0">
                    {step === "welcome" && (
                        <div />
                    )}

                    {step === "selection" && (
                        <>
                            <Button variant="ghost" onClick={() => setStep("welcome")}>
                                Back
                            </Button>
                            <Button
                                className="ai-gradient"
                                onClick={() => setStep("confirm")}
                                disabled={!selectedArchetype}
                            >
                                Continue
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </>
                    )}

                    {step === "confirm" && (
                        <>
                            <Button variant="ghost" onClick={() => setStep("selection")}>
                                Change Selection
                            </Button>
                            <Button
                                className="ai-gradient"
                                onClick={handleConfirm}
                                disabled={isSaving}
                            >
                                {isSaving ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Saving...
                                    </>
                                ) : (
                                    <>
                                        Let's Go! 🚀
                                    </>
                                )}
                            </Button>
                        </>
                    )}
                </div>
            </div>
        </div >
    )
}
