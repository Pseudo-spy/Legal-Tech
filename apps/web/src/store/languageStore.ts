import { create } from "zustand";

interface LanguageState {
  activeLanguage: string;
  detectedLanguage: string | null;
  isTranslating: boolean;
  setDetectedLanguage: (language: string | null) => void;
  switchLanguage: (language: string) => void;
  setTranslating: (translating: boolean) => void;
}

export const useLanguageStore = create<LanguageState>()((set) => ({
  activeLanguage: "en",
  detectedLanguage: null,
  isTranslating: false,
  setDetectedLanguage: (language) => set({ detectedLanguage: language }),
  switchLanguage: (language) => set({ activeLanguage: language }),
  setTranslating: (translating) => set({ isTranslating: translating }),
}));