"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  BookOpen,
  UploadCloud,
  FileText,
  Video,
  Presentation,
  Search,
  ExternalLink,
  Download,
  Trash2,
  CheckCircle2,
  Clock,
  Sparkles,
  ClipboardCheck,
  ChevronRight,
  Layers,
  X,
  AlertCircle,
  Loader2,
  FileCheck
} from "lucide-react";
import { client } from "@/lib/api/client";
import { StudyLibraryItem } from "@/lib/api/types";
import { cn } from "@/lib/cn";

export default function StudyLibraryPage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<StudyLibraryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<"all" | "pdf" | "pptx" | "youtube">("all");
  const [selectedDoc, setSelectedDoc] = useState<any | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const fetchLibrary = async () => {
    setIsLoading(true);
    try {
      const res = await client.get<StudyLibraryItem[]>("/api/content/library");
      if (Array.isArray(res)) {
        setDocuments(res);
      }
    } catch (err) {
      console.warn("Could not load library documents:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLibrary();
  }, []);

  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      const matchesSearch =
        !searchQuery ||
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.competency_mapped.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (doc.concepts || []).some((c) => c.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesType =
        filterType === "all" ||
        (filterType === "pdf" && doc.source_type.toLowerCase().includes("pdf")) ||
        (filterType === "pptx" && doc.source_type.toLowerCase().includes("pptx")) ||
        (filterType === "youtube" && doc.source_type.toLowerCase().includes("youtube"));

      return matchesSearch && matchesType;
    });
  }, [documents, searchQuery, filterType]);

  const handleStartAssessment = async (doc: StudyLibraryItem) => {
    try {
      // Fetch full document with questions
      const fullDoc = await client.get<any>(`/api/content/library/${doc.id}`);
      if (fullDoc && Array.isArray(fullDoc.questions) && fullDoc.questions.length > 0) {
        localStorage.setItem("active_assessment_questions", JSON.stringify(fullDoc.questions));
        router.push(`/dashboard/assessments?session_id=lib_${doc.id}`);
      } else {
        router.push("/dashboard/assessments");
      }
    } catch (err) {
      console.warn("Failed loading document questions:", err);
      router.push("/dashboard/assessments");
    }
  };

  const handleViewDetails = async (docId: number) => {
    setIsDetailLoading(true);
    try {
      const docDetail = await client.get<any>(`/api/content/library/${docId}`);
      setSelectedDoc(docDetail);
    } catch (err) {
      console.warn("Failed loading detail:", err);
    } finally {
      setIsDetailLoading(false);
    }
  };

  const handleDelete = async (docId: number) => {
    try {
      await client.delete(`/api/content/library/${docId}`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      if (selectedDoc?.id === docId) setSelectedDoc(null);
      setDeleteConfirmId(null);
    } catch (err) {
      console.warn("Failed deleting document:", err);
    }
  };

  const totalQuestions = documents.reduce((acc, d) => acc + (d.questions_count || 15), 0);

  return (
    <div className="space-y-6 w-full">
      {/* HEADER BANNER */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold border border-blue-200">
              Personalized Knowledge Base
            </span>
            <span className="text-xs text-slate-500 font-medium">
              {documents.length} Materials Ingested • {totalQuestions} AI-Generated MCQs
            </span>
          </div>
          <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-wide">
            Study Library & Document Archive
          </h2>
          <p className="text-sm text-slate-600 font-sans mt-1">
            Access your ingested policy handbooks, research presentations, and lecture transcripts. Review key concepts and take 15-question assessments anytime.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            href="/dashboard/ingestion"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm hover:shadow"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Ingest New Material</span>
          </Link>
        </div>
      </div>

      {/* SEARCH AND FILTER BAR */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search documents, topics, or competencies..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          {[
            { id: "all", label: "All Items" },
            { id: "pdf", label: "PDFs" },
            { id: "pptx", label: "Presentations" },
            { id: "youtube", label: "YouTube" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilterType(tab.id as any)}
              className={cn(
                "px-3 py-1.5 rounded-lg text-xs font-semibold transition whitespace-nowrap",
                filterType === tab.id
                  ? "bg-slate-900 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* DOCUMENT CARDS GRID */}
      {isLoading ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-xs">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-3" />
          <p className="text-sm font-medium text-slate-600">Loading your study library...</p>
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-dashed border-slate-300 shadow-xs max-w-2xl mx-auto my-6">
          <div className="w-14 h-14 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4 border border-blue-100">
            <BookOpen className="w-7 h-7" />
          </div>
          <h3 className="font-heading text-xl text-slate-900 mb-2">
            {searchQuery ? "No matching documents found" : "Your Study Library is Empty"}
          </h3>
          <p className="text-sm text-slate-600 max-w-md mx-auto mb-6">
            {searchQuery
              ? "Try adjusting your search query or filter criteria."
              : "Whenever you ingest training manuals (PDF/PPTX) or YouTube lectures in the Ingestion Hub, they are saved here along with 15 AI-generated MCQs."}
          </p>
          <Link
            href="/dashboard/ingestion"
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition shadow-sm"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Ingest Your First Document</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredDocs.map((doc) => {
            const isPdf = doc.source_type.toLowerCase().includes("pdf");
            const isPptx = doc.source_type.toLowerCase().includes("pptx");
            const isYt = doc.source_type.toLowerCase().includes("youtube");

            return (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  {/* Top Badge & Delete */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider",
                        isPdf
                          ? "bg-rose-50 text-rose-700 border border-rose-200"
                          : isPptx
                          ? "bg-amber-50 text-amber-700 border border-amber-200"
                          : "bg-purple-50 text-purple-700 border border-purple-200"
                      )}
                    >
                      {isPdf ? (
                        <FileText className="w-3.5 h-3.5" />
                      ) : isPptx ? (
                        <Presentation className="w-3.5 h-3.5" />
                      ) : (
                        <Video className="w-3.5 h-3.5" />
                      )}
                      {doc.source_type.toUpperCase()}
                    </span>

                    <button
                      onClick={() => setDeleteConfirmId(doc.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                      title="Remove from library"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Document Title */}
                  <h3 className="font-heading font-bold text-base text-slate-900 leading-snug mb-2 line-clamp-2">
                    {doc.title}
                  </h3>

                  {/* Competency Pill */}
                  <div className="inline-block px-2.5 py-0.5 bg-slate-100 text-slate-700 rounded-md text-xs font-medium mb-3">
                    {doc.competency_mapped}
                  </div>

                  {/* Summary Snippet */}
                  {doc.summary && (
                    <p className="text-xs text-slate-600 line-clamp-3 mb-4 font-sans leading-relaxed">
                      {doc.summary}
                    </p>
                  )}

                  {/* Concept Tags */}
                  {doc.concepts && doc.concepts.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {doc.concepts.slice(0, 3).map((concept, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-0.5 bg-slate-50 text-slate-500 rounded text-[11px] font-medium border border-slate-100"
                        >
                          #{concept}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Footer and Actions */}
                <div className="pt-4 border-t border-slate-100 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
                    <span className="flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      {doc.questions_count || 15} MCQs Generated
                    </span>
                    <span className="text-[11px]">
                      {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "Recent"}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleStartAssessment(doc)}
                      className="flex-1 py-2 px-3 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs flex items-center justify-center gap-1.5"
                    >
                      <ClipboardCheck className="w-3.5 h-3.5" />
                      <span>Take Assessment</span>
                    </button>

                    <button
                      onClick={() => handleViewDetails(doc.id)}
                      className="py-2 px-3 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                      title="View concepts & questions preview"
                    >
                      Details
                    </button>

                    {isYt && doc.source_url ? (
                      <a
                        href={doc.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
                        title="Open YouTube video"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    ) : doc.has_file ? (
                      <a
                        href={`http://localhost:8000/api/content/library/${doc.id}/file`}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition"
                        title="Download / View File"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    ) : null}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* DETAIL MODAL */}
      <AnimatePresence>
        {selectedDoc && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto border border-slate-200 shadow-xl p-6 sm:p-7 relative"
            >
              <button
                onClick={() => setSelectedDoc(null)}
                className="absolute top-4 right-4 p-1.5 text-slate-400 hover:bg-slate-100 rounded-full transition"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-2 mb-2">
                <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-bold uppercase">
                  {selectedDoc.source_type}
                </span>
                <span className="text-xs text-slate-500">
                  {selectedDoc.competency_mapped}
                </span>
              </div>

              <h3 className="font-heading text-2xl font-bold text-slate-900 mb-3">
                {selectedDoc.title}
              </h3>

              {selectedDoc.summary && (
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mb-5">
                  <h4 className="text-xs font-bold uppercase text-slate-500 mb-1">Extracted Summary</h4>
                  <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-sans whitespace-pre-line">
                    {selectedDoc.summary}
                  </p>
                </div>
              )}

              {/* Concepts */}
              {selectedDoc.concepts && selectedDoc.concepts.length > 0 && (
                <div className="mb-5">
                  <h4 className="text-xs font-bold uppercase text-slate-500 mb-2">Identified Knowledge Concepts</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedDoc.concepts.map((c: string, i: number) => (
                      <span key={i} className="px-2.5 py-1 bg-blue-50 text-blue-800 rounded-lg text-xs font-medium border border-blue-200">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 15 Questions Preview */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold uppercase text-slate-500">
                    Generated Assessment Bank ({selectedDoc.questions?.length || 15} Questions)
                  </h4>
                  <span className="text-xs font-medium text-emerald-600">
                    70% Passing Standard
                  </span>
                </div>

                <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                  {(selectedDoc.questions || []).map((q: any, idx: number) => (
                    <div key={q.id || idx} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                      <p className="font-semibold text-slate-900 mb-1.5">
                        {idx + 1}. {q.text}
                      </p>
                      <div className="space-y-1 pl-2 border-l-2 border-slate-200">
                        {(q.options || []).map((opt: any) => (
                          <div
                            key={opt.id}
                            className={cn(
                              "text-slate-600",
                              opt.id === q.correct_answer && "text-emerald-700 font-semibold"
                            )}
                          >
                            {opt.id}. {opt.text}
                          </div>
                        ))}
                      </div>
                      {q.explanation && (
                        <p className="mt-2 text-[11px] text-slate-500 italic">
                          Rationale: {q.explanation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  onClick={() => setSelectedDoc(null)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    handleStartAssessment(selectedDoc);
                  }}
                  className="px-5 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition shadow-xs flex items-center gap-1.5"
                >
                  <ClipboardCheck className="w-3.5 h-3.5" />
                  <span>Launch 15-MCQ Assessment</span>
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* DELETE CONFIRMATION MODAL */}
      <AnimatePresence>
        {deleteConfirmId && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-xl max-w-sm w-full border border-slate-200 shadow-xl p-6 text-center"
            >
              <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-3">
                <Trash2 className="w-6 h-6" />
              </div>
              <h3 className="font-heading font-bold text-lg text-slate-900 mb-1">
                Remove from Library?
              </h3>
              <p className="text-xs text-slate-600 mb-5">
                This will delete the document, its stored file, and its 15 generated assessment questions from your library.
              </p>
              <div className="flex items-center gap-2 justify-center">
                <button
                  onClick={() => setDeleteConfirmId(null)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDelete(deleteConfirmId)}
                  className="px-4 py-2 text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white rounded-lg transition shadow-xs"
                >
                  Confirm Delete
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
