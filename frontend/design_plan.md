# GyanSetu Frontend — Complete Landing Page Design Plan

> **Who is this for?** This document is written for a developer or an AI agent who has ZERO context about this project. Every section describes exactly what appears on screen, how every card looks, how every animation behaves frame-by-frame, what the user sees as they scroll, and what micro-interactions exist. Follow this document top-to-bottom to build the entire landing page.
>
> **Product:** GyanSetu — An AI-driven competency intelligence platform for India's official statistical workforce.
> **Tech Stack:** Next.js 14+ (App Router) · TypeScript · Tailwind CSS · Framer Motion · GSAP + ScrollTrigger · Spline 3D · Lucide React
> **Design Philosophy:** White canvas + Blue accents (Coursera-style). Geometric grid patterns (Linear/Raycast style). Bold uppercase typography. Structural scroll animations. No videos, no GIFs.

---

# ⚙️ PREREQUISITE: TOOLS TO INSTALL BEFORE BUILDING

Before writing any code, install the following. **Everything below is self-contained — you do NOT need any external plugin, private folder, or paid account to complete this build.** All animations, patterns, and performance techniques are fully specified inside this document.

1. **Lucide React Icons** — Install via `npm install lucide-react`. Import icons like `import { Brain, Target, Layers } from 'lucide-react'`. Use these throughout for all icon needs instead of custom SVGs where possible.

2. **(OPTIONAL — reference only, NOT required)** A guidance plugin named `modern-web-guidance-plugin` was used while authoring this document. It is **not** a build dependency and **must not** block your work. If (and only if) you happen to have it installed locally, you may skim its guides on `scroll-driven-animations`, `defer-rendering-heavy-content`, `break-up-long-tasks`, and `content-visibility` for extra background. If you do not have it — which is the normal case — **ignore this item entirely**; the patterns it describes are already written out in PART II and in each section below. Do not hardcode any machine-specific path (e.g. a `C:\Users\...` path) into the project.

> **Note on "View Transitions":** This project is a **single scrolling landing page with no route changes**, so the CSS/JS View Transitions API is **NOT** used. All perceived "transitions" are scroll-triggered reveals and smooth in-page anchor scrolling (see PART II). Do not attempt to implement `document.startViewTransition` or `@view-transition` — there are no routes to transition between.

---

# PART I — DESIGN SYSTEM (Every Token & Rule)

## 1.1 Color Palette

| Token Name | Hex Code | Where to Use It |
|------------|----------|-----------------|
| `--white` | `#FFFFFF` | Page background for sections 01, 02, 05, 09 |
| `--off-white` | `#F8FAFC` | Alternating section backgrounds (sections 03, 04, 08) |
| `--gray-50` | `#F1F5F9` | Card hover fill states, subtle backgrounds |
| `--gray-100` | `#E2E8F0` | ALL borders on cards, grid overlay lines, section dividers |
| `--gray-200` | `#CBD5E1` | Disabled states, dot pattern dots, secondary borders |
| `--gray-400` | `#94A3B8` | Muted text (captions, timestamps, labels) |
| `--gray-600` | `#475569` | Body text, paragraph descriptions |
| `--gray-900` | `#0F172A` | Primary headings, hero text, footer background |
| `--blue-50` | `#EFF6FF` | Icon container backgrounds, light card tints |
| `--blue-100` | `#DBEAFE` | Tag backgrounds, light fills, watermark number color |
| `--blue-400` | `#60A5FA` | Links (hover state), interactive accents |
| `--blue-500` | `#3B82F6` | Primary CTA buttons, active/selected states, logo color |
| `--blue-600` | `#2563EB` | CTA button hover state, strong accents |
| `--blue-700` | `#1D4ED8` | Deep blue gradient end |
| `--blue-900` | `#1E3A5F` | Dark CTA section background (Section 10) |
| `--teal-400` | `#2DD4BF` | 3D element secondary accent, success indicators |
| `--indigo-500` | `#6366F1` | Gradient mid-tone, 3D mesh glow |
| `--coral-400` | `#FB7185` | Warning/problem indicators, "before" state color |

### Gradient Tokens (copy these into globals.css as CSS custom properties)
```css
--gradient-hero: linear-gradient(135deg, #3B82F6 0%, #6366F1 50%, #2DD4BF 100%);
--gradient-cta: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
--gradient-3d-mesh: linear-gradient(135deg, #3B82F6, #6366F1, #2DD4BF, #FB7185);
--gradient-section-divider: linear-gradient(90deg, transparent 0%, #E2E8F0 50%, transparent 100%);
```

## 1.2 Typography System

| Element | Font Family | Weight | Desktop Size | Mobile Size | Text Transform | Letter Spacing |
|---------|-------------|--------|--------------|-------------|----------------|----------------|
| Hero H1 | **Bebas Neue** | 400 | `80px` / `5rem` | `48px` / `3rem` | `UPPERCASE` | `0.02em` |
| Section H2 | **Bebas Neue** | 400 | `56px` / `3.5rem` | `36px` / `2.25rem` | `UPPERCASE` | `0.02em` |
| Section Subtitle | **Inter** | 400 | `20px` / `1.25rem` | `16px` / `1rem` | `none` | `normal` |
| Body Text | **Inter** | 400 | `16px` / `1rem` | `14px` / `0.875rem` | `none` | `normal` |
| Card Title | **Inter** | 700 | `20px` / `1.25rem` | `18px` / `1.125rem` | `none` | `-0.01em` |
| Card Body | **Inter** | 400 | `15px` / `0.9375rem` | `14px` / `0.875rem` | `none` | `normal` |
| Badge / Tag | **Inter** | 600 | `12px` / `0.75rem` | `11px` | `UPPERCASE` | `0.08em` |
| Section Label (e.g. `[ 01 ]`) | **JetBrains Mono** | 500 | `13px` / `0.8125rem` | `12px` | `UPPERCASE` | `0.1em` |
| Nav Links | **Inter** | 500 | `15px` / `0.9375rem` | `14px` | `none` | `normal` |
| CTA Button Text | **Inter** | 600 | `16px` / `1rem` | `14px` | `none` | `0.01em` |
| Stat Numbers (big) | **Bebas Neue** | 400 | `72px` / `4.5rem` | `48px` / `3rem` | `none` | `0.02em` |
| Watermark Numbers (behind steps) | **Bebas Neue** | 400 | `120px` / `7.5rem` | `80px` / `5rem` | `none` | `0` |

### Google Fonts to Load (in `layout.tsx` via `next/font/google`)
```
Bebas Neue — weight 400
Inter — weights 400, 500, 600, 700
JetBrains Mono — weight 500
```

## 1.3 Spacing & Layout Tokens

| Token | Value | Notes |
|-------|-------|-------|
| Max content width | `1280px` | All section content is centered within this |
| Section vertical padding | `120px` desktop / `80px` mobile | Consistent breathing room between sections |
| Section horizontal padding | `24px` mobile / `48px` tablet / `0` desktop | Content is max-width centered on desktop |
| Card border-radius | `16px` | ALL cards, everywhere |
| Card padding | `32px` desktop / `24px` mobile | Internal padding for every card |
| Card border | `1px solid var(--gray-100)` | ALL cards use this exact border |
| Grid gap (between cards) | `24px` | Consistent gap in all grid layouts |
| Button border-radius | `9999px` (fully rounded / pill shape) | ALL buttons are pill-shaped |
| Button height | `40px` (small) / `48px` (large CTA) | Two button sizes |
| Button horizontal padding | `24px` (small) / `32px` (large CTA) | |

## 1.4 Geometric Design Language (What Makes the Page Look Premium)

These decorative patterns appear throughout the page. The implementing agent should build them as **reusable components** (`GridOverlay.tsx`, `DotPattern.tsx`) and layer them behind content using `position: absolute` with `z-index: 0`.

### Grid Overlay Lines
- Thin `1px` vertical and horizontal lines in `var(--gray-100)` color
- Lines spaced `80px` apart, forming a subtle engineering-paper-like grid
- Visible behind the Hero section and Problem section
- Built with CSS: repeating `linear-gradient` or absolute-positioned `<div>`s
- **Animation:** On page load, vertical lines draw in from top to bottom (`scaleY: 0 → 1`, `transformOrigin: top`), staggered `0.2s` apart — use GSAP ScrollTrigger

### Dot Patterns
- Tiny dots (`1px` radius) in `var(--gray-200)` color
- Spaced at `24px` intervals, forming a dot-grid
- Built with CSS: `background: radial-gradient(circle, var(--gray-200) 1px, transparent 1px); background-size: 24px 24px;`
- Used in Hero section and CTA section backgrounds

### Section Labels
- Format: `[ 01 ] SECTION NAME` — e.g. `[ 02 ] THE PROBLEM`
- Font: JetBrains Mono, 13px, weight 500, uppercase, letter-spacing `0.1em`
- Color: `var(--gray-400)`
- Position: Top-left of each section's content area, with `margin-bottom: 16px` before the heading
- **Animation:** Slides in from left on scroll — `x: -30 → 0`, `opacity: 0 → 1`, tied to scroll

### Corner Markers (Optional Enhancement)
- Small `+` symbols at grid line intersections in the background
- Color: `var(--gray-200)`, font-size `10px`
- Creates a technical/blueprint aesthetic

### Section Dividers
- Between every section, place a horizontal gradient line:
  `background: var(--gradient-section-divider)` — transparent at edges, `var(--gray-100)` in the center
- Height: `1px`, width: `100%`
- This creates visual continuity between sections without hard breaks

## 1.5 The "Valley.co Reference" (described in full — NO image file required)

Earlier drafts referenced a screenshot at `assets/image.png`. **That file is not part of this build and does not exist in the repo.** Do not look for it, import it, or block on it. Everything you need from that reference is written out here. There are exactly two patterns borrowed from it:

**(A) The Hero input-bar pattern** (used in Section 02):
- A single rounded "pill/rounded-rectangle" container that *looks* like a search/email input with a solid button fused to its right end.
- Left ~75% of the width: muted placeholder text (an email-looking string), left-aligned, vertical-centered.
- Right ~25%: a solid dark filled button with short white label text, fully inside the container's padding (the button's rounded corners nest inside the outer container's corners).
- The whole thing reads as one unit: outer border `1px solid var(--gray-200)`, radius `12px`, small internal padding, the button radius `8px`. It is **decorative only** — it does not submit anything.

**(B) The "floating node cards connected by thin lines" pattern** (used in Section 03):
- A central focal graphic with several small info cards positioned around it (not in a grid — offset at varied angles).
- Each surrounding card is a small white rounded card with a light border and soft shadow, containing one icon + one short stat/quote.
- Thin **dashed** lines connect each surrounding card back toward the center, like nodes wired to a hub.
- Exact positions, sizes, and responsive behavior for this are fully specified in Section 03 below — you do not need the screenshot to reproduce it.

Wherever the text below says "Valley.co style / see the reference," it means exactly these two patterns as described here.

---

# PART II — ANIMATION SYSTEM (Every Animation Explained)

## 2.1 Animation Libraries & Their Roles

