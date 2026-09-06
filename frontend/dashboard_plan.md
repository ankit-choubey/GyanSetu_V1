# GyanSetu — Learner Dashboard Implementation Plan (Researched)

> **Who is this for?** The frontend owner building the *actual product* (not the landing page). It takes Antigravity's Phase-1 proposal, pressure-tests it against how production dashboards are built at real companies, and turns it into an exact, buildable spec grounded in GyanSetu's real backend contract.
>
> **Companion docs:** [`design_plan.md`](design_plan.md) (landing page — design tokens live there), [`../GyanSetu_BUILD_GUIDE (2).md`](../GyanSetu_BUILD_GUIDE%20(2).md) (API contract, competency engine), [`../PROJECT_CONTEXT (3).md`](../PROJECT_CONTEXT%20(3).md) (non-negotiable rules).
>
> **Stack (confirmed from Build Guide §3):** Next.js 14+ (App Router) · TypeScript · Tailwind · **Recharts** · Framer Motion. Reuse the exact color/type tokens from `design_plan.md §1.1–1.2`.

---

## 0. TL;DR — Decisions & Answers to the Open Questions

Antigravity asked two questions and proposed a Phase 1. Here are researched answers **before** you write code.

### Q1 — Dark theme or the White/Blue landing theme? → **White/Blue, light-first. Do NOT ship a dark glassmorphism dashboard as the default.**
Reasons (sourced in §3):
- **Brand consistency.** The landing page is explicitly white-only (`design_plan.md` "What We Are NOT Doing"). A dark app behind a white marketing site feels like two different products.
- **Data legibility & accessibility.** This is a *dense, numeric, government* product (MoSPI/NSSTA). Light backgrounds give charts higher, more predictable contrast and better print/report behavior; glassmorphism (blur + translucency) is a known anti-pattern *behind data* because it lowers text/chart contrast and fails WCAG AA easily. Keep glass for the navbar only.
- **The premium look comes from hierarchy, spacing, and restraint — not darkness.** Linear/Vercel/Tremor dashboards read "premium" on light surfaces.
- **Compromise that keeps the "premium" ask:** build every color as a **token** and add an **optional** dark-mode toggle later (Tremor and most design systems ship dark mode this way). Light is the default and the demo theme; dark is a Phase-3 nice-to-have, not the foundation.

### Q2 — Mock JSON data for Phase 1? → **Yes — but shape it to the real API contract and label it.**
- Put mocks behind a typed **data-access layer** that mirrors the Build Guide's endpoints (§4 below), so switching to the live API is a one-line swap, not a refactor.
- Honor the project's non-negotiable honesty rule: every screen using demo data shows a `[SANDBOX DATA]` badge (`PROJECT_CONTEXT §5`). Never present mock numbers as measured.

### Q3 (implicit) — Charting library? → **Recharts for charts + your own card components. Not Tremor as the base.**
- Recharts is the best **balance** for a Next.js App-Router dashboard: declarative, SSR-friendly, and it has a first-class `RadarChart` (which you need for the 5-axis competency profile). Tremor is faster for stock KPI/table layouts but **has no radar chart** and "fights you" when your design system has custom colors — which yours does. Use Recharts for the radar/bars, and hand-build the KPI/NBA cards with your own tokens (optionally borrowing shadcn/ui primitives). (Sourced §3.4.)

### Q4 (implicit) — Is "Learner Dashboard first" the right Phase 1? → **Yes, with a sharper spec.**
Antigravity's instinct is correct — the Learner Dashboard is the hero screen that proves the "closed loop" in one glance. But upgrade it from "Radar + NBA card" to a **proper dashboard information hierarchy** (§5): an above-the-fold KPI row of the 5 metrics → radar → active gap → explainable NBA → agent-activity strip, with **confidence/uncertainty treated as a first-class citizen** (the single biggest differentiator vs a normal LMS).

---

