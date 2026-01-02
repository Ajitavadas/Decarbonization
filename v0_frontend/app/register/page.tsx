"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { register } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Cloud } from "lucide-react"

export default function RegisterPage() {
    const [formData, setFormData] = useState({
        email: "",
        username: "",
        password: "",
        full_name: "",
        organization_name: ""
    })
    const [error, setError] = useState("")
    const [loading, setLoading] = useState(false)
    const router = useRouter()

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value })
    }

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault()
        setError("")
        setLoading(true)

        try {
            await register(formData)
            router.push("/login")
        } catch (err: any) {
            setError(err.message || "An error occurred during registration")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
            <Card className="w-full max-w-md border-border bg-card shadow-lg">
                <CardHeader className="space-y-1 text-center">
                    <div className="flex justify-center mb-2">
                        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
                            <Cloud className="h-6 w-6 text-primary" />
                        </div>
                    </div>
                    <CardTitle className="text-2xl font-bold tracking-tight">Create an account</CardTitle>
                    <CardDescription>Enter your details to get started with Decarbonization Platform</CardDescription>
                </CardHeader>
                <form onSubmit={handleRegister}>
                    <CardContent className="space-y-4">
                        {error && <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive">{error}</div>}

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="full_name">Full Name</label>
                            <Input id="full_name" placeholder="John Doe" onChange={handleChange} required />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="username">Username</label>
                            <Input id="username" placeholder="johndoe" onChange={handleChange} required />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="organization_name">Organization Name</label>
                            <Input id="organization_name" placeholder="Acme Corp" onChange={handleChange} required />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="email">Email</label>
                            <Input id="email" type="email" placeholder="name@example.com" onChange={handleChange} required />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium leading-none" htmlFor="password">Password</label>
                            <Input id="password" type="password" onChange={handleChange} required />
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-4">
                        <Button className="w-full" type="submit" disabled={loading}>
                            {loading ? "Creating account..." : "Register"}
                        </Button>
                        <div className="text-center text-sm text-muted-foreground">
                            Already have an account?{" "}
                            <Link href="/login" className="text-primary hover:underline underline-offset-4">
                                Sign in
                            </Link>
                        </div>
                    </CardFooter>
                </form>
            </Card>
        </div>
    )
}
