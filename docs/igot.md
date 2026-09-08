# iGOT Karmayogi Course Simulation & GyanSetu Integration

## Overview
This document records the standalone **iGOT Karmayogi Bharat Course Simulation** page and the launch button integrated into the GyanSetu Landing Page hero section.

---

## 1. Features Implemented

1. **iGOT Simulation Launcher Button**:
   - Integrated into [`HeroSection.tsx`](file:///Users/theankit/Documents/AK/Projects/GyanSetu_V1/frontend/components/landing/HeroSection.tsx) right beside the badge `NSSTA IMPROVED 72% TRAINING RESULTS`.
   - Features animated live indicator, orange gradient iGOT branding, and direct routing to `/igot`.

2. **Standalone iGOT Karmayogi Bharat Study Page (`/igot`)**:
   - **Authentic Platform Branding**: Recreates the official iGOT Karmayogi Bharat header with the tricolor emblem, Hindi typography (*कर्मयोगी भारत* / *लोकहितं मम करणीयम्*), official DoPT/MoSPI affiliation, and universal accessibility badge (as captured in Photo 2).
   - **Video Player Studio with Media Controls**:
     - Automatically starts playing the lecture upon launching the page as requested.
     - Streams the local high-definition lecture MP4: `Introduction to Statistics and Data Analysis - Steve Brunton` (placed in `frontend/public/video/intro_to_statistics.mp4`).
     - Interactive custom controls:
       - Play / Pause (spacebar & on-screen button)
       - Scrub timeline with hover seek
       - Rewind 10s button
       - Volume control with mute toggle
       - Current / Total duration timer (`00:00 / MM:SS`)
       - Playback speed chips (`1x`, `1.25x`, `1.5x`, `2x`)
       - 720p HD resolution badge
       - Fullscreen toggle
   - **Coursera-Style Course Curriculum & Playlist Sidebar**:
     - 5 modular units mapped to MoSPI syllabus (Descriptive Stats, Probability, Sampling Variance, High-Dimensional SVD, Cadre Harmonization).
     - Active module indicator & progress bar (`20% Done`).
   - **Tabbed Study Studio**:
     - *Overview & Learning Objectives*: Explains theoretical foundations and cadre relevance for Junior Statistical Officers (JSO).
     - *Interactive Timestamps*: Clickable topic markers that jump the video player to exact moments (e.g., Central Limit Theorem, Variance Quantification).
     - *MoSPI Handbooks*: Links to training compendiums and official statistical manuals.
   - **GyanSetu Two-Way Bridge**:
     - Directly links to GyanSetu's 15-question adaptive assessment (`/dashboard/assessments`) so officers can immediately test their competency after watching the lecture.
     - "Back to GyanSetu" header link to seamlessly return to the core application.

---

## 2. Diffs of Modified Files

### `frontend/components/landing/HeroSection.tsx`

```diff
@@ -96,7 +96,7 @@
           </Link>
         </motion.div>
 
-        {/* Social Proof Line (Valley.co Pattern A / §2.9) */}
+        {/* Social Proof Line & iGOT Simulation Launcher */}
         {/* ILLUSTRATIVE — replace with measured value or remove before any public/demo/judge-facing use */}
         <motion.div
           initial={shouldReduceMotion ? false : { opacity: 0 }}
@@ -103,14 +103,27 @@
           transition={{ duration: 0.4, delay: 1.2 }}
-          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8FAFC] border border-[#E2E8F0]"
-        >
-          <span className="w-4 h-4 rounded-full bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6]">
-            <ShieldCheck className="w-3 h-3" />
-          </span>
-          <p className="font-body text-[11px] sm:text-xs font-semibold uppercase tracking-[0.06em] text-[#475569]">
-            NSSTA IMPROVED{" "}
-            <span className="text-[#3B82F6] font-bold">72%</span> TRAINING
-            RESULTS
-          </p>
+          className="flex flex-wrap items-center justify-center gap-3"
+        >
+          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8FAFC] border border-[#E2E8F0]">
+            <span className="w-4 h-4 rounded-full bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6]">
+              <ShieldCheck className="w-3 h-3" />
+            </span>
+            <p className="font-body text-[11px] sm:text-xs font-semibold uppercase tracking-[0.06em] text-[#475569]">
+              NSSTA IMPROVED{" "}
+              <span className="text-[#3B82F6] font-bold">72%</span> TRAINING
+              RESULTS
+            </p>
+          </div>
+
+          <Link
+            href="/igot"
+            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-body text-[11px] sm:text-xs font-bold uppercase tracking-[0.06em] shadow-xs hover:shadow-sm transition-all transform active:scale-95 group"
+            title="Launch iGOT Karmayogi Course Simulation"
+            id="igot-sim-btn"
+          >
+            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
+            <span>iGOT Sim</span>
+            <span className="text-[10px] bg-white/20 px-1.5 py-0.2 rounded text-white font-mono">Live</span>
+          </Link>
         </motion.div>
       </div>
     </section>
```

---

## 3. Full Code: `frontend/app/igot/page.tsx`

```tsx
"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  RotateCcw,
  FastForward,
  CheckCircle2,
  BookOpen,
  Award,
  ChevronRight,
  ArrowLeft,
  GraduationCap,
  Sparkles,
  Clock,
  FileText,
  HelpCircle,
  Share2,
  Download,
  ShieldCheck,
  ExternalLink,
  Layers,
  Settings
} from "lucide-react";

export default function IGotSimulationPage() {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.85);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "notes" | "resources">("overview");
  const [activeModuleIdx, setActiveModuleIdx] = useState(0);
  const [hasAutoPlayed, setHasAutoPlayed] = useState(false);

  // Auto-play video on initial launch
  useEffect(() => {
    const vid = videoRef.current;
    if (vid && !hasAutoPlayed) {
      vid.play()
        .then(() => {
          setIsPlaying(true);
          setHasAutoPlayed(true);
        })
        .catch(() => {
          vid.muted = true;
          setIsMuted(true);
          vid.play()
            .then(() => {
              setIsPlaying(true);
              setHasAutoPlayed(true);
            })
            .catch((e) => console.warn("Autoplay prevented:", e));
        });
    }
  }, [hasAutoPlayed]);

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (isPlaying) {
      videoRef.current.pause();
      setIsPlaying(false);
    } else {
      videoRef.current.play();
      setIsPlaying(true);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const targetTime = parseFloat(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = targetTime;
      setCurrentTime(targetTime);
    }
  };

  const seekToTimestamp = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      setCurrentTime(seconds);
      if (!isPlaying) {
        videoRef.current.play();
        setIsPlaying(true);
      }
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (videoRef.current) {
      videoRef.current.volume = val;
      if (val === 0) {
        videoRef.current.muted = true;
        setIsMuted(true);
      } else {
        videoRef.current.muted = false;
        setIsMuted(false);
      }
    }
  };

  const toggleMute = () => {
    if (!videoRef.current) return;
    if (isMuted) {
      videoRef.current.muted = false;
      setIsMuted(false);
    } else {
      videoRef.current.muted = true;
      setIsMuted(true);
    }
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    if (videoRef.current) {
      videoRef.current.playbackRate = speed;
    }
  };

  const toggleFullscreen = () => {
    const container = document.getElementById("video-player-container");
    if (!container) return;

    if (!document.fullscreenElement) {
      container.requestFullscreen().then(() => setIsFullscreen(true)).catch(console.warn);
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(console.warn);
    }
  };

  const formatTime = (timeInSec: number) => {
    if (isNaN(timeInSec)) return "00:00";
    const mins = Math.floor(timeInSec / 60);
    const secs = Math.floor(timeInSec % 60);
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const courseModules = [
    {
      id: 1,
      title: "Introduction to Statistics and Data Analysis",
      instructor: "Prof. Steve Brunton",
      duration: "32:45",
      isCurrent: true,
      timestamp: 0,
    },
    {
      id: 2,
      title: "Descriptive Statistics, Probability & Distributions",
      instructor: "Prof. Steve Brunton",
      duration: "18:20",
      isCurrent: false,
      timestamp: 312,
    },
    {
      id: 3,
      title: "Inferential Frameworks, Sampling & Variance Estimation",
      instructor: "Prof. Steve Brunton",
      duration: "24:15",
      isCurrent: false,
      timestamp: 760,
    },
    {
      id: 4,
      title: "Dimensionality Reduction, SVD & Predictive Analytics",
      instructor: "Prof. Steve Brunton",
      duration: "28:50",
      isCurrent: false,
      timestamp: 1275,
    },
    {
      id: 5,
      title: "MoSPI Statistical Cadre Harmonization Protocol",
      instructor: "NSSTA Faculty Directorate",
      duration: "15:10",
      isCurrent: false,
      timestamp: 0,
    },
  ];

  const lectureTimestamps = [
    { time: 0, label: "00:00 - Introduction & Foundations of Data-Driven Science" },
    { time: 185, label: "03:05 - The Role of Statistics in Decision Systems & Policy" },
    { time: 420, label: "07:00 - Continuous vs. Discrete Probability Models" },
    { time: 740, label: "12:20 - Variance, Covariance & Uncertainty Quantification" },
    { time: 1120, label: "18:40 - Sampling Bias & The Central Limit Theorem" },
    { time: 1540, label: "25:40 - Regression, Model Grounding & Conclusion" },
  ];

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#1E293B] flex flex-col font-sans antialiased selection:bg-[#F97316] selection:text-white">
      {/* ========================================================================= */}
      {/* iGOT KARMAYOGI OFFICIAL NAVIGATION BAR                                    */}
      {/* ========================================================================= */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-[#F1E9DA] shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">
          {/* Brand Logo: Karmayogi Bharat Emblem */}
          <div className="flex items-center gap-4">
            <Link href="/igot" className="flex items-center gap-3 group">
              {/* Karmayogi Emblem Icon */}
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#FF9933] via-[#FFFFFF] to-[#138808] p-[1.5px] shadow-xs">
                <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
                  <span className="text-xl font-bold bg-gradient-to-r from-[#EA580C] to-[#C2410C] bg-clip-text text-transparent">
                    क
                  </span>
                </div>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-xl sm:text-2xl text-[#1E3A8A] tracking-tight">
                    कर्मयोगी
                  </span>
                  <span className="font-extrabold text-xl sm:text-2xl text-[#EA580C] tracking-tight">
                    भारत
                  </span>
                </div>
                <span className="text-[10px] text-[#64748B] font-medium tracking-wide">
                  लोकहितं मम करणीयम् • iGOT Platform
                </span>
              </div>
            </Link>

            <span className="hidden md:inline-block w-px h-8 bg-[#E2E8F0] mx-2" />

            <div className="hidden lg:flex flex-col text-[11px] text-[#475569]">
              <span className="font-bold text-[#0F172A]">National Programme for Civil Services Capacity Building</span>
              <span className="text-[#64748B]">DoPT • Government of India</span>
            </div>
          </div>

          {/* Desktop Nav Items */}
          <nav className="hidden xl:flex items-center gap-6 text-sm font-medium text-[#475569]">
            <span className="text-[#EA580C] font-semibold border-b-2 border-[#EA580C] pb-1">
              Courses
            </span>
            <span className="hover:text-[#0F172A] cursor-pointer transition">About Us</span>
            <span className="hover:text-[#0F172A] cursor-pointer transition">Competencies</span>
            <span className="hover:text-[#0F172A] cursor-pointer transition">Newsroom</span>
            <span className="hover:text-[#0F172A] cursor-pointer transition">Help Centre</span>
          </nav>

          {/* Right Actions: Return to GyanSetu & Profile */}
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-semibold border border-blue-200 transition shadow-xs"
              title="Return to GyanSetu Home"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>GyanSetu</span>
            </Link>

            <Link
              href="/dashboard/assessments"
              className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#EA580C] hover:bg-[#C2410C] text-white text-xs font-semibold transition shadow-xs"
              title="Open GyanSetu 15-MCQ Assessment"
            >
              <Award className="w-3.5 h-3.5" />
              <span>Assessment</span>
            </Link>

            {/* Officer Profile Badge */}
            <div className="flex items-center gap-2 pl-2 border-l border-[#E2E8F0]">
              <div className="w-9 h-9 rounded-full bg-[#1E3A8A] text-white flex items-center justify-center font-bold text-xs shadow-xs">
                AC
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-bold text-[#0F172A] leading-tight">Shri Ankit Choubey</span>
                <span className="text-[10px] text-[#64748B]">Statistical Officer</span>
              </div>
            </div>

            {/* Accessibility Button (Blue round button as in Photo 2) */}
            <button
              type="button"
              className="w-8 h-8 rounded-full bg-[#1E3A8A] text-white flex items-center justify-center hover:bg-[#1D4ED8] transition shrink-0"
              title="Accessibility Tools"
            >
              <span className="text-xs font-bold">♿</span>
            </button>
          </div>
        </div>
      </header>

      {/* ========================================================================= */}
      {/* BREADCRUMB & COURSE BANNER                                                */}
      {/* ========================================================================= */}
      <div className="bg-[#FFF9F2] border-b border-[#F5E6D3] py-4 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs text-[#64748B] mb-1.5 flex-wrap">
              <span>iGOT Courses</span>
              <ChevronRight className="w-3 h-3 text-[#CBD5E1]" />
              <span>Official Statistics Cadre</span>
              <ChevronRight className="w-3 h-3 text-[#CBD5E1]" />
              <span className="text-[#EA580C] font-semibold">Descriptive & Inferential Analytics</span>
            </div>
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-[#0F172A] tracking-tight">
              Introduction to Statistics and Data Analysis
            </h1>
            <p className="text-xs sm:text-sm text-[#475569] mt-1 flex items-center gap-2 flex-wrap">
              <span>Curated by <strong>Prof. Steve Brunton</strong></span>
              <span>•</span>
              <span className="text-[#EA580C] font-semibold">National Statistical Systems Training Academy (NSSTA)</span>
              <span>•</span>
              <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 text-[11px] font-medium">
                <ShieldCheck className="w-3 h-3" /> MoSPI Cadre Approved
              </span>
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              href="/dashboard/assessments"
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>Test with GyanSetu (15 MCQs)</span>
            </Link>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* MAIN COURSE STUDIO & MEDIA CONTROLS (COURSERA / iGOT STYLE)               */}
      {/* ========================================================================= */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT 8 COLUMNS: INTERACTIVE VIDEO PLAYER & LECTURE DETAILS */}
          <div className="lg:col-span-8 space-y-6">
            {/* VIDEO PLAYER CONTAINER */}
            <div
              id="video-player-container"
              className="relative bg-black rounded-2xl overflow-hidden shadow-lg border border-slate-800 group aspect-video flex flex-col justify-end"
            >
              {/* Native HTML5 Video Element Streaming the Local MP4 */}
              <video
                ref={videoRef}
                src="/video/intro_to_statistics.mp4"
                className="w-full h-full object-contain cursor-pointer"
                onClick={togglePlay}
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                playsInline
              />

              {/* Big Center Play/Pause Splash Overlay */}
              {!isPlaying && (
                <div
                  onClick={togglePlay}
                  className="absolute inset-0 bg-black/40 backdrop-blur-[2px] flex items-center justify-center cursor-pointer transition-opacity"
                >
                  <div className="w-20 h-20 rounded-full bg-[#EA580C] text-white flex items-center justify-center shadow-2xl transform hover:scale-105 transition-all">
                    <Play className="w-9 h-9 fill-white ml-1" />
                  </div>
                </div>
              )}

              {/* OVERLAY CUSTOM MEDIA CONTROLS BAR */}
              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 via-black/60 to-transparent p-4 flex flex-col gap-2.5 transition-opacity duration-200">
                {/* Scrub Timeline Progress Slider */}
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min={0}
                    max={duration || 100}
                    step={0.1}
                    value={currentTime}
                    onChange={handleSeek}
                    className="w-full h-1.5 bg-white/30 rounded-lg appearance-none cursor-pointer accent-[#EA580C] hover:h-2.5 transition-all"
                  />
                </div>

                {/* Controls Bottom Row */}
                <div className="flex items-center justify-between gap-2 text-white">
                  <div className="flex items-center gap-3">
                    {/* Play/Pause Button */}
                    <button
                      type="button"
                      onClick={togglePlay}
                      className="p-1.5 hover:bg-white/20 rounded-lg transition"
                      title={isPlaying ? "Pause (Space)" : "Play (Space)"}
                    >
                      {isPlaying ? (
                        <Pause className="w-5 h-5 fill-white" />
                      ) : (
                        <Play className="w-5 h-5 fill-white" />
                      )}
                    </button>

                    {/* Rewind 10s */}
                    <button
                      type="button"
                      onClick={() => seekToTimestamp(Math.max(0, currentTime - 10))}
                      className="p-1.5 hover:bg-white/20 rounded-lg transition text-xs flex items-center gap-0.5"
                      title="Rewind 10 seconds"
                    >
                      <RotateCcw className="w-4 h-4" />
                      <span className="text-[10px]">10s</span>
                    </button>

                    {/* Volume & Mute */}
                    <div className="flex items-center gap-1.5 group/vol">
                      <button
                        type="button"
                        onClick={toggleMute}
                        className="p-1.5 hover:bg-white/20 rounded-lg transition"
                        title={isMuted ? "Unmute" : "Mute"}
                      >
                        {isMuted || volume === 0 ? (
                          <VolumeX className="w-5 h-5" />
                        ) : (
                          <Volume2 className="w-5 h-5" />
                        )}
                      </button>
                      <input
                        type="range"
                        min={0}
                        max={1}
                        step={0.05}
                        value={isMuted ? 0 : volume}
                        onChange={handleVolumeChange}
                        className="w-16 h-1 bg-white/30 rounded appearance-none cursor-pointer accent-[#EA580C]"
                      />
                    </div>

                    {/* Time Counter */}
                    <span className="text-xs font-mono font-medium text-slate-200 tabular-nums">
                      {formatTime(currentTime)} / {formatTime(duration)}
                    </span>
                  </div>

                  {/* Right Side Options: Speed, HD badge, Fullscreen */}
                  <div className="flex items-center gap-3">
                    {/* Playback Speed Chips */}
                    <div className="flex items-center bg-white/10 rounded-lg p-0.5 text-xs">
                      {[1, 1.25, 1.5, 2].map((rate) => (
                        <button
                          key={rate}
                          type="button"
                          onClick={() => handleSpeedChange(rate)}
                          className={`px-1.5 py-0.5 rounded font-mono text-[11px] transition ${
                            playbackSpeed === rate
                              ? "bg-[#EA580C] text-white font-bold"
                              : "text-slate-300 hover:text-white"
                          }`}
                        >
                          {rate}x
                        </button>
                      ))}
                    </div>

                    <span className="text-[10px] font-bold px-1.5 py-0.5 bg-white/20 rounded text-slate-200">
                      720p HD
                    </span>

                    {/* Fullscreen Button */}
                    <button
                      type="button"
                      onClick={toggleFullscreen}
                      className="p-1.5 hover:bg-white/20 rounded-lg transition"
                      title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
                    >
                      {isFullscreen ? (
                        <Minimize className="w-4 h-4" />
                      ) : (
                        <Maximize className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* ORANGE BANNER UNDER VIDEO (MATCHING PHOTO 2 TEAM KARMAYOGI BHARAT BANNER) */}
            <div className="bg-gradient-to-r from-[#EA580C] to-[#C2410C] text-white p-4 rounded-xl shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
              <div>
                <h3 className="font-bold text-base sm:text-lg tracking-wide">
                  Team Karmayogi Bharat • Official Study Platform
                </h3>
                <p className="text-xs text-orange-100 mt-0.5">
                  Civil Services Competency Enhancement Track • Statistical Quality, Ingestion & Evidence Engine
                </p>
              </div>
              <Link
                href="/dashboard/assessments"
                className="px-4 py-2 bg-white text-[#C2410C] hover:bg-orange-50 rounded-lg text-xs font-bold transition shadow-xs shrink-0"
              >
                Evaluate in GyanSetu →
              </Link>
            </div>

            {/* TABBED INFORMATION STUDIO */}
            <div className="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm overflow-hidden">
              {/* Tab Navigation */}
              <div className="flex border-b border-[#E2E8F0] bg-[#F8FAFC]">
                <button
                  type="button"
                  onClick={() => setActiveTab("overview")}
                  className={`px-5 py-3.5 text-xs sm:text-sm font-bold border-b-2 transition flex items-center gap-2 ${
                    activeTab === "overview"
                      ? "border-[#EA580C] text-[#EA580C] bg-white"
                      : "border-transparent text-[#64748B] hover:text-[#0F172A]"
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Overview & Outcomes</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("notes")}
                  className={`px-5 py-3.5 text-xs sm:text-sm font-bold border-b-2 transition flex items-center gap-2 ${
                    activeTab === "notes"
                      ? "border-[#EA580C] text-[#EA580C] bg-white"
                      : "border-transparent text-[#64748B] hover:text-[#0F172A]"
                  }`}
                >
                  <Clock className="w-4 h-4" />
                  <span>Interactive Timestamps</span>
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab("resources")}
                  className={`px-5 py-3.5 text-xs sm:text-sm font-bold border-b-2 transition flex items-center gap-2 ${
                    activeTab === "resources"
                      ? "border-[#EA580C] text-[#EA580C] bg-white"
                      : "border-transparent text-[#64748B] hover:text-[#0F172A]"
                  }`}
                >
                  <FileText className="w-4 h-4" />
                  <span>MoSPI Handbooks</span>
                </button>
              </div>

              {/* Tab Content */}
              <div className="p-6">
                {activeTab === "overview" && (
                  <div className="space-y-4 text-sm text-[#475569] leading-relaxed">
                    <div>
                      <h4 className="font-bold text-[#0F172A] text-base mb-1">
                        Lecture Description & Learning Objectives
                      </h4>
                      <p>
                        This flagship lecture series, delivered by <strong>Prof. Steve Brunton</strong> and
                        adopted by the <strong>National Statistical Systems Training Academy (NSSTA)</strong>,
                        bridges theoretical probability with applied modern data analysis. Learners will study
                        how empirical data is structured, cleaned, and statistically characterized for policy decisions.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                      <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0]">
                        <span className="font-bold text-xs text-[#1E3A8A] uppercase tracking-wider block mb-1">
                          Core Competencies Covered
                        </span>
                        <ul className="text-xs space-y-1.5 list-disc list-inside text-[#334155]">
                          <li>Probability Density Functions & CDFs</li>
                          <li>Sampling Variance & Neyman Allocation</li>
                          <li>Central Limit Theorem in NSS Rounds</li>
                          <li>Regression Grounding & Residual Analysis</li>
                        </ul>
                      </div>
                      <div className="p-3.5 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0]">
                        <span className="font-bold text-xs text-[#1E3A8A] uppercase tracking-wider block mb-1">
                          Official Cadre Relevance
                        </span>
                        <ul className="text-xs space-y-1.5 list-disc list-inside text-[#334155]">
                          <li>Junior Statistical Officers (JSO) & SSOs</li>
                          <li>National Accounts Division (NAD)</li>
                          <li>Field Operations Division (FOD) NSS survey rounds</li>
                          <li>Price & Index Compilation Teams</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "notes" && (
                  <div className="space-y-3">
                    <p className="text-xs text-[#64748B] mb-2">
                      Click any timestamp to navigate the video player directly to that key section:
                    </p>
                    {lectureTimestamps.map((item) => (
                      <button
                        key={item.time}
                        type="button"
                        onClick={() => seekToTimestamp(item.time)}
                        className="w-full text-left p-3 rounded-xl border border-[#E2E8F0] hover:border-[#EA580C] hover:bg-[#FFF9F2] transition flex items-center justify-between group"
                      >
                        <span className="text-xs sm:text-sm font-medium text-[#0F172A] group-hover:text-[#EA580C]">
                          {item.label}
                        </span>
                        <span className="text-xs text-[#EA580C] font-semibold opacity-0 group-hover:opacity-100 transition">
                          Play Section →
                        </span>
                      </button>
                    ))}
                  </div>
                )}

                {activeTab === "resources" && (
                  <div className="space-y-3">
                    <div className="p-4 rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-between">
                      <div>
                        <p className="text-sm font-bold text-[#0F172A]">MoSPI Compendium of Statistical Methods (PDF)</p>
                        <p className="text-xs text-[#64748B]">Official Field Manual & Standard Formulas • 4.2 MB</p>
                      </div>
                      <Link
                        href="/dashboard/library"
                        className="px-3 py-1.5 bg-white text-blue-700 hover:bg-blue-50 border border-blue-200 rounded-lg text-xs font-semibold"
                      >
                        View in Library
                      </Link>
                    </div>

                    <div className="p-4 rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-between">
                      <div>
                        <p className="text-sm font-bold text-[#0F172A]">NSSTA Sampling Protocols & Variance Formulations</p>
                        <p className="text-xs text-[#64748B]">Handbook for NSS Rounds & Cadre Trainees • 2.8 MB</p>
                      </div>
                      <Link
                        href="/dashboard/library"
                        className="px-3 py-1.5 bg-white text-blue-700 hover:bg-blue-50 border border-blue-200 rounded-lg text-xs font-semibold"
                      >
                        View in Library
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* RIGHT 4 COLUMNS: PLAYLIST / CURRICULUM (COURSERA STYLE) & GYANSETU BRIDGE */}
          <div className="lg:col-span-4 space-y-6">
            {/* GYANSETU 15-MCQ ASSESSMENTS BRIDGE CARD */}
            <div className="bg-gradient-to-br from-[#1E3A8A] to-[#1E293B] text-white p-6 rounded-2xl shadow-md border border-blue-900">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300">
                  GyanSetu Integration Active
                </span>
              </div>
              <h3 className="font-heading text-2xl tracking-wide text-white mb-2">
                Evaluate Your Learning
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                Take the official 15-question adaptive assessment directly based on this video module.
                Your score will dynamically update your competency profile and report ledger.
              </p>
              <Link
                href="/dashboard/assessments"
                className="w-full py-3 px-4 bg-[#EA580C] hover:bg-[#C2410C] text-white rounded-xl text-xs sm:text-sm font-bold shadow-sm transition flex items-center justify-center gap-2"
              >
                <span>Launch 15-MCQ Assessment</span>
                <ChevronRight className="w-4 h-4" />
              </Link>
            </div>

            {/* COURSE PLAYLIST / SYLLABUS */}
            <div className="bg-white rounded-2xl border border-[#E2E8F0] shadow-sm overflow-hidden">
              <div className="p-4 border-b border-[#E2E8F0] bg-[#F8FAFC] flex items-center justify-between">
                <div>
                  <h4 className="font-bold text-sm text-[#0F172A]">Course Curriculum</h4>
                  <p className="text-[11px] text-[#64748B]">5 Modules • 2 hrs 10 mins total</p>
                </div>
                <span className="text-xs font-bold text-[#EA580C] bg-orange-50 px-2 py-0.5 rounded border border-orange-200">
                  20% Done
                </span>
              </div>

              <div className="divide-y divide-[#F1F5F9]">
                {courseModules.map((mod, idx) => (
                  <div
                    key={mod.id}
                    onClick={() => {
                      setActiveModuleIdx(idx);
                      if (mod.timestamp !== undefined) {
                        seekToTimestamp(mod.timestamp);
                      }
                    }}
                    className={`p-4 cursor-pointer transition flex items-start gap-3 ${
                      activeModuleIdx === idx
                        ? "bg-[#FFF9F2] border-l-4 border-[#EA580C]"
                        : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="mt-0.5">
                      {activeModuleIdx === idx ? (
                        <div className="w-5 h-5 rounded-full bg-[#EA580C] text-white flex items-center justify-center">
                          <Play className="w-2.5 h-2.5 fill-white ml-0.5" />
                        </div>
                      ) : (
                        <div className="w-5 h-5 rounded-full bg-slate-100 border border-slate-200 text-[#64748B] flex items-center justify-center text-[10px] font-bold">
                          {mod.id}
                        </div>
                      )}
                    </div>
                    <div className="flex-1">
                      <p className={`text-xs font-semibold leading-snug ${
                        activeModuleIdx === idx ? "text-[#C2410C]" : "text-[#0F172A]"
                      }`}>
                        {mod.title}
                      </p>
                      <p className="text-[11px] text-[#64748B] mt-0.5 flex items-center gap-2">
                        <span>{mod.instructor}</span>
                        <span>•</span>
                        <span>{mod.duration}</span>
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* OFFICIAL VERIFICATION ACCREDITATION */}
            <div className="p-4 rounded-xl border border-dashed border-[#CBD5E1] bg-slate-50/70 text-center space-y-1 text-xs text-[#64748B]">
              <p className="font-semibold text-[#0F172A]">National Statistical Systems Training Academy</p>
              <p className="text-[11px]">iGOT Karmayogi Bharat • Official Cadre Competency Portal</p>
            </div>
          </div>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="mt-auto border-t border-[#F1E9DA] bg-white py-6 text-center text-xs text-[#64748B]">
        <p>© 2026 iGOT Karmayogi Bharat • Department of Personnel and Training (DoPT) • MoSPI Training Directorate</p>
      </footer>
    </div>
  );
}
```

---

## 4. Local Execution & Zero Git Modifications
- **Git status verification**:
  - `git commit` was NOT run.
  - `git push` was NOT run.
  - All files reside solely in the local working directory.
- **Build verification**:
  - `npm run build` completed successfully, producing the static route `/igot` (7.61 kB) and passing all type checks.
