"use client";

import { useState } from "react";
import { Clause } from "@/types/clause";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { CounterOfferPanel } from "@/features/counter-offer/CounterOfferPanel";
import { PrecedentPanel } from "@/features/precedent/PrecedentPanel";

interface ConsequencePanelProps {
  clause: Clause;
}

const probabilityConfig = {
  Low: {
    label: "Low",
    color: "bg-green-100 text-green-700 dark:bg-green-950/40 dark:text-green-400 border-green-300",
  },
  Medium: {
    label: "Medium",
    color: "bg-amber-100 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-300",
  },
  High: {
    label: "High",
    color: "bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 border-red-300",
  },
};

export function ConsequencePanel({ clause }: ConsequencePanelProps) {
  if (!clause.worst_case && !clause.headline) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-sm text-muted-foreground">
        <div className="text-center">
          <p>Consequence analysis not available for this clause.</p>
          <p className="mt-2 text-xs text-muted-foreground/70">
            Analysis data may still be loading.
          </p>
        </div>
      </div>
    );
  }

  const headline = clause.headline || clause.worst_case || "";
  const scenario = clause.scenario || clause.plain_english || "";
  const probability = clause.probability || "Medium";
  const probConfig = probabilityConfig[probability] || probabilityConfig.Medium;
  const isNegotiable = clause.negotiable;

  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-muted/30 p-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Original Clause Text
        </h4>
        <p className="text-sm leading-relaxed text-foreground/80">{clause.text}</p>
      </div>

      <div className="space-y-4">
        <h2 className="text-2xl font-bold tracking-tight text-foreground md:text-3xl">
          {headline}
        </h2>

        {clause.financial_exposure && (
          <div className="text-3xl font-extrabold tracking-tight text-red-600 dark:text-red-500 md:text-4xl">
            {clause.financial_exposure.startsWith("$") ? "" : "$"}
            {clause.financial_exposure}
            <span className="ml-2 text-lg font-normal text-muted-foreground">
              potential liability
            </span>
          </div>
        )}

        <div className="prose prose-sm dark:prose-invert max-w-none text-foreground/90 leading-relaxed">
          <p>{scenario}</p>
        </div>

        <div className="flex flex-wrap items-center gap-4 border-t pt-4">
          <span
            className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold ${probConfig.color}`}
          >
            {probConfig.label} Probability
          </span>

          {clause.similar_case && (
            <span className="text-xs italic text-muted-foreground">
              Similar case: {clause.similar_case}
            </span>
          )}

          {isNegotiable ? (
            <span className="ml-auto flex items-center gap-1.5 rounded-full bg-green-50 px-3 py-1 text-sm font-medium text-green-700 dark:bg-green-950/30 dark:text-green-400 border border-green-300">
              <CheckCircle2 className="h-4 w-4" />
              Negotiable
            </span>
          ) : (
            <span className="ml-auto flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-400 border border-slate-300">
              <AlertCircle className="h-4 w-4" />
              Typically Non-Negotiable
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
