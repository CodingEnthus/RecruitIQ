"use client";

import React from "react";
import { Sparkles, ShieldCheck, ShieldAlert, Sliders, Cpu } from "lucide-react";

interface NavbarProps {
  anonymousMode: boolean;
  setAnonymousMode: (val: boolean) => void;
  isBackendConnected: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  anonymousMode,
  setAnonymousMode,
  isBackendConnected
}) => {
  return (
    <header className="h-16 border-b border-slate-800 glass-panel sticky top-0 z-40 px-6 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
          <Sparkles className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight gradient-text">RecruitIQ</span>
            <span className="text-[10px] font-mono uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full">
              Explainable RAG v1.0
            </span>
          </div>
          <p className="text-xs text-slate-400">AI-Powered Resume Intelligence & Deterministic Screener</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Connection Status */}
        <div className="flex items-center gap-2 text-xs bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg">
          <Cpu className={`w-3.5 h-3.5 ${isBackendConnected ? "text-emerald-400" : "text-amber-400 animate-pulse"}`} />
          <span className="text-slate-300">
            Engine: <strong className={isBackendConnected ? "text-emerald-400" : "text-amber-400"}>
              {isBackendConnected ? "BGE-M3 + Groq Online" : "Initializing..."}
            </strong>
          </span>
        </div>

        {/* Anonymous Mode Toggle */}
        <button
          onClick={() => setAnonymousMode(!anonymousMode)}
          className={`flex items-center gap-2 text-xs font-medium px-3.5 py-1.5 rounded-lg border transition-all ${
            anonymousMode
              ? "bg-purple-500/20 border-purple-500/50 text-purple-300 shadow-md shadow-purple-500/10"
              : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
          }`}
          title="Exclude candidate identity attributes (Name, Photo, Email) from scoring"
        >
          {anonymousMode ? (
            <ShieldCheck className="w-4 h-4 text-purple-400" />
          ) : (
            <ShieldAlert className="w-4 h-4 text-slate-400" />
          )}
          <span>Anonymous Mode</span>
          <span className={`w-2 h-2 rounded-full ${anonymousMode ? "bg-purple-400" : "bg-slate-600"}`}></span>
        </button>
      </div>
    </header>
  );
};