| Library | Install Command | What It Does | When to Use |
|---------|----------------|--------------|-------------|
| **Framer Motion** | `npm install framer-motion` | Component-level enter/exit animations, hover effects, layout transitions, in-view triggers | Use for: text fade-ins, card reveals, button hover states, number counters |
| **GSAP + ScrollTrigger** | `npm install gsap` | Scroll-driven animations, timeline sequencing, pinned sections, parallax | Use for: grid line drawing, timeline drawing, pipeline flow, section-level scroll reveals |
| **@splinetool/react-spline** | `npm install @splinetool/react-spline` | Embedding interactive 3D scenes from Spline | Use for: the 3D object in Section 07 |
| **Lucide React** | `npm install lucide-react` | Icon library with 1000+ clean line icons | Use for: every icon in every section |

## 2.2 Global Animations (Apply Across All Sections)

### Page Load Sequence (What happens when the user first opens the page)
1. **Frame 0–0.3s:** Entire page is `opacity: 0`, `filter: blur(20px)` — everything is invisible and blurry
2. **Frame 0.3–0.8s:** Page fades in — `opacity: 0 → 1`, `filter: blur(20px) → blur(0)` with `ease: easeOut`
3. **Frame 0.5–1.5s:** Navbar slides down from above — `y: -64 → 0`, `opacity: 0 → 1`
4. **Frame 0.8–2.0s:** Hero section elements appear in staggered sequence (see Section 02 animations below)

**Implementation:** Wrap the entire `<main>` in a Framer Motion `<motion.div>` with `initial={{ opacity: 0, filter: 'blur(20px)' }}` and `animate={{ opacity: 1, filter: 'blur(0px)' }}` with `transition={{ duration: 0.8, ease: 'easeOut' }}`.

### Scroll-Triggered Fade-Up (Default for all content blocks)
When ANY content block (heading, card, paragraph, image) enters the viewport:
- **Start state:** `y: 40px` (shifted down), `opacity: 0` (invisible)
- **End state:** `y: 0px` (normal position), `opacity: 1` (visible)
- **Duration:** `0.6s`
- **Ease:** `easeOut`
- **Trigger:** When element is 20% visible in viewport
- **Stagger:** If multiple children (like a grid of cards), each child delays by `0.1s`

**Implementation:** Use Framer Motion's `whileInView` prop:
```tsx
<motion.div
  initial={{ y: 40, opacity: 0 }}
  whileInView={{ y: 0, opacity: 1 }}
  transition={{ duration: 0.6, ease: 'easeOut' }}
  viewport={{ once: true, amount: 0.2 }}
>
```

### Smooth Scroll (Global)
- Add `scroll-behavior: smooth` to `<html>` in `globals.css`
- Navbar links use anchor `href="#section-id"` to jump between sections smoothly

### Counter Animation (For any large stat number)
When a number like `73%` or `0.74` enters the viewport:
- Starts at `0`, counts up to the target number over `2s`
- Uses `easeInOut` easing (starts slow, speeds up, slows down at end)
- Number should display with the correct format (e.g., `0.42` not `42`)

**Implementation:** Use Framer Motion's `useMotionValue` + `useTransform` + `useInView`:
```tsx
const count = useMotionValue(0);
const rounded = useTransform(count, (v) => Math.round(v));
// When in view, animate count from 0 to target
useEffect(() => {
  if (isInView) {
    animate(count, targetNumber, { duration: 2, ease: 'easeInOut' });
  }
}, [isInView]);
```

Build this as a reusable `<AnimatedCounter target={73} suffix="%" />` component.

## 2.3 Animation Library Ownership (READ THIS — prevents conflicting animations)

Three animation systems are used. To stop two libraries from fighting over the same element, follow this **strict ownership rule**. Each visual effect is owned by exactly ONE library:

| Effect type | OWNER (use only this) | Never use for this |
|-------------|----------------------|--------------------|
| Element enters viewport on scroll (fade-up, slide-in, blur-in, scale-in) | **Framer Motion** `whileInView` | GSAP, CSS |
| Scroll-*scrubbed* progress (timeline line drawing, parallax tied to scroll position, pipeline reveal that tracks the scrollbar) | **GSAP ScrollTrigger** (`scrub: true`) | Framer Motion |
| Infinite idle loops (float/bob, marquee, pulse-glow, dashed-line flow, active-node cycle) | **CSS `@keyframes`** (or GSAP only when the loop must sequence across multiple elements, e.g. the Solution active-node cycle and the bento timeline dots) | Framer Motion `animate` loops |
| Hover / press / focus states | **CSS transitions** | Framer Motion, GSAP |
| Number count-up | **Framer Motion** (`AnimatedCounter`) | — |

### The one hard conflict rule
**A single DOM element must never be animated by both Framer Motion and GSAP at the same time.** Both write to `transform`/`opacity` and will overwrite each other, causing flicker.

- If an element needs BOTH an entrance reveal AND a scroll-scrubbed effect (e.g. a "How It Works" text block that fades up *and* has a parallax watermark behind it): put the **entrance** on the element itself via Framer Motion, and put the **scrubbed parallax** on a *separate child element* (the watermark `<div>`) owned by GSAP. Never target the same node twice.
- Where a section table below lists an animation under "Framer Motion" AND something scroll-scrubbed, assume they are on different nested elements.
- If a spec ever appears ambiguous, the table above wins: entrance → Framer, scrubbed → GSAP, infinite idle → CSS.

## 2.4 Reduced Motion (`prefers-reduced-motion`) — REQUIRED, not optional

This page has continuous motion, so it **must** respect users who ask their OS to reduce motion. Implement all three layers:

1. **Global CSS kill-switch** — add to `globals.css`:
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
}
```
This instantly disables every CSS loop (float, marquee, pulse-glow, dash-flow) and hover transitions become instant.

2. **Framer Motion** — read the user preference and skip enter animations. Build a tiny hook and use it everywhere you set `initial`/`whileInView`:
```tsx
import { useReducedMotion } from 'framer-motion';
// inside a component:
const reduce = useReducedMotion();
// then:
initial={reduce ? false : { y: 40, opacity: 0 }}
whileInView={reduce ? {} : { y: 0, opacity: 1 }}
```
When `reduce` is true, content simply appears in its final state — no movement, no blur.

3. **GSAP** — guard every ScrollTrigger/timeline setup so scrubbed and looping animations do not run:
```tsx
import gsap from 'gsap';
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduce) {
  // build ScrollTriggers / timelines here
} else {
  // set elements to their final visible state directly, e.g.:
  gsap.set('.timeline-line', { scaleY: 1 });
}
```
**Rule:** with reduced motion on, the page must be fully readable and complete — every number shows its final value, every element is in its final position. Nothing should be stuck invisible waiting for an animation that never runs.

## 2.5 Page-Load Blur — SCOPE IT, don't blur the whole page

The page-load sequence in 2.2 says to blur `<main>`. **Do NOT apply `filter: blur()` to the entire `<main>` wrapper** — a full-page blur forces the browser to rasterize everything (including the Spline canvas and all GSAP layers) every frame, which janks on load and can wash out the whole viewport.

Instead:
- Apply the blur-in ONLY to the **navbar + hero content** (the above-the-fold elements the user actually sees at t=0). Use a `<motion.div>` wrapping just the hero's text/label/input group.
- Everything below the fold uses the normal per-section scroll reveals (2.2) and needs no load-time blur.
- The blur value stays modest: `blur(12px) → blur(0)` over `0.6s`, not `20px`. Animate `filter` and `opacity` only; never blur an element that contains the Spline `<canvas>`.
- If `prefers-reduced-motion` is set, skip the blur entirely (see 2.4).

## 2.6 Responsive Breakpoints (single source of truth)

Every section MUST use these exact breakpoints — do not invent per-section ones. These map to Tailwind's defaults so you can use `sm:` `md:` `lg:` `xl:` directly.

| Name | Range | Tailwind prefix | Layout intent |
|------|-------|-----------------|---------------|
| Mobile | `< 640px` (base) | (none) | Single column, everything stacks vertically |
| SM | `≥ 640px` | `sm:` | Still largely single-column; larger type/spacing |
| Tablet (MD) | `≥ 768px` | `md:` | 2-column grids appear; navbar shows full links |
| Desktop (LG) | `≥ 1024px` | `lg:` | Full multi-column layouts, absolute-positioned decorations enabled |
| Wide (XL) | `≥ 1280px` | `xl:` | Max content width `1280px` reached; centered |

**Test at exactly these widths:** `375px`, `768px`, `1024px`, `1440px`.

**Default responsive collapse rule (applies to every section unless that section overrides it):**
- Below `1024px`, any layout described as "floating / absolutely-positioned / orbiting around a center" collapses to a **simple vertical stack** in normal document flow (see per-section mobile rules for 03, 04, 05).
- Below `768px`, all multi-column grids become a single column.
- Absolute positioning, dashed connector lines, and orbit layouts are a **desktop-only (`lg:` and up) enhancement**. On mobile they are removed from the DOM or hidden, not merely shrunk.

## 2.7 Z-Index Layering Map (single source of truth)

Use ONLY these z-index values. Never invent ad-hoc ones. Decorative backgrounds are always behind content.

| Layer | z-index | What lives here |
|-------|---------|-----------------|
| Decorative backgrounds | `0` | `GridOverlay`, `DotPattern`, watermark numbers, section accent gradients |
| Connector lines / SVG behind cards | `1` | Problem-section dashed lines, Solution loop lines, Tech-stack flow lines |
| Section content (default) | `10` | All headings, cards, text, buttons, the Spline canvas |
| Floating/orbiting cards (Problem sec.) | `20` | The 6 problem bubbles (must sit above their connector lines) |
| Sticky navbar | `50` | `Navbar.tsx` |
| Mobile nav drawer / any overlay | `60` | Full-screen mobile menu |

Within a section, set `position: relative; z-index: 10;` on the content wrapper and `position: absolute; inset: 0; z-index: 0;` on the decoration wrapper. Backgrounds must always use `pointer-events: none` so they never intercept clicks.

## 2.8 Overflow / No-Horizontal-Scroll Rule (prevents mobile side-scroll)

Floating, orbiting, marquee, and off-canvas-animated elements are the #1 cause of accidental horizontal scrolling. Enforce:

1. In `globals.css`: `html, body { overflow-x: hidden; max-width: 100%; }`.
2. Any section that contains absolutely-positioned decorations or a marquee gets `position: relative; overflow-x: clip;` (prefer `clip` over `hidden` so it doesn't create an unwanted scroll container; fall back to `hidden` if `clip` is unsupported).
3. Entrance animations that start off-screen (`x: -40`, `x: 60`, etc.) must animate *within* a container that clips overflow — never let a pre-animation element widen the page.
4. After building each section, verify at `375px` that the page has **no horizontal scrollbar** (`document.documentElement.scrollWidth === window.innerWidth`).

## 2.9 Data Honesty — Label every number as ILLUSTRATIVE or MEASURED

Several numbers in this document are **design/demo values used to make the UI look real**, not verified project metrics. To avoid shipping a page that misrepresents the project, follow this rule:

- Treat **every** stat in this document as **`ILLUSTRATIVE` (demo/placeholder)** unless the person building the site has a real, verifiable source for it.
- Numbers currently written as design values include (non-exhaustive): `72% / 73%` training-result and completion figures, `41%`, `0.42 → 0.74` mastery, `6 evidence types`, `3 AI agents`, and **`103 tests passing`**.
- **`103 TESTS PASSING` is the most sensitive one.** Do NOT present it as a verified metric unless the repository actually has a passing test suite that has been run and counted. If unverified, either (a) remove the stat, or (b) relabel the tile to something non-numeric-claiming like "AUTOMATED TESTS" or "QUALITY-CHECKED PIPELINE".
- **How to handle in code:** For any number without a confirmed source, add an HTML comment at its usage site: `{/* ILLUSTRATIVE — replace with measured value or remove before any public/demo/judge-facing use */}`. If you DO have a real measured value, replace the number and change the comment to `{/* MEASURED — source: <where> */}`.
- The person integrating this page for SIH judging must consciously confirm or replace each number. This document does not certify any of them as true.

---

# PART III — LANDING PAGE SECTIONS (Exhaustive Section-by-Section Blueprint)

## Section Order Overview

```
┌──────────────────────────────────────────────────────────────┐
│  SECTION 01  │  NAVBAR (Sticky, blur-glass, always visible)  │
├──────────────────────────────────────────────────────────────┤
│  SECTION 02  │  HERO (AI Learning — Valley.co inspired)      │
├──────────────────────────────────────────────────────────────┤
│  SECTION 03  │  THE PROBLEM (Centered SVG + floating UI)     │
├──────────────────────────────────────────────────────────────┤
│  SECTION 04  │  OUR SOLUTION (Closed Loop Diagram)           │
├──────────────────────────────────────────────────────────────┤
│  SECTION 05  │  HOW IT WORKS (6-Step Vertical Timeline)      │
├──────────────────────────────────────────────────────────────┤
│  SECTION 06  │  THE HERO MOMENT (Before/After Cards)         │
├──────────────────────────────────────────────────────────────┤
│  SECTION 07  │  SOCIAL PROOF + SPLINE 3D (Stripe Style)      │
├──────────────────────────────────────────────────────────────┤
│  SECTION 08  │  DIFFERENTIATORS (Bento Grid Features)        │
├──────────────────────────────────────────────────────────────┤
│  SECTION 09  │  TECHNOLOGY STACK (Pipeline Architecture)     │
├──────────────────────────────────────────────────────────────┤
│  SECTION 10  │  CTA + FOOTER (Dark Section)                  │
└──────────────────────────────────────────────────────────────┘
```

---

## SECTION 01 — NAVBAR

**File:** `components/landing/Navbar.tsx`
**Scroll ID:** None (always visible at top)

### What the User Sees
A thin glass-like navigation bar pinned to the top of the screen. It has a frosted glass effect so page content is softly visible through it. The logo is on the left, navigation links are centered, and action buttons are on the right.

### Exact Layout Specification
```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  GYANSETU          Features  How It Works  Technology  About    Login  [Get Started]  │
│  (Bebas Neue)      (Inter 500, gray-600)                        (text)  (filled btn)  │
│                                                                         │
│─────────────────────────────────────────────────────────────────────────│  ← 1px border-bottom
```

- **Position:** `fixed`, `top: 0`, `left: 0`, `right: 0`, `z-index: 50`
- **Height:** `64px`
- **Background:** `rgba(255, 255, 255, 0.8)` with `backdrop-filter: blur(12px)` — creates frosted glass
- **Border bottom:** `1px solid var(--gray-100)`
- **Content container:** max-width `1280px`, centered, `padding: 0 24px`
- **Logo:** Text "GYANSETU" in Bebas Neue font, color `var(--blue-500)`, font-size `24px`
- **Nav links:** `Features` | `How It Works` | `Technology` | `About` — Inter 500, 15px, `var(--gray-600)`, gap `32px`
- **Login:** Plain text link, Inter 500, `var(--gray-600)`
- **Get Started:** Pill button, `background: var(--gradient-cta)`, color white, height `40px`, padding `0 24px`, border-radius `9999px`
- **Mobile (< 768px):** Hide nav links and show a hamburger icon (`Menu` from Lucide). Tapping it opens a full-screen slide-out drawer with the links stacked vertically.

### Animations & Micro-Interactions

| What | When | Animation | Library | Exact Values |
|------|------|-----------|---------|--------------|
| Navbar entrance | Page load | Slides down from above | Framer Motion | `y: -64 → 0`, `opacity: 0 → 1`, `duration: 0.5s`, `delay: 0.3s` |
| Scroll hide/show | User scrolls | Hides when scrolling down, shows when scrolling up | Framer Motion `useScroll` + `useMotionValueEvent` | Track `scrollY` direction. If going down → `y: -64` (hide). If going up → `y: 0` (show). Transition: `0.3s ease` |
| Nav link hover | Mouse hover | An underline grows from left to right under the link | CSS transition | `::after` pseudo-element, `scaleX: 0 → 1`, `transform-origin: left`, `transition: 0.3s ease` |
| CTA button hover | Mouse hover | Button slightly enlarges and shadow deepens | CSS transition | `transform: scale(1.03)`, `box-shadow: 0 4px 20px rgba(59,130,246,0.3)`, `transition: 0.2s ease` |
| CTA button press | Mouse click | Button scales down briefly | CSS | `transform: scale(0.97)`, `transition: 0.1s` |

---

## SECTION 02 — HERO SECTION

**File:** `components/landing/HeroSection.tsx`
**Scroll ID:** `#hero`
**Background:** White with geometric grid overlay + dot pattern

