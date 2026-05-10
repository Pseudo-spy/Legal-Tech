"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useClauseStore } from "@/store/clauseStore";
import { useScanStore } from "@/store/scanStore";
import {
  DEMO_CLAUSES,
  DEMO_SUMMARY,
  DEMO_POWER,
  DEMO_SCAN_JOB,
  DEMO_JOB_ID,
  DEMO_CONTRACT_ID,
} from "@/lib/demo-data";

interface DemoContextValue {
  isDemoMode: boolean;
  simulateScan: () => void;
  resetDemo: () => void;
}

const DemoContext = createContext<DemoContextValue>({
  isDemoMode: false,
  simulateScan: () => {},
  resetDemo: () => {},
});

export function DemoProvider({ children }: { children: ReactNode }) {
  const [isDemoMode, setIsDemoMode] = useState(false);
  const { setClauses, selectClause, reset } = useClauseStore();
  const { setScanJob, setPowerResult, setSummaryResult, setComplete, reset: resetScan } = useScanStore();

  const simulateScan = () => {
    setIsDemoMode(true);
    setScanJob(DEMO_JOB_ID, DEMO_CONTRACT_ID);

    const totalClauses = DEMO_CLAUSES.length;
    let currentIndex = 0;

    const addClause = () => {
      if (currentIndex < totalClauses) {
        const clause = DEMO_CLAUSES[currentIndex];
        useClauseStore.getState().addClause({ ...clause, id: `${clause.id}-${Date.now()}` });
        currentIndex++;
        const delay = 400 + Math.random() * 300;
        setTimeout(addClause, delay);
      } else {
        useScanStore.getState().setComplete();
      }
    };

    addClause();
  };

  const resetDemo = () => {
    reset();
    resetScan();
    setIsDemoMode(false);
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "true") {
      simulateScan();
      setPowerResult(DEMO_POWER);
      setSummaryResult(DEMO_SUMMARY);
      setComplete();
    }
  }, []);

  return (
    <DemoContext.Provider value={{ isDemoMode, simulateScan, resetDemo }}>
      {children}
    </DemoContext.Provider>
  );
}

export function useDemo() {
  return useContext(DemoContext);
}