"use client";

import React from "react";
import { CheckCircle2, AlertCircle, HelpCircle, FileText, Bookmark } from "lucide-react";

interface EvidenceMatch {
  requirement: string;
  evidence_text: string;
  section: string;
  match_status: string;
  badge_status?: string;
  evidence_strength?: number;
}

interface EvidenceListProps {
  evidenceList: EvidenceMatch[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidenceList }) => {
  if (!evidenceList || evidenceList.length === 0) {
    return (
      <p className="text-xs text-slate-500 italic p-4 text-center">
        No specific requirement evidence chunks retrieved.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {evidenceList.map((item, idx) => {
        const rawBadge = item.badge_status || (item.match_status === "matched" ? "DEMONSTRATED" : item.match_status === "partial" ? "CLAIMED" : "NOT_FOUND");
        const hasTextAndStrength = Boolean(item.evidence_text && item.evidence_text.length > 0 && item.evidence_strength !== undefined && item.evidence_strength > 0);
        
        // Strict invariant: if evidence_text exists AND evidence_strength > 0, status cannot be NOT_FOUND
        let badge = rawBadge;
        if (hasTextAndStrength && badge === "NOT_FOUND") {
          badge = "DEMONSTRATED";
        }

        const isVerified = badge === "VERIFIED";
        const isDemonstrated = badge === "DEMONSTRATED";
        const isIndirect = badge === "INDIRECT";
        const isClaimed = badge === "CLAIMED";
        
        const badgeColor = isVerified || isDemonstrated
          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 font-bold"
          : isIndirect
          ? "bg-blue-500/10 text-blue-400 border-blue-500/30 font-bold"
          : isClaimed
          ? "bg-amber-500/10 text-amber-400 border-amber-500/30 font-bold"
          : "bg-red-500/10 text-red-400 border-red-500/30 font-bold";

        const badgeIcon = isVerified
          ? "✓ VERIFIED"
          : isDemonstrated
          ? "✓ DEMONSTRATED"
          : isIndirect
          ? "◐ INDIRECT"
          : isClaimed
          ? "◐ CLAIMED"
          : "✗ NOT FOUND";

        return (
          <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                {(isVerified || isDemonstrated) && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
                {isIndirect && <AlertCircle className="w-4 h-4 text-blue-400 shrink-0" />}
                {isClaimed && <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />}
                {!isVerified && !isDemonstrated && !isIndirect && !isClaimed && <HelpCircle className="w-4 h-4 text-red-400 shrink-0" />}

                Requirement: <strong className="text-slate-100">{item.requirement}</strong>
              </span>

              <div className="flex items-center gap-2">
                <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                  <Bookmark className="w-3 h-3 text-slate-500" />
                  Source: <strong className="text-slate-300">{item.section}</strong>
                </span>
                <span className={`text-[10px] tracking-wider px-2.5 py-0.5 rounded-md border ${badgeColor}`}>
                  {badgeIcon}
                </span>
              </div>
            </div>

            <div className="p-3 bg-slate-950/90 rounded-lg border border-slate-800/80 text-xs text-slate-300 font-mono leading-relaxed flex items-start gap-2.5">
              <FileText className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p>"{item.evidence_text}"</p>
                {item.evidence_strength !== undefined && (
                  <p className="text-[10px] text-slate-500">
                    Evidence Weight: <strong className="text-blue-400">{item.evidence_strength.toFixed(1)}</strong> / 1.0
                  </p>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
