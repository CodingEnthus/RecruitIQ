import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RecruitIQ — Explainable RAG-Powered AI Resume Intelligence",
  description: "Production-grade AI resume screening, deterministic explainable scoring, BGE-M3 hybrid retrieval, and recruiter RAG co-pilot."
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-slate-950 text-slate-100`}>
        {children}
      </body>
    </html>
  );
}
