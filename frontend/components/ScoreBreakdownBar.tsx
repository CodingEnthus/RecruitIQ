"use client";

import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

interface ScoreBreakdownBarProps {
  breakdown: {
    skill_score: number;
    semantic_score: number;
    experience_score: number;
    education_score: number;
    project_score: number;
    evidence_score: number;
    skill_points?: number;
    semantic_points?: number;
    experience_points?: number;
    education_points?: number;
    project_points?: number;
    evidence_points?: number;
  };
}

export const ScoreBreakdownBar: React.FC<ScoreBreakdownBarProps> = ({ breakdown }) => {
  const data = [
    { name: `Skills (${(breakdown.skill_points ?? (breakdown.skill_score * 0.35)).toFixed(1)}/35 pts)`, score: breakdown.skill_score, fill: "#3b82f6" },
    { name: `Semantic (${(breakdown.semantic_points ?? (breakdown.semantic_score * 0.25)).toFixed(1)}/25 pts)`, score: breakdown.semantic_score, fill: "#8b5cf6" },
    { name: `Exp (${(breakdown.experience_points ?? (breakdown.experience_score * 0.15)).toFixed(1)}/15 pts)`, score: breakdown.experience_score, fill: "#10b981" },
    { name: `Edu (${(breakdown.education_points ?? (breakdown.education_score * 0.10)).toFixed(1)}/10 pts)`, score: breakdown.education_score, fill: "#f59e0b" },
    { name: `Projects (${(breakdown.project_points ?? (breakdown.project_score * 0.10)).toFixed(1)}/10 pts)`, score: breakdown.project_score, fill: "#ec4899" },
    { name: `Evidence (${(breakdown.evidence_points ?? (breakdown.evidence_score * 0.05)).toFixed(1)}/5 pts)`, score: breakdown.evidence_score, fill: "#06b6d4" }
  ];

  return (
    <div className="h-64 w-full pt-2">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
          <XAxis type="number" domain={[0, 100]} stroke="#64748b" tick={{ fontSize: 11 }} />
          <YAxis dataKey="name" type="category" stroke="#94a3b8" tick={{ fontSize: 11 }} width={160} />
          <Tooltip
            contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", fontSize: "12px" }}
            formatter={(value: any) => [`${value}%`, "Component Rating"]}
          />
          <Bar dataKey="score" radius={[0, 6, 6, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
