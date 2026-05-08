"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { 
  FileText, ShieldAlert, AlertTriangle, CheckCircle, 
  Share2, Download, Search, Info, ShieldCheck, Scale, ArrowRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

// Mock Data
const MOCK_CONTRACT = {
  name: "Acme_Corp_NDA_2026.pdf",
  type: "NDA",
  overallScore: 68,
  verdict: "REVIEW REQUIRED",
};

const MOCK_CLAUSES = [
  {
    id: "c1",
    text: "Receiving Party agrees not to use any Confidential Information of the Disclosing Party for any purpose whatsoever, in perpetuity, even if such information enters the public domain.",
    type: "Non-Use",
    risk: "CRITICAL",
    confidence: 94,
    explanation: "This clause attempts to bind you to confidentiality forever, even after the information is no longer secret. This is highly unusual and legally dubious.",
    consequence: "$500,000 potential liability for accidental disclosure after 10 years.",
    negotiable: true,
  },
  {
    id: "c2",
    text: "Receiving Party shall return or destroy all materials containing Confidential Information within 2 days of a written request.",
    type: "Return of Materials",
    risk: "HIGH",
    confidence: 88,
    explanation: "The 2-day turnaround is too tight for modern IT infrastructure. Standard is 10-30 days.",
    consequence: "Breach of contract if you cannot wipe backups within 48 hours.",
    negotiable: true,
  },
  {
    id: "c3",
    text: "This Agreement shall be governed by the laws of the State of Delaware.",
    type: "Governing Law",
    risk: "SAFE",
    confidence: 99,
    explanation: "Standard governing law clause for US corporate agreements.",
    consequence: "Any disputes will be handled under Delaware law.",
    negotiable: false,
  }
];

