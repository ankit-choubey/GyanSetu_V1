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
  RotateCcw
} from "lucide-react";
import { cn } from "@/lib/cn";

// Mock subskill catalog based on official curriculum
const MOCK_SUBSKILLS = [
  { id: "sub_prob_01", name: "Bayes' Theorem & Conditional Probability", comp: "Probability" },
  { id: "sub_prob_06", name: "Law of Large Numbers (Weak & Strong)", comp: "Probability" },
  { id: "sub_samp_01", name: "Simple Random Sampling (SRSWR & SRSWOR)", comp: "Sampling" },
  { id: "sub_samp_02", name: "Stratified Random Sampling & Neyman Allocation", comp: "Sampling" },
  { id: "sub_macro_01", name: "GDP Compilation (Production, Income, Expenditure)", comp: "Macroeconomics" },
];

export function IngestionHub() {
  const router = useRouter();
  
  // State for form fields
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [files, setFiles] = useState<{ pdf?: File; pptx?: File; audio?: File }>({});
  const [selectedSubskill, setSelectedSubskill] = useState<string | null>(null);
  
  // State for UI interaction
  const [isSubskillsOpen, setIsSubskillsOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0-3 for stepper

  // Post-ingestion state
  const [isIngested, setIsIngested] = useState(false);
  const [ingestedSessionId, setIngestedSessionId] = useState<string | null>(null);
  const [ingestedSummary, setIngestedSummary] = useState<{
    sources: string[];
    chunks: number;
    subskillName?: string;
  } | null>(null);

  // Refs for hidden file inputs
  const pdfInputRef = useRef<HTMLInputElement>(null);
  const pptxInputRef = useRef<HTMLInputElement>(null);
  const audioInputRef = useRef<HTMLInputElement>(null);

  const handleFileDrop = (type: "pdf" | "pptx" | "audio", file: File) => {
    setFiles((prev) => ({ ...prev, [type]: file }));
  };

  const removeFile = (type: "pdf" | "pptx" | "audio") => {
    setFiles((prev) => {
      const newFiles = { ...prev };
      delete newFiles[type];
      return newFiles;
    });
  };

  const hasInputs = youtubeUrl.length > 5 || Object.keys(files).length > 0 || selectedSubskill !== null;

  const handleSubmit = async () => {
    if (!hasInputs) return;
    
    setIsProcessing(true);
    
    // Simulate the 4-step ingestion process
    const steps = [
      "Extracting Text & Transcribing Media",
      "Segmenting into Semantic Knowledge Chunks",
      "Cross-Modal Deduplication",
      "Vector Store Indexing & 3-Tier Generation"
    ];

    for (let i = 0; i < steps.length; i++) {
      setCurrentStep(i);
      await new Promise(resolve => setTimeout(resolve, selectedSubskill && Object.keys(files).length === 0 ? 300 : 700));
    }

    // Done! Set session in localStorage and store ingested details
    const sessionId = "sess_" + Math.random().toString(36).substring(7);
    localStorage.setItem("active_session_id", sessionId);

    const sources: string[] = [];
    if (youtubeUrl) sources.push(`YouTube: ${youtubeUrl.substring(0, 36)}...`);
    if (files.pdf) sources.push(`Document: ${files.pdf.name}`);
    if (files.pptx) sources.push(`Slides: ${files.pptx.name}`);
    if (files.audio) sources.push(`Audio: ${files.audio.name}`);
    
    const subskillObj = selectedSubskill ? MOCK_SUBSKILLS.find(s => s.id === selectedSubskill) : null;
    if (subskillObj) sources.push(`Curriculum Module: ${subskillObj.name}`);

    setIngestedSummary({
      sources,
      chunks: Math.floor(Math.random() * 15) + 28,
      subskillName: subskillObj?.name,
    });
    setIngestedSessionId(sessionId);
    setIsProcessing(false);
    setIsIngested(true);
  };

  const handleReset = () => {
    setIsIngested(false);
    setIngestedSummary(null);
    setIngestedSessionId(null);
    setYoutubeUrl("");
    setFiles({});
    setSelectedSubskill(null);
  };

  // POST-INGESTION SCREEN: Displays ingested status + "Start Assessment" button
  if (isIngested && ingestedSummary && ingestedSessionId) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col w-full"
      >
        {/* Success Header Banner */}
        <div className="p-6 border-b border-slate-100 bg-emerald-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-xl bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-700 shrink-0 shadow-xs">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="font-heading text-xl text-slate-900">
                  Data Successfully Ingested & Processed
                </h2>
                <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full border border-emerald-200">
                  Ready for Assessment
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">
                Your materials have been parsed, indexed into semantic concept nodes, and synthesized into a 3-tier assessment.
              </p>
            </div>
          </div>

          {/* Top action buttons */}
          <div className="flex items-center gap-2.5 shrink-0">
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium text-slate-700 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg transition"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span>Ingest More Data</span>
            </button>
            <button
              id="start-assessment-btn-top"
              onClick={() => router.push(`/dashboard/assessments?session_id=${ingestedSessionId}`)}
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-lg shadow-xs transition"
            >
              <ClipboardCheck className="w-4 h-4" />
              <span>Start Assessment</span>
            </button>
          </div>
        </div>

        {/* Content Breakdown Cards */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-50/40">
          {/* Card 1: Session Details */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Session Reference
              </span>
              <div className="font-mono text-sm font-semibold text-slate-800 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 inline-block mb-3">
                {ingestedSessionId}
              </div>
              <div className="flex items-center gap-1.5 text-xs text-slate-600">
                <Layers className="w-4 h-4 text-blue-600" />
                <span>{ingestedSummary.chunks} semantic concept chunks extracted</span>
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
              Cross-modal deduplication active & verified
            </div>
          </div>

          {/* Card 2: Ingested Sources */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Ingested Sources & Curriculum
              </span>
              <div className="space-y-2">
                {ingestedSummary.sources.map((src, i) => (
                  <div key={i} className="text-xs text-slate-800 flex items-start gap-2 bg-slate-50/80 p-2 rounded-lg border border-slate-100">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0 mt-1.5" />
                    <span className="font-medium truncate">{src}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
              {ingestedSummary.sources.length} active knowledge stream(s)
            </div>
          </div>

          {/* Card 3: 3-Tier Assessment Preview & Primary Start Button */}
          <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Target Evaluation
              </span>
              <p className="text-xs text-slate-600 leading-relaxed mb-3">
                A 3-tier diagnostic assessment (<strong>Easy</strong>, <strong>Medium</strong>, <strong>Tough</strong>) has been generated to evaluate and calibrate your competency.
              </p>
              <div className="flex items-center gap-2 text-xs">
                <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">Tier 1: Easy</span>
                <span className="px-2 py-0.5 rounded bg-amber-50 text-amber-700 font-medium border border-amber-200">Tier 2: Med</span>
                <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 font-medium border border-purple-200">Tier 3: Tough</span>
              </div>
            </div>

            <button
              id="start-assessment-btn-main"
              onClick={() => router.push(`/dashboard/assessments?session_id=${ingestedSessionId}`)}
              className="w-full mt-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center justify-center gap-2"
            >
              <span>Start Assessment</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden flex flex-col w-full">
      <div className="p-6 border-b border-slate-100 bg-slate-50/50">
        <h2 className="font-heading text-xl text-slate-900 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-600" />
          Multi-Modal Material & Curriculum Selection
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          Combine custom study materials or select a targeted competency module to calibrate and synthesize your assessment.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
        
        {/* PATHWAY 1: Custom Media */}
        <div className="p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-2">
              Pathway 1: Custom Study Materials
            </h3>
            <span className="text-[10px] text-slate-400">Multi-source</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            {/* YouTube Input */}
            <div className="col-span-1 sm:col-span-2 relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Youtube className="w-4 h-4 text-slate-400" />
              </div>
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="Paste YouTube Video URL..."
                className="w-full pl-9 pr-4 py-2.5 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition outline-none"
              />
              {youtubeUrl && (
                <button 
                  type="button"
                  onClick={() => setYoutubeUrl("")}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Hidden native file inputs */}
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

            {/* PDF Dropzone */}
            <div 
              onClick={() => pdfInputRef.current?.click()}
              className={cn(
                "border border-dashed rounded-lg p-4 flex flex-col items-center justify-center text-center cursor-pointer transition",
                files.pdf ? "border-blue-500 bg-blue-50/50" : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              <FileText className={cn("w-6 h-6 mb-2", files.pdf ? "text-blue-600" : "text-slate-400")} />
              <span className="text-xs font-medium text-slate-700">
                {files.pdf ? files.pdf.name : "Upload PDF Document"}
              </span>
              <span className="text-[10px] text-slate-400 mt-1">Lecture notes, manuals</span>
              {files.pdf && (
                <button 
                  onClick={(e) => { e.stopPropagation(); removeFile("pdf"); }}
                  className="mt-2 text-[10px] text-rose-600 hover:underline flex items-center gap-0.5"
                >
                  <X className="w-3 h-3" /> Remove
                </button>
              )}
            </div>

            {/* PPTX Dropzone */}
            <div 
              onClick={() => pptxInputRef.current?.click()}
              className={cn(
                "border border-dashed rounded-lg p-4 flex flex-col items-center justify-center text-center cursor-pointer transition",
                files.pptx ? "border-blue-500 bg-blue-50/50" : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              <MonitorPlay className={cn("w-6 h-6 mb-2", files.pptx ? "text-blue-600" : "text-slate-400")} />
              <span className="text-xs font-medium text-slate-700">
                {files.pptx ? files.pptx.name : "Upload PPTX Slides"}
              </span>
              <span className="text-[10px] text-slate-400 mt-1">Presentation decks</span>
              {files.pptx && (
                <button 
                  onClick={(e) => { e.stopPropagation(); removeFile("pptx"); }}
                  className="mt-2 text-[10px] text-rose-600 hover:underline flex items-center gap-0.5"
                >
                  <X className="w-3 h-3" /> Remove
                </button>
              )}
            </div>

            {/* Audio Dropzone */}
            <div 
              onClick={() => audioInputRef.current?.click()}
              className={cn(
                "border border-dashed rounded-lg p-4 flex flex-col items-center justify-center text-center cursor-pointer transition col-span-1 sm:col-span-2",
                files.audio ? "border-blue-500 bg-blue-50/50" : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
              )}
            >
              <FileAudio className={cn("w-6 h-6 mb-2", files.audio ? "text-blue-600" : "text-slate-400")} />
              <span className="text-xs font-medium text-slate-700">
                {files.audio ? files.audio.name : "Upload Audio Recording"}
              </span>
              <span className="text-[10px] text-slate-400 mt-1">Lecture recordings, dictations</span>
              {files.audio && (
                <button 
                  onClick={(e) => { e.stopPropagation(); removeFile("audio"); }}
                  className="mt-2 text-[10px] text-rose-600 hover:underline flex items-center gap-0.5"
                >
                  <X className="w-3 h-3" /> Remove
                </button>
              )}
            </div>

          </div>
        </div>

        {/* PATHWAY 2: Targeted Curriculum Subskills */}
        <div className="p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-700 uppercase tracking-wider flex items-center gap-2">
              Pathway 2: Targeted Curriculum Modules
            </h3>
            <span className="text-[10px] text-slate-400">Official library</span>
          </div>

          <p className="text-xs text-slate-500">
            Select a verified competency from the official statistical training catalog. You can combine it with custom uploads or assess it immediately.
          </p>

          <div className="space-y-3">
            <button
              type="button"
              onClick={() => setIsSubskillsOpen(!isSubskillsOpen)}
              className="w-full flex items-center justify-between p-3.5 border border-slate-200 rounded-lg hover:border-slate-300 hover:bg-slate-50 transition text-left"
            >
              <div className="flex items-center gap-2.5">
                <Target className="w-4 h-4 text-blue-600 shrink-0" />
                <span className="text-xs font-medium text-slate-700">
                  {selectedSubskill 
                    ? MOCK_SUBSKILLS.find(s => s.id === selectedSubskill)?.name 
                    : "Browse Curated Statistical Modules..."}
                </span>
              </div>
              <ChevronRight className={cn("w-4 h-4 text-slate-400 transition-transform", isSubskillsOpen && "rotate-90")} />
            </button>

            {/* Subskills Selection List */}
            {isSubskillsOpen && (
              <div className="border border-slate-200 rounded-lg max-h-52 overflow-y-auto divide-y divide-slate-100 bg-white shadow-xs">
                {MOCK_SUBSKILLS.map((subskill) => {
                  const isSelected = selectedSubskill === subskill.id;
                  return (
                    <div
                      key={subskill.id}
                      onClick={() => {
                        setSelectedSubskill(isSelected ? null : subskill.id);
                        setIsSubskillsOpen(false);
                      }}
                      className={cn(
                        "p-3 flex items-center justify-between cursor-pointer text-xs transition",
                        isSelected ? "bg-blue-50/70 text-blue-900 font-semibold" : "hover:bg-slate-50 text-slate-700"
                      )}
                    >
                      <div>
                        <div className="font-medium">{subskill.name}</div>
                        <div className="text-[10px] text-slate-400 mt-0.5">{subskill.comp}</div>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-blue-600 shrink-0" />}
                    </div>
                  );
                })}
              </div>
            )}

            {selectedSubskill && (
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-600" />
                  <span className="text-xs font-medium text-blue-900">
                    Selected Module: {MOCK_SUBSKILLS.find(s => s.id === selectedSubskill)?.name}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedSubskill(null)}
                  className="text-xs text-blue-700 hover:text-blue-900 font-medium"
                >
                  Clear
                </button>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* FOOTER ACTION BAR */}
      <div className="p-6 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {hasInputs ? "Materials ready for calibration & indexing." : "Add at least one source or select a module to proceed."}
        </span>
        <button
          onClick={handleSubmit}
          disabled={!hasInputs || isProcessing}
          className={cn(
            "px-6 py-2.5 rounded-lg text-xs font-semibold text-white shadow-xs transition flex items-center gap-2",
            !hasInputs ? "bg-slate-300 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700 hover:shadow-sm"
          )}
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Processing Materials...</span>
            </>
          ) : (
            <>
              <span>Ingest & Process Data</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
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
              <h3 className="font-heading text-lg text-slate-900 mb-5 text-center">Processing Knowledge Engine</h3>
              <div className="space-y-3.5">
                {[
                  "Extracting Text & Transcribing Media",
                  "Segmenting into Semantic Knowledge Chunks",
                  "Cross-Modal Deduplication",
                  "Vector Store Indexing & 3-Tier Generation"
                ].map((step, idx) => {
                  const isActive = currentStep === idx;
                  const isDone = currentStep > idx;
                  return (
                    <div key={idx} className="flex items-center gap-3">
                      <div className={cn(
                        "w-6 h-6 shrink-0 rounded-full flex items-center justify-center border",
                        isDone ? "bg-emerald-50 border-emerald-200 text-emerald-600" :
                        isActive ? "bg-blue-50 border-blue-200 text-blue-600" :
                        "bg-slate-50 border-slate-200 text-slate-400"
                      )}>
                        {isDone ? <Check className="w-3.5 h-3.5" /> : 
                         isActive ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 
                         <span className="text-[10px] font-medium">{idx + 1}</span>}
                      </div>
                      <span className={cn(
                        "text-xs font-medium transition-colors",
                        isDone ? "text-slate-700" :
                        isActive ? "text-blue-700 font-semibold" :
                        "text-slate-400"
                      )}>
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
