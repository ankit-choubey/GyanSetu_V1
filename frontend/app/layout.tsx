import type { Metadata } from "next";
import { bebasNeue, inter, jetbrainsMono } from "@/lib/fonts";
import "./globals.css";

export const metadata: Metadata = {
  title: "GyanSetu — AI-Driven Competency Intelligence",
  description:
    "An AI-driven competency intelligence platform for India's official statistical workforce. Identify gaps, target interventions, and prove learning.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${bebasNeue.variable} ${inter.variable} ${jetbrainsMono.variable} scroll-smooth`}
    >
      <body className="min-h-screen bg-white text-[#0F172A] font-body antialiased overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
