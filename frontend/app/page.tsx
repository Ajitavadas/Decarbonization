'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { apiClient } from '@/lib/api';

export default function Home() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-card">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center">
              <h1 className="text-xl font-bold">Decarbonization Platform</h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">{user.email}</span>
              <button
                onClick={logout}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-2">Dashboard</h2>
          <p className="text-muted-foreground">
            Upload your organization's activity data to automatically classify and calculate carbon emissions.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Link
            href="/upload"
            className="bg-card border rounded-lg p-6 hover:border-primary transition-colors"
          >
            <h3 className="text-lg font-semibold mb-2">Upload Data</h3>
            <p className="text-sm text-muted-foreground">
              Upload CSV or XLSX files with activity data for AI classification and emission calculation.
            </p>
          </Link>

          <div className="bg-card border rounded-lg p-6 opacity-50">
            <h3 className="text-lg font-semibold mb-2">Projects</h3>
            <p className="text-sm text-muted-foreground">
              Manage your reporting projects (Coming soon)
            </p>
          </div>

          <div className="bg-card border rounded-lg p-6 opacity-50">
            <h3 className="text-lg font-semibold mb-2">Reports</h3>
            <p className="text-sm text-muted-foreground">
              View emission reports and analytics (Coming soon)
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