## 1. How Production Dashboards Are *Actually* Built (Research Summary)

Five patterns show up consistently across production analytics/skills products. Each maps to a concrete rule for GyanSetu.

1. **Design-system / component-driven, not page-driven.** Teams build a small kit of tokens + primitives (KPI card, chart wrapper, badge, data bar) and compose screens from them. Vercel's Tremor codifies this as *"show the data, hide the chrome."* → We build `ui/dashboard/*` primitives first, then compose pages.
2. **Strict information hierarchy (F-pattern).** Eye-tracking shows users scan top-to-bottom, left-to-right; the most important KPI goes **top-left**, with **3–7 KPI cards above the fold** answering the primary question with zero interaction. → Our above-fold row = the 5 competency metrics; top-left = Mastery.
3. **A grid + spacing system.** A 12-column grid on an 8px base unit with generous white space between card groups is the industry default for alignment and responsiveness. → Tailwind's grid + 8px spacing scale (already in `design_plan.md §1.3`).
4. **Separated, typed data layer with explicit states.** Production dashboards always render **loading / empty / error / partial** states, not just the happy path. Data fetching is isolated from presentation. → A `lib/api` layer returning typed contracts + skeleton/empty/error components.
5. **Uncertainty is shown, not hidden.** Mature analytics/BI and XAI products display *how sure* a number is (confidence bands, ranges, subtle cues), because it builds calibrated trust. → This is literally GyanSetu's thesis ("No evidence ≠ low competency"); confidence gets equal visual weight to mastery.

### 1.1 The reference products (competency / skills intelligence)
Study these for *what to show* on a competency dashboard — skill profiles, proficiency vs target, gap lists, and org roll-ups:
- **Pluralsight Skill IQ / Role IQ** — diagnostic assessment → proficiency level benchmarked to a standard. (Closest analog to our diagnostic → mastery loop.)
- **Degreed Skills+** — dashboards of skill distribution and progress against targets.
- **Eightfold AI / Gloat** — deep skill profiles and adjacency; org-level talent intelligence (analog to our Admin Workforce view).
- **Workday Skills Cloud / Viva Skills** — enterprise skills graph roll-ups.

**What we do that they largely don't (our wedge):** surface **evidence type + confidence + coverage** per skill and an **explainable next-best-action**, instead of a single opaque score. Lean into that in the UI.

---

## 2. GyanSetu's Real Data Model (what the dashboard must render)

Ground every component in this — it comes from the Build Guide, not invention.

### 2.1 The 5-metric competency profile (per competency)
From the competency engine (`GyanSetu_BUILD_GUIDE §12`) and the demo script (§21):

| Metric | Meaning | Range | UI note |
|---|---|---|---|
| **Mastery** | How good the officer is | `0.0–1.0` **or `null`** (`null` = *Unknown*, never 0) | Primary number; `null` must render as "Unassessed", not a low score |
| **Confidence** | How sure the *system* is of the mastery estimate | `0.0–1.0` (shown Low/Med/High) | Equal visual weight to mastery |
| **Coverage** | How much of the subskills have been tested | `0.0–1.0` (%) | Progress bar |
| **Recency** | How fresh the newest evidence is | days since `last_assessed` | "3 days ago" |
| **Diversity** | How many distinct evidence types back it | integer count (of 6) | "2 of 6 sources" |

> **Hard rule (non-negotiable, `PROJECT_CONTEXT §5`):** *No evidence ≠ low competency.* Missing data → **Unknown / Unassessed** with confidence 0, never a failing number. The dashboard must visually distinguish "low mastery" (red) from "unassessed" (neutral/gray).

### 2.2 The 6 evidence types (Build Guide §12)
`ASSESSMENT`, `PRACTICAL_TASK`, `PROJECT`, `PEER_REVIEW`, `SELF_REPORT`, `CERTIFICATION` (fused, **not averaged**; conflicts flagged). Diversity = how many of these are present.

