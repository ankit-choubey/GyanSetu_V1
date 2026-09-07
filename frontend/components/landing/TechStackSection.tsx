"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Upload,
  Brain,
  Database,
  HelpCircle,
  CheckCircle,
  Gauge,
  TrendingUp,
  Layers,
  Calculator,
  Shield,
  ArrowDown,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface PipelineStep {
  id: number;
  title: string;
  description: string;
  icons: [React.ComponentType<{ className?: string }>, React.ComponentType<{ className?: string }>];
  badges: string[];
  accentColor: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 1,
    title: "Document Upload & Processing",
    description:
      "PDF / PPT / Video manual ingestion with sliding window semantic chunking, OCR degradation fallback, and table boundary preservation.",
    icons: [FileText, Upload],
    badges: ["PyMuPDF", "python-pptx", "pdfplumber", "pytesseract"],
    accentColor: "#DBEAFE",
  },
  {
    id: 2,
    title: "Concept Extraction & Vector Indexing",
    description:
      "Statistical syllabus ontology parsing mapped into local 384-dimensional dense embeddings stored in ChromaDB.",
    icons: [Brain, Database],
    badges: ["ChromaDB", "VectorStore", "LangChain", "FastLocalEmbeddings"],
    accentColor: "#93C5FD",
  },
  {
    id: 3,
    title: "Grounding & MCQ Validation",
    description:
      "Automated item generation followed by a 5-stage validation pipeline: word-overlap grounding (>0.30), distractor entropy, and option shuffle.",
    icons: [HelpCircle, CheckCircle],
    badges: ["Groq Llama-3", "MCQValidator", "BloomTaxonomy"],
    accentColor: "#60A5FA",
  },
  {
    id: 4,
    title: "Adaptive Assessment Engine",
    description:
      "3-tier dynamic difficulty state machine (easy → medium → hard) with zero repetition and weak subskill isolation on learner errors.",
    icons: [Gauge, TrendingUp],
    badges: ["FastAPI", "AdaptiveSelector", "Next.js 14", "Framer Motion"],
    accentColor: "#3B82F6",
  },
  {
    id: 5,
    title: "Competency Engine & Evidence Fusion",
    description:
      "Deterministic 5-point state calculation (Mastery, Confidence, Coverage, Recency, Diversity) fusing 6 distinct evidentiary streams.",
    icons: [Layers, Calculator],
    badges: ["Python", "NumPy", "SQLModel", "Alembic"],
    accentColor: "#2563EB",
  },
  {
    id: 6,
    title: "4-Tier High-Resilience Fallback",
    description:
      "Graceful degradation pipeline (Live LLM → Cached LLM → Pre-generated Bank → Deterministic Mock) ensuring 100% test session uptime.",
    icons: [Shield, ArrowDown],
    badges: ["SQLite", "PostgreSQL", "FaultTolerant", "ResilienceTier"],
    accentColor: "#1D4ED8",
  },
];

export function TechStackSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="technology"
      className="relative py-24 md:py-32 px-6 bg-[#F8FAFC] border-b border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="08" text="TECHNOLOGY STACK" />
        <SectionHeading
          title="PIPELINE ARCHITECTURE"
          subtitle="How raw statistical manuals and assessment responses flow through our high-resilience AI infrastructure."
        />

        {/* Vertical Pipeline Stack */}
        <div className="max-w-4xl mx-auto my-12 text-left">
          {PIPELINE_STEPS.map((step, index) => {
            const [Icon1, Icon2] = step.icons;

            return (
              <React.Fragment key={step.id}>
                {/* Pipeline Step Card */}
                <motion.div
                  initial={
                    shouldReduceMotion ? false : { y: 25, opacity: 0 }
                  }
                  whileInView={
                    shouldReduceMotion ? {} : { y: 0, opacity: 1 }
                  }
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.45, delay: index * 0.08 }}
                  className="relative bg-white border border-[#E2E8F0] rounded-2xl p-6 md:p-7 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden"
                >
                  {/* Progressive Left Accent Color Bar */}
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1.5"
                    style={{ backgroundColor: step.accentColor }}
                  />

                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pl-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className="font-mono text-xs font-bold text-[#94A3B8]">
                          STEP 0{step.id}
                        </span>
                        <div className="flex items-center gap-1 text-[#3B82F6]">
                          <Icon1 className="w-4 h-4" />
                          <Icon2 className="w-4 h-4" />
                        </div>
                      </div>

                      <h3 className="font-heading text-xl md:text-2xl text-[#0F172A] tracking-wide mb-1">
                        {step.title}
                      </h3>
                      <p className="font-body text-xs md:text-sm text-[#64748B] leading-relaxed max-w-2xl">
                        {step.description}
                      </p>
                    </div>

                    {/* Tech Badges */}
                    <div className="flex flex-wrap md:flex-col items-start md:items-end gap-1.5 shrink-0">
                      {step.badges.map((badge) => (
                        <span
                          key={badge}
                          className="px-2.5 py-1 rounded-md bg-[#F1F5F9] border border-[#E2E8F0] text-[11px] font-mono font-medium text-[#475569]"
                        >
                          {badge}
                        </span>
                      ))}
                    </div>
                  </div>
                </motion.div>

                {/* Animated Connecting Flow Line between cards */}
                {index < PIPELINE_STEPS.length - 1 && (
                  <div className="flex justify-center my-1.5">
                    <svg className="w-4 h-6" viewBox="0 0 16 24">
                      <line
                        x1="8"
                        y1="0"
                        x2="8"
                        y2="24"
                        stroke="#CBD5E1"
                        strokeWidth="2"
                        strokeDasharray="4 3"
                        className="animate-dash-flow"
                      />
                    </svg>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </section>
  );
}
