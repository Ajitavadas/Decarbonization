'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    useEffect(() => {
        console.error(error)
    }, [error])

    return (
        <div className="flex min-h-screen flex-col items-center justify-center">
            <div className="text-center">
                <h2 className="mb-4 text-2xl font-bold">Something went wrong!</h2>
                <p className="mb-4 text-muted-foreground">{error.message}</p>
                <Button onClick={() => reset()}>Try again</Button>
            </div>
        </div>
    )
}
