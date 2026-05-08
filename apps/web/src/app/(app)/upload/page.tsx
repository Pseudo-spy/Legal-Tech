"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { FileText, AlertCircle, Upload as UploadIcon, CheckCircle2, Loader2, Sparkles, X, ShieldCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const PROCESSING_STEPS = [
  "Uploading File",
  "Parsing Document Structure",
  "Extracting Text Elements",
  "Splitting into Clauses",
  "Detecting Contract Type",
  "Finding Risky Clauses",
  "AI Analysis in Progress",
  "Preparing Results"
];

export default function UploadPage() {
  const router = useRouter();
  
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "processing" | "complete" | "error">("idle");
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      startProcessing(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      startProcessing(e.target.files[0]);
    }
  }, []);

  const startProcessing = (file: File) => {
    setSelectedFile(file);
    setStatus("processing");
    setCurrentStepIndex(0);
  };

  useEffect(() => {
    if (status === "processing") {
      if (currentStepIndex < PROCESSING_STEPS.length) {
        const timer = setTimeout(() => {
          setCurrentStepIndex(prev => prev + 1);
        }, 1500); // 1.5 seconds per step
        return () => clearTimeout(timer);
      } else {
        // Once all steps complete, transition to complete state
        setTimeout(() => setStatus("complete"), 500);
      }
    }
  }, [status, currentStepIndex]);

  const handleContinue = () => {
    // Navigate to a mock scan id
    router.push(`/scan/mock-job-123`);
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6 relative flex flex-col justify-center flex-1 min-h-[70vh]">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none" />

      <div className="text-center mb-10 relative z-10">
        <h1 className="text-3xl font-bold text-white mb-3">New Analysis</h1>
        <p className="text-zinc-400">Upload your contract to securely analyze risks and generate safer counter-offers.</p>
      </div>

      <div className="relative z-10 w-full">
        {status === "idle" && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className={`
              glass-panel relative rounded-3xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center p-16 cursor-pointer
              ${isDragging ? 'border-blue-500 bg-blue-500/5 shadow-[0_0_30px_rgba(59,130,246,0.2)]' : 'border-white/20 hover:border-white/40 hover:bg-white/5'}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-upload")?.click()}
          >
            <input 
              id="file-upload" 
              type="file" 
              className="hidden" 
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
            />
            <div className="h-20 w-20 rounded-full bg-white/5 flex items-center justify-center mb-6 border border-white/10">
              <UploadIcon className="h-8 w-8 text-blue-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Click or drag file to upload</h3>
            <p className="text-zinc-500 mb-6 text-sm">PDF, DOCX, or TXT up to 25MB</p>
            <div className="flex items-center gap-2 text-xs text-zinc-400 bg-white/5 px-3 py-1.5 rounded-full border border-white/10">
               <ShieldCheck className="h-3 w-3 text-green-400" /> Encrypted before leaving device
            </div>
          </motion.div>
        )}

        {status === "processing" && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="glass-panel p-8 rounded-3xl border border-white/10 max-w-xl mx-auto"
          >
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-blue-400" />
                <div>
                  <h3 className="text-white font-medium">{selectedFile?.name}</h3>
                  <p className="text-zinc-500 text-sm">{(selectedFile?.size ? (selectedFile.size / 1024 / 1024).toFixed(2) : "0.00")} MB</p>
                </div>
              </div>
              <Sparkles className="h-6 w-6 text-blue-400 animate-pulse" />
            </div>

            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-[11px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-white/10 before:to-transparent">
              {PROCESSING_STEPS.map((step, index) => {
                const isComplete = index < currentStepIndex;
                const isActive = index === currentStepIndex;
                const isPending = index > currentStepIndex;

                return (
                  <div key={step} className={`relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active`}>
                    <div className="flex items-center justify-center w-6 h-6 rounded-full border-2 border-black bg-zinc-900 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 relative z-10 mr-4 md:mr-0">
                      {isComplete ? (
                        <CheckCircle2 className="h-4 w-4 text-green-400" />
                      ) : isActive ? (
                        <Loader2 className="h-3 w-3 text-blue-400 animate-spin" />
                      ) : (
                        <div className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
                      )}
                    </div>
                    <div className={`w-[calc(100%-3rem)] md:w-[calc(50%-1.5rem)] p-3 rounded-lg border transition-colors ${
                      isActive ? 'bg-blue-500/10 border-blue-500/30' : 
                      isComplete ? 'bg-white/5 border-white/5' : 'bg-transparent border-transparent'
                    }`}>
                      <p className={`text-sm font-medium ${
                        isActive ? 'text-blue-400' : 
                        isComplete ? 'text-zinc-300' : 'text-zinc-600'
                      }`}>{step}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {status === "complete" && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-panel p-10 rounded-3xl border border-green-500/30 bg-green-500/5 max-w-md mx-auto text-center"
          >
            <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(34,197,94,0.3)]">
              <CheckCircle2 className="h-10 w-10 text-green-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Analysis Complete</h2>
            <p className="text-zinc-400 mb-8">
              We've scanned {selectedFile?.name} and found items requiring your attention.
            </p>
            <button
              onClick={handleContinue}
              className="w-full py-4 bg-white text-black font-bold rounded-xl hover:bg-zinc-200 transition-all shadow-[0_0_20px_rgba(255,255,255,0.1)]"
            >
              View Results
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}