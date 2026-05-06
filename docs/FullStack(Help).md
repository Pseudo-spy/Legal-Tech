# API Hooks Documentation

This document outlines the API hooks and expected mock data structures used in the frontend. The backend developer should replace the mock data implementations with real API calls using these hook signatures.

## 1. Dashboard Hooks

### `useDashboardData()`
Fetches the summary statistics and recent contracts for the dashboard.

**Signature:**
```typescript
interface DashboardData {
  stats: {
    activeContracts: number;
    highRiskFlags: number;
    averagePowerScore: number;
  };
  recentContracts: Array<{
    id: string;
    name: string;
    type: string;
    status: 'analyzed' | 'processing' | 'failed';
    riskScore: number;
    verdict: 'SAFE' | 'REVIEW' | 'DANGER';
    date: string;
  }>;
}

export function useDashboardData(): { data: DashboardData | null; isLoading: boolean; error: Error | null };
```

## 2. Upload Hooks

### `useUploadContract()`
Handles the contract upload process.

**Signature:**
```typescript
export function useUploadContract(): {
  upload: (file: File, options: any) => Promise<{ jobId: string }>;
  isUploading: boolean;
  progress: number;
  error: Error | null;
};
```

## 3. Analysis Hooks

### `useContractAnalysis(jobId: string)`
Fetches the full analysis results for a given contract.

**Signature:**
```typescript
interface Clause {
  id: string;
  text: string;
  riskLevel: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'SAFE';
  category: string;
  confidence: number;
  explanation: string;
  consequence: {
    financialExposure: string | null;
    scenario: string;
    probability: 'High' | 'Medium' | 'Low';
    negotiable: boolean;
  };
}

interface AnalysisData {
  contractId: string;
  overallRiskScore: number;
  verdict: 'YES AS-IS' | 'YES WITH CHANGES' | 'NO';
  powerScore: number;
  powerLabel: string;
  clauses: Clause[];
  summary: {
    concerns: string[];
    positives: string[];
  };
}

export function useContractAnalysis(jobId: string): { data: AnalysisData | null; isLoading: boolean; error: Error | null };
```

### `useDeepDive(clauseId: string)`
Fetches the deep-dive information (precedents, counter-offers) for a specific clause.

**Signature:**
```typescript
interface DeepDiveData {
  clauseId: string;
  counterOffer: {
    aggressive: string;
    balanced: string;
    conservative: string;
    emailTemplate: string;
  };
  precedent: {
    summary: string;
    enforcementLikelihood: 'Very Likely' | 'Likely' | 'Uncertain' | 'Unlikely';
    cases: Array<{
      name: string;
      year: number;
      jurisdiction: string;
      outcome: 'Enforced' | 'Unenforceable';
    }>;
  };
}

export function useDeepDive(clauseId: string): { data: DeepDiveData | null; isLoading: boolean; error: Error | null };
```

### `useChat(contractId: string)`
Handles the Q&A chat interactions for the contract.

**Signature:**
```typescript
export function useChat(contractId: string): {
  messages: Array<{ id: string; role: 'user' | 'ai'; text: string; citations?: string[] }>;
  sendMessage: (text: string) => Promise<void>;
  isTyping: boolean;
};
```

## Hard Linking with the Backend

*Note to backend dev: Currently, these hooks are implemented in `src/lib/api-mock.ts` returning static mock data. To hard-link the real API, follow these integration steps:*

### 1. Replace the Mock Fetcher
Update the implementations of the hooks to use `fetch`, `axios`, or preferably `@tanstack/react-query` to hit the real endpoints.
For example, to link `useDashboardData`:

```typescript
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@clerk/nextjs';

export function useDashboardData() {
  const { getToken } = useAuth();

  const query = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const token = await getToken();
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dashboard`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      if (!response.ok) throw new Error('Failed to fetch dashboard data');
      return response.json();
    }
  });

  return { data: query.data, isLoading: query.isLoading, error: query.error };
}
```

### 2. Authentication Context
The application uses Clerk for authentication. You MUST pass the Clerk session token in the `Authorization` header as a Bearer token for every request, as shown in the example above. The backend must verify this JWT.

### 3. Error Handling and Loading States
Ensure your API hooks consistently return `{ data, isLoading, error }` so the frontend components (like the loaders and error banners) continue to function without modification. Do not throw unhandled promise rejections inside the hooks.

### 4. WebSocket / Polling for Processing
For the `useUploadContract` and `useContractAnalysis` hooks, the contract processing can be lengthy. 
- You must either implement a WebSocket connection to stream the `PROCESSING_STEPS` status.
- OR implement a polling mechanism in the hook that fetches `/api/jobs/{jobId}/status` every 2 seconds until the status is `COMPLETE`.
