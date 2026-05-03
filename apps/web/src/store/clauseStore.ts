import { create } from "zustand";
import { Clause, RiskLevel } from "@/types/clause";

interface ClauseState {
  clauses: Clause[];
  selectedClauseId: string | null;
  filter: RiskLevel | "ALL";
  addClause: (clause: Clause) => void;
  setClauses: (clauses: Clause[]) => void;
  selectClause: (clauseId: string | null) => void;
  setFilter: (filter: RiskLevel | "ALL") => void;
  reset: () => void;
}

export const useClauseStore = create<ClauseState>()((set) => ({
  clauses: [],
  selectedClauseId: null,
  filter: "ALL",
  addClause: (clause) =>
    set((state) => ({ clauses: [...state.clauses, clause] })),
  setClauses: (clauses) => set({ clauses }),
  selectClause: (clauseId) => set({ selectedClauseId: clauseId }),
  setFilter: (filter) => set({ filter }),
  reset: () => set({ clauses: [], selectedClauseId: null, filter: "ALL" }),
}));