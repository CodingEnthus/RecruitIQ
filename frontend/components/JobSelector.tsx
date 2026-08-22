"use client";

import React, { useState } from "react";
import { Briefcase, Plus, CheckCircle2, Sparkles, FileCode } from "lucide-react";
import { createJob } from "@/lib/api";

interface JobSelectorProps {
  jobs: any[];
  selectedJobId: string | null;
  onSelectJob: (jobId: string) => void;
  onJobCreated: (job: any) => void;
}

export const JobSelector: React.FC<JobSelectorProps> = ({
  jobs,
  selectedJobId,
  onSelectJob,
  onJobCreated
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!title || !rawText) return;
    setLoading(true);
    try {
      const job = await createJob(title, rawText);
      onJobCreated(job);
      setIsCreating(false);
      setTitle("");
      setRawText("");
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const selectedJob = jobs.find((j) => j.id === selectedJobId);

  return (
    <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-400" />
            Target Job Profile
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Select an active job profile or create a new structured position.
          </p>
        </div>

        <button
          onClick={() => setIsCreating(!isCreating)}
          className="flex items-center gap-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-lg transition-all shadow-md shadow-blue-600/20"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{isCreating ? "Cancel" : "New Job Profile"}</span>
        </button>
      </div>

      {isCreating ? (
        <div className="p-4 bg-slate-900/80 rounded-xl border border-slate-800 space-y-3">
          <input
            type="text"
            placeholder="Job Role Title (e.g. Senior AI Backend Engineer)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <textarea
            placeholder="Paste raw Job Description text here..."
            rows={5}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={handleCreate}
              disabled={loading || !title || !rawText}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition-all"
            >
              {loading ? "Analyzing Job Profile..." : "Analyze & Save Position"}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 overflow-x-auto pb-1">
          {jobs.map((job) => {
            const isSelected = job.id === selectedJobId;
            return (
              <button
                key={job.id}
                onClick={() => onSelectJob(job.id)}
                className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border text-xs font-medium whitespace-nowrap transition-all ${
                  isSelected
                    ? "bg-indigo-600/20 border-indigo-500/50 text-indigo-300 shadow-md shadow-indigo-500/10"
                    : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200"
                }`}
              >
                <FileCode className={`w-4 h-4 ${isSelected ? "text-indigo-400" : "text-slate-500"}`} />
                <span>{job.title}</span>
                {isSelected && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />}
              </button>
            );
          })}
        </div>
      )}

      {selectedJob && selectedJob.structured_profile && (
        <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">Must-Have Required Skills:</span>
            <span className="text-slate-500">Min Experience: {selectedJob.structured_profile.min_experience_years || 2} Years</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {selectedJob.structured_profile.required_skills?.map((skill: string, i: number) => (
              <span key={i} className="text-xs bg-blue-500/10 border border-blue-500/30 text-blue-400 px-2.5 py-0.5 rounded-full font-medium">
                ✓ {skill}
              </span>
            ))}
            {selectedJob.structured_profile.preferred_skills?.map((skill: string, i: number) => (
              <span key={i} className="text-xs bg-purple-500/10 border border-purple-500/30 text-purple-400 px-2.5 py-0.5 rounded-full font-medium">
                + {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