### 2.3 The 12 explainability fields for the Next-Best-Action (Build Guide §29, line 2753)
Every recommendation must expose all 12:
`selected action · justification · role relevance · competency alignment · subskill coverage · prerequisites · gap severity · evidence confidence · learner state · modality · availability · expected outcome`.
The NBA card renders these — with progressive disclosure (headline first, all 12 in a "Why this?" expansion).

### 2.4 The exact API contract (Build Guide §12 — mock these shapes verbatim)
- `GET /api/competency/state` → `{ competencies: [{ id, name, domain, mastery, confidence, coverage, last_assessed, gap, status }] }`
- `POST /api/assessment/submit` → `{ score, competency_update: { mastery_before, mastery_after, confidence_before, confidence_after, identified_gaps[], next_best_action{ type, name, reason } }, agent_activity[] }`
- `GET /api/admin/workforce` → `{ total_officers, competency_distribution[], top_gaps[], training_effectiveness{} }`

> The live contract's `next_best_action` currently has only `{type, name, reason}`. The **12 fields are the target shape** — in the mock, extend it to all 12 and note it so the backend owner aligns. Build the card for 12; degrade gracefully if some are absent.

---

## 3. The Recommended Phase-1 Screen — Learner Dashboard

### 3.1 Layout (F-pattern, above-the-fold first)
```
┌───────────────────────────────────────────────────────────────────────────┐
│ Sidebar │  Top bar: officer name · role (JSO) · [SANDBOX DATA] badge        │
│ (nav)   ├───────────────────────────────────────────────────────────────────┤
│         │  ROW 1 — KPI STRIP (above the fold, 5 cards, Mastery top-left)     │
│  ▸ Dash │  [Mastery 0.42 ▾conf Low] [Confidence] [Coverage 25%] [Recency] [Diversity 1/6] │
│  ▸ Assess├───────────────────────────────────────────────────────────────────┤
│  ▸ Tasks │  ROW 2                                                             │
│  ▸ Admin │  ┌───────────────────────┐   ┌───────────────────────────────────┐ │
│         │  │  COMPETENCY RADAR     │   │  ACTIVE GAP CARD                  │ │
│         │  │  (5-axis, current vs  │   │  "Variance Estimation in          │ │
│         │  │   role target overlay)│   │   Stratified Sampling"            │ │
│         │  └───────────────────────┘   │   severity · why it's the pick    │ │
│         │                              └───────────────────────────────────┘ │
│         ├───────────────────────────────────────────────────────────────────┤
│         │  ROW 3 — NEXT BEST ACTION (full width, 12 explainability fields)    │
│         ├───────────────────────────────────────────────────────────────────┤
│         │  ROW 4 — AGENT ACTIVITY STRIP (audit trail; Diagnostic→…→Monitoring)│
└─────────┴───────────────────────────────────────────────────────────────────┘
```
- **12-column grid, 8px spacing.** Row 2 = radar (`col-span-7`) + gap (`col-span-5`) on desktop; stacks to single column below `1024px` (reuse `design_plan.md §2.6` breakpoints).
- **Most important element is largest:** Mastery KPI and the radar dominate; agent strip is smallest.

### 3.2 Components to build (Phase 1)

**`components/ui/dashboard/MetricCard.tsx`** — one KPI cell.
- Big number (Bebas Neue, per `design_plan.md`), label, and — critically — a **confidence chip** and a subtle state color: `mastery ≥ 0.7` teal, `0.4–0.7` amber, `< 0.4` coral, **`null` → neutral gray "Unassessed"**. Never color an unassessed metric red.
- Optional 7-point sparkline (Recharts `<LineChart>`) if history exists.

