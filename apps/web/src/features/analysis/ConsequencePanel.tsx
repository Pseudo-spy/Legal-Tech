import { Clause } from "@/types/clause";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface ConsequencePanelProps {
  clause: Clause;
}

export function ConsequencePanel({ clause }: ConsequencePanelProps) {
  if (!clause.worst_case) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-sm text-muted-foreground">
        Consequence analysis not available for this clause.
      </div>
    );
  }

  const isNegotiable = clause.negotiable;

  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-muted/30 p-4">
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Original Clause Text
        </h4>
        <p className="text-sm leading-relaxed text-foreground/80">{clause.text}</p>
      </div>

      <div className="space-y-3">
        <h2 className="text-xl font-bold tracking-tight text-foreground md:text-2xl">
          {clause.worst_case}
        </h2>
        
        {clause.financial_exposure && (
          <div className="text-3xl font-extrabold tracking-tight text-red-600 dark:text-red-500 md:text-4xl">
            {clause.financial_exposure.startsWith("$") ? "" : "$"}
            {clause.financial_exposure}
          </div>
        )}

        <div className="prose prose-sm dark:prose-invert max-w-none text-foreground/90">
          <p>{clause.plain_english}</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 border-t pt-4">
        {isNegotiable ? (
          <span className="flex items-center gap-1.5 rounded-full bg-green-50 px-2.5 py-1 text-sm font-medium text-green-700 dark:bg-green-950/30 dark:text-green-400">
            <CheckCircle2 className="h-4 w-4" />
            Negotiable ✓
          </span>
        ) : (
          <span className="flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-sm font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-400">
            <AlertCircle className="h-4 w-4" />
            Typically Non-Negotiable
          </span>
        )}
      </div>
    </div>
  );
}
