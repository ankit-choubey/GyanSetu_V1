"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Youtube,
  FileText,
  MonitorPlay,
  FileAudio,
  X,
  Check,
  ChevronRight,
  Loader2,
  CheckCircle2,
  Layers,
  ClipboardCheck,
  ArrowRight,
  RotateCcw,
  Upload
} from "lucide-react";
import { cn } from "@/lib/cn";
import { StatusChip, IconTile, SectionHeader } from "@/components/ui/dashboard/primitives";

interface SubskillModule {
  id: string;
  name: string;
  comp: string;
  category: "Probability" | "Sampling Design" | "National Accounts";
  subskillsCount: number;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
}

const MOCK_MODULES: SubskillModule[] = [
  {
    id: "sub_prob_01",
    name: "Bayes' Theorem & Conditional Probability",
    comp: "Probability",
    category: "Probability",
    subskillsCount: 4,
    difficulty: "Intermediate",
  },
  {
    id: "sub_samp_01",
    name: "Simple Random Sampling (SRSWR & SRSWOR)",
    comp: "Sampling Design",
    category: "Sampling Design",
    subskillsCount: 5,
    difficulty: "Beginner",
  },
  {
    id: "sub_samp_02",
    name: "Stratified Random Sampling & Neyman Allocation",
    comp: "Sampling Design",
    category: "Sampling Design",
    subskillsCount: 6,
    difficulty: "Advanced",
  },
  {
    id: "sub_macro_01",
    name: "GDP Compilation (Production, Income, Expenditure)",
    comp: "National Accounts",
    category: "National Accounts",
    subskillsCount: 4,
    difficulty: "Intermediate",
  },
  {
    id: "sub_prob_06",
    name: "Law of Large Numbers (Weak & Strong)",
    comp: "Probability",
    category: "Probability",
    subskillsCount: 3,
    difficulty: "Intermediate",
  },
  {
    id: "sub_macro_02",
    name: "Gross Value Added (GVA) & Deflator Mechanics",
    comp: "National Accounts",
    category: "National Accounts",
    subskillsCount: 4,
    difficulty: "Advanced",
  },
];

const CATEGORIES = ["All", "Probability", "Sampling Design", "National Accounts"] as const;

