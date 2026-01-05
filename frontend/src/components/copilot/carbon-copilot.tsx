"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Send, Sparkles, AlertCircle, Loader2, Bot, User, Lightbulb, FileQuestion } from "lucide-react"

interface Message {
    id: string
    role: "user" | "assistant" | "system"
    content: string
    type?: "ping" | "suggestion" | "confirmation"
    timestamp: Date
}

interface CarbonCopilotProps {
    open: boolean
    onClose: () => void
}

const initialMessages: Message[] = [
    {
        id: "1",
        role: "assistant",
        content:
            "Hello! I'm your Carbon Copilot. I'm constantly monitoring your emissions data and will ping you when I detect gaps or anomalies that need attention.",
        timestamp: new Date(Date.now() - 60000),
    },
    {
        id: "2",
        role: "system",
        type: "ping",
        content:
            "I noticed some patterns in your uploaded data. Would you like me to help analyze your Scope 1 emissions or suggest reduction strategies?",
        timestamp: new Date(Date.now() - 30000),
    },
]

const quickActions = [
    { label: "What data is missing?", icon: FileQuestion },
    { label: "Explain my emissions", icon: Lightbulb },
    { label: "Generate report", icon: Sparkles },
]

// Mock responses for skeleton mode
const mockResponses = [
    "Based on your uploaded data, I can see your Scope 2 emissions are primarily driven by electricity consumption. Consider exploring renewable energy certificates (RECs) to reduce your market-based emissions.",
    "Your total emissions have been calculated from the uploaded CSV. The main contributors are stationary combustion and electricity usage. I recommend reviewing your natural gas consumption patterns.",
    "I've analyzed your emissions data. To get a complete picture, you may want to upload additional data covering business travel and employee commuting for comprehensive Scope 3 reporting.",
    "Looking at your activity data, I notice some opportunities for emission reductions. Would you like me to suggest specific strategies for your highest-impact emission sources?",
]

export function CarbonCopilot({ open, onClose }: CarbonCopilotProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages)
    const [input, setInput] = useState("")
    const [isTyping, setIsTyping] = useState(false)
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    const handleSend = async () => {
        if (!input.trim()) return

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input,
            timestamp: new Date(),
        }

        setMessages((prev) => [...prev, userMessage])
        setInput("")
        setIsTyping(true)

        // Simulate AI response (skeleton mode - no real backend)
        setTimeout(() => {
            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: mockResponses[Math.floor(Math.random() * mockResponses.length)],
                timestamp: new Date(),
            }

            setMessages((prev) => [...prev, assistantMessage])
            setIsTyping(false)
        }, 1500)
    }

    const handleQuickAction = (action: string) => {
        setInput(action)
    }

    return (
        <div
            className={cn(
                "flex h-full w-96 flex-col border-l border-border bg-sidebar transition-all duration-300",
                !open && "w-0 overflow-hidden border-0",
            )}
        >
            {/* Header */}
            <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4">
                <div className="flex items-center gap-2">
                    <div className="relative flex h-8 w-8 items-center justify-center rounded-lg ai-gradient">
                        <Sparkles className="h-4 w-4 text-primary-foreground" />
                        <span className="pulse-ring absolute inset-0 rounded-lg" />
                    </div>
                    <div>
                        <h2 className="text-sm font-semibold text-sidebar-foreground">Carbon Copilot</h2>
                        <p className="text-xs text-muted-foreground">AI-powered assistant</p>
                    </div>
                </div>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onClose}
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>

            {/* Skeleton Mode Notice */}
            <div className="mx-4 mt-4 rounded-lg border border-info/30 bg-info/10 p-3">
                <p className="text-xs text-info flex items-center gap-2">
                    <Sparkles className="h-3 w-3" />
                    <span>Copilot is in demo mode. Full AI integration coming soon!</span>
                </p>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                <div className="space-y-4">
                    {messages.map((message) => (
                        <div key={message.id} className={cn("flex gap-3", message.role === "user" && "flex-row-reverse")}>
                            {/* Avatar */}
                            <div
                                className={cn(
                                    "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
                                    message.role === "user" && "bg-primary",
                                    message.role === "assistant" && "ai-gradient",
                                    message.role === "system" && "bg-warning/20",
                                )}
                            >
                                {message.role === "user" && <User className="h-4 w-4 text-primary-foreground" />}
                                {message.role === "assistant" && <Bot className="h-4 w-4 text-primary-foreground" />}
                                {message.role === "system" && <AlertCircle className="h-4 w-4 text-warning" />}
                            </div>

                            {/* Content */}
                            <div className={cn("max-w-[80%] space-y-1", message.role === "user" && "items-end")}>
                                {message.type === "ping" && <span className="text-xs font-medium text-warning">Data Insight</span>}
                                <div
                                    className={cn(
                                        "rounded-lg px-3 py-2 text-sm",
                                        message.role === "user" && "bg-primary text-primary-foreground",
                                        message.role === "assistant" && "bg-secondary text-foreground",
                                        message.role === "system" && "border border-warning/30 bg-warning/10 text-foreground",
                                    )}
                                >
                                    {message.content}
                                </div>
                                <span className="text-[10px] text-muted-foreground">
                                    {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                </span>
                            </div>
                        </div>
                    ))}

                    {isTyping && (
                        <div className="flex gap-3">
                            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full ai-gradient">
                                <Bot className="h-4 w-4 text-primary-foreground" />
                            </div>
                            <div className="flex items-center gap-1 rounded-lg bg-secondary px-3 py-2">
                                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                                <span className="text-sm text-muted-foreground">Analyzing...</span>
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Quick Actions */}
            <div className="border-t border-sidebar-border px-4 py-3">
                <div className="mb-3 flex flex-wrap gap-2">
                    {quickActions.map((action) => (
                        <Button
                            key={action.label}
                            variant="outline"
                            size="sm"
                            className="h-7 gap-1.5 border-border bg-secondary text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
                            onClick={() => handleQuickAction(action.label)}
                        >
                            <action.icon className="h-3 w-3" />
                            {action.label}
                        </Button>
                    ))}
                </div>

                {/* Input */}
                <div className="flex gap-2">
                    <Input
                        placeholder="Ask about your emissions..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleSend()}
                        className="bg-secondary border-0 focus-visible:ring-1 focus-visible:ring-primary"
                    />
                    <Button
                        size="icon"
                        onClick={handleSend}
                        disabled={!input.trim() || isTyping}
                        className="shrink-0 ai-gradient border-0"
                    >
                        <Send className="h-4 w-4" />
                    </Button>
                </div>
            </div>
        </div>
    )
}