**`components/ui/dashboard/CompetencyRadar.tsx`** — the hero chart.
- Recharts `<RadarChart>` with 5 axes: Mastery, Confidence, Coverage, Recency (normalized 0–1), Diversity (count/6).
- **Two overlaid polygons:** the officer's *current* state (filled `--blue-500` @ ~18% opacity) and the *role target* (dashed `--gray-400` outline). The gap between them IS the story.
- Animate in with Framer Motion (grow from center); respect `prefers-reduced-motion` (`design_plan.md §2.4`).
- Show a `null`/unassessed axis as a hollow node at the center with a small "?" — not as zero.

**`components/ui/dashboard/ActiveGapCard.tsx`**
- Headline: the single highest-confidence actionable gap (`competency.gap`), phrased defensibly: *"Highest-confidence actionable gap: Variance Estimation in Stratified Sampling."* (Build Guide §1 exact language — no "AI magically knows".)
- Shows **gap severity** and a one-line evidence basis ("based on 2 assessments, confidence: Medium").

**`components/ui/dashboard/NextBestActionCard.tsx`** — the differentiator.
- **Progressive disclosure (XAI best practice):** headline recommendation + the top 3 fields always visible (`selected action`, `justification`, `expected outcome`); a **"Why this? →"** expander reveals all 12 fields in a labeled 2-column grid.
- Each field is a labeled row (JetBrains Mono label, Inter value) so it reads as an audit record, not marketing.
- Include a modality icon (iGOT/NSSTA/TPAC/Practical) and an `availability` state.
- **Trust calibration, not blind trust:** add a quiet "Not relevant?" / override affordance — mature XAI UIs let users disagree; it signals the system isn't pretending to be infallible.

**`components/ui/dashboard/AgentActivityStrip.tsx`**
- Renders `agent_activity[]` as a horizontal timeline: Diagnostic → Competency Engine → Intervention → Monitoring, each with its one-line action. Cheap to build, and it visibly demonstrates the "3 agents + orchestrator" claim.

**`app/dashboard/page.tsx`** — composes the above with the data layer (§4), skeleton loading, and an empty state for a brand-new officer (everything "Unassessed" — this is a *feature* to show, not an error).

### 3.3 The honesty/uncertainty UI rules (make these explicit in code)
1. Every mastery number is accompanied by its confidence — never shown alone.
2. `null` mastery renders as **"Unassessed"** in neutral gray, visually distinct from low-but-measured (coral).
3. Low confidence (< 0.4) adds a subtle hatched/blurred treatment or a "Low confidence" chip on that metric (uncertainty-visualization best practice).
4. Conflicting evidence (if the API flags it) is surfaced with a small "Conflicting evidence" badge — flagged, not hidden (Build Guide §12).
5. Any demo dataset shows `[SANDBOX DATA]`; any replayed retention event shows `[REPLAY]`.

---

## 4. Architecture — Data Layer, Folders, States

### 4.1 Folder structure (extends the landing-page structure)
```
app/
├── dashboard/
│   ├── page.tsx                 # Learner dashboard (Phase 1)
│   ├── layout.tsx               # Sidebar + top bar shell (shared by app pages)
│   └── loading.tsx              # Route-level skeleton
components/
├── ui/dashboard/
│   ├── MetricCard.tsx
│   ├── CompetencyRadar.tsx
│   ├── ActiveGapCard.tsx
│   ├── NextBestActionCard.tsx
│   ├── AgentActivityStrip.tsx
│   ├── SandboxBadge.tsx
│   └── states/ { CardSkeleton.tsx, EmptyState.tsx, ErrorState.tsx }
lib/
├── api/
│   ├── types.ts                 # TS types mirroring the Build Guide contract (§2.4)
│   ├── client.ts                # fetch wrapper; reads NEXT_PUBLIC_API_BASE
│   └── competency.ts            # getCompetencyState() — returns typed contract
└── mock/
    └── officer-jso.json         # [SANDBOX] JSO struggling with Sampling (matches types.ts)
```

