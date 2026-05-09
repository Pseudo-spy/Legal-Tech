"use client";

import { useState } from "react";
import { Clause } from "@/types/clause";
import { PrecedentMatch } from "@/types/api";
import { useApiClient } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { CaseCard } from "./CaseCard";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { EnforcementBadge } from "./EnforcementBadge";

interface PrecedentPanelProps {
  clause: Clause;
}

export function PrecedentPanel({ clause }: PrecedentPanelProps) {
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("idle");
  const [precedent, setPrecedent] = useState<PrecedentMatch | null>(null);
  const { getPrecedent } = useApiClient();

  if (clause.risk_level !== "HIGH") {
    return (
      <div className="flex h-full items-center justify-center p-8 text-sm text-muted-foreground">
        Legal precedent analysis is available for high-risk clauses.
      </div>
    );
  }

  const loadPrecedent = async () => {
    setStatus("loading");
    try {
      const data = await getPrecedent(clause.id);
      setPrecedent(data);
      setStatus("ready");
    } catch (err) {
      setStatus("error");
    }
  };

  if (status === "idle") {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <p className="text-muted-foreground">
          Find relevant case law and enforcement history for this type of clause.
        </p>
        <button
          onClick={loadPrecedent}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
        >
          Load Precedents
        </button>
      </div>
    );
  }

  if (status === "loading") {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="animate-pulse text-sm font-medium text-muted-foreground">
          Searching legal databases...
        </p>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex h-full flex-col items-center justify-center space-y-4 p-8 text-center">
        <p className="text-sm text-red-500">Failed to load precedent data.</p>
        <button
          onClick={loadPrecedent}
          className="rounded-md border bg-background px-4 py-2 text-sm font-medium shadow-sm hover:bg-muted"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!precedent) return null;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 space-y-8 duration-500">
      <div className="flex flex-col justify-between gap-6 md:flex-row md:items-start">
        <div className="flex-1 space-y-4">
          <h3 className="text-lg font-semibold text-foreground">Precedent Summary</h3>
          <p className="text-sm leading-relaxed text-foreground/90">{precedent.precedent_summary}</p>
          <div className="mt-4">
            <span className="mb-2 block text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Enforcement Likelihood
            </span>
            <EnforcementBadge likelihood={precedent.enforcement_likelihood as any} />
          </div>
        </div>
        <div className="flex shrink-0 justify-center">
          <ConfidenceBadge score={precedent.confidence_score} />
        </div>
      </div>

      <div className="border-t pt-6 space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          Cited Case Law
        </h3>
        <div className="grid grid-cols-1 gap-4">
          {precedent.cited_cases.map((c, idx) => (
            <CaseCard
              key={idx}
              caseName={c.name}
              year={c.year}
              jurisdiction={c.jurisdiction}
              outcome={c.outcome}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
