import { Link } from "lucide-react";
import NextLink from "next/link";

interface ClauseCitationProps {
  clauseId: string;
  jobId: string;
  label?: string;
}

export function ClauseCitation({ clauseId, jobId, label = "Cited Clause" }: ClauseCitationProps) {
  return (
    <NextLink
      href={`/scan/${jobId}?clause=${clauseId}`}
      className="mt-2 inline-flex items-center gap-1.5 rounded-full border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
    >
      <Link className="h-3 w-3" />
      {label}
    </NextLink>
  );
}
