"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ChatWindow } from "@/features/chat/ChatWindow";
import { useApiClient } from "@/lib/api";
import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ChatPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const contractId = params?.contractId as string;
  const jobId = searchParams.get("job") || ""; 
  
  const { getContracts } = useApiClient();
  const [contractName, setContractName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await getContracts();
        const contract = data.contracts.find((c) => c.id === contractId);
        if (contract) setContractName(contract.original_filename);
      } catch (err) {
      } finally {
        setLoading(false);
      }
    }
    if (contractId) load();
  }, [contractId, getContracts]);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center gap-4 border-b bg-card px-6 py-4">
        {jobId ? (
          <Link href={`/scan/${jobId}`} className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        ) : (
          <Link href={`/dashboard`} className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-muted transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        )}
        <div>
          <h1 className="text-lg font-bold text-foreground">
            {loading ? <span className="animate-pulse bg-muted rounded h-5 w-32 inline-block"></span> : (contractName || "Contract Q&A")}
          </h1>
          <p className="text-xs text-muted-foreground">AI Legal Assistant</p>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <ChatWindow contractId={contractId} jobId={jobId} />
      </div>
    </div>
  );
}