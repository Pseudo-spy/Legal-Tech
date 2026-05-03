"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, X } from "lucide-react";
import { useUIStore } from "@/store/uiStore";

interface SidebarContract {
  id: string;
  file_name: string;
  overall_risk_score: number;
}

interface SidebarProps {
  recentContracts?: SidebarContract[];
  isOpen?: boolean;
  onClose?: () => void;
}

function RiskBadge({ score }: { score: number }) {
  const getColor = () => {
    if (score <= 30) return "bg-green-100 text-green-700";
    if (score <= 60) return "bg-yellow-100 text-yellow-700";
    return "bg-red-100 text-red-700";
  };

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded ${getColor()}`}>
      {score}
    </span>
  );
}

export function Sidebar({ recentContracts = [], isOpen = true, onClose }: SidebarProps) {
  const pathname = usePathname();
  const isScanPage = pathname?.startsWith("/scan/");

  if (isScanPage) return null;

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/20 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-16 z-40 h-[calc(100vh-4rem)] w-64 transform bg-white border-r border-zinc-200 overflow-y-auto
          transition-transform duration-200 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          md:relative md:translate-x-0
        `}
      >
        <div className="flex items-center justify-between p-4 border-b border-zinc-100 md:hidden">
          <h2 className="font-semibold text-zinc-900">Recent Contracts</h2>
          <button onClick={onClose} className="p-1 hover:bg-zinc-100 rounded">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4">
          <h2 className="hidden md:block font-semibold text-zinc-900 mb-4">
            Recent Contracts
          </h2>

          {recentContracts.length === 0 ? (
            <p className="text-sm text-zinc-500">No contracts yet</p>
          ) : (
            <ul className="space-y-2">
              {recentContracts.slice(0, 5).map((contract) => (
                <li key={contract.id}>
                  <Link
                    href={`/scan/${contract.id}`}
                    className="flex items-center justify-between p-2 rounded-md hover:bg-zinc-50 transition-colors"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="h-4 w-4 flex-shrink-0 text-zinc-400" />
                      <span className="text-sm text-zinc-700 truncate">
                        {contract.file_name}
                      </span>
                    </div>
                    <RiskBadge score={contract.overall_risk_score} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-zinc-100">
          <Link
            href="/upload"
            className="flex items-center justify-center w-full px-4 py-2 text-sm font-medium bg-zinc-900 text-white rounded-md hover:bg-zinc-800 transition-colors"
          >
            + New Scan
          </Link>
        </div>
      </aside>
    </>
  );
}