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
  Library,
  Upload
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
    <div className="space-y-8 w-full">
      {/* ========================================================================= */}
      {/* SECTION 1: 4-COLUMN SYMMETRICAL MULTI-MODAL UPLOADER STUDIO */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        {/* Section 1 Header */}
        <div className="p-6 border-b border-slate-100 bg-slate-50/70 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-xl bg-blue-600 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                1
              </span>
              <h2 className="font-heading text-lg font-bold text-slate-900 tracking-tight">
                Upload Custom Study Materials
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 pl-9">
              Stage video lectures, training manuals, presentation slides, or audio recordings for automated knowledge extraction.
            </p>
          </div>

          {(youtubeUrl || Object.keys(files).length > 0) && (
            <button
              onClick={() => {
                setYoutubeUrl("");
                setFiles({});
              }}
              className="text-xs text-rose-600 hover:text-rose-700 font-semibold inline-flex items-center gap-1.5 self-start sm:self-auto px-3 py-1.5 rounded-lg bg-rose-50 border border-rose-100 transition"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear Uploaded Materials</span>
            </button>
          )}
        </div>

        {/* 4 Equal, Vibrant Dropzone Cards */}
        <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {/* Card 1: Video / YouTube (Rose Accent) */}
          <div className={cn(
            "rounded-2xl border-2 p-5 flex flex-col justify-between transition-all duration-200 min-h-[220px]",
            youtubeUrl.length > 5
              ? "border-rose-400 bg-rose-50/30 ring-2 ring-rose-500/10 shadow-xs"
              : "border-slate-200 bg-gradient-to-b from-rose-50/30 via-white to-white hover:border-rose-300 hover:shadow-xs"
          )}>
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center shadow-xs">
                    <Youtube className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Video Lecture</h3>
                    <span className="text-[11px] text-slate-500 font-medium">YouTube / MP4</span>
                  </div>
                </div>

                {youtubeUrl.length > 5 && (
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200">
                    <Check className="w-3 h-3" /> Staged
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                Paste link to an educational lecture or webinar recording
              </p>

              <div className="relative">
                <input
                  type="url"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..."
                  className="w-full text-xs py-2.5 px-3.5 pr-8 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-rose-500/20 focus:border-rose-400 bg-white shadow-2xs font-medium placeholder:text-slate-400"
                />
                {youtubeUrl && (
                  <button
                    onClick={() => setYoutubeUrl("")}
                    className="absolute right-2.5 top-3 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 flex items-center justify-between">
              <span>Transcribed & Indexed</span>
              {youtubeUrl.length > 5 ? (
                <span className="text-emerald-600 font-semibold">Active</span>
              ) : (
                <span className="text-slate-400">Optional</span>
              )}
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

          {/* Card 2: PDF Document (Blue Accent) */}
          <div
            onClick={() => pdfInputRef.current?.click()}
            className={cn(
              "rounded-2xl border-2 p-5 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[220px]",
              files.pdf
                ? "border-blue-400 bg-blue-50/30 ring-2 ring-blue-500/10 shadow-xs"
                : "border-slate-200 bg-gradient-to-b from-blue-50/30 via-white to-white hover:border-blue-300 hover:shadow-xs"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center shadow-xs">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">PDF Document</h3>
                    <span className="text-[11px] text-slate-500 font-medium">Text & Manuals</span>
                  </div>
                </div>

                {files.pdf ? (
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200">
                    <Check className="w-3 h-3" /> Staged
                  </span>
                ) : (
                  <span className="text-xs font-medium text-slate-400">PDF</span>
                )}
              </div>

              <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                Upload survey guides, notes, or official ministry circulars
              </p>

              {files.pdf ? (
                <div className="bg-white border border-blue-200 rounded-xl p-3 flex items-center justify-between shadow-2xs">
                  <span className="text-xs text-slate-800 font-semibold truncate max-w-[150px]">
                    {files.pdf.name}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile("pdf");
                    }}
                    className="text-slate-400 hover:text-rose-600 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-3.5 text-center text-xs font-medium text-slate-600 hover:text-blue-600 hover:border-blue-300 bg-slate-50/60 transition flex items-center justify-center gap-2">
                  <Upload className="w-4 h-4 text-slate-400" />
                  <span>Click or drop PDF</span>
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 flex items-center justify-between">
              <span>Text & OCR Parser</span>
              {files.pdf ? (
                <span className="text-emerald-600 font-semibold">Active</span>
              ) : (
                <span className="text-slate-400">Optional</span>
              )}
            </div>
          </div>

          {/* Card 3: PPTX Slides (Amber Accent) */}
          <div
            onClick={() => pptxInputRef.current?.click()}
            className={cn(
              "rounded-2xl border-2 p-5 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[220px]",
              files.pptx
                ? "border-amber-400 bg-amber-50/30 ring-2 ring-amber-500/10 shadow-xs"
                : "border-slate-200 bg-gradient-to-b from-amber-50/30 via-white to-white hover:border-amber-300 hover:shadow-xs"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center shadow-xs">
                    <MonitorPlay className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">PPTX Slides</h3>
                    <span className="text-[11px] text-slate-500 font-medium">Decks & Pitch</span>
                  </div>
                </div>

                {files.pptx ? (
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200">
                    <Check className="w-3 h-3" /> Staged
                  </span>
                ) : (
                  <span className="text-xs font-medium text-slate-400">PPTX</span>
                )}
              </div>

              <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                Upload training workshop presentation slides or summaries
              </p>

              {files.pptx ? (
                <div className="bg-white border border-amber-200 rounded-xl p-3 flex items-center justify-between shadow-2xs">
                  <span className="text-xs text-slate-800 font-semibold truncate max-w-[150px]">
                    {files.pptx.name}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile("pptx");
                    }}
                    className="text-slate-400 hover:text-rose-600 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-3.5 text-center text-xs font-medium text-slate-600 hover:text-amber-600 hover:border-amber-300 bg-slate-50/60 transition flex items-center justify-center gap-2">
                  <Upload className="w-4 h-4 text-slate-400" />
                  <span>Click or drop PPTX</span>
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 flex items-center justify-between">
              <span>Deck & Outline Parser</span>
              {files.pptx ? (
                <span className="text-emerald-600 font-semibold">Active</span>
              ) : (
                <span className="text-slate-400">Optional</span>
              )}
            </div>
          </div>

          {/* Card 4: Audio Lecture (Purple Accent) */}
          <div
            onClick={() => audioInputRef.current?.click()}
            className={cn(
              "rounded-2xl border-2 p-5 flex flex-col justify-between cursor-pointer transition-all duration-200 min-h-[220px]",
              files.audio
                ? "border-purple-400 bg-purple-50/30 ring-2 ring-purple-500/10 shadow-xs"
                : "border-slate-200 bg-gradient-to-b from-purple-50/30 via-white to-white hover:border-purple-300 hover:shadow-xs"
            )}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center shadow-xs">
                    <FileAudio className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-900">Audio Lecture</h3>
                    <span className="text-[11px] text-slate-500 font-medium">MP3 / WAV</span>
                  </div>
                </div>

                {files.audio ? (
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200">
                    <Check className="w-3 h-3" /> Staged
                  </span>
                ) : (
                  <span className="text-xs font-medium text-slate-400">Audio</span>
                )}
              </div>

              <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                Upload voice notes, audio lectures, or panel discussions
              </p>

              {files.audio ? (
                <div className="bg-white border border-purple-200 rounded-xl p-3 flex items-center justify-between shadow-2xs">
                  <span className="text-xs text-slate-800 font-semibold truncate max-w-[150px]">
                    {files.audio.name}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile("audio");
                    }}
                    className="text-slate-400 hover:text-rose-600 p-1"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-3.5 text-center text-xs font-medium text-slate-600 hover:text-purple-600 hover:border-purple-300 bg-slate-50/60 transition flex items-center justify-center gap-2">
                  <Upload className="w-4 h-4 text-slate-400" />
                  <span>Click or drop Audio</span>
                </div>
              )}
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 flex items-center justify-between">
              <span>Speech-to-Text Pipeline</span>
              {files.audio ? (
                <span className="text-emerald-600 font-semibold">Active</span>
              ) : (
                <span className="text-slate-400">Optional</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 2: CURATED CURRICULUM COMPETENCY CATALOG (DIFFERENT VISUAL STYLE) */}
      {/* ========================================================================= */}
      <div className="bg-white rounded-2xl border border-slate-200/90 shadow-xs overflow-hidden">
        {/* Section 2 Header */}
        <div className="p-6 border-b border-slate-100 bg-slate-50/70 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                2
              </span>
              <h2 className="font-heading text-lg font-bold text-slate-900 tracking-tight">
                Curriculum Competencies Catalog
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 pl-9">
              Select verified competencies from the official statistical training syllabus to test directly or combine with uploaded media.
            </p>
          </div>

          {/* Distinct Category Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap self-start md:self-center pl-9 md:pl-0">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                className={cn(
                  "px-3.5 py-1.5 text-xs font-semibold rounded-xl transition-all duration-150",
                  activeCategory === cat
                    ? "bg-slate-900 text-white shadow-xs font-bold"
                    : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
                )}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Distinct Catalog Cards: Distinct Left Border & Structured Metadata */}
        <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredModules.map((module) => {
            const isSelected = selectedSubskill === module.id;
            
            // Distinct left border color based on competency
            const leftBorderColor = 
              module.category === "Probability" ? "border-l-indigo-600" :
              module.category === "Sampling Design" ? "border-l-blue-600" :
              "border-l-teal-600";

            return (
              <div
                key={module.id}
                onClick={() => setSelectedSubskill(isSelected ? null : module.id)}
                className={cn(
                  "p-5 rounded-xl border border-l-4 cursor-pointer transition-all duration-200 flex flex-col justify-between min-h-[140px] relative bg-white",
                  leftBorderColor,
                  isSelected
                    ? "border-blue-600 ring-2 ring-blue-600/15 bg-blue-50/30 shadow-xs"
                    : "border-slate-200 hover:border-slate-300 hover:shadow-xs hover:-translate-y-0.5"
                )}
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2.5">
                    <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200/80">
                      {module.comp}
                    </span>
                    <div className={cn(
                      "w-5 h-5 rounded-full flex items-center justify-center border transition-all shrink-0",
                      isSelected ? "bg-blue-600 border-blue-600 text-white shadow-2xs" : "border-slate-300 bg-white"
                    )}>
                      {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                    </div>
                  </div>
                  
                  <h3 className="text-sm font-bold text-slate-900 leading-snug">
                    {module.name}
                  </h3>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                  <span className="font-medium">{module.subskillsCount} Subskills</span>
                  <span className={cn(
                    "font-semibold px-2 py-0.5 rounded",
                    module.difficulty === "Advanced" ? "bg-purple-50 text-purple-700 border border-purple-100" :
                    module.difficulty === "Intermediate" ? "bg-amber-50 text-amber-700 border border-amber-100" : 
                    "bg-emerald-50 text-emerald-700 border border-emerald-100"
                  )}>
                    {module.difficulty}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 3: CALIBRATION & INGESTION ACTION BAR (PERSISTENT AT BOTTOM) */}
      {/* ========================================================================= */}
      <div className={cn(
        "rounded-2xl border-2 shadow-xs p-6 flex flex-col md:flex-row md:items-center justify-between gap-5 transition-all duration-300",
        isIngested ? "bg-emerald-50/50 border-emerald-300" : "bg-white border-slate-200"
      )}>
        {/* Left Side Status */}
        <div className="flex items-center gap-4">
          {isIngested ? (
            <div className="w-12 h-12 rounded-2xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0 shadow-xs">
              <CheckCircle2 className="w-6 h-6" />
            </div>
          ) : (
            <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0 shadow-xs">
              <Layers className="w-6 h-6" />
            </div>
          )}

          <div>
            {isIngested ? (
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-bold text-slate-900">
                    Ingestion & Calibration Complete:
                  </span>
                  <span className="font-mono text-xs bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-lg font-bold border border-emerald-200">
                    {ingestedSessionId}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1">
                  {ingestedSummary?.chunks} semantic knowledge nodes indexed • 3 Assessment Tiers Ready (Easy, Medium, Tough)
                </p>
              </div>
            ) : (
              <div>
                <div className="text-sm font-bold text-slate-800">
                  {stagedSourcesCount > 0
                    ? `${stagedSourcesCount} source(s) staged for synthesis`
                    : "No materials or modules selected"}
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {stagedSourcesCount > 0
                    ? "Ready to extract semantics and calibrate 3-tier adaptive assessment"
                    : "Select at least one custom material above or a curriculum module to begin"}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-3 shrink-0">
          {isIngested ? (
            <>
              <button
                type="button"
                onClick={handleReset}
                className="px-5 py-2.5 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition shadow-xs flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4 text-slate-400" />
                <span>Reset & Ingest New</span>
              </button>
              <button
                type="button"
                id="start-assessment-btn"
                onClick={() => router.push(`/dashboard/assessments?session_id=${ingestedSessionId}`)}
                className="px-7 py-3 text-sm font-bold bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm transition flex items-center gap-2.5"
              >
                <ClipboardCheck className="w-5 h-5" />
                <span>Start Assessment</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!hasInputs || isProcessing}
              className={cn(
                "px-7 py-3 rounded-xl text-sm font-bold text-white shadow-xs transition flex items-center gap-2.5",
                !hasInputs
                  ? "bg-slate-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 hover:shadow-sm"
              )}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing Knowledge Engine...</span>
                </>
              ) : (
                <>
                  <span>Ingest & Process Data</span>
                  <ChevronRight className="w-4 h-4" />
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
              className="bg-white rounded-2xl shadow-xl max-w-md w-full p-7 border border-slate-200"
            >
              <h3 className="font-heading text-xl font-bold text-slate-900 mb-6 text-center">
                Processing Knowledge Engine
              </h3>
              <div className="space-y-4">
                {[
                  "Extracting Text & Transcribing Media",
                  "Segmenting into Semantic Knowledge Chunks",
                  "Cross-Modal Deduplication",
                  "Vector Store Indexing & 3-Tier Generation",
                ].map((step, idx) => {
                  const isActive = currentStep === idx;
                  const isDone = currentStep > idx;
                  return (
                    <div key={idx} className="flex items-center gap-3.5">
                      <div
                        className={cn(
                          "w-7 h-7 shrink-0 rounded-full flex items-center justify-center border transition-all",
                          isDone
                            ? "bg-emerald-50 border-emerald-200 text-emerald-600"
                            : isActive
                            ? "bg-blue-50 border-blue-200 text-blue-600"
                            : "bg-slate-50 border-slate-200 text-slate-400"
                        )}
                      >
                        {isDone ? (
                          <Check className="w-4 h-4" />
                        ) : isActive ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <span className="text-xs font-semibold">{idx + 1}</span>
                        )}
                      </div>
                      <span
                        className={cn(
                          "text-sm font-semibold transition-colors",
                          isDone
                            ? "text-slate-700"
                            : isActive
                            ? "text-blue-700 font-bold"
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
