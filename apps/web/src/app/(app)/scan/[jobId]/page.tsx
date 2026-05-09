"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useScanStore } from "@/store/scanStore";
import { useClauseStore } from "@/store/clauseStore";
import { useApiClient } from "@/lib/api";
import { ClauseList } from "@/features/analysis/ClauseList";
import { ConsequencePanel } from "@/features/analysis/ConsequencePanel";
import { PowerMeter } from "@/features/power/PowerMeter";
import { CounterOfferPanel } from "@/features/counter-offer/CounterOfferPanel";
import { PrecedentPanel } from "@/features/precedent/PrecedentPanel";
import { Loader2, MessageSquare, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function ScanPage() {
  const params = useParams();
  const jobId = params?.jobId as string;
  const { status, setScanJob } = useScanStore();
  const { clauses, selectedClauseId } = useClauseStore();
  const { getScanJob, getClauses, getAnalysis, getPower } = useApiClient();
  const [activeTab, setActiveTab] = useState<"consequence" | "counter-offer" | "precedent">("consequence");
  const [initialLoading, setInitialLoading] = useState(true);

  // In a real app, we'd use useSSE hook here to stream clauses.
  // For now, we'll just mock the fetch or fetch completed data.
  useEffect(() => {
    async function loadData() {
      try {
        const job = await getScanJob(jobId);
        setScanJob(job.id, job.contract_id);
        
        if (job.status === "complete") {
          const fetchedClauses = await getClauses(job.contract_id);
          useClauseStore.getState().setClauses(fetchedClauses);
          
          const power = await getPower(job.contract_id);
          useScanStore.getState().setPowerResult(power);
          
          useScanStore.getState().setComplete();
        }
      } catch (err) {
        console.error(err);
      } finally {
        setInitialLoading(false);
      }
    }
    if (jobId) loadData();
  }, [jobId, getScanJob, getClauses, getPower, setScanJob]);

  const selectedClause = clauses.find(c => c.id === selectedClauseId);

  if (initialLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 h-full min-h-0 overflow-hidden container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">Contract Analysis</h1>
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">Integrity Scan In Progress</p>
          </div>
        </div>

        <Link
          href={`/chat/${useScanStore.getState().contractId}?job=${jobId}`}
          className="flex items-center gap-2 rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
        >
          <MessageSquare className="h-4 w-4" />
          Chat with AI
        </Link>
      </div>

      <div className="flex flex-col lg:flex-row flex-1 gap-6 overflow-y-auto lg:overflow-hidden min-h-0">
        
        {/* LEFT: Clause List */}
        <div className="w-full lg:w-[400px] xl:w-[450px] shrink-0 flex flex-col min-h-0 bg-background">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold tracking-tight">Contract Clauses</h2>
          </div>
          <div className="flex-1 min-h-0 relative">
             <ClauseList />
          </div>
        </div>

        {/* CENTER: Detail Panel */}
        <div className="flex-1 flex flex-col min-h-0 bg-card border rounded-xl shadow-sm overflow-hidden">
          {selectedClause ? (
            <div className="flex flex-col h-full">
               <div className="border-b bg-muted/30 p-4">
                 <div className="flex space-x-6">
                    <button 
                      onClick={() => setActiveTab("consequence")}
                      className={`pb-2 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'consequence' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
                    >
                      Consequence
                    </button>
                    <button 
                      onClick={() => setActiveTab("counter-offer")}
                      className={`pb-2 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'counter-offer' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
                    >
                      Counter-Offer
                    </button>
                    <button 
                      onClick={() => setActiveTab("precedent")}
                      className={`pb-2 text-sm font-semibold transition-colors border-b-2 ${activeTab === 'precedent' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
                    >
                      Precedent
                    </button>
                 </div>
               </div>
               <div className="flex-1 overflow-y-auto p-6">
                  {activeTab === "consequence" && <ConsequencePanel clause={selectedClause} />}
                  {activeTab === "counter-offer" && <CounterOfferPanel clause={selectedClause} />}
                  {activeTab === "precedent" && <PrecedentPanel clause={selectedClause} />}
               </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground flex-col gap-4">
               <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                 <span className="text-2xl opacity-50">📄</span>
               </div>
               <p>Select a clause from the list to see detailed analysis</p>
            </div>
          )}
        </div>

        {/* RIGHT: Power Meter */}
        <div className="w-full lg:w-[350px] shrink-0">
           <PowerMeter />
        </div>

      </div>
    </div>
  );
}