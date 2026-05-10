"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { useScanStore } from "@/store/scanStore";
import { useClauseStore } from "@/store/clauseStore";
import { useApiClient } from "@/lib/api";
import { useSSE, ClauseResult } from "@/hooks/useSSE";
import { ClauseList } from "@/features/analysis/ClauseList";
import { ConsequencePanel } from "@/features/analysis/ConsequencePanel";
import { PowerMeter } from "@/features/power/PowerMeter";
import { CounterOfferPanel } from "@/features/counter-offer/CounterOfferPanel";
import { PrecedentPanel } from "@/features/precedent/PrecedentPanel";
import { SummaryCard, SummaryCardSkeleton } from "@/features/summary/SummaryCard";
import { ProsConsSnapshot } from "@/features/summary/ProsConsSnapshot";
import { Loader2, MessageSquare, ShieldCheck, X } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Clause, RiskLevel, RiskCategory } from "@/types/clause";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function mapRiskLevel(s: string): RiskLevel {
  const upper = s.toUpperCase();
  if (upper === "HIGH") return "HIGH";
  if (upper === "MEDIUM") return "MEDIUM";
  if (upper === "LOW") return "LOW";
  return "SAFE";
}

function mapRiskCategory(cats: string[]): RiskCategory {
  if (!cats || cats.length === 0) return "other";
  const cat = cats[0].toLowerCase();
  if (cat.includes("indemnity")) return "indemnity";
  if (cat.includes("ip") || cat.includes("intellectual")) return "ip_assignment";
  if (cat.includes("non-compete") || cat.includes("non_compete")) return "non_compete";
  if (cat.includes("renewal") || cat.includes("auto_renewal")) return "auto_renewal";
  if (cat.includes("liability") || cat.includes("limitation")) return "limitation_of_liability";
  if (cat.includes("termination")) return "termination";
  if (cat.includes("payment")) return "payment";
  if (cat.includes("governing")) return "governing_law";
  return "other";
}