### What the User Sees
The first thing you see after the page loads. A massive headline in bold uppercase letters, centered on the page. Below it, a subtitle explaining what GyanSetu does. Below that, a stylized input/search bar (inspired by the Valley.co "Find my buyer" pattern — see §1.5 pattern A, fully described in words). Below the input bar, a social proof stat line. The background has subtle engineering-paper-style grid lines that animate in on page load.

### Exact Layout Specification
```
                              ┌────────────────────────────────────────┐
                              │  [ 01 ] COMPETENCY INTELLIGENCE        │  ← Section label
                              │                                        │
                              │       IDENTIFY GAPS.                   │  ← Line 1 (Bebas Neue 80px)
                              │       TARGET INTERVENTIONS.            │  ← Line 2
                              │       PROVE LEARNING.                  │  ← Line 3
                              │                                        │
                              │  GyanSetu uses AI-driven evidence      │  ← Subtitle (Inter 20px, gray-600)
                              │  fusion to identify, fix, and verify   │
                              │  competency gaps in India's official   │
                              │  statistical workforce.                │
                              │                                        │
                              │  ┌────────────────────────────────┐    │
                              │  │  officer.sharma@mospi.gov.in   │ [Find my gap]  │  ← Stylized input bar
                              │  └────────────────────────────────┘    │
                              │                                        │
                              │  ● NSSTA IMPROVED 72% TRAINING RESULTS │  ← Social proof line (like Valley.co)
                              │                                        │
                              └────────────────────────────────────────┘
```

- **Container:** `min-height: 100vh`, `display: flex`, `align-items: center`, `justify-content: center`, `flex-direction: column`, `text-align: center`
- **Background layer 1 (behind content):** `GridOverlay` component — thin `1px` lines at `80px` intervals in `var(--gray-100)`
- **Background layer 2 (behind content):** `DotPattern` component — dots at `24px` intervals in `var(--gray-200)`
- **Section label:** `[ 01 ] COMPETENCY INTELLIGENCE` — JetBrains Mono, 13px, uppercase, `var(--gray-400)`
- **Hero headline:** 3 lines, each on its own line. Bebas Neue, 80px, uppercase, `var(--gray-900)`, `line-height: 1.1`
- **Subtitle:** Inter, 20px, `var(--gray-600)`, max-width `600px`, `line-height: 1.6`, centered
- **Input bar (Valley.co style):**
  - A `div` styled as an input field with a button inside
  - Border: `1px solid var(--gray-200)`, border-radius `12px`, padding `8px 8px 8px 20px`
  - Left side: Placeholder text "officer.sharma@mospi.gov.in" in Inter 400, gray-400
  - Right side: Black/dark filled button with white text "Find my gap" — like the Valley.co screenshot
  - Width: `480px` max, centered
  - **Note:** This is purely decorative / illustrative on the landing page — it doesn't actually submit
- **Social proof line:** Below the input bar, a small line of text with a tiny avatar circle and text like "NSSTA IMPROVED 72% TRAINING RESULTS" — Inter 600, 12px, uppercase, gray-600. The stat number `72%` is in `var(--blue-500)`. **`72%` is ILLUSTRATIVE (§2.9)** — replace with a real figure or soften the wording (e.g. "faster gap identification") before any judge-facing use; do not present it as a measured outcome without a source.

### Animations (Exact Sequence — Timed from Page Load)

| # | Element | Delay | Animation | Duration | Library |
|---|---------|-------|-----------|----------|---------|
| 1 | Background grid lines | `0s` | Vertical lines draw from top to bottom (`scaleY: 0 → 1`) | `1.5s` per line, stagger `0.2s` | GSAP |
| 2 | Section label `[ 01 ]` | `0.2s` | Slides in from left + fades in | `0.5s` | Framer Motion: `x: -40 → 0`, `opacity: 0 → 1` |
| 3 | Headline Line 1 "IDENTIFY GAPS." | `0.3s` | Blur-in + fade up | `0.6s` | Framer Motion: `filter: blur(20px) → blur(0)`, `y: 30 → 0`, `opacity: 0 → 1` |
| 4 | Headline Line 2 "TARGET INTERVENTIONS." | `0.5s` | Same blur-in + fade up | `0.6s` | Framer Motion |
| 5 | Headline Line 3 "PROVE LEARNING." | `0.7s` | Same blur-in + fade up | `0.6s` | Framer Motion |
| 6 | Subtitle paragraph | `0.9s` | Fade up | `0.5s` | Framer Motion: `y: 20 → 0`, `opacity: 0 → 1` |
| 7 | Input bar | `1.1s` | Scale-in + fade | `0.4s` | Framer Motion: `scale: 0.95 → 1`, `opacity: 0 → 1` |
| 8 | Social proof stat line | `1.3s` | Fade-in | `0.4s` | Framer Motion: `opacity: 0 → 1` |

### Micro-Interactions
- **Input bar hover:** Border color changes from `gray-200` to `gray-400`, subtle shadow appears. `transition: 0.2s ease`.
- **"Find my gap" button hover:** Background slightly lightens, `transform: scale(1.02)`.

---

## SECTION 03 — THE PROBLEM

