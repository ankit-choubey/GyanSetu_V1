import { Navbar } from "@/components/landing/Navbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { ProblemSection } from "@/components/landing/ProblemSection";
import { SolutionSection } from "@/components/landing/SolutionSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { HeroMomentSection } from "@/components/landing/HeroMomentSection";
import { SocialProofSection } from "@/components/landing/SocialProofSection";
import { TechStackSection } from "@/components/landing/TechStackSection";
import { Footer } from "@/components/landing/Footer";

export default function Home() {
  return (
    <main className="relative min-h-screen bg-white text-[#0F172A] overflow-x-hidden">
      {/* SECTION 01 — Fixed Frosted Glass Navbar */}
      <Navbar />

      {/* SECTION 02 — Hero Section */}
      <HeroSection />

      {/* Subtle Horizontal Gradient Divider */}
      <div className="section-divider" />

      {/* SECTION 03 — The Problem */}
      <ProblemSection />

      {/* Subtle Horizontal Gradient Divider */}
      <div className="section-divider" />

      {/* SECTION 04 — Our Solution (Closed Loop) */}
      <SolutionSection />

      {/* Subtle Horizontal Gradient Divider */}
      <div className="section-divider" />

      {/* SECTION 05 — How It Works (Timeline) */}
      <HowItWorksSection />

      {/* Subtle Horizontal Gradient Divider */}
      <div className="section-divider" />

      {/* SECTION 06 — The Hero Moment (Before / After) */}
      <HeroMomentSection />

      {/* Subtle Horizontal Gradient Divider */}
      <div className="section-divider" />

      {/* SECTION 07 — Social Proof + 3D DataMesh Visual */}
      <SocialProofSection />

      {/* Subtle Horizontal Gradient Divider */}
      <div className="section-divider" />

      {/* SECTION 09 — Technology Stack (Pipeline) */}
      <TechStackSection />

      {/* SECTION 10 — Dark CTA & Footer */}
      <Footer />
    </main>
  );
}
