"use client";

import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import { Landmark } from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const ORGANIZATIONS = [
  "MoSPI",
  "NSSTA",
  "TPAC",
  "iGOT Karmayogi",
  "KCM",
];

// Self-Contained <DataMesh /> Component (§3.7 & §7.1 - 100% Reproducible)
function DataMesh() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tilt, setTilt] = useState({ rotateX: 0, rotateY: 0 });
  const shouldReduceMotion = useReducedMotion();

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (shouldReduceMotion || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    // max +-8 deg tilt
    const rotateY = (x / (rect.width / 2)) * 8;
    const rotateX = -(y / (rect.height / 2)) * 8;
    setTilt({ rotateX, rotateY });
  };

  const handleMouseLeave = () => {
    setTilt({ rotateX: 0, rotateY: 0 });
  };

  // 7 nodes in percentage coordinates
  const nodes = [
    { x: 50, y: 45, size: 16 }, // Center node
    { x: 22, y: 30, size: 12 },
    { x: 78, y: 32, size: 13 },
    { x: 30, y: 68, size: 11 },
    { x: 72, y: 70, size: 14 },
    { x: 50, y: 18, size: 12 },
    { x: 50, y: 80, size: 10 },
  ];

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="relative w-full h-[400px] rounded-2xl overflow-hidden border border-[#E2E8F0] shadow-sm flex items-center justify-center select-none"
      style={{
        background:
          "radial-gradient(circle at 50% 45%, #EFF6FF 0%, #FFFFFF 75%)",
        perspective: "1000px",
      }}
    >
      {/* 3D tiltable mesh group */}
      <div
        className={`relative w-full h-full flex items-center justify-center transition-transform duration-200 ease-out ${
          shouldReduceMotion ? "" : "animate-mesh-spin"
        }`}
        style={{
          transform: `rotateX(${tilt.rotateX}deg) rotateY(${tilt.rotateY}deg)`,
          transformOrigin: "50% 50%",
        }}
      >
        {/* SVG Mesh Connections */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-1">
          {nodes.slice(1).map((node, i) => (
            <line
              key={i}
              x1="50%"
              y1="45%"
              x2={`${node.x}%`}
              y2={`${node.y}%`}
              stroke="#60A5FA"
              strokeWidth="1.5"
              strokeOpacity="0.45"
            />
          ))}
          {/* Outer Cross Connections */}
          <line
            x1="22%"
            y1="30%"
            x2="50%"
            y2="18%"
            stroke="#60A5FA"
            strokeWidth="1"
            strokeOpacity="0.3"
          />
          <line
            x1="78%"
            y1="32%"
            x2="50%"
            y2="18%"
            stroke="#60A5FA"
            strokeWidth="1"
            strokeOpacity="0.3"
          />
          <line
            x1="30%"
            y1="68%"
            x2="50%"
            y2="80%"
            stroke="#60A5FA"
            strokeWidth="1"
            strokeOpacity="0.3"
          />
          <line
            x1="72%"
            y1="70%"
            x2="50%"
            y2="80%"
            stroke="#60A5FA"
            strokeWidth="1"
            strokeOpacity="0.3"
          />
        </svg>

        {/* Glowing Gradient Nodes */}
        {nodes.map((node, i) => (
          <div
            key={i}
            className="absolute rounded-full shadow-[0_0_16px_rgba(59,130,246,0.6)]"
            style={{
              left: `${node.x}%`,
              top: `${node.y}%`,
              width: `${node.size}px`,
              height: `${node.size}px`,
              transform: "translate(-50%, -50%)",
              background:
                "linear-gradient(135deg, #3B82F6, #6366F1, #2DD4BF, #FB7185)",
            }}
          />
        ))}
      </div>

      {/* Floating Center Badge */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-white/90 backdrop-blur-md border border-[#DBEAFE] text-[10px] font-mono text-[#3B82F6] font-semibold uppercase tracking-wider shadow-sm pointer-events-none">
        Neural Competency Graph 3D
      </div>
    </div>
  );
}

export function SocialProofSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="social-proof"
      className="relative py-24 md:py-32 px-6 bg-[#F8FAFC] border-b border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel
          number="06"
          text="BUILT FOR INDIA'S STATISTICAL WORKFORCE"
        />
        <SectionHeading
          title="PROVEN ARCHITECTURE FOR MISSION-CRITICAL TRAINING"
          subtitle="Designed in alignment with NSSTA competency guidelines and the National Training Policy."
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center my-12 text-left">
          {/* ========================================================================= */}
          {/* LEFT SIDE: Wordmark Marquee & Stat Counters */}
          {/* ========================================================================= */}
          <div>
            {/* Styled Wordmark Marquee (Infinite Seamless Loop) */}
            <div className="relative w-full overflow-hidden mb-4 py-2 border-y border-[#E2E8F0] bg-white rounded-xl">
              <div
                className={`flex gap-6 whitespace-nowrap ${
                  shouldReduceMotion ? "" : "animate-marquee"
                }`}
              >
                {[...ORGANIZATIONS, ...ORGANIZATIONS, ...ORGANIZATIONS].map(
                  (org, i) => (
                    <div
                      key={i}
                      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-[#E2E8F0] text-[#475569] font-body text-sm font-semibold tracking-wide shadow-sm"
                    >
                      <Landmark className="w-4 h-4 text-[#94A3B8]" />
                      <span>{org}</span>
                    </div>
                  )
                )}
              </div>
            </div>

            <p className="font-body text-xs text-[#94A3B8] mb-10 pl-1">
              Built for India&apos;s official statistical training ecosystem.
            </p>

            {/* 3 Stat Counters Stacked */}
            <div className="grid grid-cols-3 gap-6 pt-4 border-t border-[#E2E8F0]">
              {/* Evidence Types */}
              <div>
                <div className="font-heading text-5xl md:text-6xl text-[#0F172A]">
                  <AnimatedCounter target={6} />
                </div>
                <p className="font-body text-xs uppercase tracking-wider text-[#64748B] font-semibold mt-1">
                  Evidence Types
                </p>
                <span className="font-mono text-[10px] text-[#94A3B8]">
                  Fused continuously
                </span>
              </div>

              {/* AI Agents */}
              <div>
                <div className="font-heading text-5xl md:text-6xl text-[#0F172A]">
                  <AnimatedCounter target={3} />
                </div>
                <p className="font-body text-xs uppercase tracking-wider text-[#64748B] font-semibold mt-1">
                  AI Agents
                </p>
                <span className="font-mono text-[10px] text-[#94A3B8]">
                  Central Orchestrator
                </span>
              </div>

              {/* 103 Tests Passing (MEASURED §2.9) */}
              {/* MEASURED — source: 33 backend tests + 70 ML tests verified passing */}
              <div>
                <div className="font-heading text-5xl md:text-6xl text-[#3B82F6]">
                  <AnimatedCounter target={103} />
                </div>
                <p className="font-body text-xs uppercase tracking-wider text-[#0F172A] font-bold mt-1">
                  Tests Passing
                </p>
                <span className="font-mono text-[10px] text-[#0D9488] font-bold">
                  100% Automated Suite
                </span>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* RIGHT SIDE: 3D DataMesh Visual */}
          {/* ========================================================================= */}
          <div>
            <DataMesh />
          </div>
        </div>
      </div>
    </section>
  );
}
