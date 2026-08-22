"use client";

import React, { useEffect, useState } from "react";
import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";
import { UploadCard } from "@/components/UploadCard";
import { JobSelector } from "@/components/JobSelector";
import { CandidateTable } from "@/components/CandidateTable";
import { CandidateDetailDrawer } from "@/components/CandidateDetailDrawer";
import { ComparisonView } from "@/components/ComparisonView";
import { RecruiterChatPanel } from "@/components/RecruiterChatPanel";
import { AnalyticsView } from "@/components/AnalyticsView";

import {
  fetchHealth,
  fetchJobs,
  fetchCandidates,
  screenCandidates,
  createJob,
  deleteCandidate,
  deleteAllCandidates
} from "@/lib/api";
import { Play, Sparkles, AlertCircle } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("dashboard");
  const [anonymousMode, setAnonymousMode] = useState<boolean>(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  const [jobs, setJobs] = useState<any[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);

  const [candidates, setCandidates] = useState<any[]>([]);
  const [rankings, setRankings] = useState<any[]>([]);

  const [selectedCandidate, setSelectedCandidate] = useState<any | null>(null);
  const [selectedCompareIds, setSelectedCompareIds] = useState<string[]>([]);

  const [isScreening, setIsScreening] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Load initial data on startup
  useEffect(() => {
    async function initData() {
      try {
        const health = await fetchHealth();
        if (health.status === "healthy") {
          setIsBackendConnected(true);
        }

        const jobsData = await fetchJobs();
        if (jobsData && jobsData.length > 0) {
          setJobs(jobsData);
          setSelectedJobId(jobsData[0].id);
        } else {
          // Create default Senior AI Backend Engineer Job Profile if empty
          const defaultJob = await createJob(
            "Senior AI Backend Engineer",
            "We are looking for a Senior AI Backend Engineer to build high-performance REST APIs, vector search pipelines, and RAG architectures.\n\nRequired Skills:\n- Python\n- FastAPI\n- PostgreSQL\n- REST APIs\n- RAG / Vector Databases\n\nNice to Have:\n- Docker\n- AWS\n- Kubernetes\n\nExperience: 3+ years backend development."
          );
          setJobs([defaultJob]);
          setSelectedJobId(defaultJob.id);
        }

        const candsData = await fetchCandidates();
        setCandidates(candsData || []);
      } catch (e) {
        console.error("Backend connection error:", e);
        setIsBackendConnected(false);
      }
    }
    initData();
  }, []);

  // Run screening for selected job & candidates
  const handleRunScreening = async () => {
    if (!selectedJobId) {
      setError("Please select a target job profile to screen candidates against.");
      return;
    }
    setIsScreening(true);
    setError(null);
    try {
      const res = await screenCandidates(selectedJobId, undefined, anonymousMode);
      setRankings(res.rankings || []);
    } catch (err: any) {
      setError(err.message || "Screening execution failed");
    } finally {
      setIsScreening(false);
    }
  };

  const handleUploadSuccess = async (res: any) => {
    const updatedCands = await fetchCandidates();
    setCandidates(updatedCands);
    if (selectedJobId) {
      handleRunScreening();
    }
  };

  const handleCompareSelect = (candidateId: string) => {
    if (selectedCompareIds.includes(candidateId)) {
      setSelectedCompareIds(selectedCompareIds.filter((id) => id !== candidateId));
    } else {
      if (selectedCompareIds.length >= 2) {
        setSelectedCompareIds([selectedCompareIds[1], candidateId]);
      } else {
        setSelectedCompareIds([...selectedCompareIds, candidateId]);
      }
    }
  };

  const handleDeleteCandidate = async (candidateId: string) => {
    try {
      await deleteCandidate(candidateId);
      setCandidates((prev) => prev.filter((c) => c.id !== candidateId));
      setRankings((prev) => prev.filter((r) => r.candidate_id !== candidateId && r.id !== candidateId));
      setSelectedCompareIds((prev) => prev.filter((id) => id !== candidateId));
      if (selectedCandidate && (selectedCandidate.candidate_id === candidateId || selectedCandidate.id === candidateId)) {
        setSelectedCandidate(null);
      }
    } catch (err: any) {
      setError(err.message || "Failed to delete candidate");
    }
  };

  const handleDeleteAllCandidates = async () => {
    try {
      await deleteAllCandidates();
      setCandidates([]);
      setRankings([]);
      setSelectedCompareIds([]);
      setSelectedCandidate(null);
    } catch (err: any) {
      setError(err.message || "Failed to delete all candidates");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans">
      {/* Top Navbar */}
      <Navbar
        anonymousMode={anonymousMode}
        setAnonymousMode={setAnonymousMode}
        isBackendConnected={isBackendConnected}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          candidateCount={rankings.length || candidates.length}
        />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-8 space-y-6">
          {/* TAB 1: DASHBOARD & SCREENING */}
          {activeTab === "dashboard" && (
            <div className="space-y-6 max-w-7xl mx-auto">
              {/* Header Hero Banner */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-2xl glass-panel border border-slate-800">
                <div>
                  <h1 className="text-xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2">
                    Recruiter Screening Workspace
                    <Sparkles className="w-5 h-5 text-blue-400" />
                  </h1>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                    Ingest candidate resumes, analyze job requirements, run BGE-M3 hybrid retrieval with BM25 & RRF, and generate evidence-grounded deterministic rankings.
                  </p>
                </div>

                <button
                  onClick={handleRunScreening}
                  disabled={isScreening || !selectedJobId}
                  className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs px-5 py-3 rounded-xl transition-all shadow-lg shadow-blue-600/25 disabled:opacity-50"
                >
                  <Play className="w-4 h-4 fill-white" />
                  <span>{isScreening ? "Running Hybrid AI Screening..." : "Screen & Rank Candidates"}</span>
                </button>
              </div>

              {error && (
                <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-xs text-red-400 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Upload Card & Job Selector Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <UploadCard onUploadSuccess={handleUploadSuccess} />
                <JobSelector
                  jobs={jobs}
                  selectedJobId={selectedJobId}
                  onSelectJob={(id) => setSelectedJobId(id)}
                  onJobCreated={(job) => {
                    setJobs([job, ...jobs]);
                    setSelectedJobId(job.id);
                  }}
                />
              </div>

              {/* Candidate Rankings Table */}
              <CandidateTable
                rankings={rankings}
                onSelectCandidate={(c) => setSelectedCandidate(c)}
                onCompareSelect={handleCompareSelect}
                onDeleteCandidate={handleDeleteCandidate}
                onDeleteAllCandidates={handleDeleteAllCandidates}
                selectedCompareIds={selectedCompareIds}
                anonymousMode={anonymousMode}
              />
            </div>
          )}

          {/* TAB 2: CANDIDATE COMPARISON */}
          {activeTab === "compare" && (
            <div className="max-w-7xl mx-auto">
              <ComparisonView
                candidates={rankings.length > 0 ? rankings : candidates}
                jobId={selectedJobId}
                anonymousMode={anonymousMode}
              />
            </div>
          )}

          {/* TAB 3: RECRUITER RAG CHAT */}
          {activeTab === "assistant" && (
            <div className="max-w-6xl mx-auto">
              <RecruiterChatPanel jobId={selectedJobId} anonymousMode={anonymousMode} />
            </div>
          )}

          {/* TAB 4: TALENT ANALYTICS */}
          {activeTab === "analytics" && (
            <div className="max-w-7xl mx-auto">
              <AnalyticsView />
            </div>
          )}
        </main>
      </div>

      {/* Candidate Detail Slide-Over Modal */}
      {selectedCandidate && (
        <CandidateDetailDrawer
          candidate={selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
          onDeleteCandidate={handleDeleteCandidate}
          anonymousMode={anonymousMode}
        />
      )}
    </div>
  );
}