export function IngestionHub() {
  const router = useRouter();

  // Inputs state
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [files, setFiles] = useState<{ pdf?: File; pptx?: File; audio?: File }>({});
  const [selectedSubskill, setSelectedSubskill] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<string>("All");

  // Processing & Ingested State
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isIngested, setIsIngested] = useState(false);
  const [ingestedSessionId, setIngestedSessionId] = useState<string | null>(null);
  const [ingestedSummary, setIngestedSummary] = useState<{
    sourcesCount: number;
    chunks: number;
    moduleName?: string;
  } | null>(null);

  // Hidden file input refs
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const pptxInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handleFileDrop = (type: "pdf" | "pptx" | "audio", file: File) => {
    setFiles((prev) => ({ ...prev, [type]: file }));
  };

  const removeFile = (type: "pdf" | "pptx" | "audio") => {
    setFiles((prev) => {
      const copy = { ...prev };
      delete copy[type];
      return copy;
    });
  };

  const stagedSourcesCount =
    (youtubeUrl.trim().length > 5 ? 1 : 0) +
    Object.keys(files).length +
    (selectedSubskill ? 1 : 0);

  const hasInputs = stagedSourcesCount > 0;

  const handleSubmit = async () => {
    if (!hasInputs) return;

    setIsProcessing(true);

    const steps = [
      "Extracting text & transcribing",
      "Segmenting content",
      "Removing duplicates",
      "Indexing & building questions",
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(i);
      await new Promise((resolve) =>
        setTimeout(resolve, selectedSubskill && Object.keys(files).length === 0 ? 300 : 700)
      );
    }

    const sessionId = "sess_" + Math.random().toString(36).substring(7);
    localStorage.setItem("active_session_id", sessionId);

    const activeModule = selectedSubskill ? MOCK_MODULES.find((m) => m.id === selectedSubskill) : null;

    setIngestedSummary({
      sourcesCount: stagedSourcesCount,
      chunks: Math.floor(Math.random() * 15) + 32,
      moduleName: activeModule?.name,
    });
    setIngestedSessionId(sessionId);
    setIsProcessing(false);
    setIsIngested(true);
  };

  const handleReset = () => {
    setIsIngested(false);
    setIngestedSessionId(null);
    setIngestedSummary(null);
    setYoutubeUrl("");
    setFiles({});
    setSelectedSubskill(null);
  };

  const filteredModules =
    activeCategory === "All"
      ? MOCK_MODULES
      : MOCK_MODULES.filter((m) => m.category === activeCategory);

  return (
    <div className="space-y-6 w-full">
      {/* ========================================================================= */}
      {/* SECTION 1: 4-COLUMN NEUTRAL MULTI-MODAL UPLOADER STUDIO */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Section 1 Header */}
        <div className="p-5 border-b border-slate-100 bg-slate-50/50">
          <SectionHeader
            eyebrow="Step 1"
            title="Upload materials"
            subtitle="Stage video lectures, training manuals, presentation slides, or audio recordings."
            action={
              (youtubeUrl || Object.keys(files).length > 0) ? (
                <button
                  type="button"
                  onClick={() => {
                    setYoutubeUrl("");
                    setFiles({});
                  }}
                  className="text-xs text-rose-600 hover:text-rose-700 font-medium inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg hover:bg-rose-50 transition"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>Clear materials</span>
                </button>
              ) : undefined
            }
          />
        </div>

        {/* 4 Equal, Neutral Dropzone Cards */}
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Video / YouTube */}
          <div className={cn(
            "rounded-xl border p-4 flex flex-col justify-between transition-all duration-200 min-h-[176px]",
            youtubeUrl.length > 5
              ? "border-blue-300 ring-1 ring-blue-500/15 bg-blue-50/20"
              : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs"
          )}>
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <IconTile icon={Youtube} />
                  <h3 className="text-xs font-semibold text-slate-900">Video lecture</h3>
                </div>

                {youtubeUrl.length > 5 ? (
                  <StatusChip status="high" size="sm">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </StatusChip>
                ) : (
                  <span className="text-[11px] text-slate-400 font-sans">URL</span>
                )}
              </div>

              <p className="text-xs text-slate-500 mb-3 font-sans">
                Paste link to lecture or webinar recording
              </p>

              <div className="relative">
                <input
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://youtube.com/..."
                  className="w-full text-xs py-2 px-3 pr-7 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                />
                {youtubeUrl && (
                  <button
                    type="button"
                    onClick={() => setYoutubeUrl("")}
                    className="absolute right-2 top-2.5 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between font-sans">
              <span>Automatic transcription</span>
              {youtubeUrl.length > 5 && <span className="text-teal-600 font-medium">Ready</span>}
            </div>
          </div>

          {/* Hidden native inputs */}
          <input
            type="file"
            ref={pdfInputRef}
            accept=".pdf"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileDrop("pdf", e.target.files[0])}
          />
          <input
            type="file"
            ref={pptxInputRef}
            accept=".pptx,.ppt"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileDrop("pptx", e.target.files[0])}
          />
          <input
            type="file"
            ref={audioInputRef}
            accept="audio/*,video/*"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileDrop("audio", e.target.files[0])}
          />

          {/* Card 2: PDF Document */}
          <div
            onClick={() => pdfInputRef.current?.click()}
            className={cn(
              "rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[176px]",
              files.pdf
                ? "border-blue-300 ring-1 ring-blue-500/15 bg-blue-50/20"
                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <IconTile icon={FileText} />
                  <h3 className="text-xs font-semibold text-slate-900">PDF document</h3>
                </div>

                {files.pdf ? (
                  <StatusChip status="high" size="sm">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </StatusChip>
                ) : (
                  <span className="text-[11px] text-slate-400 font-sans">PDF</span>
                )}
              </div>

              <p className="text-xs text-slate-500 mb-3 font-sans">
                Upload survey guides, notes, or manuals
              </p>

              {files.pdf ? (
                <div className="bg-white border border-slate-200 rounded-lg p-2.5 flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium truncate max-w-[140px]">
                    {files.pdf.name}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile("pdf");
                    }}
                    className="text-slate-400 hover:text-rose-600 p-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <div className="border border-dashed border-slate-200 rounded-lg p-2.5 text-center text-xs text-slate-500 hover:border-slate-300 hover:bg-slate-50/50 transition flex items-center justify-center gap-1.5">
                  <Upload className="w-3.5 h-3.5 text-slate-400" />
                  <span>Choose PDF file</span>
                </div>
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between font-sans">
              <span>Text parser</span>
              {files.pdf && <span className="text-teal-600 font-medium">Ready</span>}
            </div>
          </div>

          {/* Card 3: PPTX Slides */}
          <div
            onClick={() => pptxInputRef.current?.click()}
            className={cn(
              "rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[176px]",
              files.pptx
                ? "border-blue-300 ring-1 ring-blue-500/15 bg-blue-50/20"
                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <IconTile icon={MonitorPlay} />
                  <h3 className="text-xs font-semibold text-slate-900">PPTX slides</h3>
                </div>

                {files.pptx ? (
                  <StatusChip status="high" size="sm">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </StatusChip>
                ) : (
                  <span className="text-[11px] text-slate-400 font-sans">PPTX</span>
                )}
              </div>

              <p className="text-xs text-slate-500 mb-3 font-sans">
                Upload workshop slide decks or outlines
              </p>

              {files.pptx ? (
                <div className="bg-white border border-slate-200 rounded-lg p-2.5 flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium truncate max-w-[140px]">
                    {files.pptx.name}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile("pptx");
                    }}
                    className="text-slate-400 hover:text-rose-600 p-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <div className="border border-dashed border-slate-200 rounded-lg p-2.5 text-center text-xs text-slate-500 hover:border-slate-300 hover:bg-slate-50/50 transition flex items-center justify-center gap-1.5">
                  <Upload className="w-3.5 h-3.5 text-slate-400" />
                  <span>Choose PPTX file</span>
                </div>
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between font-sans">
              <span>Deck parser</span>
              {files.pptx && <span className="text-teal-600 font-medium">Ready</span>}
            </div>
          </div>

          {/* Card 4: Audio Lecture */}
          <div
            onClick={() => audioInputRef.current?.click()}
            className={cn(
              "rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[176px]",
              files.audio
                ? "border-blue-300 ring-1 ring-blue-500/15 bg-blue-50/20"
                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-xs"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <IconTile icon={FileAudio} />
                  <h3 className="text-xs font-semibold text-slate-900">Audio lecture</h3>
                </div>

                {files.audio ? (
                  <StatusChip status="high" size="sm">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </StatusChip>
                ) : (
                  <span className="text-[11px] text-slate-400 font-sans">MP3</span>
                )}
              </div>

              <p className="text-xs text-slate-500 mb-3 font-sans">
                Upload voice notes or audio lectures
              </p>

              {files.audio ? (
                <div className="bg-white border border-slate-200 rounded-lg p-2.5 flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium truncate max-w-[140px]">
                    {files.audio.name}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile("audio");
                    }}
                    className="text-slate-400 hover:text-rose-600 p-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ) : (
                <div className="border border-dashed border-slate-200 rounded-lg p-2.5 text-center text-xs text-slate-500 hover:border-slate-300 hover:bg-slate-50/50 transition flex items-center justify-center gap-1.5">
                  <Upload className="w-3.5 h-3.5 text-slate-400" />
                  <span>Choose audio file</span>
                </div>
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-xs text-slate-400 flex items-center justify-between font-sans">
              <span>Speech transcription</span>
              {files.audio && <span className="text-teal-600 font-medium">Ready</span>}
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 2: CURRICULUM COMPETENCIES CATALOG */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Section 2 Header */}
        <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <SectionHeader
            eyebrow="Step 2"
            title="Curriculum modules"
            subtitle="Select verified competencies from the official training syllabus."
          />

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                className={cn(
                  "px-3 py-1 text-xs rounded-lg transition-colors font-medium",
                  activeCategory === cat
                    ? "bg-slate-900 text-white font-semibold shadow-xs"
                    : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Clean Neutral Catalog Cards */}
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredModules.map((module) => {
            const isSelected = selectedSubskill === module.id;

            return (
              <div
                key={module.id}
                onClick={() => setSelectedSubskill(isSelected ? null : module.id)}
                className={cn(
                  "p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col justify-between min-h-[120px] bg-white",
                  isSelected
                    ? "border-blue-600 ring-1 ring-blue-500/20 bg-blue-50/20 shadow-xs"
                    : "border-slate-200 hover:border-slate-300 hover:shadow-xs"
                )}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
                      {module.comp}
                    </span>
                    <div className={cn(
                      "w-4 h-4 rounded-full flex items-center justify-center border transition-all shrink-0",
                      isSelected ? "bg-blue-600 border-blue-600 text-white" : "border-slate-300 bg-white"
                    )}>
                      {isSelected && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                    </div>
                  </div>
                  
                  <h3 className="text-xs font-semibold text-slate-900 leading-snug">
                    {module.name}
                  </h3>
                </div>

                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-sans">
                  <span>{module.subskillsCount} subskills</span>
                  <StatusChip
                    status={
                      module.difficulty === "Advanced" ? "low" :
                      module.difficulty === "Intermediate" ? "med" : "high"
                    }
                    size="sm"
                  >
                    {module.difficulty}
                  </StatusChip>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 3: CALIBRATION & INGESTION ACTION BAR */}
      {/* ========================================================================= */}
      <div className={cn(
        "rounded-xl border shadow-sm p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-200",
        isIngested ? "bg-teal-50/30 border-teal-200" : "bg-white border-slate-200"
      )}>
        {/* Left Side Status */}
        <div className="flex items-center gap-3">
          {isIngested ? (
            <div className="w-9 h-9 rounded-lg bg-teal-100 border border-teal-200 flex items-center justify-center text-teal-700 shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-9 h-9 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center shrink-0">
              <Layers className="w-4 h-4" />
            </div>
          )}

          <div>
            {isIngested ? (
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs font-semibold text-slate-900">
                    Processing complete:
                  </span>
                  <span className="font-mono text-xs bg-white text-slate-700 px-2 py-0.5 rounded border border-slate-200">
                    {ingestedSessionId}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 font-sans">
                  {ingestedSummary?.chunks} content chunks indexed • 3 levels ready
                </p>
              </div>
            ) : (
              <div>
                <div className="text-xs font-semibold text-slate-800">
                  {stagedSourcesCount > 0
                    ? `${stagedSourcesCount} source(s) staged`
                    : "No materials selected"}
                </div>
                <p className="text-xs text-slate-500 mt-0.5 font-sans">
                  {stagedSourcesCount > 0
                    ? "Ready to build your assessment"
                    : "Select study materials or a curriculum module to proceed"}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-2.5 shrink-0">
          {isIngested ? (
            <>
              <button
                type="button"
                onClick={handleReset}
                className="px-3.5 py-2 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg transition"
              >
                Reset / Ingest new
              </button>
              <button
                type="button"
                id="start-assessment-btn"
                onClick={() => router.push(`/dashboard/assessments?session_id=${ingestedSessionId}`)}
                className="px-5 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition flex items-center gap-2"
              >
                <ClipboardCheck className="w-4 h-4" />
                <span>Start assessment</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!hasInputs || isProcessing}
              className={cn(
                "px-5 py-2 rounded-lg text-xs font-semibold text-white shadow-xs transition flex items-center gap-2",
                !hasInputs
                  ? "bg-slate-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              )}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing…</span>
                </>
              ) : (
                <>
                  <span>Process materials</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* FULLSCREEN PROCESSING STEPPER OVERLAY */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white rounded-xl shadow-lg max-w-md w-full p-6 border border-slate-200"
            >
              <h3 className="font-heading text-lg text-slate-900 mb-5 text-center">
                Processing…
              </h3>
              <div className="space-y-3.5 font-sans">
                {[
                  "Extracting text & transcribing",
                  "Segmenting content",
                  "Removing duplicates",
                  "Indexing & building questions",
                ].map((step, idx) => {
                  const isActive = currentStep === idx;
                  const isDone = currentStep > idx;
                  return (
                    <div key={idx} className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-6 h-6 shrink-0 rounded-full flex items-center justify-center border transition-all",
                          isDone
                            ? "bg-teal-50 border-teal-200 text-teal-600"
                            : isActive
                            ? "bg-blue-50 border-blue-200 text-blue-600"
                            : "bg-slate-50 border-slate-200 text-slate-400"
                        )}
                      >
                        {isDone ? (
                          <Check className="w-3.5 h-3.5" />
                        ) : isActive ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <span className="text-[10px] font-medium">{idx + 1}</span>
                        )}
                      </div>
                      <span
                        className={cn(
                          "text-xs transition-colors",
                          isDone
                            ? "text-slate-700 font-medium"
                            : isActive
                            ? "text-blue-700 font-semibold"
                            : "text-slate-400"
                        )}
                      >
                        {step}
                      </span>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
