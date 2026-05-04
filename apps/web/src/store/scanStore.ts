import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ScanStatus } from "@/types/scan";

interface ScanState {
  jobId: string | null;
  contractId: string | null;
  status: ScanStatus;
  progressPct: number;
  error: string | null;
  setScanJob: (jobId: string, contractId: string) => void;
  updateProgress: (progressPct: number, status?: ScanStatus) => void;
  setComplete: () => void;
  setFailed: (error: string) => void;
  reset: () => void;
}

export const useScanStore = create<ScanState>()(
  persist(
    (set) => ({
      jobId: null,
      contractId: null,
      status: "queued",
      progressPct: 0,
      error: null,
      setScanJob: (jobId, contractId) =>
        set({ jobId, contractId, status: "queued", progressPct: 0, error: null }),
      updateProgress: (progressPct, status) =>
        set((state) => ({
          progressPct,
          status: status || state.status,
        })),
      setComplete: () => set({ status: "complete", progressPct: 100 }),
      setFailed: (error) => set({ status: "failed", error }),
      reset: () =>
        set({
          jobId: null,
          contractId: null,
          status: "queued",
          progressPct: 0,
          error: null,
        }),
    }),
    {
      name: "scan-store",
      partialize: (state) => ({
        jobId: state.jobId,
        contractId: state.contractId,
      }),
    }
  )
);