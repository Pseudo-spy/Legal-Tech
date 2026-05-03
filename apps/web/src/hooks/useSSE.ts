import { useState, useEffect, useCallback, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useScanStore } from "@/store/scanStore";
import { useClauseStore } from "@/store/clauseStore";

interface SSEEvent {
  event_type: "clause_result" | "power_result" | "summary_result" | "heartbeat" | "complete";
  data: unknown;
}

export function useSSE(jobId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const retriesRef = useRef(0);
  const { getToken } = useAuth();

  const { updateProgress, setComplete } = useScanStore();
  const { addClause } = useClauseStore();

  const connect = useCallback(async () => {
    if (!jobId) return;

    setConnectionError(null);
    const token = await getToken();

    try {
      const eventSource = new EventSource(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/scan/${jobId}/stream?token=${token}`
      );

      eventSource.onopen = () => {
        setIsConnected(true);
        retriesRef.current = 0;
      };

      eventSource.onmessage = (event) => {
        try {
          const parsed: SSEEvent = JSON.parse(event.data);
          setLastEvent(parsed);

          if (parsed.event_type === "clause_result") {
            addClause(parsed.data as any);
          } else if (parsed.event_type === "power_result") {
            updateProgress(0, "processing");
          } else if (parsed.event_type === "summary_result") {
            updateProgress(100, "complete");
          } else if (parsed.event_type === "complete") {
            setComplete();
            eventSource.close();
            setIsConnected(false);
          }
        } catch (e) {
          console.error("Failed to parse SSE event:", e);
        }
      };

      eventSource.onerror = () => {
        setIsConnected(false);
        eventSource.close();

        if (retriesRef.current < 5) {
          retriesRef.current++;
          setTimeout(() => connect(), Math.min(2000 * retriesRef.current, 30000));
        } else {
          setConnectionError("Connection failed after multiple retries");
        }
      };

      eventSourceRef.current = eventSource;
    } catch (e) {
      setConnectionError("Failed to connect");
    }
  }, [jobId, getToken, addClause, updateProgress, setComplete]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return { isConnected, lastEvent, connectionError, connect };
}