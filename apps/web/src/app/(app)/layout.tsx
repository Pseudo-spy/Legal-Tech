"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter, usePathname } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { Footer } from "@/components/layout/Footer";
import { Menu } from "lucide-react";
import { useApiClient } from "@/lib/api";
import { Contract } from "@/types/api";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [recentContracts, setRecentContracts] = useState<Contract[]>([]);
  const { getContracts } = useApiClient();

  useEffect(() => {
    if (isSignedIn) {
      getContracts()
        .then((response) => {
          setRecentContracts(response.contracts || []);
        })
        .catch(console.error);
    }
  }, [isSignedIn, getContracts]);

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-200 border-t-zinc-900" />
      </div>
    );
  }

  if (!isSignedIn) {
    router.push("/sign-in");
    return null;
  }

  const isScanPage = pathname?.startsWith("/scan/");

  return (
    <div className="min-h-screen flex flex-col bg-zinc-50">
      <Navbar />
      <div className="flex flex-1">
        {!isScanPage && (
          <>
            <button
              onClick={() => setSidebarOpen(true)}
              className="fixed left-4 bottom-4 z-30 p-2 bg-zinc-900 text-white rounded-full shadow-lg md:hidden"
            >
              <Menu className="h-5 w-5" />
            </button>
            <Sidebar 
              isOpen={sidebarOpen} 
              onClose={() => setSidebarOpen(false)}
              recentContracts={recentContracts.map(c => ({
                id: c.id,
                file_name: c.original_filename,
                overall_risk_score: 0
              }))}
            />
          </>
        )}
        <main className="flex-1 p-4 md:p-8">
          {children}
        </main>
      </div>
      <Footer />
    </div>
  );
}