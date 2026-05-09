"use client";

import { useState } from "react";
import { AlertCircle, X } from "lucide-react";
import { useApiClient } from "@/lib/api";

interface LanguageDetectionBannerProps {
  detectedLanguage: string;
  contractId: string;
}

export function LanguageDetectionBanner({ detectedLanguage, contractId }: LanguageDetectionBannerProps) {
  const [isVisible, setIsVisible] = useState(true);
  const [isTranslating, setIsTranslating] = useState(false);
  const { translate } = useApiClient();

  if (!isVisible || !detectedLanguage || detectedLanguage.toLowerCase().startsWith("en")) return null;

  const handleTranslate = async () => {
    setIsTranslating(true);
    try {
      await translate(contractId, "en");
      setIsVisible(false);
    } catch (error) {
      console.error(error);
    } finally {
      setIsTranslating(false);
    }
  };

  return (
    <div className="flex items-center justify-between rounded-lg bg-blue-50 px-4 py-3 text-sm text-blue-900 dark:bg-blue-950/30 dark:text-blue-300">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-4 w-4 shrink-0" />
        <span>
          This document appears to be in <strong>{detectedLanguage.toUpperCase()}</strong>. 
          Would you like to translate it to English?
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-3 ml-4">
        <button
          onClick={handleTranslate}
          disabled={isTranslating}
          className="rounded-md bg-blue-600 px-3 py-1.5 font-medium text-white shadow-sm hover:bg-blue-700 disabled:opacity-50 dark:bg-blue-600 dark:hover:bg-blue-500"
        >
          {isTranslating ? "Translating..." : "Translate to EN"}
        </button>
        <button onClick={() => setIsVisible(false)} className="text-blue-700/50 hover:text-blue-700 dark:text-blue-300/50 dark:hover:text-blue-300">
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