**File:** `components/landing/ProblemSection.tsx`
**Scroll ID:** `#problem`
**Background:** `var(--off-white)` (#F8FAFC)

### What the User Sees
A section that dramatically presents the problems with current training systems. In the CENTER of the viewport, there is a large SVG vector illustration (e.g., a frustrated person at a desk, or a broken loop diagram). AROUND this central illustration, floating UI elements orbit: chat bubbles with problem quotes, data stat cards, warning icons — all connected by thin dashed lines radiating from the center (the Valley.co node pattern — see §1.5 pattern B, fully described in words). Above everything, a bold headline reads "COMPLETION ≠ COMPETENCY."

### Exact Layout Specification
```
          [ 02 ] THE PROBLEM

         COMPLETION ≠ COMPETENCY                    ← Heading (Bebas Neue 56px)

    ┌─────────────┐                    ┌──────────────┐
    │ 💬 "I passed │                    │ 73% courses  │
    │  14 courses  │╌╌╌╌╌╌┐            │ completed,   │
    │  but can't   │      │            │ gaps unseen" │
    │  sample."    │      │            └──────┬───────┘
    └──────────────┘      │                   │
                          │                   │
    ┌──────────────┐      ▼                   ▼
    │ ⚠ 0 subskill │╌╌╌ [CENTER SVG] ╌╌╌╌╌╌╌╌╌╌┐
    │ gaps found   │    (large vector            │
    └──────────────┘     illustration)    ┌──────▼──────┐
                          │               │ 100% same   │
                          │               │ training    │
    ┌──────────────┐      │               │ for all     │
    │ 🔒 0 retention│╌╌╌╌╌┘               └─────────────┘
    │ checks done  │
    └──────────────┘
```

- **Center illustration — EXACT implementation (pick this one, do NOT freestyle a custom SVG):** Build a **composed Lucide-icon graphic**, not hand-drawn vector art. This is chosen because it is deterministic and reproducible. Spec:
  - A `280px × 280px` (mobile `200px × 200px`) square wrapper, `position: relative`, centered in the section, `z-index: 10`.
  - **Center:** a circle `120px` diameter, `background: var(--blue-50)`, `border: 1px solid var(--blue-100)`, containing a Lucide `BookOpen` icon at `48px` in `var(--blue-500)`.
  - **A "broken loop" ring:** an SVG circle (`viewBox 0 0 280 280`, `r=110`, centered) drawn as a **dashed** stroke (`stroke: var(--gray-200)` = `#CBD5E1`, `stroke-width: 2`, `stroke-dasharray: 10 8`) with an intentional **gap** — leave a ~60° arc of the ring undrawn at the top-right to signal "broken loop" (achieve via `stroke-dasharray` + `stroke-dashoffset`, or simply draw an SVG arc `path` that stops short of full circle).
  - **Two overlaid status icons** pinned on the ring to reinforce the "broken" idea: a Lucide `XCircle` (`28px`, `var(--coral-400)`) at the top-right gap, and a Lucide `AlertTriangle` (`24px`, `var(--coral-400)`) at the bottom-left of the ring.
  - That is the entire central graphic — one blue hub + one broken dashed ring + two coral status icons. No other interpretation.

- **Floating UI elements (6 total) — DESKTOP (`lg:` ≥ 1024px only):** These are small cards positioned absolutely around the center graphic. Use a `position: relative` stage of fixed size **`720px` wide × `520px` tall**, centered; position each card with `position: absolute` using the exact top/left percentages below (percentages are of the stage box; each card is anchored by its own center via `transform: translate(-50%, -50%)`). Stage `z-index`: cards `20`, center graphic `10`, dashed lines `1` (see §2.7).

  | # | Card center — `left`, `top` (% of stage) | Corner it reads as |
  |---|------------------------------------------|--------------------|
  | 1 | `12%`, `18%`  | Top-left |
  | 2 | `88%`, `18%`  | Top-right |
  | 3 | `6%`,  `50%`  | Middle-left |
  | 4 | `94%`, `50%`  | Middle-right |
  | 5 | `18%`, `84%`  | Bottom-left |
  | 6 | `82%`, `84%`  | Bottom-right |

  - Each card: fixed `width: 180px`, auto height, styling as specified below.
  - **Dashed connector lines:** one SVG (`position:absolute; inset:0; width:100%; height:100%; z-index:1; pointer-events:none`) sized to the stage's pixel box; draw a `<line>` from the stage center (`50%,50%`) to each card's center coordinate above. `stroke: var(--gray-200)`, `stroke-width: 1`, `stroke-dasharray: 4 4`.

- **TABLET (`md:` 768–1023px):** Abandon the orbit. Render the center graphic on top, then the 6 cards in a **2-column grid** (`gap: 24px`) below it. **No absolute positioning, no dashed lines** (remove the connector SVG from the DOM at this breakpoint).

- **MOBILE (`< 768px`):** Center graphic (`200px`) on top, then the 6 cards in a **single vertical column** (`gap: 16px`), full width (max `340px`, centered). No absolute positioning, no dashed lines, no float/bob idle animation (see §2.4/§2.8 — this prevents horizontal scroll).

- **Floating UI elements — shared card styling (all breakpoints):** small cards/bubbles:
  - Each bubble: `background: white`, `border: 1px solid var(--gray-100)`, `border-radius: 12px`, `padding: 16px`, `box-shadow: 0 2px 8px rgba(0,0,0,0.05)`
  - Contains: An icon (from Lucide) + a stat or quote text
  - Size: `~180px wide`, auto height
  - Connected to center by thin dashed lines (`1px dashed var(--gray-200)`) — use SVG `<line>` elements or absolute-positioned divs with dashed borders

- **The 6 floating problem bubbles:**

| # | Icon (Lucide) | Content | Position (relative to center) |
|---|---------------|---------|------------------------------|
| 1 | `MessageSquare` | "I passed 14 courses but can't sample." | Top-left |
| 2 | `BarChart3` | `73%` courses completed, gaps unmeasured | Top-right |
| 3 | `AlertTriangle` | `0` subskill gaps identified by iGOT | Middle-left |
| 4 | `Equal` | `100%` same training for all roles | Middle-right |
| 5 | `Lock` | `0` retention checks performed | Bottom-left |
| 6 | `EyeOff` | `41%` capability gaps unseen by directors | Bottom-right |

- **Stat numbers inside bubbles:** Use `Bebas Neue`, `36px`, `var(--blue-500)` for the numbers. Use `Inter 400`, `13px`, `var(--gray-600)` for the description below. **The bubble numbers (`73%`, `0`, `100%`, `0`, `41%`) are ILLUSTRATIVE (§2.9)** — they dramatize the problem, not measured findings. Keep them framed as the *problem with legacy systems* (not GyanSetu's results), and add the §2.9 comment at each.

### Animations (Scroll-Triggered)

| # | Element | Animation | Trigger | Library | Exact Values |
|---|---------|-----------|---------|---------|--------------|
| 1 | Section label `[ 02 ]` | Slide in from left | Scroll into view | Framer Motion | `x: -30 → 0`, `opacity: 0 → 1` |
| 2 | Heading "COMPLETION ≠ COMPETENCY" | Blur-in | Scroll into view | Framer Motion | `filter: blur(15px) → 0`, `opacity: 0 → 1`, `duration: 0.6s` |
| 3 | Center SVG illustration | Scale-in from center | Scroll into view | Framer Motion | `scale: 0.8 → 1`, `opacity: 0 → 1`, `duration: 0.7s` |
| 4 | Dashed connection lines | Draw-in (line grows from center outward) | After center SVG appears | GSAP | `stroke-dashoffset: 100% → 0%`, `duration: 0.8s`, stagger `0.1s` |
| 5 | Floating bubbles | Pop in from center with slight overshoot | After lines draw | Framer Motion | `scale: 0 → 1.05 → 1` (spring), `opacity: 0 → 1`, stagger `0.15s` per bubble |
| 6 | Stat numbers inside bubbles | Counter animation | After bubble appears | AnimatedCounter | `0 → target`, `duration: 2s` |

### Micro-Interactions
- **Bubble hover:** `translateY(-4px)`, border color changes to `var(--blue-100)`, shadow deepens to `0 4px 16px rgba(0,0,0,0.08)`. `transition: 0.3s ease`.
- **Floating idle animation:** Each bubble gently bobs up and down `translateY(±3px)` on a loop (CSS `@keyframes float`, 6s infinite, staggered start times so they don't move in sync).

---

## SECTION 04 — OUR SOLUTION (The Closed Loop)

**File:** `components/landing/SolutionSection.tsx`
**Scroll ID:** `#solution`
**Background:** White

### What the User Sees
A section explaining GyanSetu's core mechanism: the closed loop. At the top, a heading with subtitle. In the middle, 5 connected nodes in a horizontal flow showing the cycle: Assess → Identify Gap → Recommend → Intervene → Verify, with animated dashed lines connecting them that "flow" continuously. Below the loop diagram, two comparison cards side-by-side: "Regular LMS" (dull) vs "GyanSetu" (vibrant).

### Exact Layout Specification
```
                     [ 03 ] THE SOLUTION

              THE EVIDENCE-DRIVEN CLOSED LOOP         ← Heading (Bebas Neue 56px)

    Not another LMS. A continuous cycle that identifies,  ← Subtitle (Inter 20px)
    fixes, and verifies competency — forever.

    ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐    ┌───────┐
    │ 🎯    │╌╌╌→│ 🔍    │╌╌╌→│ 💡    │╌╌╌→│ 🔧    │╌╌╌→│ ✅    │
    │Assess │    │Find   │    │Recom- │    │Inter- │    │Verify │
    │       │    │Gap    │    │mend   │    │vene   │    │       │
    └───────┘    └───────┘    └───────┘    └───────┘    └───────┘
         ↑                                                    │
         └────────────────────────────────────────────────────┘  ← loop-back arrow

    ┌──────────────────────┐    ┌──────────────────────────┐
    │   REGULAR LMS        │    │    GYANSETU               │
    │                      │    │                           │
    │ "You completed       │    │ "For your role as JSO:    │
    │  14 courses.         │    │  Mastery in Sampling      │
    │  Good job."          │    │  Design is 0.52.          │
    │                      │    │  Gap: Variance Estimation │
    │ ❌ No gap ID         │    │  Next: NSSTA Practical"   │
    │ ❌ No evidence       │    │                           │
    │ ❌ No retention      │    │ ✅ Subskill precision     │
    │                      │    │ ✅ 6 evidence types       │
    │                      │    │ ✅ Scheduled re-testing   │
    └──────────────────────┘    └──────────────────────────┘
      border: gray-200            border: blue-500
      bg: white                   bg: blue-50
```

- **Loop nodes:** 5 rounded-square nodes (`80px × 80px`, `border: 1px solid var(--gray-100)`, `border-radius: 16px`, `background: white`). Each has a Lucide icon on top (24px, gray-600) and a label below (Inter 600, 13px).
- **Connecting lines:** SVG dashed lines between nodes. Stroke: `var(--gray-200)`, stroke-dasharray: `6 4`, animated dash offset flowing left-to-right (CSS, see §2.3 — this loop is CSS-owned).
- **Loop-back path — EXACT geometry (DESKTOP `lg:` ≥ 1024px):** Draw it as ONE SVG that sits *behind* the node row (`z-index: 1`, `pointer-events:none`), spanning the full node-row width plus a curve underneath.
  - The 5 nodes sit in a row of total width `W` (the `1280px`-capped content width; treat `W = 1000px` for the reference math, scale with the container). Node centers are evenly spaced; node 1 center at `x1`, node 5 center at `x5`, all at vertical center `yTop` of the node row.
  - SVG element: `viewBox="0 0 1000 240"`, `width: 100%`, placed so `y=0` aligns with the node vertical center. Node centers in this viewBox: node1 `x=90`, node5 `x=910`, all at `y=40`.
  - **The loop-back path** goes from node 5's bottom, down and back to node 1's bottom, as a smooth rounded-rectangle-style curve dipping ~`160px` below the row:
    ```
    M 910 70            <!-- start just below node 5 -->
    C 910 190, 700 200, 500 200   <!-- curve down and left -->
    C 300 200, 90 190, 90 70      <!-- continue left and up to below node 1 -->
    ```
  - Stroke: `var(--blue-500)`, `stroke-width: 2`, `stroke-dasharray: 6 4`. **Arrowhead** at the end (near node 1): use an SVG `<marker>` (`markerWidth=8 markerHeight=8`, a small filled triangle in `var(--blue-500)`) referenced via `marker-end`.
  - Total SVG block reserves **`~200px` of vertical space** below the node row so the curve is never clipped. The dash flows continuously along the path (CSS `dash-flow`, §2.3), reading as "the loop never stops."
- **Loop nodes + loop-back — RESPONSIVE:**
  - **Tablet & Mobile (`< 1024px`):** Stack the 5 nodes **vertically** (single column, centered, `gap: 32px`). The connectors between nodes become short **vertical** dashed segments (top-to-bottom flow). The loop-back path becomes a **vertical** curve running down the **left gutter** from node 5 back up to node 1: an SVG (`viewBox="0 0 120 H"`, height = node-column height) with a path hugging the left edge, e.g. `M 60 <y5> C 8 <y5>, 8 <y1>, 60 <y1>`, same stroke/arrowhead. If implementing the vertical curve is impractical at a given width, fall back to a single straight dashed vertical line down the left gutter with an upward arrowhead at the top and a small "loops back" label — the requirement is only that the closed-loop idea stays visible.
  - No horizontal scroll at any width (§2.8): the loop-back SVG must be inside an `overflow-x: clip` wrapper.
- **Active node highlight:** The "currently active" node (cycling automatically, GSAP-owned per §2.3) has: `border-color: var(--blue-500)`, `background: var(--blue-50)`, `box-shadow: 0 0 20px rgba(59,130,246,0.15)`.

- **Comparison cards:**
  - **Left card ("Regular LMS"):** `border: 1px solid var(--gray-200)`, `background: white`, text in `var(--gray-600)`. ❌ icons in `var(--coral-400)`.
  - **Right card ("GyanSetu"):** `border: 2px solid var(--blue-500)`, `background: var(--blue-50)`, text in `var(--gray-900)`. ✅ icons in `var(--teal-400)`. This card has a subtle `box-shadow: 0 4px 20px rgba(59,130,246,0.1)`.

### Animations

| # | Element | Animation | Library | Values |
|---|---------|-----------|---------|--------|
| 1 | Loop nodes | Stagger fade-up from left to right | Framer Motion | `y: 30 → 0`, `opacity: 0 → 1`, stagger `0.15s` |
| 2 | Connecting dashes | Continuous flowing animation (dashes move left to right forever) | CSS | `@keyframes dash-flow { to { stroke-dashoffset: -20px; } }`, `animation: dash-flow 1s linear infinite` |
| 3 | Active node highlight | Sequential cycle through nodes 1→2→3→4→5→1 | GSAP Timeline | Each node is highlighted for `1.5s`, then the next one. `repeat: -1` |
| 4 | Left comparison card | Slide in from left | Framer Motion `whileInView` | `x: -40 → 0`, `opacity: 0 → 1`, `duration: 0.6s` |
| 5 | Right comparison card | Slide in from right | Framer Motion `whileInView` | `x: 40 → 0`, `opacity: 0 → 1`, `duration: 0.6s`, `delay: 0.2s` |
| 6 | ❌ and ✅ icons | Scale bounce-in | Framer Motion | `scale: 0 → 1.2 → 1` (spring), stagger `0.1s` per line |

---

## SECTION 05 — HOW IT WORKS (Step by Step)

**File:** `components/landing/HowItWorksSection.tsx`
**Scroll ID:** `#how-it-works`
**Background:** `var(--off-white)` (#F8FAFC)

### What the User Sees
A vertical timeline flowing down the page. A central vertical line draws itself as the user scrolls. On alternating sides (left/right), content blocks appear showing each step of the GyanSetu journey. Behind the text, giant watermark numbers (01, 02, 03...) are faintly visible. Each step has a text description on one side and a small CSS-drawn UI illustration on the other side.

### Exact Layout Specification
```
                         [ 04 ] HOW IT WORKS
                  FROM LOGIN TO VERIFIED COMPETENCY

                              │  ← vertical timeline line (draws on scroll)
                              │
    ┌─────────────────────┐   │
    │  01                 │   ●  ← circle marker on timeline
    │                     │   │
    │  OFFICER LOGS IN    │   │   ┌─────────────────────┐
    │  Profile loaded.    │   │   │  [CSS illustration:  │
    │  Role-based reqs    │   │   │   Login form mockup] │
    │  identified.        │   │   └─────────────────────┘
    └─────────────────────┘   │
                              │
                              │   ┌─────────────────────┐
    ┌─────────────────────┐   ●   │  02                 │
    │  [CSS illustration: │   │   │                     │
    │   MCQ card with     │   │   │  DIAGNOSTIC         │
    │   difficulty bar]   │   │   │  ASSESSMENT          │
    └─────────────────────┘   │   │  Adaptive questions  │
                              │   └─────────────────────┘
                              │
    ... (continues alternating for all 6 steps)
```

- **Timeline line:** A vertical `div`, `width: 2px`, `background: var(--blue-500)`, centered. Starts at `scaleY: 0` and grows to `scaleY: 1` as the user scrolls (GSAP ScrollTrigger with `scrub: true`). `transformOrigin: top`.
- **Circle markers:** At each step, a `12px` diameter circle on the timeline line. `background: var(--blue-500)`, `border: 3px solid white`, creating a "pin" effect.
- **Watermark numbers:** Behind each step's text content, a giant number in Bebas Neue `120px` (mobile `80px`), color `var(--blue-100)` (very faint). `position: absolute`, `z-index: 0`, `pointer-events:none`. Slight parallax offset on scroll (GSAP, on the watermark element ONLY — never on the text block; see §2.3).

### Responsive behavior — REQUIRED (the alternating layout is desktop-only)

- **Desktop (`lg:` ≥ 1024px):** The alternating left/right layout as drawn above. Timeline line runs down the **center**; steps alternate text-left/illustration-right, then text-right/illustration-left. Circle markers sit on the center line.
- **Tablet & Mobile (`< 1024px`):** **Do NOT alternate sides.** Switch to a single-column left-rail timeline:
  - The vertical timeline line and its circle markers move to a **fixed left rail** (line at ~`20px` from the left edge; markers centered on it).
  - Every step becomes one full-width block to the **right of the rail** (left padding ~`44px` to clear the line), regardless of step number.
  - **Order within each step:** number/title → description → the CSS illustration **below** the text (illustration never sits beside the text on mobile). Steps flow top-to-bottom `01 → 06`.
  - The timeline still draws top-to-bottom on scroll (GSAP scrub) exactly as on desktop; only the horizontal arrangement changes.
  - Watermark numbers shrink to `80px` and sit behind the text at low opacity; ensure they never push page width (§2.8).

### The 6 Steps (Content)

| Step | Title | Description | Illustration (CSS-drawn, no images) |
|------|-------|-------------|--------------------------------------|
| 01 | Officer Logs In | Profile loaded. Role-based competency requirements automatically identified. | A simple login form mockup: two input fields + a button, drawn with CSS borders |
| 02 | Diagnostic Assessment | Adaptive questions start — harder if correct, easier if wrong. 5–10 minutes only. | An MCQ card with 4 options and a colored difficulty bar at the top |
| 03 | Competency State Calculated | 5-point profile generated: Mastery, Confidence, Coverage, Recency, Diversity. | A radar/pentagon chart (SVG) with 5 axes labeled |
| 04 | Gap Identified | Gaps found at subskill level. Priority = Role Importance × Gap Size × Uncertainty. | A card showing "Variance Estimation" with a red progress bar at 42% |
| 05 | Next Best Action | 12 explainability fields. Not "take this course" — WHY, for THIS gap, at THIS priority. iGOT/NSSTA/TPAC options ranked. | A recommendation card with icon, title, and a "Why this?" expandable area |
| 06 | Loop Closes | Learner completes intervention + post-assessment. New evidence generated → State updates → back to Step 01. | Two small metric cards side by side: "0.42 → 0.74" with an up arrow |

### Animations

| # | Element | Animation | Trigger | Library | Values |
|---|---------|-----------|---------|---------|--------|
| 1 | Timeline vertical line | Draws from top to bottom proportional to scroll | Scroll position | GSAP ScrollTrigger | `scaleY: 0 → 1`, `scrub: true`, `transformOrigin: top` |
| 2 | Circle markers | Scale-in when timeline reaches them | Timeline progress | GSAP | `scale: 0 → 1`, spring easing |
| 3 | Watermark numbers (01, 02...) | Slight parallax upward shift | Scroll | GSAP ScrollTrigger | `y: 20 → -20`, `scrub: true` |
| 4 | Text content blocks | Fade-up + slide-in from the side they're on | Scroll into view | Framer Motion `whileInView` | `x: ±40 → 0`, `y: 20 → 0`, `opacity: 0 → 1`, `duration: 0.6s` |
| 5 | CSS illustrations | Scale-in with slight rotation | Scroll into view | Framer Motion | `scale: 0.9 → 1`, `rotate: -2 → 0`, `opacity: 0 → 1` |

---

## SECTION 06 — THE HERO MOMENT (Before / After)

**File:** `components/landing/HeroMomentSection.tsx`
**Scroll ID:** `#hero-moment`
**Background:** White with subtle `var(--blue-50)` gradient at edges

### What the User Sees
Two large cards side-by-side. The left card ("BEFORE") shows a learner's poor competency state in muted red/gray colors. The right card ("AFTER") shows the improved state in vibrant green/blue. Between them, an arrow or transition indicator. Numbers animate from the "before" values to the "after" values as the section scrolls into view. Below the cards, a badge shows what intervention caused the improvement.

### Exact Layout Specification
```
                     [ 05 ] THE RESULT

                     THE HERO MOMENT                  ← Heading
          Watch competency improve in real-time       ← Subtitle
          after a targeted intervention.

    ┌────────────── BEFORE ─────────────┐   ┌────────────── AFTER ──────────────┐
    │                                    │   │                                    │
    │  Mastery:     0.42      ████░░░░  │   │  Mastery:     0.74  ↑  ████████░  │
    │  Confidence:  Low                  │   │  Confidence:  High  ↑             │
    │  Coverage:    25%                  │   │  Coverage:    60%   ↑             │
    │  Evidence:    1 type               │   │  Evidence:    2 types ↑           │
    │  Status:      ⚠ Needs Work        │   │  Status:      ✅ Verified         │
    │                                    │   │                                    │
    │  ┌────────────────────────────┐    │   │  ┌────────────────────────────┐    │
    │  │    [Small Radar Chart]    │    │   │  │  [Expanded Radar Chart]   │    │
    │  │    (collapsed polygon)    │    │   │  │  (full polygon)           │    │
    │  └────────────────────────────┘    │   │  └────────────────────────────┘    │
    │                                    │   │                                    │
    │  ❌ Variance Estimation gap       │   │  ✅ Variance Estimation resolved  │
    └────────────────────────────────────┘   └────────────────────────────────────┘

           INTERVENTION: NSSTA Practical Task — Neyman Allocation Module
```

- **Before card:** `border: 1px solid var(--gray-200)`, `background: white`. Mastery number in `var(--coral-400)`. Progress bar fill in `var(--coral-400)`.
- **After card:** `border: 2px solid var(--teal-400)`, `background: linear-gradient(135deg, white 0%, var(--blue-50) 100%)`. Mastery number in `var(--teal-400)`. Progress bar fill in `var(--teal-400)`. Arrow indicators `↑` in `var(--teal-400)`.
- **Radar charts — EXACT geometry & values (no guesswork):** Both charts share one coordinate system so they read as the same profile improving.
  - **SVG:** `viewBox="0 0 200 200"`. Center `(100,100)`. Max radius `R = 80`. **5 axes**, in this fixed order, at angles starting at the top and going clockwise every 72°: **Mastery** (top), **Confidence**, **Coverage**, **Recency**, **Diversity**.
  - **Axis endpoints at value = 1.0** (draw the faint pentagon grid + 5 spokes in `var(--gray-100)` connecting these): `(100,20)`, `(176.09,75.28)`, `(147.02,164.72)`, `(52.98,164.72)`, `(23.91,75.28)`.
  - **A vertex for value `v` on axis `k`** is `center + v·R·(unit vector of that axis)`. The two profiles below are pre-computed for you — use these exact `points` strings.
  - **BEFORE profile** — Mastery `0.42`, Confidence `0.30`, Coverage `0.25`, Recency `0.35`, Diversity `0.20`:
    `points="100,66.4 122.83,92.58 111.76,116.18 83.54,122.65 84.78,95.06"`
  - **AFTER profile** — Mastery `0.74`, Confidence `0.80`, Coverage `0.60`, Recency `0.70`, Diversity `0.55`:
    `points="100,40.8 160.87,80.22 128.21,138.83 67.09,145.3 58.15,86.4"`
  - Polygon styling both charts: `stroke: var(--blue-500)`, `stroke-width: 2`, `fill: var(--blue-500)`, `fill-opacity: 0.12` (before) / `0.22` (after). (These profile values are **ILLUSTRATIVE** — see §2.9.)
- **Intervention badge:** Below both cards, centered. `background: var(--blue-50)`, `border: 1px solid var(--blue-100)`, `border-radius: 8px`, `padding: 12px 24px`. Text in `var(--blue-700)`, Inter 600, 14px.

### Animations

| # | Element | Animation | Library | Values |
|---|---------|-----------|---------|--------|
| 1 | Before card | Slide in from left | Framer Motion `whileInView` | `x: -60 → 0`, `opacity: 0 → 1`, `duration: 0.6s` |
| 2 | After card | Slide in from right | Framer Motion | `x: 60 → 0`, `opacity: 0 → 1`, `duration: 0.6s`, `delay: 0.3s` |
| 3 | Mastery number (Before) | Counter: `0 → 0.42` | AnimatedCounter | `duration: 1.5s` |
| 4 | Mastery number (After) | Counter: `0 → 0.74` with color shift (gray → teal) | AnimatedCounter | `duration: 2s`, `delay: 0.5s` |
| 5 | Progress bars | Width grows from `0%` to target width | Framer Motion | `width: 0% → 42%` (before) / `0% → 74%` (after), `duration: 1.5s` |
| 6 | Radar chart polygon (After card) | Morphs from the BEFORE profile to the AFTER profile | **Framer Motion** (NOT CSS) | See method below — `duration: 1.2s`, `ease: easeOut`, starts when the After card is in view |

> **Radar animation method (important):** CSS `transition` on an SVG `points` attribute does **not** animate reliably across browsers — do not use it. Instead drive it with Framer Motion: keep a motion value `t` (0→1), animate it to 1 when in view, and interpolate each of the 5 vertices between the BEFORE and AFTER coordinate arrays with `useTransform`, feeding the result into a `motion.polygon`'s `points`. The **Before** card's polygon is static (always the BEFORE profile); only the **After** card's polygon morphs. If `prefers-reduced-motion` is set, render the After polygon at the final AFTER profile immediately with no morph (§2.4).
| 7 | ↑ arrow indicators | Bounce in | Framer Motion | `scale: 0 → 1.3 → 1` (spring), `delay: 1s` |
| 8 | Intervention badge | Fade-up | Framer Motion | `y: 20 → 0`, `opacity: 0 → 1`, `delay: 1.2s` |

---

## SECTION 07 — SOCIAL PROOF + SPLINE 3D (Stripe Style)

**File:** `components/landing/SocialProofSection.tsx`
**Scroll ID:** `#social-proof`
**Background:** `var(--off-white)`

### What the User Sees
An immersive section mimicking Stripe's homepage. On the left side, bold statistics and logos of organizations GyanSetu is built for. On the right side (or center), a large interactive 3D object (Spline) that the user can orbit with their mouse — it rotates slowly by default and responds to cursor movement. The 3D object should be an abstract tech visualization (glowing neural nodes, data mesh, etc.) in blue/teal/indigo gradients.

### Exact Layout Specification
```
    [ 06 ] BUILT FOR INDIA'S STATISTICAL WORKFORCE

    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │   LEFT SIDE (50%)                │  RIGHT SIDE (50%)         │
    │                                  │                           │
    │   ┌────┐ ┌────┐ ┌────┐          │    ┌─────────────────┐    │
    │   │MoSPI│ │NSSTA│ │iGOT│  ...   │    │                 │    │
    │   └────┘ └────┘ └────┘          │    │   [SPLINE 3D    │    │
    │   (grayscale logos, marquee)     │    │    INTERACTIVE   │    │
    │                                  │    │    OBJECT]       │    │
    │   6                              │    │                 │    │
    │   EVIDENCE TYPES                 │    │   Responds to   │    │
    │                                  │    │   mouse hover   │    │
    │   3                              │    └─────────────────┘    │
    │   AI AGENTS                      │                           │
    │                                  │                           │
    │   103                            │                           │
    │   TESTS PASSING                  │                           │
    │                                  │                           │
    └──────────────────────────────────────────────────────────────┘
```

- **Logo ticker — render as TEXT wordmarks, not image files (no logo assets exist, do not invent or download any):** A horizontal marquee of the organisation names **MoSPI · NSSTA · TPAC · iGOT Karmayogi · KCM**. These are the real bodies GyanSetu is built for, but **you do not have their official logo files and must not fabricate look-alike logos or pull them off the web.** Instead render each as a styled **text wordmark**:
  - Each item: the name in **Inter 600, 16px, `var(--gray-400)`, `letter-spacing: 0.04em`**, inside a pill (`padding: 8px 16px`, `border: 1px solid var(--gray-100)`, `border-radius: 8px`, `background: white`).
  - Optionally prefix each with a small neutral Lucide icon (e.g. `Building2` or `Landmark`, `16px`, `var(--gray-200)`) — a generic institution glyph, never a claimed official emblem.
  - The row scrolls infinitely via CSS `@keyframes marquee` (`30s linear infinite`, see tailwind config). Duplicate the list once in the DOM so the loop is seamless.
  - Add a caption below the ticker in `var(--gray-400)`, 12px: "Built for India's official statistical training ecosystem." Do **not** imply endorsement or partnership.
  - If real, properly-licensed logo SVGs are provided later, they can drop in to replace the wordmarks without changing layout.
- **Stat counters:** 3 large numbers stacked vertically. **All three are `ILLUSTRATIVE` until verified — see §2.9 and add the required source/placeholder comment at each.**
  - `6` — "Evidence Types" (Bebas Neue 72px, `var(--gray-900)`)
  - `3` — "AI Agents" (same styling)
  - `103` — "Tests Passing" (same styling) — **⚠ do NOT ship this as a real metric unless the repo actually has 103 passing tests that were run and counted (§2.9). If unverified, relabel to a non-numeric claim such as "AUTOMATED TESTS" / "QUALITY-CHECKED PIPELINE", or remove it.**
  - Labels below each number in Inter 400, 14px, `var(--gray-400)`, uppercase
- **Right-side 3D visual:** occupies `50%` of the section width (full width, stacked below the stats, on `< 1024px`), `400px` tall. **This document ships a fully self-contained CSS/SVG fallback as the DEFAULT** (see below) so the page is 100% reproducible with zero external accounts or scene URLs. Spline is an **optional upgrade**, not a requirement.

### The 3D Visual — build the FALLBACK first (this is the required, reproducible path)

> **Why:** A Spline scene requires a specific `scene.splinecode` URL that does not exist in this document, so a Spline-only spec is **not one-shot reproducible**. Therefore the **default deliverable is a self-contained animated CSS/SVG "data mesh"** that needs no account, no URL, and no external asset. Build this. Spline is an optional swap-in described afterward.

**DEFAULT — `<DataMesh />` component (CSS/SVG, fully specified):**
- A `400px`-tall, full-width `position: relative` box with `overflow: hidden`, `border-radius: 16px`, `background: radial-gradient(circle at 50% 45%, var(--blue-50) 0%, white 70%)`.
- **Nodes:** 7 circles scattered in the box (use these approximate positions as % of the box: `[50,45] [22,30] [78,32] [30,68] [72,70] [50,18] [50,80]`). Each node: `10–16px` diameter, `background: var(--gradient-3d-mesh)` (the blue→indigo→teal→coral gradient token), soft glow `box-shadow: 0 0 16px rgba(59,130,246,0.5)`.
- **Connections:** one absolutely-positioned SVG (`inset:0`, `z-index:1`) drawing thin lines (`stroke: var(--blue-400)`, `stroke-width: 1`, `opacity: 0.4`) between the center node and each outer node, plus a few outer-to-outer links, forming a mesh.
- **Motion (CSS keyframes, §2.3-owned, all disabled under reduced-motion):**
  - The whole node/line group slowly rotates: `@keyframes mesh-spin { to { transform: rotate(360deg); } }`, `40s linear infinite`, `transform-origin: 50% 50%` (this is the "0.5 RPM slow spin").
  - Each node also gently pulses opacity/scale (`float`-style loop, staggered).
- **Mouse-responsive tilt (optional, cheap):** on `mousemove` over the box, apply a small `transform: rotateX()/rotateY()` (max ±8°) toward the cursor via a tiny React handler with `will-change: transform`. Skip under reduced-motion. This mimics the Spline "orbit on hover" feel without a 3D engine.
- No `<canvas>`, no WebGL, no external files. This is the version that ships.

**OPTIONAL UPGRADE — real Spline scene (only if the builder chooses to and has a scene):**
Spline needs a real scene URL, which this document does not provide, so treat it as a nice-to-have. If (and only if) someone creates one:
1. Create a scene at [spline.design](https://spline.design/) (abstract mesh, colors `#3B82F6` / `#6366F1` / `#2DD4BF`, idle spin + hover-rotate), then File → Export → copy the `https://prod.spline.design/…/scene.splinecode` URL.
2. `npm install @splinetool/react-spline @splinetool/runtime`.
3. Render it **behind a feature flag / prop** so the component falls back to `<DataMesh />` when no URL is set:
```tsx
const SPLINE_SCENE = process.env.NEXT_PUBLIC_SPLINE_SCENE ?? ''; // empty by default
// if empty → render <DataMesh />; else lazy-load Spline:
const Spline = React.lazy(() => import('@splinetool/react-spline'));
// <Suspense fallback={<DataMesh />}> <Spline scene={SPLINE_SCENE} style={{width:'100%',height:'400px'}} /> </Suspense>
```
Using `<DataMesh />` as the Suspense fallback means the page looks correct whether or not Spline ever loads. **Never** hardcode a fake/guessed Spline URL — an invalid URL renders an error box.

### Animations

| # | Element | Animation | Library | Values |
|---|---------|-----------|---------|--------|
| 1 | Logo marquee | Infinite horizontal scroll | CSS | `@keyframes marquee { 0% { translateX(0) } 100% { translateX(-50%) } }`, `30s linear infinite` |
| 2 | Stat numbers | Counter animation | AnimatedCounter | `0 → 6`, `0 → 3`, `0 → 103`, each `2s`, staggered `0.3s` |
| 3 | 3D visual (`<DataMesh />` default) | Slow auto-rotation (`mesh-spin` 40s) + node pulse + optional mouse-tilt | CSS (§2.3); Spline built-in only if the optional Spline scene is used | See `<DataMesh />` spec above; disabled under reduced-motion |
| 4 | Section enter | Fade-up | Framer Motion `whileInView` | Standard fade-up pattern |

---

## SECTION 08 — DIFFERENTIATORS (Bento Grid)

**File:** `components/landing/FeaturesSection.tsx`
**Scroll ID:** `#features`
**Background:** White

### What the User Sees
A bento-box grid (like Linear.app's feature grid) of 5-6 feature cards with varied sizes. Each card has a small blue icon, a title, a short description, and a tiny CSS-drawn visual element showing a miniature preview of that feature. Cards have subtle hover lift effects and soft borders.

### Exact Layout (Bento Grid)
```
    [ 07 ] DIFFERENTIATORS
    WHAT MAKES GYANSETU DIFFERENT

    ┌────────────────────┬────────────────────┬────────────────────┐
    │                    │                    │                    │
    │  🧠 ADAPTIVE       │  📊 EVIDENCE       │  🎯 NEXT BEST     │
    │  ASSESSMENT        │  FUSION            │  ACTION            │
    │                    │                    │                    │
    │  Questions adapt   │  6 evidence types  │  12 explainability │
    │  to your level.    │  fused, not avg'd. │  fields. Not just  │
    │  Harder if right,  │  Conflicts flagged │  "take this course"│
    │  easier if wrong.  │  not hidden.       │  but WHY.          │
    │                    │                    │                    │
    │  [difficulty bar]  │  [stacked pills]   │  [mini rec card]   │
    │                    │                    │                    │
    ├────────────────────┴────────────────────┼────────────────────┤
    │                                         │                    │
    │  ⚡ AGENTIC AI PIPELINE                 │  ⏰ RETENTION      │
    │  3 autonomous agents orchestrated       │  VERIFICATION      │
    │  by a central coordinator.              │                    │
    │                                         │  Scheduled re-tests│
    │  [agent timeline: ●──●──●──●]           │  verify memory.    │
    │                                         │                    │
    └─────────────────────────────────────────┴────────────────────┘
```

- **Grid:** CSS Grid, `grid-template-columns: repeat(3, 1fr)`, `gap: 24px`. Bottom row: first card spans 2 columns (`grid-column: span 2`).
- **Each card:**
  - `background: white`
  - `border: 1px solid var(--gray-100)`
  - `border-radius: 16px`
  - `padding: 32px`
  - **Icon container:** `48px × 48px`, `background: var(--blue-50)`, `border-radius: 12px`, icon in `var(--blue-500)` at `24px` size
  - **Title:** Inter 700, 20px, `var(--gray-900)`, `margin-top: 16px`
  - **Description:** Inter 400, 15px, `var(--gray-600)`, `margin-top: 8px`, `line-height: 1.6`
  - **Visual element:** A tiny CSS-drawn miniature at the bottom of the card (not an image)

### Feature Card Details

| Card | Icon (Lucide) | Title | Description | Mini Visual |
|------|---------------|-------|-------------|-------------|
| 1 | `Brain` | Adaptive Assessment | Questions adapt to your level in real-time. Get harder if right, easier if wrong. 5-10 minutes, not a full exam. | A horizontal slider bar with a dot that moves left/right |
| 2 | `Layers` | Evidence Fusion | 6 distinct evidence types fused — not averaged. Conflicting evidence is flagged, not hidden. | 3 stacked colored pills/chips (like tags) |
| 3 | `Target` | Next Best Action | 12 explainability fields. Not "take this course" — WHY this course, for THIS gap, at THIS priority. | A mini card with a title and 2 bullet points |
| 4 (wide) | `Workflow` | Agentic AI Pipeline | 3 autonomous agents — Diagnostic, Intervention, Monitoring — orchestrated by a central coordinator. | A horizontal timeline with 4 dots connected by a line |
| 5 | `Clock` | Retention Verification | Scheduled re-tests verify you remember. Knowledge decay is measured, not assumed. | A mini curve graph showing decay over time |

### Animations & Micro-Interactions

| # | Element | Animation | Library | Values |
|---|---------|-----------|---------|--------|
| 1 | Grid cards | Stagger fade-up | Framer Motion `whileInView` | `y: 40 → 0`, `opacity: 0 → 1`, stagger: `0.12s` per card |
| 2 | Card hover | Lift + shadow + border color change | CSS transition | `transform: translateY(-4px)`, `box-shadow: 0 8px 30px rgba(0,0,0,0.08)`, `border-color: var(--blue-100)`, `transition: 0.3s ease` |
| 3 | Card icon | Gentle floating bob (infinite loop) | Framer Motion `animate` | `y: [0, -3, 0]`, `duration: 3s`, `repeat: Infinity`, `ease: easeInOut` |
| 4 | Wide card timeline dots | Sequential dot pulse animation | GSAP Timeline | Each dot scales `1 → 1.5 → 1` with a blue glow, sequentially, `repeat: -1` |

---

## SECTION 09 — TECHNOLOGY STACK (Pipeline Architecture)

**File:** `components/landing/TechStackSection.tsx`
**Scroll ID:** `#technology`
**Background:** `var(--off-white)`

### What the User Sees
A vertical pipeline diagram showing how data flows through the GyanSetu system. 6 pipeline step cards are stacked vertically, connected by animated SVG flow lines. Each card has a left-side accent color bar that gets progressively darker blue (light at top → deep at bottom). On the right side of each card, small tech badges (like "ChromaDB", "Gemini") appear.

### Pipeline Cards (Top to Bottom)

| # | Title | Description | Icons (Lucide) | Tech Badges |
|---|-------|-------------|-----------------|-------------|
| 1 | Document Upload | PDF / PPT / Video → Text extraction. 9 failure categories handled. | `FileText`, `Upload` | `PyMuPDF`, `python-pptx` |
| 2 | Concept Extraction | Semantic chunking → ChromaDB vector embeddings. | `Brain`, `Database` | `ChromaDB`, `LangChain` |
| 3 | MCQ Generation | LLM-generated → 5-check quality validation pipeline. | `HelpCircle`, `CheckCircle` | `Gemini`, `LangChain` |
| 4 | Adaptive Assessment | Difficulty adapts per response → Evidence recorded per question. | `Gauge`, `TrendingUp` | `FastAPI`, `React` |
| 5 | Competency Engine | 6 evidence types fused → Mastery + Confidence + Coverage calculated. | `Layers`, `Calculator` | `Python`, `NumPy` |
| 6 | 4-Tier Fallback | Four graceful-degradation tiers — Live LLM → Cached → Question Bank → Deterministic — so the system keeps serving questions if a tier is unavailable. | `Shield`, `ArrowDown` | `Redis`, `SQLite` |

> **Copy rule for card 6:** describe the *behaviour* ("keeps serving if a tier is unavailable"), not an absolute architectural guarantee. Do **not** print "zero single-point-of-failure" or similar unqualified claims — they are hard to prove and read as marketing. The four-tier list itself is the value; let it speak.

- **Each card:** `background: white`, `border: 1px solid var(--gray-100)`, `border-radius: 16px`, `padding: 24px 32px`. Left accent bar: `4px wide`, `border-radius: 2px`, color gets darker from card 1 (`--blue-100`) to card 6 (`--blue-700`).
- **Flow lines:** SVG `<line>` elements between cards, `stroke: var(--gray-200)`, `stroke-width: 2`, animated via `stroke-dashoffset`.
- **Tech badges:** Small pill-shaped badges (`background: var(--gray-50)`, `border: 1px solid var(--gray-100)`, `border-radius: 6px`, `padding: 4px 8px`, `font-size: 11px`, `font-family: JetBrains Mono`).

### Animations

| # | Element | Animation | Library | Values |
|---|---------|-----------|---------|--------|
| 1 | Pipeline cards | Scroll-driven sequential reveal | GSAP ScrollTrigger | Cards 1→6 appear one by one as user scrolls, `scrub: true` |
| 2 | Flow lines | SVG line drawing between each card | GSAP | `stroke-dashoffset: 100 → 0`, triggered after parent card reveals |
| 3 | Tech badges | Fade-in alongside their card | Framer Motion | `opacity: 0 → 1`, `x: 10 → 0`, same timing as parent card |
| 4 | Accent bars | Color animation (subtly shifts shade) | CSS | `transition: background 0.3s` on scroll |

---

## SECTION 10 — CTA + FOOTER

**File:** `components/landing/Footer.tsx`
**Scroll ID:** `#footer`

### What the User Sees
A dramatic dark section. The CTA block has a deep blue background with a dot-pattern overlay. A large centered heading asks "READY TO CLOSE THE LOOP?" with a white glowing CTA button that pulses softly. Below that, a dark footer with 4 columns of links and a copyright bar.

### CTA Block Layout
- **Background:** `var(--blue-900)` (#1E3A5F) with `DotPattern` overlay (dots in `rgba(255,255,255,0.05)`)
- **Padding:** `120px` vertical
- **Heading:** "READY TO CLOSE THE LOOP?" — Bebas Neue, `48px`, white, centered
- **Subtitle:** "Start identifying competency gaps with evidence, not guesswork." — Inter, 18px, `rgba(255,255,255,0.7)`, centered
- **Button:** `Start Assessment →` — `background: white`, `color: var(--blue-900)`, pill shape, height `48px`, padding `0 32px`. Subtle pulsing glow animation.

### Footer Layout
- **Background:** `var(--gray-900)` (#0F172A)
- **4 columns:**
  - **Col 1:** GYANSETU logo (white) + one-liner description
  - **Col 2:** Product — Dashboard, Assessment, Admin, Chatbot
  - **Col 3:** Resources — Build Guide, API Docs, Architecture
  - **Col 4:** Team — SIH 2026, Team CodeHashiras
- **Bottom bar:** Thin top border, copyright text + "Built for SIH 2026"

### Animations

| # | Element | Animation | Library | Values |
|---|---------|-----------|---------|--------|
| 1 | CTA heading | Blur-in on scroll | Framer Motion | `filter: blur(10px) → 0`, `opacity: 0 → 1` |
| 2 | CTA button | Infinite pulse glow | CSS | `@keyframes pulse-glow { 0%,100% { box-shadow: 0 0 20px rgba(255,255,255,0.3) } 50% { box-shadow: 0 0 40px rgba(255,255,255,0.6) } }`, `2s ease-in-out infinite` |
| 3 | CTA button hover | Scale up + stronger glow | CSS | `transform: scale(1.05)`, `box-shadow: 0 0 50px rgba(255,255,255,0.5)` |
| 4 | Footer columns | Stagger fade-up | Framer Motion | `y: 30 → 0`, `opacity: 0 → 1`, stagger `0.1s` |

---

# PART IV — PAGE CONTINUITY & FLOW

### How Sections Connect Visually
- **Between every section**, a horizontal gradient divider line provides seamless transition (see Section 1.4 — Section Dividers above)
- **Background colors alternate:** White → Off-white → White → Off-white → White → Off-white → White → Off-white → Dark
- **Grid overlay lines** from the Hero section fade out at the bottom, giving way to the Problem section's floating elements — this creates a "zooming in" feeling
- **Vertical rhythm:** All sections have consistent `120px` top/bottom padding on desktop, `80px` on mobile
- **Typography rhythm:** Every section starts with: `Section Label → Heading → Subtitle → Content`. This consistent pattern helps the user know where they are

### Scroll Experience
1. Page loads with blur-in → Hero appears with staggered text
2. User scrolls → grid lines subtly parallax behind the hero
3. Problem section appears with center SVG + floating bubbles popping in
4. Solution section shows the animated closed loop cycling through nodes
5. How It Works timeline DRAWS as the user scrolls — this is the most satisfying scroll interaction
6. Hero Moment cards slide in from opposite sides with animated numbers
7. Social Proof section reveals the 3D element — the most visually striking moment
8. Feature bento cards stagger in one by one
9. Technology pipeline draws its flow lines sequentially
10. Dark CTA section creates a dramatic tonal shift with the glowing button

---

# PART V — FRONTEND PROJECT ARCHITECTURE

## 5.1 Folder Structure

```
Frontend/
├── app/
│   ├── layout.tsx                    # Root layout — load fonts, wrap in providers
│   ├── page.tsx                      # Landing page — import & stack all 10 sections
│   └── globals.css                   # CSS variables, grid overlays, dot patterns, keyframes
│
├── components/
│   ├── landing/                      # One file per section
│   │   ├── Navbar.tsx                # [SECTION 01]
│   │   ├── HeroSection.tsx           # [SECTION 02]
│   │   ├── ProblemSection.tsx        # [SECTION 03]
│   │   ├── SolutionSection.tsx       # [SECTION 04]
│   │   ├── HowItWorksSection.tsx     # [SECTION 05]
│   │   ├── HeroMomentSection.tsx     # [SECTION 06]
│   │   ├── SocialProofSection.tsx    # [SECTION 07] — Spline 3D
│   │   ├── FeaturesSection.tsx       # [SECTION 08]
│   │   ├── TechStackSection.tsx      # [SECTION 09]
│   │   └── Footer.tsx                # [SECTION 10]
│   │
│   └── ui/                           # Reusable primitives (used by ALL sections)
│       ├── Button.tsx                # Primary (filled pill) + Secondary (outlined pill)
│       ├── Badge.tsx                 # Small colored pill badges with optional icon
│       ├── Card.tsx                  # Base card: border, radius, padding, hover lift
│       ├── SectionLabel.tsx          # "[ 01 ] SECTION NAME" — monospace label
│       ├── SectionHeading.tsx        # Bebas Neue heading + Inter subtitle combo
│       ├── AnimatedCounter.tsx       # Scroll-triggered number counter (0 → target)
│       ├── GridOverlay.tsx           # Absolute-positioned grid lines background
│       └── DotPattern.tsx            # Dot grid background pattern (CSS radial-gradient)
│
├── hooks/
│   ├── useScrollProgress.ts          # Returns 0-1 scroll progress for GSAP
│   └── useInView.ts                  # Intersection Observer wrapper
│
├── lib/
│   ├── gsap.ts                       # Register GSAP + ScrollTrigger plugin
│   ├── fonts.ts                      # next/font/google font declarations
│   └── cn.ts                         # clsx + tailwind-merge utility
│
├── public/
│   # OPTIONAL — only if you use the optional Spline upgrade (Section 07).
│   # The default build ships the self-contained <DataMesh /> and needs NO files here.
│   └── spline/                       # (optional) Spline 3D scene files, if any
│
│   # NOTE: no `assets/` reference-image folder is needed. The design references
│   # (the "Valley.co" patterns) are described in words in §1.5 — do not create
│   # or depend on any `assets/image.png` file.
│
├── tailwind.config.ts                # Extended with brand colors, fonts, keyframes
├── next.config.js
├── tsconfig.json
├── package.json
└── postcss.config.js
```

## 5.2 Package Dependencies

```json
{
  "dependencies": {
    "next": "^14.2",
    "react": "^18.3",
    "react-dom": "^18.3",
    "framer-motion": "^11.0",
    "gsap": "^3.12",
    "@splinetool/react-spline": "^4.0",
    "@splinetool/runtime": "^1.9",
    "lucide-react": "^0.400",
    "clsx": "^2.1",
    "tailwind-merge": "^2.3"
  },
  "devDependencies": {
    "typescript": "^5.4",
    "@types/react": "^18.3",
    "@types/node": "^20",
    "tailwindcss": "^3.4",
    "postcss": "^8.4",
    "autoprefixer": "^10.4"
  }
}
```

## 5.3 Tailwind Configuration

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        heading: ['Bebas Neue', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          50: '#EFF6FF',
          100: '#DBEAFE',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          900: '#1E3A5F',
        },
      },
      animation: {
        'marquee': 'marquee 30s linear infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 6s ease-in-out infinite',
        'dash-flow': 'dash-flow 1s linear infinite',
        'mesh-spin': 'mesh-spin 40s linear infinite',
      },
      keyframes: {
        'mesh-spin': {
          'to': { transform: 'rotate(360deg)' },
        },
        marquee: {
          '0%': { transform: 'translateX(0%)' },
          '100%': { transform: 'translateX(-50%)' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(59, 130, 246, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(59, 130, 246, 0.6)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'dash-flow': {
          'to': { strokeDashoffset: '-20px' },
        },
      },
    },
  },
  plugins: [],
};
export default config;
```

---

# PART VI — BUILD CHECKLIST (Track Progress Here)

## Phase 1: Foundation
- [ ] Initialize Next.js 14+ project in `Frontend/` with `npx -y create-next-app@latest ./ --typescript --tailwind --eslint --app --src-dir=false`
- [ ] Install all dependencies: `npm install framer-motion gsap @splinetool/react-spline @splinetool/runtime lucide-react clsx tailwind-merge`
- [ ] Configure `tailwind.config.ts` with exact brand colors, fonts, and keyframes from Section 5.3
- [ ] Create `globals.css` with all CSS custom properties (color tokens, gradient tokens)
- [ ] Set up Google Fonts in `layout.tsx` using `next/font/google` for Bebas Neue, Inter, JetBrains Mono
- [ ] Create `lib/cn.ts` — `import { clsx } from 'clsx'; import { twMerge } from 'tailwind-merge'; export const cn = (...inputs) => twMerge(clsx(inputs));`
- [ ] Create `lib/gsap.ts` — `import gsap from 'gsap'; import { ScrollTrigger } from 'gsap/ScrollTrigger'; gsap.registerPlugin(ScrollTrigger);`

## Phase 2: Reusable UI Components
- [ ] `ui/Button.tsx` — Two variants: primary (blue filled pill) and secondary (outlined pill)
- [ ] `ui/Badge.tsx` — Small colored pill with optional Lucide icon
- [ ] `ui/Card.tsx` — Border, radius, padding, hover-lift effect
- [ ] `ui/SectionLabel.tsx` — `[ 01 ] SECTION NAME` in JetBrains Mono
- [ ] `ui/SectionHeading.tsx` — Bebas Neue heading + Inter subtitle
- [ ] `ui/AnimatedCounter.tsx` — Scroll-triggered `0 → N` counter using Framer Motion
- [ ] `ui/GridOverlay.tsx` — Absolute-positioned CSS grid lines
- [ ] `ui/DotPattern.tsx` — CSS radial-gradient dot background

## Phase 3: Landing Page Sections
- [ ] **SEC 01** — Navbar (sticky, blur glass, responsive hamburger on mobile)
- [ ] **SEC 02** — Hero (blur-in headlines, Valley.co input bar, grid background)
- [ ] **SEC 03** — Problem (centered SVG, 6 floating bubbles, dashed connection lines)
- [ ] **SEC 04** — Solution (5-node closed loop with cycling highlight, comparison cards)
- [ ] **SEC 05** — How It Works (scroll-drawn timeline, 6 alternating steps, watermark numbers)
- [ ] **SEC 06** — Hero Moment (before/after cards, animated counters, radar charts)
- [ ] **SEC 07** — Social Proof (Spline 3D, logo marquee, stat counters)
- [ ] **SEC 08** — Differentiators (bento grid, 5 feature cards with hover lift)
- [ ] **SEC 09** — Tech Stack (6 pipeline cards, SVG flow lines, tech badges)
- [ ] **SEC 10** — CTA + Footer (dark section, pulse-glow button, 4-col footer)

## Phase 4: Polish & Integration
- [ ] Compose all 10 sections in `app/page.tsx` with section IDs and dividers
- [ ] Wire up navbar anchor links for smooth scroll navigation
- [ ] Add page-load blur-in sequence — **scoped to navbar + hero only, NOT the whole `<main>`** (§2.5)
- [ ] **Animation ownership pass** — confirm no element is animated by both Framer Motion and GSAP; entrances=Framer, scrubbed=GSAP, idle loops=CSS (§2.3)
- [ ] **Reduced-motion pass** — add the global CSS kill-switch, gate all Framer `whileInView` and all GSAP timelines; verify the page is fully readable with motion disabled (§2.4)
- [ ] **Z-index audit** — every decoration at `z:0`, connectors `z:1`, content `z:10`, problem bubbles `z:20`, navbar `z:50`, drawer `z:60`; all backgrounds `pointer-events:none` (§2.7)
- [ ] **No-horizontal-scroll check** at `375px` — `document.documentElement.scrollWidth === window.innerWidth`; add `overflow-x: clip` on decorated/marquee sections (§2.8)
- [ ] Mobile responsive pass at `375px`, `768px`, `1024px`, `1440px` — verify the per-section mobile rules for Sections 03, 04, 05 (orbit/loop/timeline all collapse to single column) (§2.6)
- [ ] **Data-honesty pass (§2.9)** — every stat carries an `ILLUSTRATIVE`/`MEASURED` comment; `103 TESTS PASSING` is verified-or-relabeled; no unqualified claims (e.g. "zero single-point-of-failure")
- [ ] SEO: `<title>GyanSetu — AI-Driven Competency Intelligence</title>`, meta description, OG image
- [ ] Performance: 3D visual ships as self-contained `<DataMesh />`; if the optional Spline scene is used, lazy-load it with `<DataMesh />` as the Suspense fallback; use `content-visibility: auto` on off-screen sections
- [ ] Lighthouse audit: target 90+ performance score

---

# PART VII — DESIGN REFERENCE SUMMARY

### Inspiration Sources & What We Take From Each
| Source | What We Borrow |
|--------|---------------|
| **Linear.app** | Grid overlay lines, hairline card borders, monospace section labels, bento grid layout |
| **Raycast.com** | Feature card grids, bold heading hierarchy, dot pattern backgrounds |
| **Valley.co** (described in §1.5, no image file) | Hero CTA input bar pattern, floating node cards connected by lines, social proof stat line |
| **Stripe.com** | Spline 3D interactive hero element, gradient 3D meshes, vertical pipeline diagrams |
| **Coursera** | Blue color palette (#2563EB family), clean white educational aesthetic |

### What We Are NOT Doing
- ❌ No video backgrounds or GIF animations — all visuals are CSS-drawn, SVG, or Spline 3D
- ❌ No dark theme for the landing page — white canvas only
- ❌ No complex parallax that hurts performance — only subtle depth shifts
- ❌ No placeholder stock images — every visual is built with code (SVG, CSS, or Lucide icons). The Section 07 3D visual ships as the self-contained `<DataMesh />`; the external Spline scene is an OPTIONAL upgrade, never a hard dependency, and the page must be complete and correct without it.
- ❌ No ShadcnUI or TailwindUI — all components are custom-built
