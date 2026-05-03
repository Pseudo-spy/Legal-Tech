import { Shield } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-zinc-200 bg-zinc-50 py-6 px-4">
      <div className="flex flex-col items-center justify-between gap-2 md:flex-row md:px-8">
        <div className="flex items-center gap-2 text-sm text-zinc-500">
          <Shield className="h-4 w-4" />
          <span>Not legal advice. For informational purposes only.</span>
        </div>
        <p className="text-sm text-zinc-400">
          © {new Date().getFullYear()} LegalTech AI. All rights reserved.
        </p>
      </div>
    </footer>
  );
}