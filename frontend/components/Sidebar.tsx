"use client";

import React from "react";
import { LayoutDashboard, Users, GitCompare, MessageSquareCode, BarChart3, ShieldAlert } from "lucide-react";

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  candidateCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  candidateCount
}) => {
  const navItems = [
    { id: "dashboard", label: "Dashboard & Screening", icon: LayoutDashboard },
    { id: "compare", label: "Compare Candidates", icon: GitCompare },
    { id: "assistant", label: "Recruiter RAG Chat", icon: MessageSquareCode },
    { id: "analytics", label: "Talent Analytics", icon: BarChart3 }
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-950 flex flex-col p-4 space-y-6">
      <div className="space-y-1">
        <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Navigation</p>
        <nav className="space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? "bg-blue-600/15 text-blue-400 border border-blue-500/30 font-semibold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                  <span>{item.label}</span>
                </div>
                {item.id === "dashboard" && candidateCount > 0 && (
                  <span className="text-xs bg-slate-800 border border-slate-700 px-2 py-0.5 rounded-full text-slate-300">
                    {candidateCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      <div className="mt-auto p-4 rounded-xl glass-card border border-slate-800 space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-blue-400">
          <ShieldAlert className="w-4 h-4 text-emerald-400" />
          <span>Security Guard Active</span>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          Resume text treated as <strong>untrusted user input</strong>. Prompt injection triggers are automatically isolated and tagged.
        </p>
      </div>
    </aside>
  );
};
