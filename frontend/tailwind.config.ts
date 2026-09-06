import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ["var(--font-heading)", "Bebas Neue", "sans-serif"],
        body: ["var(--font-body)", "Inter", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "monospace"],
      },
      colors: {
        brand: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
          900: "#1E3A5F",
        },
        coral: {
          400: "#FB7185",
        },
        teal: {
          400: "#2DD4BF",
        },
        indigo: {
          500: "#6366F1",
        },
      },
      animation: {
        "marquee": "marquee 30s linear infinite",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "float": "float 6s ease-in-out infinite",
        "dash-flow": "dash-flow 1s linear infinite",
        "mesh-spin": "mesh-spin 40s linear infinite",
      },
      keyframes: {
        "mesh-spin": {
          "to": { transform: "rotate(360deg)" },
        },
        marquee: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
        "pulse-glow": {
          "0%, 100%": { boxShadow: "0 0 20px rgba(59, 130, 246, 0.3)" },
          "50%": { boxShadow: "0 0 40px rgba(59, 130, 246, 0.6)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "dash-flow": {
          "to": { strokeDashoffset: "-20px" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
