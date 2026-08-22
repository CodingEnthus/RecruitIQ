"use client";

import React, { useState } from "react";
import { MessageSquareCode, Send, Sparkles, FileText, Loader2 } from "lucide-react";
import { queryRAGAssistant } from "@/lib/api";

interface Citation {
  candidate_id: string;
  candidate_name: string;
  section: string;
  excerpt: string;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

interface RecruiterChatPanelProps {
  jobId: string | null;
  anonymousMode: boolean;
}

export const RecruiterChatPanel: React.FC<RecruiterChatPanelProps> = ({ jobId, anonymousMode }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I am your RecruitIQ RAG Assistant. Ask me any question about your candidate pool, skill gaps, or experience requirements (e.g. 'Which candidates have FastAPI & PostgreSQL experience?' or 'Who lacks Kubernetes?')."
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const sampleQueries = [
    "Which candidates have FastAPI & PostgreSQL experience?",
    "Which candidates lack Kubernetes or AWS?",
    "Find candidates who have built RAG applications",
    "What are the most common skill gaps in our candidate pool?"
  ];

  const handleSend = async (queryText?: string) => {
    const q = queryText || inputQuery;
    if (!q.trim() || loading) return;

    const userMsg: Message = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    if (!queryText) setInputQuery("");
    setLoading(true);

    try {
      const res = await queryRAGAssistant(q, jobId || undefined);
      const assistantMsg: Message = {
        role: "assistant",
        content: res.answer,
        citations: res.citations
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error querying candidate knowledge base."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl glass-card border border-slate-800 space-y-4 flex flex-col h-[700px]">
      <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <MessageSquareCode className="w-5 h-5 text-blue-400" />
            Recruiter RAG Co-Pilot Assistant
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Hybrid BGE-M3 + BM25 search over candidate evidence vectors with grounded LLM reasoning.
          </p>
        </div>
        <span className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-1 rounded-full font-mono">
          RAG Active
        </span>
      </div>

      {/* Suggested Questions */}
      <div className="flex flex-wrap gap-2">
        {sampleQueries.map((sq, i) => (
          <button
            key={i}
            onClick={() => handleSend(sq)}
            className="text-[11px] bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 px-3 py-1 rounded-full transition-all text-left"
          >
            💡 {sq}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-2xl p-4 rounded-2xl text-xs space-y-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white rounded-br-none"
                  : "bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none"
              }`}
            >
              <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="pt-2 border-t border-slate-800 space-y-1.5">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-blue-400 flex items-center gap-1">
                    <FileText className="w-3 h-3" /> Grounded Evidence Citations ({msg.citations.length})
                  </p>
                  <div className="space-y-1">
                    {msg.citations.map((c, cIdx) => (
                      <div key={cIdx} className="p-2 bg-slate-950/80 rounded-lg text-[11px] border border-slate-800 font-mono text-slate-300">
                        <span className="text-blue-400 font-bold">[{c.candidate_name}]</span> Section '{c.section}': "{c.excerpt}"
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-xs text-blue-400 p-3 bg-slate-900 rounded-xl border border-slate-800 w-fit">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Retrieving candidate evidence vectors & synthesizing grounded response...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
        <input
          type="text"
          placeholder="Ask a question about candidates, skills, or job requirements..."
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !inputQuery.trim()}
          className="bg-blue-600 hover:bg-blue-500 text-white p-2.5 rounded-xl transition-all shadow-md shadow-blue-600/20 disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
