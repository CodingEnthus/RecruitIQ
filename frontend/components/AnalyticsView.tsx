"use client";

import React, { useEffect, useState } from "react";
import { BarChart3, TrendingUp, AlertTriangle, CheckCircle2, Users, Award } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from "recharts";
import { fetchAnalytics } from "@/lib/api";

export const AnalyticsView: React.FC = () => {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchAnalytics();
        setAnalytics(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-slate-400">
        Loading recruitment analytics data...
      </div>
    );
  }

  const COLORS = ["#3b82f6", "#8b5cf6", "#10b981", "#ef4444"];

  return (
    <div className="space-y-6">
      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl glass-card border border-slate-800 space-y-1">
          <p className="text-xs text-slate-400">Total Candidates Evaluated</p>
          <p className="text-2xl font-bold font-mono text-slate-100">{analytics?.total_candidates ?? 0}</p>
        </div>

        <div className="p-5 rounded-2xl glass-card border border-slate-800 space-y-1">
          <p className="text-xs text-slate-400">Average Candidate Match Score</p>
          <p className="text-2xl font-bold font-mono text-blue-400">
            {analytics?.average_match_score !== undefined ? `${analytics.average_match_score}%` : "0.0%"}
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-card border border-slate-800 space-y-1">
          <p className="text-xs text-slate-400">Strong Matches (&ge; 85%)</p>
          <p className="text-2xl font-bold font-mono text-emerald-400">
            {analytics?.strong_matches ?? 0}
          </p>
        </div>

        <div className="p-5 rounded-2xl glass-card border border-slate-800 space-y-1">
          <p className="text-xs text-slate-400">Most Missing Skill Gap</p>
          <p className="text-2xl font-bold font-mono text-amber-400">
            {analytics?.most_missing_skills?.[0]?.skill ?? "No missing skill data"}
          </p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Most Missing Required Skills */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            Most Missing Required Skills across Candidates
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.most_missing_skills || []} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis dataKey="skill" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }} />
                <Bar dataKey="count" fill="#f59e0b" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skill Demand vs Supply */}
        <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            Skill Demand vs Supply Comparison
          </h3>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={analytics?.skill_demand_vs_supply || []} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                <XAxis dataKey="skill" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }} />
                <Bar dataKey="demand" name="JD Demand" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="supply" name="Candidate Supply" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
