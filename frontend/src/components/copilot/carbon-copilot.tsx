"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { X, Send, Sparkles, AlertCircle, Loader2, Bot, User, Lightbulb, FileQuestion, Database } from "lucide-react"
import { api } from "@/lib/api"

interface Message {
    id: string
    role: "user" | "assistant" | "system"
    content: string
    type?: "ping" | "suggestion" | "confirmation"
    source?: "deterministic" | "llm" | "cache" | "error"
    suggestions?: string[]
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
            "Hello! I'm your Carbon Copilot. Ask me about your emissions data - I'm connected to your real-time analytics.",
        source: "deterministic",
        timestamp: new Date(Date.now() - 60000),
    },
]

const quickActions = [
    { label: "What are my total emissions?", icon: FileQuestion },
    { label: "Show my emission trend", icon: Lightbulb },
    { label: "How can I reduce emissions?", icon: Sparkles },
]

export function CarbonCopilot({ open, onClose }: CarbonCopilotProps) {
    const [messages, setMessages] = useState<Message[]>(initialMessages)
    const [input, setInput] = useState("")
    const [isTyping, setIsTyping] = useState(false)
    const [suggestions, setSuggestions] = useState<string[]>([])
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
        const currentInput = input
        setInput("")
        setIsTyping(true)
        setSuggestions([])

        try {
            // Build history from recent messages
            const history = messages.slice(-6).map((m) => ({
                role: m.role,
                content: m.content,
                source: m.source,
            }))

            // Call real API
            const response = await api.chatWithCopilot(currentInput, history, true)

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: response.text,
                source: response.source,
                suggestions: response.suggestions,
                timestamp: new Date(),
            }

            setMessages((prev) => [...prev, assistantMessage])
            setSuggestions(response.suggestions || [])
        } catch (error) {
            console.error("Copilot error:", error)
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: "I'm having trouble connecting to the analytics service. Please try again.",
                source: "error",
                timestamp: new Date(),
            }
            setMessages((prev) => [...prev, errorMessage])
        } finally {
            setIsTyping(false)
        }
    }

    const handleQuickAction = (action: string) => {
        setInput(action)
    }

    const handleSuggestion = (suggestion: string) => {
        setInput(suggestion)
    }

    // Source badge color
    const getSourceBadge = (source?: string) => {
        switch (source) {
            case "deterministic":
                return { label: "Data-based", icon: Database, className: "text-emerald-500" }
            case "llm":
                return { label: "AI-enhanced", icon: Sparkles, className: "text-purple-500" }
            case "cache":
                return { label: "Cached", icon: Database, className: "text-blue-500" }
            default:
                return null
        }
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
                        <p className="text-xs text-muted-foreground">Connected to your data</p>
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

            {/* Connected Notice */}
            <div className="mx-4 mt-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3">
                <p className="text-xs text-emerald-500 flex items-center gap-2">
                    <Database className="h-3 w-3" />
                    <span>Live connection to your emissions data</span>
                </p>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                <div className="space-y-4">
                    {messages.map((message) => {
                        const sourceBadge = message.role === "assistant" ? getSourceBadge(message.source) : null

                        return (
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
                                    {sourceBadge && (
                                        <span className={cn("text-[10px] font-medium flex items-center gap-1", sourceBadge.className)}>
                                            <sourceBadge.icon className="h-2.5 w-2.5" />
                                            {sourceBadge.label}
                                        </span>
                                    )}
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
                                    <span className="text-[10px] text-muted-foreground" suppressHydrationWarning>
                                        {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                    </span>
                                </div>
                            </div>
                        )
                    })}

                    {isTyping && (
                        <div className="flex gap-3">
                            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full ai-gradient">
                                <Bot className="h-4 w-4 text-primary-foreground" />
                            </div>
                            <div className="flex items-center gap-1 rounded-lg bg-secondary px-3 py-2">
                                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                                <span className="text-sm text-muted-foreground">Analyzing your data...</span>
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Dynamic Suggestions from API */}
            {suggestions.length > 0 && (
                <div className="border-t border-sidebar-border px-4 py-2">
                    <p className="text-[10px] text-muted-foreground mb-2">Suggested follow-ups:</p>
                    <div className="flex flex-wrap gap-2">
                        {suggestions.map((suggestion, idx) => (
                            <Button
                                key={idx}
                                variant="outline"
                                size="sm"
                                className="h-6 text-[10px] border-primary/20 bg-primary/5 text-primary hover:bg-primary/10"
                                onClick={() => handleSuggestion(suggestion)}
                            >
                                {suggestion}
                            </Button>
                        ))}
                    </div>
                </div>
            )}

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
