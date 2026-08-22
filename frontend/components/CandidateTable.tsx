"use client";

import React, { useState } from "react";
import { Award, ShieldAlert, Check, X, AlertCircle, Eye, GitCompare, Sparkles, Trash2 } from "lucide-react";

interface CandidateTableProps {
  rankings: any[];
  onSelectCandidate: (candidate: any) => void;
  onCompareSelect: (candidateId: string) => void;
  onDeleteCandidate?: (candidateId: string) => void;
  onDeleteAllCandidates?: () => void;
  selectedCompareIds: string[];
  anonymousMode: boolean;
}

export const CandidateTable: React.FC<CandidateTableProps> = ({
  rankings,
  onSelectCandidate,
  onCompareSelect,
  onDeleteCandidate,
  onDeleteAllCandidates,
  selectedCompareIds,
  anonymousMode
}) => {
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState<boolean>(false);

  if (!rankings || rankings.length === 0) {
    return (
      <div className="p-12 text-center glass-card rounded-2xl border border-slate-800 space-y-3">
        <Sparkles className="w-8 h-8 text-slate-600 mx-auto" />
        <h4 className="text-sm font-semibold text-slate-300">No Candidates Screened Yet</h4>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Upload resumes or click "Screen Candidates" above to trigger hybrid BGE-M3 retrieval & deterministic scoring.
        </p>
      </div>
    );
  }

  const handleDeleteClick = (candidateId: string) => {
    if (confirmDeleteId === candidateId) {
      if (onDeleteCandidate) {
        onDeleteCandidate(candidateId);
      }
      setConfirmDeleteId(null);
    } else {
      setConfirmDeleteId(candidateId);
      setConfirmDeleteAll(false);
    }
  };

  const handleDeleteAllClick = () => {
    if (confirmDeleteAll) {
      if (onDeleteAllCandidates) {
        onDeleteAllCandidates();
      }
      setConfirmDeleteAll(false);
    } else {
      setConfirmDeleteAll(true);
      setConfirmDeleteId(null);
    }
  };

  return (
    <div className="rounded-2xl glass-card border border-slate-800 overflow-hidden">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-400" />
            Candidate Intelligence Ranking
          </h3>
          <p className="text-xs text-slate-400">
            Deterministic weighted scoring: Required Skills (35%), Semantic (25%), Exp (15%), Edu (10%), Proj (10%), Evidence (5%)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs bg-slate-800 text-slate-300 px-3 py-1 rounded-full font-mono">
            {rankings.length} Screened
          </span>

          {onDeleteAllCandidates && (
            <button
              onClick={handleDeleteAllClick}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-medium border transition-all ${
                confirmDeleteAll
                  ? "bg-red-600 text-white border-red-500 shadow-md shadow-red-600/30 animate-pulse"
                  : "bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20"
              }`}
              title="Delete all candidate resumes from database & vector memory"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>{confirmDeleteAll ? "Confirm Wipe All?" : "Clear All"}</span>
            </button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900/80 uppercase text-[11px] font-semibold text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Rank</th>
              <th className="py-3 px-4">Candidate</th>
              <th className="py-3 px-4 text-center">Match Score</th>
              <th className="py-3 px-4 text-center">Confidence</th>
              <th className="py-3 px-4">Matched / Missing Skills</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {rankings.map((c, index) => {
              const isCompared = selectedCompareIds.includes(c.candidate_id);
              const isDeletingThis = confirmDeleteId === c.candidate_id;

              const scoreColor =
                c.final_score >= 85
                  ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                  : c.final_score >= 70
                  ? "text-blue-400 bg-blue-500/10 border-blue-500/30"
                  : "text-amber-400 bg-amber-500/10 border-amber-500/30";

              const confColor =
                c.confidence === "HIGH"
                  ? "text-emerald-400 bg-emerald-500/10"
                  : c.confidence === "MEDIUM"
                  ? "text-blue-400 bg-blue-500/10"
                  : "text-amber-400 bg-amber-500/10";

              return (
                <tr key={c.candidate_id} className="hover:bg-slate-900/40 transition-colors group">
                  {/* Rank */}
                  <td className="py-4 px-4 font-mono font-bold text-slate-400">
                    <div className="flex items-center gap-1.5">
                      {index === 0 && <span className="text-amber-400">🥇</span>}
                      {index === 1 && <span className="text-slate-300">🥈</span>}
                      {index === 2 && <span className="text-amber-600">🥉</span>}
                      <span>#{index + 1}</span>
                    </div>
                  </td>

                  {/* Candidate Name */}
                  <td className="py-4 px-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-100 text-sm">
                          {anonymousMode ? `Candidate-${c.candidate_id.substring(0, 6)}` : c.candidate_name}
                        </span>

                        {c.has_prompt_injection && (
                          <span
                            className="flex items-center gap-1 text-[10px] bg-red-500/15 border border-red-500/30 text-red-400 px-2 py-0.5 rounded-md"
                            title={c.injection_warning}
                          >
                            <ShieldAlert className="w-3 h-3 text-red-400 shrink-0" />
                            Injection Filtered
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-500 truncate max-w-xs">
                        {c.llm_explanation}
                      </p>
                    </div>
                  </td>

                  {/* Match Score */}
                  <td className="py-4 px-4 text-center">
                    <div className={`inline-flex flex-col items-center justify-center px-3 py-1.5 rounded-xl border ${scoreColor}`}>
                      <span className="text-base font-bold font-mono">{c.final_score}%</span>
                      <span className="text-[9px] uppercase tracking-wider opacity-80">Match</span>
                    </div>
                  </td>

                  {/* Confidence */}
                  <td className="py-4 px-4 text-center">
                    <span className={`inline-block px-2.5 py-1 rounded-md text-[10px] font-semibold font-mono uppercase ${confColor}`}>
                      {c.confidence}
                    </span>
                    <p className="text-[10px] text-slate-500 mt-1">{c.evidence_coverage}% coverage</p>
                  </td>

                  {/* Skills */}
                  <td className="py-4 px-4">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {c.skill_gap?.matched_skills?.slice(0, 3).map((s: string, idx: number) => (
                        <span key={idx} className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-md flex items-center gap-1">
                          <Check className="w-2.5 h-2.5" />
                          {s}
                        </span>
                      ))}
                      {c.skill_gap?.missing_skills?.slice(0, 2).map((s: string, idx: number) => (
                        <span key={idx} className="text-[10px] bg-red-500/10 text-red-400 border border-red-500/20 px-2 py-0.5 rounded-md flex items-center gap-1">
                          <X className="w-2.5 h-2.5" />
                          {s}
                        </span>
                      ))}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="py-4 px-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onCompareSelect(c.candidate_id)}
                        className={`p-2 rounded-lg border text-xs transition-all ${
                          isCompared
                            ? "bg-indigo-600 border-indigo-500 text-white shadow-md shadow-indigo-600/20"
                            : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                        }`}
                        title="Compare Side-by-Side"
                      >
                        <GitCompare className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => onSelectCandidate(c)}
                        className="flex items-center gap-1.5 bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 px-3 py-1.5 rounded-lg font-medium text-xs transition-all"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Evidence</span>
                      </button>

                      {onDeleteCandidate && (
                        <button
                          onClick={() => handleDeleteClick(c.candidate_id)}
                          className={`p-2 rounded-lg border text-xs transition-all flex items-center gap-1 ${
                            isDeletingThis
                              ? "bg-red-600 border-red-500 text-white shadow-md shadow-red-600/30 animate-pulse px-2.5"
                              : "bg-slate-900 border-slate-800 text-slate-500 hover:text-red-400 hover:border-red-500/30"
                          }`}
                          title="Delete Candidate Resume"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          {isDeletingThis && <span className="font-semibold text-[11px]">Delete?</span>}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

