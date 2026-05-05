"use client";

import React from "react";
import { motion } from "framer-motion";
import { ShieldCheck, FileCheck, FileWarning, Zap } from "lucide-react";

export function IntegritySection() {
  return (
    <section className="relative z-10 py-32 px-4 bg-zinc-50/30 dark:bg-[#050505]/30 backdrop-blur-md border-t border-zinc-200 dark:border-white/5 overflow-hidden">
      
      {/* Background glow for this specific section */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-zinc-200/50 dark:bg-zinc-900/50 blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-24">
          <h2 className="text-4xl md:text-5xl font-bold text-zinc-900 dark:text-white mb-6 tracking-tight">
            Document Integrity
          </h2>
          <p className="text-zinc-500 dark:text-zinc-400 max-w-xl mx-auto mb-8">
            Exploratory mission with Legal Horizon & navigating through the vast possibilities.
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-200 dark:bg-white/10 text-zinc-900 dark:text-white text-sm">
            How it works?
          </div>
        </div>

        <div className="flex flex-col lg:flex-row items-center justify-between gap-16 lg:gap-8">
          
          {/* Left Graphic: Nested Ovals / Flow */}
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 w-full max-w-lg relative h-[350px] md:h-[400px]"
          >
            <div className="absolute top-0 left-0 md:left-4">
              <h3 className="text-zinc-500 dark:text-zinc-400 text-xs md:text-sm mb-1">Legal Review System</h3>
              <p className="text-3xl md:text-4xl font-bold text-zinc-900 dark:text-white">+A3.7</p>
            </div>

            {/* Simulated orbital paths */}
            <svg viewBox="0 0 400 400" className="absolute inset-0 w-full h-full opacity-30 text-zinc-400 dark:text-white">
              <ellipse cx="200" cy="200" rx="180" ry="80" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" transform="rotate(-15 200 200)" />
              <ellipse cx="200" cy="200" rx="120" ry="50" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(-15 200 200)" />
            </svg>

            {/* Nodes on paths - Spaced out and scaled for mobile */}
            <div className="absolute top-[20%] right-[-10px] md:right-[5%] glass-panel px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 md:gap-3 border border-zinc-200 dark:border-white/10 shadow-xl scale-90 md:scale-100 origin-right">
              <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-white dark:bg-zinc-800 flex items-center justify-center shrink-0">
                <FileWarning className="w-3 h-3 text-red-500 dark:text-red-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] md:text-xs text-zinc-900 dark:text-white leading-tight">Pending</span>
                <span className="text-[8px] md:text-[10px] text-zinc-500 leading-tight">from 0x938</span>
              </div>
              <span className="text-[10px] md:text-xs font-mono text-zinc-500 dark:text-zinc-400 ml-1 md:ml-2">12 docs</span>
            </div>

            <div className="absolute top-[50%] left-[-10px] md:left-[10%] glass-panel px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 md:gap-3 border border-zinc-200 dark:border-white/10 shadow-xl scale-90 md:scale-100 origin-left">
              <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-white dark:bg-zinc-800 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-3 h-3 text-teal-500 dark:text-teal-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] md:text-xs text-zinc-900 dark:text-white leading-tight">Verified</span>
                <span className="text-[8px] md:text-[10px] text-zinc-500 leading-tight">from 0xB47</span>
              </div>
              <span className="text-[10px] md:text-xs font-mono text-zinc-500 dark:text-zinc-400 ml-1 md:ml-2">1,038 docs</span>
            </div>

            <div className="absolute bottom-[-5%] md:bottom-[10%] left-[50%] -translate-x-1/2 md:translate-x-0 md:left-[20%] glass-panel px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 md:gap-3 border border-zinc-200 dark:border-white/10 shadow-xl scale-90 md:scale-100">
              <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-white dark:bg-zinc-800 flex items-center justify-center shrink-0">
                <FileCheck className="w-3 h-3 text-blue-500 dark:text-blue-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] md:text-xs text-zinc-900 dark:text-white leading-tight">Sent</span>
                <span className="text-[8px] md:text-[10px] text-zinc-500 leading-tight">to x7360</span>
              </div>
              <span className="text-[10px] md:text-xs font-mono text-zinc-500 dark:text-zinc-400 ml-1 md:ml-2">4,948</span>
            </div>
            
            <div className="absolute bottom-[10%] md:bottom-[5%] right-[10%] md:right-[25%] text-[10px] md:text-xs text-zinc-500">
              Done
            </div>
          </motion.div>

          {/* Right Graphic: Circular Progress Ring */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 w-full max-w-sm flex flex-col items-center justify-center relative"
          >
            <div className="relative w-64 h-64 flex items-center justify-center">
              {/* Outer Ring */}
              <svg className="absolute inset-0 w-full h-full -rotate-90">
                <circle cx="128" cy="128" r="110" fill="none" className="stroke-zinc-200 dark:stroke-white/5" strokeWidth="20" />
                <circle cx="128" cy="128" r="110" fill="none" className="stroke-zinc-800 dark:stroke-white/80 drop-shadow-[0_0_15px_rgba(0,0,0,0.1)] dark:drop-shadow-[0_0_15px_rgba(255,255,255,0.5)]" strokeWidth="20" strokeDasharray="690" strokeDashoffset="500" />
              </svg>
              
              {/* Inner Glowing Orb */}
              <div className="absolute inset-0 m-auto w-32 h-32 rounded-full bg-white dark:bg-zinc-900 shadow-[0_0_50px_rgba(0,0,0,0.05)] dark:shadow-[0_0_50px_rgba(255,255,255,0.1)] flex flex-col items-center justify-center border border-zinc-200 dark:border-white/10 z-10">
                <Zap className="w-6 h-6 text-zinc-900 dark:text-white mb-1" />
                <span className="text-xs font-bold text-zinc-900 dark:text-white tracking-widest">Step 01</span>
              </div>
              
              {/* Little floating indicators */}
              <div className="absolute top-[-10px] md:top-4 right-[-10px] md:-right-4 text-[10px] text-zinc-500 font-mono text-right md:text-left bg-zinc-50/80 dark:bg-zinc-950/80 p-1 rounded-md backdrop-blur-sm z-20">
                Target<br/>2024<br/>Legal API
              </div>
            </div>

            {/* Bottom Tags */}
            <div className="mt-12 flex flex-wrap justify-center gap-3">
              <span className="px-3 py-1.5 rounded-full bg-zinc-200 dark:bg-white/5 text-zinc-600 dark:text-zinc-400 text-xs border border-zinc-300 dark:border-white/10 flex items-center gap-2">
                <ShieldCheck className="w-3 h-3" /> 2.7K Assets
              </span>
              <span className="px-3 py-1.5 rounded-full bg-zinc-200 dark:bg-white/5 text-zinc-600 dark:text-zinc-400 text-xs border border-zinc-300 dark:border-white/10 flex items-center gap-2">
                <FileCheck className="w-3 h-3" /> Success
              </span>
              <span className="px-3 py-1.5 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-medium text-xs border border-transparent dark:border-white flex items-center gap-2 shadow-[0_0_15px_rgba(0,0,0,0.2)] dark:shadow-[0_0_15px_rgba(255,255,255,0.3)]">
                <Zap className="w-3 h-3" /> Decentralized
              </span>
            </div>
            <div className="mt-3 flex flex-wrap justify-center gap-3">
              <span className="px-3 py-1.5 rounded-full bg-zinc-200 dark:bg-white/5 text-zinc-600 dark:text-zinc-400 text-xs border border-zinc-300 dark:border-white/10">
                ◆ Smart Contracts
              </span>
              <span className="px-3 py-1.5 rounded-full bg-zinc-200 dark:bg-white/5 text-zinc-600 dark:text-zinc-400 text-xs border border-zinc-300 dark:border-white/10">
                ◆ Tokenized Trust
              </span>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
