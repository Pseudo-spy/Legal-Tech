import { create } from "zustand";

type ActivePanel = "consequence" | "counter-offer" | "precedent" | null;

interface UIState {
  isCounterOfferPanelOpen: boolean;
  isPrecedentPanelOpen: boolean;
  activePanel: ActivePanel;
  openCounterOfferPanel: () => void;
  openPrecedentPanel: () => void;
  closePanel: () => void;
}

export const useUIStore = create<UIState>()((set) => ({
  isCounterOfferPanelOpen: false,
  isPrecedentPanelOpen: false,
  activePanel: null,
  openCounterOfferPanel: () =>
    set({ isCounterOfferPanelOpen: true, activePanel: "counter-offer" }),
  openPrecedentPanel: () =>
    set({ isPrecedentPanelOpen: true, activePanel: "precedent" }),
  closePanel: () =>
    set({
      isCounterOfferPanelOpen: false,
      isPrecedentPanelOpen: false,
      activePanel: null,
    }),
}));