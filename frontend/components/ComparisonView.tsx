"use client";

import React, { useState } from "react";
import { GitCompare, Trophy, CheckCircle2, ArrowRight, Sparkles, AlertCircle } from "lucide-react";
import { compareCandidates } from "@/lib/api";

interface ComparisonViewProps {
  candidates: any[];
  jobId: string | null;
  anonymousMode: boolean;
}

export const ComparisonView: React.FC<ComparisonViewProps> = ({
  candidates,
  jobId,
  anonymousMode
}) => {
  const [candIdA, setCandIdA] = useState<string>(candidates[0]?.candidate_id || "");
  const [candIdB, setCandIdB] = useState<string>(candidates[1]?.candidate_id || "");
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!jobId || !candIdA || !candIdB) {
      setError("Please select a target job and two candidates to compare.");
      return;
    }
    if (candIdA === candIdB) {
      setError("Please select two distinct candidates for comparison.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await compareCandidates(jobId, candIdA, candIdB);
      setComparisonResult(res);
    } catch (e: any) {
      setError(e.message || "Failed to compare candidates.");
    } finally {
      setLoading(false);
    }
  };

  const getCandidateName = (c: any) => {
    if (!c) return "";
    return anonymousMode ? `Candidate-${c.candidate_id?.substring(0, 6)}` : c.candidate_name;
  };

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-indigo-400" />
            Candidate Comparison Engine ("Why Candidate A &gt; Candidate B?")
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Side-by-side evidence grounded breakdown contrasting technical competencies, scores, and evidence depth.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-slate-400 font-medium block mb-1">Candidate A:</label>
            <select
              value={candIdA}
              onChange={(e) => setCandIdA(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select Candidate A</option>
              {candidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  {getCandidateName(c)} (Score: {c.final_score}%)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-slate-400 font-medium block mb-1">Candidate B:</label>
            <select
              value={candIdB}
              onChange={(e) => setCandIdB(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="">Select Candidate B</option>
              {candidates.map((c) => (
                <option key={c.candidate_id} value={c.candidate_id}>
                  {getCandidateName(c)} (Score: {c.final_score}%)
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading || !candIdA || !candIdB}
          className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white font-semibold text-xs py-2.5 rounded-xl transition-all shadow-lg shadow-indigo-600/20"
        >
          {loading ? "Comparing Candidates..." : "Run Evidence Comparison"}
        </button>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400 flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {comparisonResult && (
        <div className="space-y-6">
          {/* Winner Explanation Summary */}
          <div className="p-6 rounded-2xl bg-indigo-500/10 border border-indigo-500/30 space-y-3">
            <div className="flex items-center gap-2 text-indigo-300 font-bold text-sm">
              <Trophy className="w-5 h-5 text-amber-400" />
              <span>Comparative Ranking Analysis</span>
            </div>
            <p className="text-xs text-slate-200 leading-relaxed">
              {comparisonResult.comparison_summary}
            </p>
            <div className="flex flex-wrap gap-2 pt-2">
              {comparisonResult.key_differentiators?.map((diff: string, idx: number) => (
                <span key={idx} className="text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />
                  {diff}
                </span>
              ))}
            </div>
          </div>

          {/* Side by side matrix table */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[comparisonResult.candidate_a, comparisonResult.candidate_b].map((cand: any, idx: number) => {
              const isWinner = cand.candidate_id === comparisonResult.winner_id;
              return (
                <div
                  key={cand.candidate_id}
                  className={`p-6 rounded-2xl glass-card border ${
                    isWinner ? "border-amber-500/50 shadow-xl shadow-amber-500/5" : "border-slate-800"
                  } space-y-4`}
                >
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-bold text-sm text-slate-100">{getCandidateName(cand)}</h4>
                        {isWinner && (
                          <span className="text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/40 px-2 py-0.5 rounded-full font-bold">
                            WINNER
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">Confidence: {cand.confidence}</p>
                    </div>
                    <div className="text-right">
                      <span className="text-xl font-mono font-bold text-blue-400">{cand.final_score}%</span>
                      <p className="text-[10px] text-slate-500">Overall Match</p>
                    </div>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-slate-800/50">
                      <span className="text-slate-400">Required Skills Score:</span>
                      <span className="font-mono font-bold text-slate-200">{cand.score_breakdown.skill_score}%</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/50">
                      <span className="text-slate-400">Semantic Fit Score:</span>
                      <span className="font-mono font-bold text-slate-200">{cand.score_breakdown.semantic_score}%</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/50">
                      <span className="text-slate-400">Experience Score:</span>
                      <span className="font-mono font-bold text-slate-200">{cand.score_breakdown.experience_score}%</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/50">
                      <span className="text-slate-400">Education Score:</span>
                      <span className="font-mono font-bold text-slate-200">{cand.score_breakdown.education_score}%</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-400">Evidence Coverage:</span>
                      <span className="font-mono font-bold text-slate-200">{cand.evidence_coverage}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
