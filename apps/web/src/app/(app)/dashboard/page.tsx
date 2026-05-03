"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useApiClient } from "@/lib/api";
import { Contract } from "@/types/api";

export default function DashboardPage() {
  const { getContracts, loading } = useApiClient();
  const [contracts, setContracts] = useState<Contract[]>([]);

  useEffect(() => {
    async function fetchContracts() {
      try {
        const response = await getContracts();
        setContracts(response.contracts || []);
      } catch (error) {
        console.error("Failed to fetch contracts:", error);
      }
    }
    fetchContracts();
  }, [getContracts]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <h1 className="text-2xl font-bold text-zinc-900 mb-4">Dashboard</h1>
      
      {loading ? (
        <p className="text-zinc-600">Loading...</p>
      ) : contracts.length > 0 ? (
        <div className="w-full max-w-2xl">
          <div className="grid gap-4">
            {contracts.map((contract) => (
              <div
                key={contract.id}
                className="p-4 border border-zinc-200 rounded-lg hover:bg-zinc-50"
              >
                <h3 className="font-semibold text-zinc-900">
                  {contract.original_filename}
                </h3>
                <p className="text-sm text-zinc-600">
                  Type: {contract.file_type} | Language: {contract.detected_language}
                </p>
                <p className="text-xs text-zinc-400">
                  Uploaded: {new Date(contract.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-zinc-600">Your contracts will appear here.</p>
      )}
      
      <Link
        href="/upload"
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
      >
        Upload Contract
      </Link>
    </div>
  );
}