export default function ScanPage() {
  const params = useParams();
  const jobId = params?.jobId as string;
  const { getToken } = useAuth();
  const api = useApiClient();
  const { clauses, selectedClauseId } = useClauseStore();
  const {
    status,
    progressPct,
    powerResult,
    summaryResult,
    setScanJob,
    updateProgress,
    setPowerResult,
    setSummaryResult,
    setComplete,
    contractId,
  } = useScanStore();

  const [initialLoading, setInitialLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"consequence" | "counter-offer" | "precedent">("consequence");
  const [mobilePanelOpen, setMobilePanelOpen] = useState(false);
  const [sseConnected, setSseConnected] = useState(false);

  const onClause = useCallback(
    (result: ClauseResult) => {
      const clause: Clause = {
        id: `${result.clause_index}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        contract_id: contractId || "",
        text: result.clause_text || "",
        position_index: result.clause_index || 0,
        risk_level: mapRiskLevel(result.risk_severity),
        risk_category: mapRiskCategory(result.risk_categories),
        plain_english: result.explanation || "",
        worst_case: result.recommendation || null,
        financial_exposure: null,
        negotiable: false,
        confidence: 0.85,
      };
      useClauseStore.getState().addClause(clause);
    },
    [contractId]
  );

  const onProgress = useCallback(
    (pct: number, _step: string) => {
      updateProgress(pct);
    },
    [updateProgress]
  );

  const onComplete = useCallback(async () => {
    if (contractId) {
      try {
        const [power, summaryData] = await Promise.all([
          api.getPower(contractId),
          api.getSummary(contractId),
        ]);
        setPowerResult(power);
        setSummaryResult(summaryData);
      } catch (e) {
        console.error("Failed to fetch final data on complete:", e);
      }
    }
    setComplete();
  }, [contractId, api, setPowerResult, setSummaryResult, setComplete]);

  const onError = useCallback((error: string) => {
    console.error("SSE Error:", error);
  }, []);

  const { status: sseStatus, connect, disconnect } = useSSE({
    token: "",
    baseUrl: `${API_URL}/api`,
    onClause,
    onProgress,
    onComplete,
    onError,
  });

  useEffect(() => {
    async function loadData() {
      if (!jobId) return;
      try {
        const job = await api.getScanJob(jobId);
        setScanJob(job.id, job.contract_id);

        if (job.status === "complete") {
          const fetchedClauses = await api.getClauses(job.contract_id);
          useClauseStore.getState().setClauses(fetchedClauses);

          try {
            const power = await api.getPower(job.contract_id);
            setPowerResult(power);
          } catch (e) {
            console.error("Failed to load power data:", e);
          }

          try {
            const summary = await api.getSummary(job.contract_id);
            setSummaryResult(summary);
          } catch (e) {
            console.error("Failed to load summary data:", e);
          }

          setComplete();
        }
      } catch (err) {
        console.error("Error loading scan data:", err);
      } finally {
        setInitialLoading(false);
      }
    }
    loadData();
  }, [jobId]);

  useEffect(() => {
    // SSE disabled - upload completes synchronously so no streaming needed
    // Data loads from REST API instead
  }, [status, sseConnected, jobId, getToken, connect, disconnect]);

  const selectedClause = clauses.find((c) => c.id === selectedClauseId);

  const openMobilePanel = (clauseId: string) => {
    useClauseStore.getState().selectClause(clauseId);
    setMobilePanelOpen(true);
    setActiveTab("consequence");
  };

  const closeMobilePanel = () => {
    setMobilePanelOpen(false);
  };

  if (initialLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const showSummaryCard = status === "complete" && summaryResult;
  const showProsCons = status === "complete" && summaryResult;
  const showPowerMeter = status === "complete" && powerResult;

  return (
    <div className="flex flex-col h-full min-h-0 overflow-hidden container mx-auto py-4 md:py-6 px-4 gap-4 md:gap-6">
      <div className="flex items-center justify-between border-b pb-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="hidden md:flex h-10 w-10 rounded-xl bg-primary/10 items-center justify-center">
            <ShieldCheck className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold tracking-tight">Contract Analysis</h1>
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold">
              {status === "complete" ? "Scan Complete" : "Integrity Scan In Progress"}
            </p>
          </div>
        </div>

        <Link
          href={`/chat/${contractId || ""}?job=${jobId}`}
          className="flex items-center gap-2 rounded-lg bg-zinc-900 px-3 md:px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
        >
          <MessageSquare className="h-4 w-4" />
          <span className="hidden sm:inline">Chat with AI</span>
        </Link>
      </div>

      {showSummaryCard ? (
        <div className="shrink-0">
          <SummaryCard data={summaryResult!} />
        </div>
      ) : (
        status !== "complete" && (
          <div className="shrink-0">
            <SummaryCardSkeleton />
          </div>
        )
      )}

      <div className="flex-1 flex flex-col lg:flex-row gap-4 md:gap-6 min-h-0 overflow-hidden">
        <div className="w-full lg:w-[380px] xl:w-[440px] shrink-0 flex flex-col min-h-0 bg-background order-2 lg:order-1">
          <div className="flex items-center justify-between mb-4 shrink-0">
            <h2 className="text-lg font-bold tracking-tight">Contract Clauses</h2>
          </div>
          <div
            className="flex-1 min-h-0 relative"
            onClick={(e) => {
              const card = (e.target as HTMLElement).closest("[data-clause-id]");
              if (card) {
                openMobilePanel(card.getAttribute("data-clause-id")!);
              }
            }}
          >
            <ClauseList onCardClick={openMobilePanel} />
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0 bg-card border rounded-xl shadow-sm overflow-hidden order-1 lg:order-2">
          <div className="border-b bg-muted/30 p-4 shrink-0">
            <div className="flex space-x-4 md:space-x-6">
              {["consequence", "counter-offer", "precedent"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab as typeof activeTab)}
                  className={`pb-2 text-sm font-semibold transition-colors border-b-2 ${
                    activeTab === tab
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <AnimatePresence mode="wait">
              {selectedClause ? (
                <motion.div
                  key={selectedClause.id + activeTab}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                >
                  {activeTab === "consequence" && <ConsequencePanel clause={selectedClause} />}
                  {activeTab === "counter-offer" && <CounterOfferPanel clause={selectedClause} />}
                  {activeTab === "precedent" && <PrecedentPanel clause={selectedClause} />}
                </motion.div>
              ) : (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center justify-center h-full text-muted-foreground flex-col gap-4"
                >
                  <div className="h-16 w-16 rounded-full bg-muted flex items-center justify-center">
                    <span className="text-2xl opacity-50">📄</span>
                  </div>
                  <p className="text-sm text-center px-4">Select a clause from the list to see detailed analysis</p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        <div className="w-full lg:w-[320px] xl:w-[360px] shrink-0 order-3 hidden lg:block">
          <div className="sticky top-0">
            {showPowerMeter ? (
              <PowerMeter />
            ) : (
              <div className="rounded-xl border bg-card p-8 shadow-sm">
                <div className="flex flex-col items-center justify-center space-y-6">
                  <div className="h-40 w-full max-w-[300px] animate-pulse rounded-t-full bg-muted/50" />
                  <div className="h-6 w-48 animate-pulse rounded bg-muted/50" />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {showProsCons && summaryResult && (
        <div className="shrink-0">
          <ProsConsSnapshot
            topConcerns={summaryResult.top_3_concerns}
            topPositives={summaryResult.top_2_positives}
            verdict={summaryResult.one_liner}
          />
        </div>
      )}

      <AnimatePresence>
        {mobilePanelOpen && selectedClause && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50 lg:hidden"
            onClick={closeMobilePanel}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="absolute bottom-0 left-0 right-0 max-h-[85vh] bg-card rounded-t-2xl shadow-xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b p-4">
                <h3 className="font-semibold text-sm">Clause Details</h3>
                <button
                  onClick={closeMobilePanel}
                  className="p-1.5 rounded-full hover:bg-muted transition-colors"
                >
                  <X className="h-5 w-5 text-muted-foreground" />
                </button>
              </div>
              <div className="border-b bg-muted/30 px-4">
                <div className="flex space-x-4">
                  {["consequence", "counter-offer", "precedent"].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab as typeof activeTab)}
                      className={`pb-2 text-sm font-semibold transition-colors border-b-2 ${
                        activeTab === tab
                          ? "border-primary text-primary"
                          : "border-transparent text-muted-foreground"
                      }`}
                    >
                      {tab.charAt(0).toUpperCase() + tab.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <div className="overflow-y-auto p-4 pb-8" style={{ maxHeight: "calc(85vh - 100px)" }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={selectedClause.id + activeTab}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    {activeTab === "consequence" && <ConsequencePanel clause={selectedClause} />}
                    {activeTab === "counter-offer" && <CounterOfferPanel clause={selectedClause} />}
                    {activeTab === "precedent" && <PrecedentPanel clause={selectedClause} />}
                  </motion.div>
                </AnimatePresence>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
