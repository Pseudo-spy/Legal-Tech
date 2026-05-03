import Link from "next/link";
import { UserButton, useUser } from "@clerk/nextjs";
import { LayoutDashboard, Upload } from "lucide-react";

export function Navbar() {
  const { isLoaded, isSignedIn } = useUser();

  if (!isLoaded) {
    return (
      <header className="sticky top-0 z-50 w-full border-b border-zinc-200 bg-white">
        <div className="flex h-16 items-center justify-between px-4">
          <div className="h-4 w-32 animate-pulse rounded bg-zinc-200" />
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-zinc-200 bg-white">
      <div className="flex h-16 items-center justify-between px-4 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-zinc-900">LegalTech AI</span>
          </Link>
          
          {isSignedIn && (
            <nav className="hidden items-center gap-6 md:flex">
              <Link
                href="/dashboard"
                className="flex items-center gap-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                <LayoutDashboard className="h-4 w-4" />
                Dashboard
              </Link>
              <Link
                href="/upload"
                className="flex items-center gap-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                <Upload className="h-4 w-4" />
                Upload
              </Link>
            </nav>
          )}
        </div>

        <div className="flex items-center gap-4">
          {isSignedIn ? (
            <UserButton />
          ) : (
            <div className="flex gap-2">
              <Link
                href="/sign-in"
                className="px-4 py-2 text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/sign-up"
                className="px-4 py-2 text-sm font-medium bg-zinc-900 text-white rounded-md hover:bg-zinc-800 transition-colors"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}