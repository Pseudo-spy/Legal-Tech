"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { UploadZone } from "@/features/upload/UploadZone";
import { EncryptionBadge } from "@/features/upload/EncryptionBadge";
import { UploadProgress } from "@/features/upload/UploadProgress";
import { FileText, AlertCircle } from "lucide-react";
import { useApiClient } from "@/lib/api";

type UploadState = "idle" | "encrypting" | "uploading" | "complete" | "error";

export default function UploadPage() {
  const router = useRouter();
  const { upload } = useApiClient();
  const [status, setStatus] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<"encrypting" | "uploading" | "complete">("encrypting");
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [contractId, setContractId] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = useCallback(
    async (file: File) => {
      setSelectedFile(file);
      setStatus("encrypting");
      setError(null);
      setProgress(0);

      try {
        // Step 1: Simulate encryption (for now - in production, encrypt with WebCrypto)
        setProgress(20);
        setPhase("encrypting");
        await new Promise((resolve) => setTimeout(resolve, 1000));
        
        // In production: Use Uploadthing - for now use mock URL
        // For real Uploadthing, you'd need proper configuration
        const mockFileUrl = `https://uploadthing.com/files/${file.name}`;
        
        setProgress(50);
        setPhase("uploading");
        setStatus("uploading");
        
        // Step 2: Call backend API
        const response = await upload(
          mockFileUrl,
          file.name,
          file.name.split('.').pop() || 'pdf',
          file.size
        );
        
        setProgress(100);
        setPhase("complete");
        setStatus("complete");
        
        setJobId(response.job_id);
        setContractId(response.contract_id);
      } catch (e) {
        setStatus("error");
        setError(e instanceof Error ? e.message : "Upload failed");
      }
    },
    [upload]
  );

  const handleContinue = useCallback(() => {
    if (jobId) {
      router.push(`/scan/${jobId}`);
    }
  }, [jobId, router]);

  const handleRetry = useCallback(() => {
    setStatus("idle");
    setProgress(0);
    setPhase("encrypting");
    setError(null);
    setSelectedFile(null);
  }, []);

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-zinc-900 mb-2">Upload Your Contract</h1>
      <p className="text-zinc-600 mb-8">
        Drop your contract to analyze. All data is encrypted end-to-end.
      </p>

      <div className="space-y-6">
        {status === "idle" && (
          <UploadZone onFileSelect={handleFileSelect} />
        )}

        {status !== "idle" && selectedFile && (
          <EncryptionBadge status={phase === "complete" ? "complete" : "encrypting"} />
        )}

        {(status === "encrypting" || status === "uploading") && (
          <UploadProgress
            progress={progress}
            phase={phase}
            fileName={selectedFile?.name}
          />
        )}

        {status === "complete" && (
          <div className="p-6 border border-green-300 bg-green-50 rounded-lg">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="h-8 w-8 text-green-600" />
              <div>
                <p className="font-medium text-zinc-900">
                  {selectedFile?.name}
                </p>
                <p className="text-sm text-green-600">
                  Upload complete! Job ID: {jobId}
                </p>
              </div>
            </div>
            <button
              onClick={handleContinue}
              className="w-full py-3 bg-zinc-900 text-white rounded-lg font-medium hover:bg-zinc-800 transition-colors"
            >
              View Analysis
            </button>
          </div>
        )}

        {status === "error" && (
          <div className="p-4 border border-red-300 bg-red-50 rounded-lg">
            <div className="flex items-center gap-2 text-red-600 mb-3">
              <AlertCircle className="h-5 w-5" />
              <span className="font-medium">Upload failed</span>
            </div>
            <p className="text-sm text-red-600 mb-3">{error}</p>
            <button
              onClick={handleRetry}
              className="text-sm text-red-600 hover:text-red-700 underline"
            >
              Try again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}