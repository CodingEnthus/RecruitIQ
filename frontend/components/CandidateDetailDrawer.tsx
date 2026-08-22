"use client";

import React, { useState } from "react";
import { X, Award, ShieldAlert, CheckCircle2, AlertTriangle, FileText, HelpCircle, UserCheck, Bookmark, GraduationCap, FolderGit2, Trash2 } from "lucide-react";
import { ScoreBreakdownBar } from "./ScoreBreakdownBar";
import { EvidenceList } from "./EvidenceList";

interface CandidateDetailDrawerProps {
  candidate: any;
  onClose: () => void;
  onDeleteCandidate?: (candidateId: string) => void;
  anonymousMode: boolean;
}

export const CandidateDetailDrawer: React.FC<CandidateDetailDrawerProps> = ({
  candidate,
  onClose,
  onDeleteCandidate,
  anonymousMode
}) => {
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (!candidate) return null;

  const candidateId = candidate.candidate_id || candidate.id;
  const displayName = anonymousMode
    ? `Candidate-${(candidateId || "").substring(0, 6)}`
    : candidate.candidate_name || candidate.name;

  const audit = candidate.score_audit_object;

  const handleDelete = () => {
    if (confirmDelete) {
      if (onDeleteCandidate && candidateId) {
        onDeleteCandidate(candidateId);
      }
      onClose();
    } else {
      setConfirmDelete(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-100">{displayName}</h2>
              <span className="text-xs font-mono bg-blue-500/10 border border-blue-500/20 text-blue-400 px-2.5 py-0.5 rounded-full font-semibold">
                Match: {candidate.final_score}%
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Confidence Level: <strong className="text-emerald-400">{candidate.confidence}</strong> ({candidate.evidence_coverage}% Real Evidence Coverage)
            </p>
          </div>

          <div className="flex items-center gap-2">
            {onDeleteCandidate && candidateId && (
              <button
                onClick={handleDelete}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  confirmDelete
                    ? "bg-red-600 text-white border-red-500 shadow-md shadow-red-600/30 animate-pulse"
                    : "bg-slate-800 text-slate-400 hover:text-red-400 hover:bg-slate-700 border-slate-700"
                }`}
                title="Delete Resume"
              >
                <Trash2 className="w-4 h-4" />
                <span>{confirmDelete ? "Confirm Delete?" : "Delete"}</span>
              </button>
            )}

            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>


        {/* Security Alert if Prompt Injection Detected */}
        {candidate.has_prompt_injection && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl space-y-1 text-xs text-red-300">
            <div className="flex items-center gap-2 font-semibold text-red-400">
              <ShieldAlert className="w-4 h-4" />
              <span>Prompt Injection Guard Alert</span>
            </div>
            <p className="leading-relaxed opacity-90">{candidate.injection_warning}</p>
          </div>
        )}

        {/* Grounded Explanation */}
        <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-2">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Award className="w-4 h-4 text-amber-400" />
            Grounded Match Explanation (Claim &rarr; Evidence)
          </h3>
          <p className="text-xs text-slate-300 leading-relaxed font-sans">
            {candidate.llm_explanation}
          </p>
        </div>

        {/* Score Breakdown Bar Chart */}
        <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Deterministic Score Component Breakdown
          </h3>
          <ScoreBreakdownBar breakdown={candidate.score_breakdown} />
        </div>

        {/* Component Audit Details Table */}
        {audit && (
          <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <FileText className="w-4 h-4 text-blue-400" />
              Score Component Audit Object
            </h3>
            <div className="space-y-2 font-mono text-xs">
              {Object.values(audit).map((comp: any, idx: number) => (
                <div key={idx} className="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex items-start justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-200">{comp.name}</span>
                      <span className="text-[10px] text-slate-500">({comp.weight_percentage}% weight)</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{comp.evidence_summary}</p>
                    {comp.verified_evidence?.length > 0 && (
                      <ul className="text-[10px] text-slate-400 space-y-0.5 mt-1">
                        {comp.verified_evidence.slice(0, 2).map((ev: string, i: number) => (
                          <li key={i} className="text-emerald-400/90">• {ev}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-blue-400 text-sm">{comp.score}%</span>
                    <p className="text-[10px] text-slate-500">{comp.weighted_points} pts</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Skill Evidence Hierarchy Table */}
        {candidate.skill_gap?.skill_evidence_details?.length > 0 && (
          <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-blue-400" />
              Skill Evidence Hierarchy Evaluation
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[10px] uppercase font-semibold text-slate-500 border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Skill</th>
                    <th className="py-2 px-3 text-center">Status</th>
                    <th className="py-2 px-3">Source Section</th>
                    <th className="py-2 px-3 text-right">Strength</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50 font-mono text-[11px]">
                  {candidate.skill_gap.skill_evidence_details.map((d: any, idx: number) => {
                    const rawBadge = d.badge_status;
                    const hasTextAndStrength = Boolean(d.evidence_text && d.evidence_text.length > 0 && d.evidence_strength !== undefined && d.evidence_strength > 0);
                    let badge = rawBadge;
                    if (hasTextAndStrength && badge === "NOT_FOUND") {
                      badge = "DEMONSTRATED";
                    }

                    const isVer = badge === "VERIFIED";
                    const isDem = badge === "DEMONSTRATED";
                    const isInd = badge === "INDIRECT";
                    const isClaim = badge === "CLAIMED";
                    const badgeClass = isVer || isDem
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold"
                      : isInd
                      ? "bg-blue-500/10 text-blue-400 border-blue-500/30 font-bold"
                      : isClaim
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/30 font-bold"
                      : "bg-red-500/10 text-red-400 border-red-500/30 font-bold";

                    return (
                      <tr key={idx} className="hover:bg-slate-950/30">
                        <td className="py-2.5 px-3 font-semibold text-slate-200">{d.skill}</td>
                        <td className="py-2.5 px-3 text-center">
                          <span className={`px-2 py-0.5 rounded text-[10px] border ${badgeClass}`}>
                            {isVer ? "✓ VERIFIED" : isDem ? "✓ DEMONSTRATED" : isInd ? "◐ INDIRECT" : isClaim ? "◐ CLAIMED" : "✗ NOT FOUND"}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-400">{d.source_section}</td>
                        <td className="py-2.5 px-3 text-right font-bold text-blue-400">{d.evidence_strength.toFixed(1)}</td>
                      </tr>

                    );
                  })}

                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recommended Interview Focus Areas */}
        {candidate.recommended_interview_focus?.length > 0 && (
          <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-300 flex items-center gap-2">
              <UserCheck className="w-4 h-4 text-indigo-400" />
              Recommended Technical Interview Questions
            </h3>
            <ul className="space-y-1.5 text-xs text-indigo-200">
              {candidate.recommended_interview_focus.map((q: string, i: number) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-indigo-400 font-bold">•</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Retrieved Evidence Excerpts */}
        <div className="p-4 rounded-xl glass-card border border-slate-800 space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Retrieved Requirement Evidence Excerpts
          </h3>
          <EvidenceList evidenceList={candidate.matched_evidence} />
        </div>
      </div>
    </div>
  );
};