### 4.2 Data-access pattern (mock↔live swap in one place)
```ts
// lib/api/competency.ts
export async function getCompetencyState(): Promise<CompetencyState> {
  if (process.env.NEXT_PUBLIC_USE_MOCK === 'true') {
    return (await import('@/lib/mock/officer-jso.json')).default as CompetencyState;
  }
  return client.get('/api/competency/state');
}
```
Presentation components never fetch directly — they receive typed props. This is the production separation-of-concerns pattern and makes the backend integration a config flip.

### 4.3 Required states (build all four, not just happy path)
- **Loading:** skeleton cards (shimmer), not spinners, to preserve layout.
- **Empty / new officer:** everything "Unassessed" + a "Take your first diagnostic" CTA. (A first-class state, per the honesty rules.)
- **Error:** a contained `ErrorState` in the card, never a white screen (Build Guide §13 warns about exactly this).
- **Partial:** some competencies assessed, others unknown — the normal real-world case.

---

## 5. Mock Dataset (Phase 1) — shape to §2.4

Create `lib/mock/officer-jso.json` for a JSO struggling with Sampling, matching the contract exactly, e.g.:
```json
{
  "_meta": { "source": "SANDBOX DATA", "persona": "JSO — Sampling struggler" },
  "competencies": [
    { "id": 1, "name": "Sampling Design", "domain": "Statistical",
      "mastery": 0.42, "confidence": 0.35, "coverage": 0.25,
      "last_assessed": "2026-09-03", "gap": "Variance Estimation", "status": "needs_improvement" },
    { "id": 2, "name": "Data Quality", "domain": "Statistical",
      "mastery": null, "confidence": 0.0, "coverage": 0.0,
      "last_assessed": null, "gap": null, "status": "unassessed" }
  ]
}
```
- Include **at least one `mastery: null` (unassessed)** competency so the "No evidence ≠ low competency" behavior is demonstrable in the demo.
- All numbers here are **ILLUSTRATIVE / SANDBOX** — same labeling discipline as `design_plan.md §2.9`.

---

## 6. Build Order & Definition of Done

### Phase 1 (this proposal) — Learner Dashboard, static-data
1. `lib/api/types.ts` + `lib/mock/officer-jso.json` (contract-shaped).
2. App shell: `app/dashboard/layout.tsx` (sidebar + top bar + SandboxBadge).
3. `MetricCard` → the 5-KPI above-fold row.
4. `CompetencyRadar` (current vs target overlay).
5. `ActiveGapCard` + `NextBestActionCard` (12 fields, progressive disclosure).
6. `AgentActivityStrip`.
7. Loading / empty / error states.
8. Responsive + reduced-motion + a11y pass.

**Definition of done for Phase 1:** at `1440/1024/768/375`, the dashboard renders the JSO persona with no horizontal scroll, shows confidence beside every mastery, renders the unassessed competency as "Unassessed" (not red/zero), expands all 12 NBA fields, and carries a `[SANDBOX DATA]` badge. No live backend required.

### Phase 2 — Wire to live API (flip `NEXT_PUBLIC_USE_MOCK`), add Diagnostic Assessment UI (consumes `/assessment/*`), feed `competency_update` back into the radar (before→after morph — reuse the radar morph method from `design_plan.md §Section 06`).
### Phase 3 — Admin Workforce Intelligence (`/api/admin/workforce`: distribution bars, top-gaps, training-effectiveness), optional dark-mode toggle, chatbot panel.

---

## 7. Accessibility, Performance, Testing (production checklist)
- [ ] **WCAG AA contrast** on every metric/chart (this is why we rejected dark glass behind data). Don't encode status by color alone — pair color with a label/icon.
- [ ] Charts have text alternatives (a visually-hidden table of the radar values) for screen readers.
- [ ] `prefers-reduced-motion` disables radar/counter animations (`design_plan.md §2.4`).
- [ ] Recharts wrapped in `<ResponsiveContainer>`; charts lazy/`dynamic()`-imported to keep TTI low on the App Router.
- [ ] Skeletons preserve layout (no content-shift) while loading.
- [ ] All four states (loading/empty/error/partial) manually verified with the mock.
- [ ] Numbers labeled SANDBOX/ILLUSTRATIVE; nothing presented as a measured result (`PROJECT_CONTEXT §5`).

