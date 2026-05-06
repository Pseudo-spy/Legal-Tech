"use client";

import { useState } from "react";
import Link from "next/link";
import { 
  FileText, Upload, AlertCircle, ShieldCheck, 
  Activity, ArrowRight, Clock, Plus
} from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const stats = {
    activeContracts: 12,
    highRiskFlags: 8,
    averagePowerScore: -14
  };

  const recentContracts = [
    { id: "1", name: "Acme_Corp_NDA_2026.pdf", type: "NDA", riskScore: 15, verdict: "SAFE", date: "Just now" },
    { id: "2", name: "Senior_Dev_Employment.docx", type: "Employment", riskScore: 78, verdict: "DANGER", date: "2 hours ago" },
    { id: "3", name: "SaaS_Subscription_MSA.pdf", type: "MSA", riskScore: 45, verdict: "REVIEW", date: "Yesterday" },
    { id: "4", name: "Freelance_Agreement.pdf", type: "Contractor", riskScore: 20, verdict: "SAFE", date: "2 days ago" },
  ];

  return (
    <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 space-y-8 relative">
      {/* Background glow */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Hero Strip */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel relative rounded-2xl p-8 border border-white/10 bg-gradient-to-r from-blue-900/20 to-purple-900/10 overflow-hidden flex flex-col md:flex-row justify-between items-center gap-6"
      >
        <div className="relative z-10">
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Welcome back, Vikas.</h1>
          <p className="text-zinc-400">You have {stats.highRiskFlags} high-risk clauses pending review across your active contracts.</p>
        </div>
        <Link
          href="/upload"
          className="relative z-10 inline-flex items-center gap-2 px-6 py-3 bg-white text-black font-semibold rounded-xl hover:bg-zinc-200 transition-all shadow-[0_0_20px_rgba(255,255,255,0.15)] whitespace-nowrap"
        >
          <Upload className="h-5 w-5" /> Upload Contract
        </Link>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Risk Summary Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="glass-panel p-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-zinc-400">High Risk Flags</h3>
            <AlertCircle className="h-4 w-4 text-red-400" />
          </div>
          <div className="text-4xl font-bold text-white mb-2">{stats.highRiskFlags}</div>
          <p className="text-sm text-red-400/80">Requires immediate attention</p>
        </motion.div>

        {/* Active Contracts Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="glass-panel p-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-zinc-400">Active Contracts</h3>
            <FileText className="h-4 w-4 text-blue-400" />
          </div>
          <div className="text-4xl font-bold text-white mb-2">{stats.activeContracts}</div>
          <p className="text-sm text-blue-400/80">Currently in workspace</p>
        </motion.div>

        {/* Suggested Actions Card */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-panel p-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-md"
        >
           <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-zinc-400">Power Trend</h3>
            <Activity className="h-4 w-4 text-yellow-400" />
          </div>
          <div className="text-4xl font-bold text-white mb-2">{stats.averagePowerScore}</div>
          <p className="text-sm text-yellow-400/80">Average score favors counterparty</p>
        </motion.div>
      </div>

      {/* Recent Contracts Table */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="glass-panel border border-white/10 bg-black/40 backdrop-blur-md rounded-2xl overflow-hidden"
      >
        <div className="p-6 border-b border-white/10 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-white">Recent Contracts</h2>
          <Link href="/history" className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors">
            View all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="divide-y divide-white/5">
          {recentContracts.map((contract, index) => (
            <Link href={`/scan/${contract.id}`} key={contract.id}>
              <div className="p-4 sm:px-6 hover:bg-white/5 transition-colors flex items-center justify-between group cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="h-10 w-10 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-zinc-400 group-hover:text-blue-400 transition-colors" />
                  </div>
                  <div>
                    <h4 className="font-medium text-zinc-200 group-hover:text-white transition-colors">{contract.name}</h4>
                    <div className="flex items-center gap-3 text-sm text-zinc-500 mt-1">
                      <span className="bg-white/10 px-2 py-0.5 rounded text-xs">{contract.type}</span>
                      <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> {contract.date}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right hidden sm:block">
                    <div className="text-sm font-medium text-white">Score: {contract.riskScore}</div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                    contract.verdict === 'SAFE' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                    contract.verdict === 'REVIEW' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                    'bg-red-500/10 text-red-400 border-red-500/20'
                  }`}>
                    {contract.verdict}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </motion.div>
    </div>
  );
}