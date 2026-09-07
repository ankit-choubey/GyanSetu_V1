"use client";

import React, { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Youtube,
  FileText,
  MonitorPlay,
  FileAudio,
  Target,
  X,
  Check,
  UploadCloud,
  ChevronRight,
  Loader2,
  BookOpen,
  CheckCircle2,
  Layers,
  ClipboardCheck,
  ArrowRight,
  RotateCcw,
  Sparkles,
  Info
} from "lucide-react";
import { cn } from "@/lib/cn";

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
      "Extracting Text & Transcribing Media",
      "Segmenting into Semantic Knowledge Chunks",
      "Cross-Modal Deduplication",
      "Vector Store Indexing & 3-Tier Generation",
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
      chunks: Math.floor(Math.random() * 15) + 30,
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
      {/* SECTION 1: 4-COLUMN SYMMETRICAL MULTI-MODAL UPLOAD MATRIX */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                1
              </span>
              <h2 className="font-heading text-base font-semibold text-slate-900">
                Custom Study Materials
              </h2>
              <span className="text-[11px] text-slate-400 font-normal">
                (Upload video, notes, decks, or voice recordings)
              </span>
            </div>
          </div>

          {(youtubeUrl || Object.keys(files).length > 0) && (
            <button
              onClick={() => {
                setYoutubeUrl("");
                setFiles({});
              }}
              className="text-xs text-rose-600 hover:text-rose-700 font-medium inline-flex items-center gap-1 self-start sm:self-auto"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Clear Materials</span>
            </button>
          )}
        </div>

        {/* 4 EQUAL COLUMNS */}
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: YouTube / Video URL */}
          <div className={cn(
            "rounded-xl border p-4 flex flex-col justify-between transition-all duration-200 min-h-[160px]",
            youtubeUrl.length > 5
              ? "border-blue-300 bg-blue-50/20 ring-1 ring-blue-500/10"
              : "border-slate-200 bg-white hover:border-slate-300"
          )}>
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-rose-600 font-medium text-xs">
                  <Youtube className="w-4 h-4" />
                  <span className="text-slate-800 font-semibold">Video Lecture</span>
                </div>
                {youtubeUrl.length > 5 && (
                  <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 mb-3">YouTube URL or video resource link</p>
              
              <div className="relative">
                <input
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://youtube.com/..."
                  className="w-full text-xs py-2 px-3 pr-7 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 bg-slate-50/50"
                />
                {youtubeUrl && (
                  <button
                    onClick={() => setYoutubeUrl("")}
                    className="absolute right-2 top-2.5 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-400 flex items-center justify-between">
              <span>Auto-transcribed</span>
              {youtubeUrl.length > 5 && <span className="text-blue-600 font-medium">Link verified</span>}
            </div>
          </div>

          {/* Hidden inputs */}
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
              "rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[160px]",
              files.pdf
                ? "border-blue-300 bg-blue-50/20 ring-1 ring-blue-500/10"
                : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-blue-600 font-medium text-xs">
                  <FileText className="w-4 h-4" />
                  <span className="text-slate-800 font-semibold">PDF Document</span>
                </div>
                {files.pdf ? (
                  <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400">PDF</span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 mb-2">Lecture notes, manuals, docs</p>

              {files.pdf ? (
                <div className="bg-white border border-slate-200 rounded-lg p-2 flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium truncate max-w-[140px]">
                    {files.pdf.name}
                  </span>
                  <button
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
                <div className="border border-dashed border-slate-200 rounded-lg p-2.5 text-center text-xs text-slate-500 hover:text-slate-700">
                  Click or drag PDF here
                </div>
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-400 flex items-center justify-between">
              <span>Text & OCR Parser</span>
              {files.pdf && <span className="text-blue-600 font-medium">Ready</span>}
            </div>
          </div>

          {/* Card 3: PPTX Slides */}
          <div
            onClick={() => pptxInputRef.current?.click()}
            className={cn(
              "rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[160px]",
              files.pptx
                ? "border-blue-300 bg-blue-50/20 ring-1 ring-blue-500/10"
                : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-amber-600 font-medium text-xs">
                  <MonitorPlay className="w-4 h-4" />
                  <span className="text-slate-800 font-semibold">PPTX Slides</span>
                </div>
                {files.pptx ? (
                  <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400">PPTX</span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 mb-2">Presentation slide decks</p>

              {files.pptx ? (
                <div className="bg-white border border-slate-200 rounded-lg p-2 flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium truncate max-w-[140px]">
                    {files.pptx.name}
                  </span>
                  <button
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
                <div className="border border-dashed border-slate-200 rounded-lg p-2.5 text-center text-xs text-slate-500 hover:text-slate-700">
                  Click or drag PPTX here
                </div>
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-400 flex items-center justify-between">
              <span>Slide Deck Parser</span>
              {files.pptx && <span className="text-blue-600 font-medium">Ready</span>}
            </div>
          </div>

          {/* Card 4: Audio Lecture */}
          <div
            onClick={() => audioInputRef.current?.click()}
            className={cn(
              "rounded-xl border p-4 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[160px]",
              files.audio
                ? "border-blue-300 bg-blue-50/20 ring-1 ring-blue-500/10"
                : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-purple-600 font-medium text-xs">
                  <FileAudio className="w-4 h-4" />
                  <span className="text-slate-800 font-semibold">Audio Lecture</span>
                </div>
                {files.audio ? (
                  <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded flex items-center gap-0.5">
                    <Check className="w-2.5 h-2.5" /> Staged
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-400">MP3 / WAV</span>
                )}
              </div>
              <p className="text-[11px] text-slate-400 mb-2">Dictation & audio recordings</p>

              {files.audio ? (
                <div className="bg-white border border-slate-200 rounded-lg p-2 flex items-center justify-between">
                  <span className="text-xs text-slate-700 font-medium truncate max-w-[140px]">
                    {files.audio.name}
                  </span>
                  <button
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
                <div className="border border-dashed border-slate-200 rounded-lg p-2.5 text-center text-xs text-slate-500 hover:text-slate-700">
                  Click or drag Audio here
                </div>
              )}
            </div>

            <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-400 flex items-center justify-between">
              <span>Speech-to-Text Pipeline</span>
              {files.audio && <span className="text-blue-600 font-medium">Ready</span>}
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: TARGET CURRICULUM MODULES (FULL-WIDTH BELOW SECTION 1) */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                2
              </span>
              <h2 className="font-heading text-base font-semibold text-slate-900">
                Target Curriculum Competencies
              </h2>
              <span className="text-[11px] text-slate-400 font-normal">
                (Official curriculum modules • Click to toggle selection)
              </span>
            </div>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                className={cn(
                  "px-2.5 py-1 text-xs font-medium rounded-lg transition",
                  activeCategory === cat
                    ? "bg-blue-600 text-white shadow-xs font-semibold"
                    : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Symmetrical Grid of Modules */}
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredModules.map((module) => {
            const isSelected = selectedSubskill === module.id;
            return (
              <div
                key={module.id}
                onClick={() => setSelectedSubskill(isSelected ? null : module.id)}
                className={cn(
                  "p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col justify-between min-h-[120px] relative",
                  isSelected
                    ? "border-blue-600 ring-2 ring-blue-600/10 bg-blue-50/30 shadow-xs"
                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/40"
                )}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                      {module.comp}
                    </span>
                    <div className={cn(
                      "w-4 h-4 rounded-full flex items-center justify-center border transition-colors",
                      isSelected ? "bg-blue-600 border-blue-600 text-white" : "border-slate-300 bg-white"
                    )}>
                      {isSelected && <Check className="w-2.5 h-2.5" />}
                    </div>
                  </div>
                  <h3 className="text-xs font-semibold text-slate-900 leading-snug">
                    {module.name}
                  </h3>
                </div>

                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                  <span>{module.subskillsCount} Subskills</span>
                  <span className={cn(
                    "font-medium",
                    module.difficulty === "Advanced" ? "text-purple-600" :
                    module.difficulty === "Intermediate" ? "text-amber-600" : "text-emerald-600"
                  )}>
                    {module.difficulty}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* SECTION 3: CALIBRATION & INGESTION ACTION BAR (PERSISTENT AT BOTTOM) */}
      <div className={cn(
        "rounded-xl border shadow-xs p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all duration-300",
        isIngested ? "bg-emerald-50/40 border-emerald-200" : "bg-white border-slate-200"
      )}>
        {/* Left Side Status */}
        <div className="flex items-center gap-3">
          {isIngested ? (
            <div className="w-10 h-10 rounded-xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0">
              <Layers className="w-5 h-5" />
            </div>
          )}

          <div>
            {isIngested ? (
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-900">
                    Ingestion & Knowledge Graph Calibrated
                  </span>
                  <span className="font-mono text-[11px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                    {ingestedSessionId}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {ingestedSummary?.chunks} concept nodes indexed • 3 Assessment Tiers Ready (Easy, Medium, Tough)
                </p>
              </div>
            ) : (
              <div>
                <div className="text-xs font-semibold text-slate-800">
                  {stagedSourcesCount > 0
                    ? `${stagedSourcesCount} source(s) staged for synthesis`
                    : "No materials or modules selected"}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {stagedSourcesCount > 0
                    ? "Ready to extract semantics and calibrate 3-tier adaptive assessment"
                    : "Select at least one source above or a curriculum module to begin"}
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
                className="px-4 py-2.5 text-xs font-medium text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition shadow-xs flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
                <span>Ingest New Data</span>
              </button>
              <button
                type="button"
                id="start-assessment-btn"
                onClick={() => router.push(`/dashboard/assessments?session_id=${ingestedSessionId}`)}
                className="px-6 py-2.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-sm transition flex items-center gap-2"
              >
                <ClipboardCheck className="w-4 h-4" />
                <span>Start Assessment</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!hasInputs || isProcessing}
              className={cn(
                "px-6 py-2.5 rounded-lg text-xs font-semibold text-white shadow-xs transition flex items-center gap-2",
                !hasInputs
                  ? "bg-slate-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 hover:shadow-sm"
              )}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Knowledge Engine...</span>
                </>
              ) : (
                <>
                  <span>Ingest & Process Data</span>
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
            className="fixed inset-0 z-[100] bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200"
            >
              <h3 className="font-heading text-lg text-slate-900 mb-5 text-center">
                Processing Knowledge Engine
              </h3>
              <div className="space-y-3.5">
                {[
                  "Extracting Text & Transcribing Media",
                  "Segmenting into Semantic Knowledge Chunks",
                  "Cross-Modal Deduplication",
                  "Vector Store Indexing & 3-Tier Generation",
                ].map((step, idx) => {
                  const isActive = currentStep === idx;
                  const isDone = currentStep > idx;
                  return (
                    <div key={idx} className="flex items-center gap-3">
                      <div
                        className={cn(
                          "w-6 h-6 shrink-0 rounded-full flex items-center justify-center border",
                          isDone
                            ? "bg-emerald-50 border-emerald-200 text-emerald-600"
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
                          "text-xs font-medium transition-colors",
                          isDone
                            ? "text-slate-700"
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