---

## 8. Sources & Resources (where this came from)

**Competency / skills-intelligence products (what to show):**
- [Docebo — 6 Skills Intelligence Platforms](https://www.docebo.com/learning-network/blog/skills-intelligence-platforms/)
- [Fuel50 — Top Skills Assessment Software 2026](https://fuel50.com/blog/skills-assessment-platforms/)
- [Cloud Assess — Best Skills Intelligence Platforms 2026](https://cloudassess.com/blog/best-skills-intelligence-platforms/)
- [HRTech SaaS — Skills Intelligence Software](https://hrtechsaas.com/blog/skills-intelligence-software/)

**Dashboard design systems & component approach:**
- [Vercel — Acquiring Tremor (open-source dashboard components)](https://vercel.com/blog/vercel-acquires-tremor)
- [Tremor dashboard templates & components (2026)](https://adminlte.io/blog/tremor-dashboard-templates/)
- [Tailkits — Tremor overview](https://tailkits.com/components/tremor/)

**Charting library comparison (why Recharts):**
- [PkgPulse — Recharts v3 vs Tremor vs Nivo (2026)](https://www.pkgpulse.com/guides/recharts-v3-vs-tremor-vs-nivo-react-charting-2026)
- [Physical Pixel — Building Dashboards with React: customization guide](https://physicalpixel.medium.com/building-dashboards-with-react-a-comparative-guide-focused-on-customization-dbccf611bc3f)
- [Chart.ts — Best React Chart Libraries 2026](https://chartts.com/blog/best-react-chart-libraries-2026)

**Information hierarchy / KPI layout science:**
- [Brand.dev — 10 Dashboard Design Best Practices for SaaS (2025)](https://www.brand.dev/blog/dashboard-design-best-practices)
- [DataCamp — Effective Dashboard Design](https://www.datacamp.com/tutorial/dashboard-design-tutorial)
- [Setproduct — Dashboard UI design: from KPIs to layouts](https://www.setproduct.com/blog/dashboard-ui-design)
- [5of10 — Dashboard Design Best Practices (2026)](https://5of10.com/articles/dashboard-design-best-practices/)

**Visualizing uncertainty / confidence (our core differentiator):**
- [Microsoft Power BI (Medium) — Visualizing Uncertainty: Advanced Techniques](https://medium.com/microsoft-power-bi/visualizing-uncertainty-advanced-techniques-for-probabilistic-data-in-business-intelligence-bi-961eaac0eb53)
- [Think Design (Medium) — Visualizing Uncertainty: Best Practices](https://medium.com/@marketingtd64/visualizing-uncertainty-best-practices-for-complex-data-eadfc9d3546f)

**Explainable-AI UI patterns (the NBA card):**
- [Eleken — Explainable AI UI Design (XAI)](https://www.eleken.co/blog-posts/explainable-ai-ui-design-xai)
- [UXmatters — Designing AI UIs That Foster Trust and Transparency](https://www.uxmatters.com/mt/archives/2025/04/designing-ai-user-interfaces-that-foster-trust-and-transparency.php)
- [Smashing Magazine — Practical Interface Patterns for AI Transparency](https://www.smashingmagazine.com/2026/05/practical-interface-patterns-ai-transparency/)
- [Smart Interface Design Patterns — Trust Calibration Spectrum](https://smart-interface-design-patterns.com/articles/the-trust-calibration-spectrum-in-ux/)

**Internal (source of truth for the data model):** `GyanSetu_BUILD_GUIDE (2).md` §2, §12, §21, §29 · `PROJECT_CONTEXT (3).md` §5 · `Frontend/design_plan.md` (tokens, breakpoints, reduced-motion).
