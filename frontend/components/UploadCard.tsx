"use client";

import React, { useState } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { uploadResume } from "@/lib/api";

interface UploadCardProps {
  onUploadSuccess: (candidate: any) => void;
}

export const UploadCard: React.FC<UploadCardProps> = ({ onUploadSuccess }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setUploadStatus("Ingesting PDF & scanning text...");

    try {
      setUploadStatus("Normalizing skills & generating BGE-M3 embeddings...");
      const result = await uploadResume(file);
      setUploadStatus("Successfully ingested candidate!");
      onUploadSuccess(result);
    } catch (err: any) {
      setError(err.message || "Failed to process resume");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-blue-400" />
            Resume Ingestion Pipeline
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Accepts PDF/TXT resumes. Runs PyMuPDF parsing, skill normalization, and Qdrant chunk indexing.
          </p>
        </div>
      </div>

      <label className="border-2 border-dashed border-slate-700 hover:border-blue-500/50 bg-slate-900/40 hover:bg-slate-900/80 rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all group">
        <input
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileChange}
          disabled={isUploading}
          className="hidden"
        />

        {isUploading ? (
          <div className="flex flex-col items-center space-y-3">
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            <p className="text-xs font-medium text-blue-300">{uploadStatus}</p>
          </div>
        ) : (
          <>
            <div className="w-12 h-12 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center group-hover:scale-110 transition-transform">
              <FileText className="w-6 h-6" />
            </div>
            <p className="mt-3 text-sm font-medium text-slate-200">
              Click or drag & drop candidate resume (PDF or TXT)
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports automated injection detection & section boundary extraction
            </p>
          </>
        )}
      </label>

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-400">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