export default function ScanPage() {
  const params = useParams();
  const jobId = params?.jobId as string;
  const [selectedClause, setSelectedClause] = useState(MOCK_CLAUSES[0]);
  const [activeTab, setActiveTab] = useState<"consequence" | "counter" | "precedent">("consequence");

  const getRiskColor = (risk: string) => {
    switch(risk) {
      case "CRITICAL": return "text-red-400 bg-red-500/10 border-red-500/30";
      case "HIGH": return "text-orange-400 bg-orange-500/10 border-orange-500/30";
      case "MEDIUM": return "text-yellow-400 bg-yellow-500/10 border-yellow-500/30";
      default: return "text-green-400 bg-green-500/10 border-green-500/30";
    }
  };

  const getHighlightColor = (risk: string) => {
    switch(risk) {
      case "CRITICAL": return "border-b-2 border-red-500 bg-red-500/20";
      case "HIGH": return "border-b-2 border-orange-500 bg-orange-500/20";
      case "MEDIUM": return "border-b-2 border-yellow-500 bg-yellow-500/20";
      default: return "border-b border-green-500/50 bg-green-500/10";
    }
  };

  return (
    <div className="flex flex-col flex-1 h-full min-h-0 overflow-hidden gap-4">
      {/* Top Bar */}
      <div className="flex items-center justify-between glass-panel p-4 rounded-xl border border-white/10 shrink-0">
        <div className="flex items-center gap-4">
          <FileText className="h-6 w-6 text-blue-400" />
          <div>
            <h1 className="text-lg font-bold text-white">{MOCK_CONTRACT.name}</h1>
            <div className="flex items-center gap-2 text-sm mt-0.5">
              <span className="bg-white/10 text-zinc-300 px-2 py-0.5 rounded text-xs">{MOCK_CONTRACT.type}</span>
              <span className="text-zinc-500">•</span>
              <span className="text-zinc-400">Analysis Complete</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-sm text-zinc-400 font-medium">Overall Risk Score</div>
            <div className="text-xl font-bold text-orange-400">{MOCK_CONTRACT.overallScore} / 100</div>
          </div>
          <div className="h-8 w-px bg-white/10" />
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm text-white transition-colors">
              <Share2 className="h-4 w-4" /> Share
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm text-white transition-colors">
              <Download className="h-4 w-4" /> Export Report
            </button>
          </div>
        </div>
      </div>

      {/* 3-Column Layout */}
      <div className="flex flex-col lg:flex-row flex-1 gap-4 overflow-y-auto lg:overflow-hidden min-h-0 pb-20 lg:pb-0">
        
        {/* LEFT PANEL: Contract Viewer */}
        <div className="w-full lg:w-1/3 h-[500px] lg:h-auto flex flex-col glass-panel border border-white/10 rounded-xl overflow-hidden shrink-0">
          <div className="p-3 border-b border-white/10 bg-white/5 flex items-center justify-between">
             <span className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">Document Viewer</span>
             <Search className="h-4 w-4 text-zinc-500" />
          </div>
          <div className="flex-1 overflow-y-auto p-6 text-sm text-zinc-300 leading-relaxed font-serif space-y-6">
             <p>This Non-Disclosure Agreement (the "Agreement") is entered into by and between Acme Corp ("Disclosing Party") and the Undersigned ("Receiving Party").</p>
             <p>1. Definition of Confidential Information. "Confidential Information" means all non-public information disclosed by Disclosing Party.</p>
             <p className={`p-1 rounded cursor-pointer transition-colors ${selectedClause.id === 'c1' ? getHighlightColor('CRITICAL') : 'hover:bg-white/5'}`} onClick={() => setSelectedClause(MOCK_CLAUSES[0])}>
               2. Non-Use and Non-Disclosure. {MOCK_CLAUSES[0].text}
             </p>
             <p className={`p-1 rounded cursor-pointer transition-colors ${selectedClause.id === 'c2' ? getHighlightColor('HIGH') : 'hover:bg-white/5'}`} onClick={() => setSelectedClause(MOCK_CLAUSES[1])}>
               3. Return of Materials. {MOCK_CLAUSES[1].text}
             </p>
             <p className={`p-1 rounded cursor-pointer transition-colors ${selectedClause.id === 'c3' ? getHighlightColor('SAFE') : 'hover:bg-white/5'}`} onClick={() => setSelectedClause(MOCK_CLAUSES[2])}>
               4. Governing Law. {MOCK_CLAUSES[2].text}
             </p>
          </div>
        </div>

        {/* CENTER PANEL: Clause Intelligence */}
        <div className="w-full lg:flex-[1.2] h-[600px] lg:h-auto flex flex-col glass-panel border border-white/10 rounded-xl overflow-hidden shrink-0 lg:min-w-0">
           <div className="p-3 border-b border-white/10 bg-white/5 flex items-center justify-between shrink-0">
             <span className="text-sm font-semibold text-zinc-300 uppercase tracking-wider">Clause Intelligence</span>
             <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-500">Confidence</span>
                <span className="text-xs font-mono bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded-full border border-blue-500/30">
                  {selectedClause.confidence}%
                </span>
             </div>
           </div>
           
           <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
              {/* Header Info */}
              <div>
                <div className="flex items-center gap-3 mb-3">
                  <span className={`px-3 py-1 text-xs font-bold rounded border ${getRiskColor(selectedClause.risk)}`}>
                    {selectedClause.risk} RISK
                  </span>
                  <span className="text-sm text-zinc-400">{selectedClause.type}</span>
                </div>
                <div className="p-4 bg-black/40 rounded-lg border border-white/5 font-mono text-sm text-zinc-300">
                  "{selectedClause.text}"
                </div>
              </div>

              {/* Plain English Translation */}
              <div className="bg-white/5 rounded-xl p-5 border border-white/10 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-blue-500" />
                <h4 className="text-sm font-semibold text-white mb-2 flex items-center gap-2">
                  <Info className="h-4 w-4 text-blue-400" /> What this means
                </h4>
                <p className="text-sm text-zinc-300 leading-relaxed">
                  {selectedClause.explanation}
                </p>
              </div>

              {/* Deep Dive Tabs */}
              <div className="flex-1 flex flex-col min-h-0 bg-white/5 border border-white/10 rounded-xl overflow-hidden mt-4">
                <div className="flex items-center border-b border-white/10 shrink-0">
                  <button 
                    onClick={() => setActiveTab("consequence")}
                    className={`flex-1 py-3 text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer ${activeTab === 'consequence' ? 'text-blue-400 border-b-2 border-blue-400 bg-white/5' : 'text-zinc-500 hover:text-zinc-300'}`}
                  >
                    Consequence
                  </button>
                  <button 
                    onClick={() => setActiveTab("counter")}
                    className={`flex-1 py-3 text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer ${activeTab === 'counter' ? 'text-blue-400 border-b-2 border-blue-400 bg-white/5' : 'text-zinc-500 hover:text-zinc-300'}`}
                  >
                    Counter-Offer
                  </button>
                  <button 
                    onClick={() => setActiveTab("precedent")}
                    className={`flex-1 py-3 text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer ${activeTab === 'precedent' ? 'text-blue-400 border-b-2 border-blue-400 bg-white/5' : 'text-zinc-500 hover:text-zinc-300'}`}
                  >
                    Precedents
                  </button>
                </div>

                <div className="p-5 overflow-y-auto flex-1 relative">
                  {/* Consequence Tab */}
                  {activeTab === "consequence" && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                      {selectedClause.risk !== "SAFE" ? (
                        <>
                          <div className="flex items-center gap-2 text-red-400 mb-2">
                            <AlertTriangle className="h-4 w-4" /> 
                            <span className="text-sm font-semibold">Real-world Consequence</span>
                          </div>
                          <p className="text-lg font-medium text-white">
                            {selectedClause.consequence}
                          </p>
                          <div className="flex gap-2 mt-4">
                            <span className="text-xs font-medium bg-red-500/20 text-red-400 px-2 py-1 rounded">High Probability</span>
                            {selectedClause.negotiable && (
                              <span className="text-xs font-medium bg-green-500/20 text-green-400 px-2 py-1 rounded flex items-center gap-1">
                                <CheckCircle className="h-3 w-3" /> Negotiable
                              </span>
                            )}
                          </div>
                        </>
                      ) : (
                        <p className="text-sm text-zinc-400">This clause represents standard terms and poses no significant risk.</p>
                      )}
                    </motion.div>
                  )}

                  {/* Counter Offer Tab */}
                  {activeTab === "counter" && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                       <h4 className="text-sm font-semibold text-zinc-300 mb-2">AI Suggested Revision (Balanced)</h4>
                       <div className="p-4 bg-zinc-900 rounded-lg border border-white/5 font-mono text-sm">
                         <span className="text-red-400 line-through opacity-50 block mb-2">{selectedClause.text}</span>
                         <span className="text-green-400 block">Receiving Party agrees not to use any Confidential Information for 3 years from the date of disclosure.</span>
                       </div>
                       <button className="w-full py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
                         Copy Suggested Revision
                       </button>
                    </motion.div>
                  )}

                  {/* Precedent Tab */}
                  {activeTab === "precedent" && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                       <h4 className="text-sm font-semibold text-zinc-300 mb-2">Relevant Case Law</h4>
                       <div className="p-3 bg-white/5 border border-white/10 rounded-lg">
                         <div className="text-sm text-blue-400 font-medium mb-1">Smith v. TechCorp (2019)</div>
                         <p className="text-xs text-zinc-400">Court struck down a perpetual NDA clause as unreasonably restrictive on trade.</p>
                       </div>
                       <div className="p-3 bg-white/5 border border-white/10 rounded-lg">
                         <div className="text-sm text-blue-400 font-medium mb-1">Delaware Chancery Court (2021)</div>
                         <p className="text-xs text-zinc-400">Standardized that NDAs without temporal limits are generally unenforceable unless concerning trade secrets.</p>
                       </div>
                    </motion.div>
                  )}
                </div>
              </div>
           </div>
        </div>

        {/* RIGHT PANEL: Metrics & Deep Dive */}
        <div className="w-full lg:w-[30%] flex flex-col gap-4 overflow-hidden shrink-0">
          
          {/* Power Asymmetry Meter */}
          <div className="glass-panel border border-white/10 rounded-xl p-6 relative overflow-hidden shrink-0">
             <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-6 flex items-center gap-2">
               <Scale className="h-4 w-4 text-purple-400" /> Power Asymmetry
             </h3>
             
             {/* SVG Gauge */}
             <div className="relative h-24 w-48 mx-auto flex items-end justify-center mb-4">
                <svg className="absolute inset-0 w-full h-full overflow-visible" viewBox="0 0 200 100">
                  {/* Background Track */}
                  <path d="M 10 100 A 90 90 0 0 1 190 100" fill="none" stroke="#27272a" strokeWidth="16" strokeLinecap="round" />
                  {/* Red Risk Segment */}
                  <path d="M 10 100 A 90 90 0 0 1 80 20" fill="none" stroke="#ef4444" strokeWidth="16" strokeLinecap="round" />
                </svg>
                {/* Needle */}
                <motion.div 
                  className="absolute bottom-0 w-1 h-20 bg-white origin-bottom rounded-full shadow-[0_0_10px_white]"
                  initial={{ rotate: -90 }}
                  animate={{ rotate: -30 }} // Favors them
                  transition={{ type: "spring", stiffness: 60, damping: 15, delay: 0.5 }}
                />
                <div className="absolute bottom-[-4px] w-4 h-4 bg-white rounded-full" />
             </div>
             
             <div className="text-center">
               <div className="text-red-400 font-bold mb-1">Strongly Favors Counterparty</div>
               <p className="text-xs text-zinc-500">This contract gives them 3x more termination rights.</p>
             </div>
          </div>

          {/* Quick Stats */}
          <div className="glass-panel border border-white/10 rounded-xl p-6 flex-1 overflow-y-auto">
             <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">Overall Breakdown</h3>
             <div className="space-y-3">
               <div className="flex justify-between items-center p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                 <span className="text-sm text-red-400 font-medium">Critical Risks</span>
                 <span className="text-white font-bold">2</span>
               </div>
               <div className="flex justify-between items-center p-3 bg-orange-500/10 border border-orange-500/20 rounded-lg">
                 <span className="text-sm text-orange-400 font-medium">High Risks</span>
                 <span className="text-white font-bold">5</span>
               </div>
               <div className="flex justify-between items-center p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                 <span className="text-sm text-yellow-400 font-medium">Medium Risks</span>
                 <span className="text-white font-bold">8</span>
               </div>
               <div className="flex justify-between items-center p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                 <span className="text-sm text-green-400 font-medium">Safe Clauses</span>
                 <span className="text-white font-bold">24</span>
               </div>
             </div>
          </div>

        </div>

      </div>
    </div>
  );
}