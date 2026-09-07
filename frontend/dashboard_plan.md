# GyanSetu Dashboard — Complete Build Plan

> **Purpose:** This is the single source of truth for your friend (or any developer) to build every dashboard section. It covers layout, components, exact data mapping to the real backend, animations, micro-interactions, and what to clean up.
>
> **Rule #1:** Every piece of data shown in the dashboard MUST come from or be derivable from the actual backend API responses. No invented fields.
>
> **Rule #2:** No AI slop. No fake-sounding headings. No unnecessary "AI-powered" or "Intelligence Engine" labels. Clean, professional, government-product language.

---

## TABLE OF CONTENTS

1. [Backend API Contract (Ground Truth)](#1-backend-api-contract)
2. [AI Slop Cleanup List](#2-ai-slop-cleanup-list)
3. [Sidebar Navigation Plan](#3-sidebar-navigation-plan)
4. [Global Design Rules](#4-global-design-rules)
5. [Color System & Theme](#5-color-system--theme)
6. [Micro-Interactions & Animation Plan](#6-micro-interactions--animation-plan)
7. [Section 1: Learner Dashboard (BUILT — Cleanup Needed)](#7-section-1-learner-dashboard)
8. [Section 2: Assessments](#8-section-2-assessments)
9. [Section 3: Practical Tasks](#9-section-3-practical-tasks)
10. [Section 4: Workforce Overview (Admin)](#10-section-4-workforce-overview)
11. [Section 5: Competency Map](#11-section-5-competency-map)
12. [Chart & Graph Specifications](#12-chart--graph-specifications)
13. [Build Priority](#13-build-priority)

---

## 1. Backend API Contract

This is what the backend **actually returns**. The frontend must only show data that maps to these responses. For mock mode, the mock JSON must match these shapes exactly so the swap is seamless.

### 1.1 `GET /api/dashboard/learner` → `DashboardResponse`

```json
{
  "user_id": 1,
  "full_name": "Ramesh Kumar",
  "role_name": "Statistical Officer",
  "total_competencies": 3,
  "competencies": [
    {
      "competency_id": 1,
      "competency_name": "Sampling Design",
      "mastery": 0.42,          // float | null (null = UNASSESSED, never treat as 0)
      "confidence": 0.35,       // float 0.0–1.0
      "coverage": 0.25,         // float 0.0–1.0
      "evidence_count": 2,      // int
      "status": "ASSESSED"      // "UNASSESSED" | "ASSESSED" | "CONFLICTING_EVIDENCE"
    }
  ]
}
```

**What the backend does NOT return** (frontend must compute or skip):
- ❌ `radar_data` — frontend must compute from competencies array
- ❌ `kpi_summary` — frontend must compute averages from competencies array
- ❌ `active_gap` as a separate object — derive from lowest-mastery competency
- ❌ `agent_activity[]` — no endpoint exists; skip or use static mock only for demo
- ❌ `officer.role`, `officer.cadre`, `officer.posting` — only `full_name` and `role_name` come from API
- ❌ `recency_label`, `diversity_count` — not in API; `evidence_count` and `coverage` are available
- ❌ 12 explainability fields on NBA — backend returns `{target_subskill_id, gap_reason, selected_intervention: {id, title, type, reason}, explanation, uncertainty}`

### 1.2 `POST /api/assessment/next` → `AdaptiveQuestionResponse`

```json
{
  "status": "QUESTION_PROPOSED",    // or "SUFFICIENT_EVIDENCE"
  "sufficient_evidence": false,
  "stop_reason": "...",
  "question_id": 5,
  "competency_id": 1,
  "subskill_id": 2,
  "question_text": "Which validation step is essential...?",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "difficulty": "easy"
}
```

### 1.3 `POST /api/assessment/submit` → `AssessmentSubmitResponse`

```json
{
  "status": "success",
  "message": "Assessment submitted successfully",
  "assessment_id": 10,
  "score": 0.75,
  "feedback": [
    {
      "question_id": 5,
      "selected": "B",
      "is_correct": true,
      "feedback": "Correct! Field consistency...",
      "identified_gap": null
    }
  ],
  "competency_status": "ASSESSED",
  "mastery": 0.68,
  "confidence": 0.45,
  "next_best_action": {
    "target_subskill_id": 2,
    "gap_reason": "low_mastery",
    "selected_intervention": {
      "id": 3,
      "title": "Sampling practice task",
      "type": "PRACTICE",
      "reason": "Directly targets the identified subskill gap."
    },
    "explanation": "Directly targets the identified subskill gap.",
    "uncertainty": null
  }
}
```

### 1.4 `GET /api/admin/analytics/competencies` → `AdminAnalyticsResponse`

```json
{
  "total_competencies": 3,
  "competencies": [
    {
      "role_id": 1,
      "role_name": "Statistical Officer",
      "competency_id": 1,
      "competency_name": "Sampling Design",
      "learner_count": 24,
      "assessed_count": 18,
      "average_mastery": 0.58,
      "average_confidence": 0.42,
      "average_coverage": 0.35,
      "total_evidence": 42,
      "status_distribution": {
        "ASSESSED": 18,
        "UNASSESSED": 6
      }
    }
  ]
}
```

### 1.5 `GET /api/competencies/{role_id}` → Competency list

```json
{
  "role_id": 1,
  "role_name": "Statistical Officer",
  "user_id": 1,
  "competencies": [
    { "id": 1, "name": "Sampling Design", "description": "..." }
  ]
}
```

### 1.6 `POST /api/chatbot/ask` → `ChatbotResponse`

```json
{
  "status": "ok",
  "answer": "The sampling frame...",
  "sources": ["page_3_paragraph_2"],
  "source_mode": "rag"
}
```

### 1.7 Database Tables (for understanding what exists)

| Table | Key Fields |
|---|---|
| `users` | id, email, full_name, role_id, is_active |
| `roles` | id, name, description |
| `competencies` | id, role_id, name, description |
| `subskills` | id, competency_id, name, description |
| `competency_states` | user_id, competency_id, mastery, confidence, coverage, evidence_count, evidence_diversity, status, updated_at |
| `evidence` | user_id, competency_id, subskill_id, evidence_type, title, score, weight, observed_at |
| `assessment_items` | user_id (null=bank item), competency_id, subskill_id, question_text, options_json, correct_option, difficulty |
| `interventions` | user_id, competency_id, subskill_id, title, description, intervention_type, priority |

### 1.8 Evidence Types (from backend enum)

`APPLICATION_SCENARIO`, `PRACTICAL_TASK`, `KNOWLEDGE_ASSESSMENT`, `TRAINING_HISTORY`, `WORKPLACE_SIGNAL`, `SELF_REPORT`

---

## 2. AI Slop Cleanup List

**These titles, labels, and headings are AI-generated fluff. Replace or remove them during build.**

### In `page.tsx` (Learner Dashboard):
| Current (AI Slop) | Replace With |
|---|---|
| `"1. Cadre Mastery"` | `"Mastery"` |
| `"2. Belief Confidence"` | `"Confidence"` |
| `"3. Subskill Coverage"` | `"Coverage"` |
| `"4. Evidence Recency"` | `"Recency"` |
| `"5. Evidence Diversity"` | `"Diversity"` |
| `"Weighted cross-domain index"` | Remove sublabel or use `"Average across competencies"` |
| `"Uncertainty calibration"` | Remove sublabel or use `"How sure the system is"` |
| `"Tested syllabus scope"` | Remove or use `"Subskills tested"` |
| `"Freshness of latest proof"` | Remove or use `"Last assessed"` |
| `"Fused data modalities"` | Remove or use `"Evidence sources used"` |
| `"ACTIVE DEMO PERSONA: ..."` banner text | Simplify to `"Demo Mode — [persona name]"` |
| `"First-Class Baseline State: Zero evidence..."` | `"New officer — no assessments taken yet"` |
| `"Active Closed-Loop State: Demonstrating gap diagnosis → 12-facet explainable intervention."` | `"Officer with active competency data"` |
| `"Adaptive Diagnostic Simulator"` modal title | `"Start Assessment"` |
| `"Official Statistics Competency Matrix"` table heading | `"Competency Breakdown"` |
| `"SSS JSO curriculum competencies mapped to MoSPI Field Operations & National Accounts"` | Remove entirely — not needed |
| `"5 Registered Competencies"` | Just show the count: `"3 competencies"` (from actual data) |
| `"Competency Key Performance Indicators"` sr-only heading | `"Overview"` |

### In `layout.tsx` (Sidebar/Topbar):
| Current (AI Slop) | Replace With |
|---|---|
| `"Workforce Navigation"` section label | `"Navigation"` or remove entirely |
| `"MoSPI · Official Statistics"` under logo | Remove — logo is enough |
| `"Competency Policy"` sidebar footer section | Remove — not useful information |
| `"SSS JSO Competency Model v2.4"` | Remove |
| `"Aligned with iGOT & NSSTA"` | Remove |
| `"Return to Public Portal"` | `"Back to Home"` |
| `"Officer Ramesh Kumar, JSO"` hardcoded name | Use `data.full_name` from API; remove "JSO" suffix |
| `"Subordinate Statistical Service (SSS) · MoSPI Regional Office (Bhopal)"` hardcoded | Use `data.role_name` from API |
| `"JSO (Sampling Deficit)"` persona button | `"Sample Learner"` |
| `"New Officer (Unassessed)"` persona button | `"New Learner"` |
| `"Hero Screen"` badge on Dashboard | Remove badge entirely |
| `"Phase 2"` / `"Phase 3"` badges | Remove badges or use `"Coming Soon"` only |

### In Component Files:
| File | Current (AI Slop) | Replace With |
|---|---|---|
| `ActiveGapCard.tsx` | `"Highest-confidence actionable gap"` | `"Top Gap"` or `"Needs Attention"` |
| `NextBestActionCard.tsx` | `"12-Facet Explainable Recommendation"` | `"Recommended Action"` |
| `NextBestActionCard.tsx` | All 12 explainability field labels | Only show what backend returns: `title`, `type`, `reason`, `explanation` |
| `AgentActivityStrip.tsx` | `"Multi-Agent Orchestration Timeline"` | `"System Activity"` or `"Recent Activity"` |
| `SandboxBadge.tsx` | Keep but simplify to just `"DEMO DATA"` |
| `CompetencyRadar.tsx` | `"5-Axis Competency Profile"` | `"Competency Overview"` |

### General Rules:
- **Remove all numbered labels** on KPI cards (`"1. Cadre Mastery"` → just `"Mastery"`)
- **Remove all MoSPI/NSSTA/SSS/JSO/KCM jargon** from UI labels — this is for internal display, the user knows their context
- **Remove the Sparkles icon** (✨) — it's the classic AI slop marker
- **Remove RefreshCw icon** next to "Simulate Diagnostic Test" — just use a normal button
- **Stop using `font-mono` for descriptive text** — mono is for code/IDs only, not for descriptions

---

## 3. Sidebar Navigation Plan

### Current Sidebar Items:
```
Learner Dashboard     → /dashboard          ✅ Built
Adaptive Diagnostics  → #                   🔨 Build
Practical Tasks & FOD → #                   🔨 Build
Workforce Intelligence→ #                   🔨 Build
Competency Ontology   → #                   🔨 Build
```

### Updated Sidebar (rename items, remove jargon):
```
Dashboard             → /dashboard          (icon: LayoutDashboard)
Assessments           → /dashboard/assessments (icon: ClipboardCheck)
Tasks                 → /dashboard/tasks     (icon: ListChecks)
Workforce             → /dashboard/workforce (icon: Users2) [Admin only]
Competency Map        → /dashboard/map       (icon: GitFork)
```

### Sidebar Behavior:
- **Expandable:** Each item can optionally have sub-items that expand on click (chevron toggle)
  - Dashboard → (no sub-items)
  - Assessments → Take Assessment, History
  - Tasks → Active, Completed
  - Workforce → Overview, By Office
  - Competency Map → (no sub-items)
- **Active state:** Blue left border + blue background tint on the active route
- **Mobile:** Slides in from left with backdrop blur overlay, closes on outside click or X
- **Width:** Fixed `w-60` (240px) on desktop

### Sidebar Footer (cleaned up):
- Just the "Back to Home" link with ArrowLeft icon
- Remove all "Competency Policy" and "Model v2.4" footer text

---

## 4. Global Design Rules

### Full-Page Usage
- **Every page uses the FULL `max-w-7xl` (1280px) content width** — no cramped center-only layouts
- Content stretches edge-to-edge within the padded content area (`p-4 sm:p-8`)
- On desktop (≥1024px), the content area is `1280px - 240px sidebar = 1040px` usable width
- Charts and tables must fill their grid column, not shrink to min-content

### Card Sizing Rules

| Card Type | Min Height | Padding | Border Radius |
|---|---|---|---|
| KPI stat card (top row) | `140px` | `p-5` (20px) | `rounded-xl` (12px) |
| Chart container card | `360px` | `p-6` (24px) | `rounded-xl` (12px) |
| Table card | Auto (content) | `p-6` (24px) | `rounded-xl` (12px) |
| Info/action card | `200px` | `p-5` (20px) | `rounded-xl` (12px) |

### Row Sizing Rules

| Row | Desktop Layout | Gap | Bottom Margin |
|---|---|---|---|
| KPI strip (top) | `grid-cols-3` or `grid-cols-4` or `grid-cols-5` depending on section | `gap-4` (16px) | `mb-8` via `space-y-8` |
| Two-column chart row | `grid-cols-12` → left `col-span-7`, right `col-span-5` | `gap-6` (24px) | `mb-8` |
| Full-width row | `col-span-12` (full width) | — | `mb-8` |
| Table row | Full width, no grid | — | `mb-8` |

### Responsive Breakpoints

| Breakpoint | Behavior |
|---|---|
| `≥1280px (xl)` | Full grid, sidebar open, max-w-7xl |
| `≥1024px (lg)` | Full grid, sidebar open |
| `768–1023px (md)` | 2-column grids, sidebar collapsed |
| `<768px (sm)` | Single column, hamburger menu |

### Card Visual Style (Consistent Across All Sections)

```
bg-white
border border-slate-200
rounded-xl
shadow-sm
hover:shadow-md (on interactive cards only)
transition-shadow duration-200
```

---

## 5. Color System & Theme

The dashboard uses a **light theme** with blue as the primary accent. All colors must come from this palette — no random hex values.

### Primary Palette

| Token | Hex | Use |
|---|---|---|
| Page background | `#F8FAFC` (slate-50) | Body/page background |
| Card background | `#FFFFFF` (white) | All cards |
| Card border | `#E2E8F0` (slate-200) | Card borders |
| Primary text | `#0F172A` (slate-900) | Headings, numbers |
| Secondary text | `#64748B` (slate-500) | Sublabels, descriptions |
| Muted text | `#94A3B8` (slate-400) | Timestamps, mono labels |

### Accent Colors (for charts and status indicators)

| Color | Hex / Tailwind | Use |
|---|---|---|
| Blue (primary) | `#3B82F6` / `blue-500` | Primary accent, active states, links, primary chart series |
| Blue dark | `#2563EB` / `blue-600` | Button hover, chart hover |
| Blue light | `#DBEAFE` / `blue-100` | Active sidebar item bg, badge bg |
| Teal (success/high) | `#14B8A6` / `teal-500` | High mastery, verified status, positive indicators |
| Amber (medium/warning) | `#F59E0B` / `amber-500` | Medium confidence, developing status |
| Rose (low/critical) | `#F43F5E` / `rose-500` | Low mastery, gaps, critical indicators |
| Slate (neutral) | `#94A3B8` / `slate-400` | Unassessed, neutral states |
| Indigo (secondary chart) | `#6366F1` / `indigo-500` | Second chart series, gradient accent |
| Emerald (good) | `#10B981` / `emerald-500` | Completed tasks, success states |

### Chart Color Palette (use these in order for multi-series charts)

```
Series 1: #3B82F6 (blue-500)
Series 2: #14B8A6 (teal-500)
Series 3: #F59E0B (amber-500)
Series 4: #6366F1 (indigo-500)
Series 5: #F43F5E (rose-500)
Series 6: #94A3B8 (slate-400)
```

### Status Color Rules

| Status | Background | Text | Border |
|---|---|---|---|
| Assessed / Verified | `bg-teal-50` | `text-teal-700` | `border-teal-200` |
| Developing | `bg-amber-50` | `text-amber-700` | `border-amber-200` |
| Low / Needs Work | `bg-rose-50` | `text-rose-700` | `border-rose-200` |
| Unassessed | `bg-slate-100` | `text-slate-600` | `border-slate-200` |
| Conflicting | `bg-amber-50` | `text-amber-700` | `border-amber-200` + warning icon |

---

## 6. Micro-Interactions & Animation Plan

### General Animation Rules
- Use **Framer Motion** for component mount/unmount and layout transitions
- Use **CSS transitions** for hover states and simple color/shadow changes
- **Respect `prefers-reduced-motion`** — wrap all motion in a check; if reduced motion, use instant opacity fade only
- **No GSAP in the dashboard** — GSAP is for the landing page only; dashboard uses Framer Motion

### Card Animations

| Interaction | Animation | Duration | Easing |
|---|---|---|---|
| Card mount (page load) | `opacity: 0 → 1`, `y: 12 → 0` | `300ms` | `ease-out` |
| Card stagger (KPI strip) | Each card delays by `60ms` × index | — | — |
| Card hover | `shadow-sm → shadow-md`, slight `translateY(-1px)` | `200ms` | `ease` |
| Card click (if interactive) | `scale(0.98)` on press, `scale(1)` on release | `100ms` | `ease` |

**Framer Motion variant example:**
```tsx
const cardVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.06, duration: 0.3, ease: "easeOut" }
  }),
};
```

### Chart Animations

| Chart Type | Animation | Duration |
|---|---|---|
| Radar chart | Polygon grows from center outward (scale 0 → 1) | `800ms` ease-in-out |
| Bar chart | Bars grow from bottom to full height, left to right stagger | `500ms` per bar, `50ms` stagger |
| Donut/Pie chart | Segments sweep clockwise from 0° to final angle | `600ms` ease-out |
| Line chart | Line draws from left to right (stroke-dashoffset animation) | `1000ms` ease-in-out |
| Progress bar (in tables) | Width grows from 0% to target | `400ms` ease-out |
| Counter number | Count-up animation from 0 to target number | `600ms` ease-out |

**Recharts animation props to use:**
```tsx
<BarChart>
  <Bar animationDuration={500} animationEasing="ease-out" animationBegin={0} />
</BarChart>

<RadarChart>
  <Radar animationDuration={800} animationEasing="ease-in-out" />
</RadarChart>

<PieChart>
  <Pie animationDuration={600} animationEasing="ease-out" animationBegin={0} />
</PieChart>
```

### Table Row Animations

| Interaction | Animation |
|---|---|
| Row mount | Fade in + slight slide-up, staggered by 30ms per row |
| Row hover | Background color transition to `slate-50`, `200ms` |
| Row click | Brief `scale(0.995)` press effect |

### Sidebar Animations

| Interaction | Animation |
|---|---|
| Sub-item expand/collapse | Height auto-animate with `overflow: hidden`, `200ms` ease |
| Active item indicator | Blue left border slides in with `width: 0 → 3px`, `150ms` |
| Mobile sidebar open/close | `translateX(-100% → 0)`, `300ms` with backdrop fade |

### Modal Animations

| Interaction | Animation |
|---|---|
| Modal open | Backdrop fades in `200ms`; modal scales `0.95 → 1` + fades in `250ms` |
| Modal close | Reverse of open, `200ms` |

### Button Micro-Interactions

| Interaction | Animation |
|---|---|
| Button hover | Background color darken, `150ms` |
| Button press | `scale(0.97)`, `100ms` |
| Button with loading | Spinner icon rotates, text changes to "Loading..." |

### Tooltip Animations

| Interaction | Animation |
|---|---|
| Tooltip show (chart hover) | Fade in + `y: 4 → 0`, `150ms` |
| Tooltip hide | Fade out `100ms` |

---

## 7. Section 1: Learner Dashboard

> **Route:** `/dashboard`
> **Status:** ✅ Built — needs cleanup per Section 2 (AI slop removal) and UI tweaks

### What to Keep:
- KPI strip (5 cards) — but rename labels, remove numbered prefixes
- Competency Radar chart — but rename heading
- Active Gap Card — but simplify title
- Next Best Action Card — but strip to only backend-returned fields
- Competency Breakdown Table — but rename heading
- Loading/Empty/Error states
- Persona switcher (for demo mode only)

### What to Remove:
- Agent Activity Strip — backend has no endpoint for this; remove entirely
- "12-facet explainable" NBA fields — backend returns only `{title, type, reason, explanation, uncertainty}`, show only those
- All numbered label prefixes on KPI cards
- All MoSPI/NSSTA/SSS jargon from labels
- Sparkles icon usage
- The overly verbose persona banner text
- "Competency Policy" sidebar footer section

### What to Change:

**KPI Strip** — Currently 5 cards. Change to **4 cards** since `recency` and `diversity` are not in the API response. The 4 KPIs should be:

| Card | Data Source | Display |
|---|---|---|
| Mastery | avg of `competencies[].mastery` (skip nulls) | Percentage, big number |
| Confidence | avg of `competencies[].confidence` | Percentage |
| Coverage | avg of `competencies[].coverage` | Percentage |
| Competencies | count of assessed vs total | `"2 of 3 assessed"` |

**Radar Chart** — Compute from competencies array. Each competency becomes an axis. `current` = mastery × 100 (null → 0 with "?" marker). `target` = 80 (configurable). Use `evidence_count` to size the dot on each axis.

**Gap Card** — Derived: find the competency with the lowest non-null mastery. Show: name, mastery %, confidence level, and the CTA button to start an assessment.

**Recommended Action** — Only show after an assessment is submitted. Display: `title`, `type` (PRACTICE/TRAINING), `reason`. That's all the backend provides. Don't invent 12 fields.

### Updated Layout:
```
┌────────────────────────────────────────────────────────────────────┐
│ Demo Mode Bar (only in mock mode)                                  │
│ "Demo Mode — Sample Learner" [Switch Persona ▾]                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ [Mastery: 42%]  [Confidence: 35%]  [Coverage: 25%]  [2/3 Assessed]│
│  ← 4 KPI cards, full width, grid-cols-4 on desktop, 2×2 on mobile │
│                                                                    │
├──────────────────────────────┬─────────────────────────────────────┤
│                              │                                     │
│ Competency Overview          │  Needs Attention                    │
│ (Radar Chart)                │  "Sampling Design" — 42%           │
│ col-span-7, min-h-[360px]   │  Confidence: Low                   │
│                              │  [Start Assessment →]              │
│                              │  col-span-5, min-h-[360px]         │
│                              │                                     │
├──────────────────────────────┴─────────────────────────────────────┤
│                                                                    │
│ Recommended Action (only shows if data.next_best_action exists)    │
│ Title: "Sampling practice task"                                    │
│ Type: PRACTICE | Reason: "Directly targets..." | [Start →]        │
│ Full width                                                         │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Competency Breakdown (full width table)                            │
│ Columns: Name | Mastery | Confidence | Coverage | Evidence | Status│
│ Click row → expand detail or open modal                            │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 8. Section 2: Assessments

> **Route:** `/dashboard/assessments`
> **Backend endpoints:** `POST /api/assessment/next`, `POST /api/assessment/submit`, `GET /api/competencies/{role_id}`

### Purpose
Browse competencies, start adaptive assessments, answer questions, see results with feedback.

### Data Mapping
- **Competency list** comes from `GET /api/competencies/{role_id}` → shows available assessments
- **Questions** come from `POST /api/assessment/next` one at a time (adaptive)
- **Results** come from `POST /api/assessment/submit` → score, feedback, mastery update, next-best-action
- **Assessment history** — not directly available from API; frontend can track locally in state or show the competency's current `evidence_count` as a proxy

### Layout:
```
┌────────────────────────────────────────────────────────────────────┐
│ H2: "Assessments"                                                  │
│ Subtitle: "Take adaptive assessments to measure your competencies" │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ROW 1 — 3 STAT CARDS (derived from dashboard/learner data)         │
│ ┌────────────────────┐ ┌────────────────────┐ ┌──────────────────┐ │
│ │ Competencies       │ │ Assessed           │ │ Avg Score        │ │
│ │ Total: 3           │ │ 2 of 3             │ │ 42%              │ │
│ │ For your role      │ │                    │ │                  │ │
│ │ min-h: 120px       │ │ min-h: 120px       │ │ min-h: 120px     │ │
│ └────────────────────┘ └────────────────────┘ └──────────────────┘ │
│ grid-cols-3, gap-4                                                 │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ROW 2 — ASSESSMENT CARDS (1 per competency, 3-col grid)            │
│ ┌────────────────────┐ ┌────────────────────┐ ┌──────────────────┐ │
│ │ [color strip top]  │ │ [color strip top]  │ │ [color strip top]│ │
│ │                    │ │                    │ │                  │ │
│ │ Sampling Design    │ │ Data Quality       │ │ Python for       │ │
│ │                    │ │                    │ │ Analytics        │ │
│ │ Mastery: 42%       │ │ Mastery: —         │ │ Mastery: —       │ │
│ │ Confidence: Low    │ │ Unassessed         │ │ Unassessed       │ │
│ │ Evidence: 2        │ │ Evidence: 0        │ │ Evidence: 0      │ │
│ │                    │ │                    │ │                  │ │
│ │ [Start Assessment] │ │ [Start Assessment] │ │ [Start]          │ │
│ │                    │ │                    │ │                  │ │
│ │ min-h: 240px       │ │ min-h: 240px       │ │ min-h: 240px     │ │
│ └────────────────────┘ └────────────────────┘ └──────────────────┘ │
│ grid-cols-3 (lg), grid-cols-1 (sm), gap-6                          │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│ Color strips: each competency gets a unique accent color from the  │
│ chart palette — blue-500, teal-500, amber-500 etc.                 │
│ Card top has a 4px colored border-top instead of a banner image.   │
└────────────────────────────────────────────────────────────────────┘
```

### Assessment Flow (within page, not separate route):
1. User clicks "Start Assessment" on a card
2. Modal or inline panel opens showing the question from `POST /api/assessment/next`
3. User selects an answer → send to `POST /api/assessment/submit`
4. Show result: score, feedback per question, updated mastery/confidence
5. If `next_best_action` returned, show a simple action card below results

### Assessment Card Icons
- Use **Lucide icons only**, not AI-themed icons:
  - `ClipboardCheck` for the assessment card header
  - `CheckCircle2` for completed/assessed state
  - `Circle` (empty) for unassessed state
  - `AlertCircle` for low mastery
  - `ArrowRight` for the CTA button

### Micro-interactions on this page:
- Cards mount with staggered fade-up (60ms delay per card)
- Color strip on card has a subtle gradient shimmer on hover
- "Start Assessment" button scales down 2% on press
- Modal slides up from bottom on mobile, fades in center on desktop
- Question options highlight on hover with border-blue-300 transition
- Correct answer flashes green, wrong flashes rose, 300ms
- Score counter animates from 0 to final value on results screen

---

## 9. Section 3: Practical Tasks

> **Route:** `/dashboard/tasks`
> **Backend endpoints:** No dedicated task endpoint exists yet. Use mock data shaped to interventions table.

### Data Source
The `interventions` table has: `id`, `title`, `description`, `intervention_type` (PRACTICE/TRAINING), `priority`, `competency_id`, `subskill_id`.
For tasks, mock data should mirror this shape plus a `status` and `progress` field that will be added to the backend later.

### Mock Data Shape (matches interventions table + frontend extensions):
```json
{
  "tasks": [
    {
      "id": 1,
      "title": "Sampling practice task",
      "description": "Practice sampling design methodology...",
      "type": "PRACTICE",
      "competency_name": "Sampling Design",
      "priority": 1,
      "status": "active",
      "progress_pct": 60,
      "due_date": "2026-09-15"
    }
  ],
  "summary": {
    "active": 2,
    "completed": 1,
    "total": 3
  }
}
```

### Layout:
```
┌────────────────────────────────────────────────────────────────────┐
│ H2: "Tasks"                                                        │
│ Subtitle: "Practical tasks and practice assignments"               │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ROW 1 — 3 STAT CARDS                                               │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────┐ │
│ │ Active           │ │ Completed        │ │ Total                │ │
│ │ 2                │ │ 1                │ │ 3                    │ │
│ │ min-h: 120px     │ │ min-h: 120px     │ │ min-h: 120px         │ │
│ └──────────────────┘ └──────────────────┘ └──────────────────────┘ │
│ grid-cols-3, gap-4                                                 │
│                                                                    │
├────────────────────────────────────┬───────────────────────────────┤
│                                    │                               │
│ TASK PROGRESS (col-span-7)         │ BREAKDOWN (col-span-5)       │
│ Horizontal stacked bar per task    │ Simple horizontal bar:       │
│ showing progress %                 │ ■ Active ■ Completed         │
│ Recharts BarChart layout=vertical  │                               │
│ min-h: 300px                       │ + count labels               │
│                                    │ min-h: 300px                 │
│                                    │                               │
├────────────────────────────────────┴───────────────────────────────┤
│                                                                    │
│ TASK LIST TABLE (full width)                                       │
│ Title | Type | Competency | Priority | Progress | Status | Actions │
│                                                                    │
│ Progress column: inline progress bar (colored by %)                │
│ Status column: badge (active=blue, completed=teal, not_started=   │
│                       slate)                                       │
│ Actions: eye icon to view details                                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Micro-interactions:
- Progress bars animate from 0 to target width on mount (400ms)
- Table rows fade-in staggered (30ms per row)
- Stacked bars grow with Recharts built-in animation (500ms)
- Badge hover shows tooltip with full status text

---

## 10. Section 4: Workforce Overview

> **Route:** `/dashboard/workforce`
> **Backend endpoint:** `GET /api/admin/analytics/competencies`
> **Access:** Admin role only (backend uses `get_current_admin` dependency)

### Data Mapping (direct from API response):

| UI Element | Data Source |
|---|---|
| Total learners | Sum of unique `learner_count` across competencies |
| Avg mastery | Average of `competencies[].average_mastery` (skip nulls) |
| Assessed vs total | Sum of `assessed_count` vs sum of `learner_count` |
| Status distribution | `competencies[].status_distribution` dict |
| Per-competency breakdown | Direct from each entry in `competencies[]` |

### Layout:
```
┌────────────────────────────────────────────────────────────────────┐
│ H2: "Workforce Overview"                                           │
│ Subtitle: "Competency analytics across all learners"               │
│ [ADMIN VIEW badge]  [DEMO DATA badge]                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ROW 1 — 4 STAT CARDS                                               │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────┐│
│ │ Learners      │ │ Avg Mastery   │ │ Assessed      │ │ Evidence ││
│ │ 24            │ │ 58%           │ │ 18 of 24      │ │ 42 total ││
│ │ min-h: 120px  │ │ min-h: 120px  │ │ min-h: 120px  │ │ min-h:   ││
│ └───────────────┘ └───────────────┘ └───────────────┘ └──────────┘│
│ grid-cols-4 (lg), grid-cols-2 (sm), gap-4                          │
│                                                                    │
├──────────────────────────────┬─────────────────────────────────────┤
│                              │                                     │
│ STATUS DISTRIBUTION          │ COMPETENCY COMPARISON              │
│ (col-span-5)                 │ (col-span-7)                       │
│                              │                                     │
│ Donut/Ring Chart             │ Grouped Horizontal Bar Chart       │
│ Recharts PieChart            │ Recharts BarChart layout=vertical  │
│ innerRadius=60               │                                     │
│                              │ Each competency as a row:          │
│ Segments:                    │ ─ avg_mastery (blue bar)           │
│ ■ ASSESSED (blue)            │ ─ avg_confidence (teal bar)        │
│ ■ UNASSESSED (slate)         │ ─ avg_coverage (amber bar)         │
│ ■ CONFLICTING (amber)        │                                     │
│                              │ Legend: Mastery | Confidence |      │
│ Center: total count          │ Coverage                           │
│ min-h: 340px                 │ min-h: 340px                       │
│                              │                                     │
├──────────────────────────────┴─────────────────────────────────────┤
│                                                                    │
│ COMPETENCY TABLE (full width)                                      │
│ Competency | Role | Learners | Assessed | Avg Mastery | Avg Conf  │
│            |      |          |          | | Avg Cov | Evidence     │
│                                                                    │
│ Each row shows a competency with its analytics from the API        │
│ Sortable by any column (click header to sort)                      │
│ Mastery cell: number + inline progress bar                         │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Charts on this page:

1. **Donut Chart** (Recharts `<PieChart>` with `innerRadius`)
   - Shows ASSESSED vs UNASSESSED distribution summed across all competencies
   - Center label: total learner count
   - Colors: blue-500 (assessed), slate-300 (unassessed), amber-500 (conflicting)
   - Animation: segments sweep clockwise, 600ms

2. **Grouped Horizontal Bar Chart** (Recharts `<BarChart layout="vertical">`)
   - One row per competency
   - Three bars per row: avg_mastery, avg_confidence, avg_coverage
   - Colors: blue-500, teal-500, amber-500
   - Animation: bars grow left-to-right, 500ms, 50ms stagger between rows

### Micro-interactions:
- Chart tooltips show exact values on hover with fade animation
- Donut segments highlight (opacity increase) on hover
- Bar chart bars darken slightly on hover
- Table headers show sort arrow on click
- Stat card numbers count-up from 0 on mount (600ms)

---

## 11. Section 5: Competency Map

> **Route:** `/dashboard/map`
> **Backend endpoints:** `GET /api/competencies/{role_id}` + `GET /api/dashboard/learner` for state

### Purpose
Visual map of the competency → subskill hierarchy with the learner's current state overlaid.

### Data Mapping
- **Competencies** from `GET /api/competencies/{role_id}` gives `{id, name, description}`
- **State** from `GET /api/dashboard/learner` gives mastery/confidence/coverage per competency
- **Subskills** — not directly exposed in current API. For now, show competency-level only. When backend adds a subskills endpoint, expand the tree.

### Layout:
```
┌────────────────────────────────────────────────────────────────────┐
│ H2: "Competency Map"                                               │
│ Subtitle: "Your role's competency structure and progress"          │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ ROW 1 — 3 STAT CARDS                                               │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────┐ │
│ │ Competencies     │ │ Assessed         │ │ Avg Coverage         │ │
│ │ 3 total          │ │ 2 of 3           │ │ 25%                  │ │
│ └──────────────────┘ └──────────────────┘ └──────────────────────┘ │
│ grid-cols-3, gap-4                                                 │
│                                                                    │
├────────────────────────────────┬───────────────────────────────────┤
│                                │                                   │
│ COMPETENCY TREE (col-span-7)   │ SELECTED DETAIL (col-span-5)    │
│                                │                                   │
│ Expandable tree view           │ Shows details of clicked node    │
│ Each node = 1 competency       │                                   │
│                                │ Name: Sampling Design            │
│ 📁 Statistical Officer         │ Mastery: 42%                     │
│ ├── Sampling Design  [42%]     │ Confidence: 35%                  │
│ ├── Data Quality     [—]       │ Coverage: 25%                    │
│ └── Python Analytics [—]       │ Evidence: 2 records              │
│                                │ Status: ASSESSED                 │
│ Click to select, highlight     │                                   │
│ active node with blue bg       │ Description: "Sample competency  │
│                                │ ..."                             │
│ min-h: 400px                   │ min-h: 400px                     │
│                                │                                   │
├────────────────────────────────┴───────────────────────────────────┤
│                                                                    │
│ COVERAGE BAR CHART (full width)                                    │
│ Horizontal bars, one per competency                                │
│ Bar fill = coverage percentage, color by mastery status            │
│ Recharts BarChart layout=vertical                                  │
│                                                                    │
│ Sampling Design    ████████████░░░░░░░░░░░░  25%  (assessed)       │
│ Data Quality       ░░░░░░░░░░░░░░░░░░░░░░░░  0%  (unassessed)     │
│ Python Analytics   ░░░░░░░░░░░░░░░░░░░░░░░░  0%  (unassessed)     │
│                                                                    │
│ min-h: 200px                                                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Tree View Component:
- Not a chart — it's a custom component with expandable/collapsible rows
- Each row: icon (folder for role, file for competency) + name + mastery badge
- Click to select → updates the right panel
- Mastery badge colors: teal (≥70%), amber (40-70%), rose (<40%), slate (unassessed)
- Expand/collapse with chevron rotation animation (200ms)

### Micro-interactions:
- Tree node hover: background slate-50, 150ms transition
- Tree node click: blue-50 background, left border blue-500 appears
- Detail panel content cross-fades when switching nodes (200ms)
- Coverage bars animate from 0 to target width (400ms)
- Stat card numbers count-up animation

---

## 12. Chart & Graph Specifications

### Recharts Configuration (Apply to ALL charts)

```tsx
// Standard chart wrapper pattern:
<ResponsiveContainer width="100%" height="100%">
  <SomeChart>
    {/* Always include: */}
    <Tooltip
      contentStyle={{
        background: "#fff",
        border: "1px solid #E2E8F0",
        borderRadius: "8px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
        padding: "8px 12px",
        fontSize: "12px",
      }}
    />
  </SomeChart>
</ResponsiveContainer>
```

### Chart-Specific Config:

**Radar Chart (Learner Dashboard):**
- `<RadarChart cx="50%" cy="50%" outerRadius="80%">`
- Two `<Radar>` polygons: current (filled, blue-500 at 20% opacity) and target (dashed, slate-400 stroke)
- `<PolarGrid stroke="#E2E8F0" />`
- `<PolarAngleAxis tick={{ fontSize: 12, fill: "#64748B" }} />`
- Animation: `animationDuration={800}`

**Donut Chart (Workforce):**
- `<PieChart>` with `<Pie innerRadius={60} outerRadius={90}>`
- Custom center label component showing total count
- `animationDuration={600} animationEasing="ease-out"`
- `<Cell>` per segment with hover opacity increase

**Horizontal Bar Chart (Workforce, Tasks, Map):**
- `<BarChart layout="vertical" barSize={20} barGap={4}>`
- `<YAxis type="category" width={150} tick={{ fontSize: 12 }} />`
- `<XAxis type="number" domain={[0, 100]} />`
- `animationDuration={500}`
- Round bar corners: `radius={[0, 4, 4, 0]}`

### Dynamic Import Rule:
All Recharts components must be dynamically imported with `next/dynamic` and `ssr: false` to avoid SSR issues and reduce initial bundle:

```tsx
const CompetencyRadar = dynamic(
  () => import("@/components/ui/dashboard/CompetencyRadar").then(m => m.CompetencyRadar),
  { ssr: false, loading: () => <ChartSkeleton /> }
);
```

---

## 13. Build Priority

| Priority | Section | Route | Complexity | Dependencies |
|---|---|---|---|---|
| 0 ⚡ | **AI Slop Cleanup** on existing dashboard | `/dashboard` | Low | None — just rename/remove |
| 1 🔵 | **Assessments** | `/dashboard/assessments` | Medium | Backend: `assessment/next`, `assessment/submit` |
| 2 🟢 | **Tasks** | `/dashboard/tasks` | Medium | Mock only for now (interventions table) |
| 3 🟡 | **Workforce** | `/dashboard/workforce` | Medium-High | Backend: `admin/analytics/competencies` |
| 4 🟣 | **Competency Map** | `/dashboard/map` | Medium | Backend: `competencies/{role_id}` + dashboard |

### For your friend — build order:

**Step 0:** Clean up existing dashboard (rename labels, remove AI slop, remove Agent Activity Strip, simplify NBA card). This takes ~1 hour.

**Step 1:** Build Assessments page — this is the most critical because it's the interactive assessment flow that connects to the live backend and actually creates evidence.

**Step 2:** Build Tasks page — simpler UI, can use mock data since no backend endpoint exists yet.

**Step 3:** Build Workforce page — admin-only, directly maps to existing backend endpoint.

**Step 4:** Build Competency Map page — visual layer on top of existing competency data.

---

## File Structure

```
app/dashboard/
├── page.tsx                              # ✅ Built (needs cleanup)
├── layout.tsx                            # ✅ Built (needs sidebar rename)
├── loading.tsx                           # ✅ Built
├── assessments/
│   └── page.tsx                          # 🆕
├── tasks/
│   └── page.tsx                          # 🆕
├── workforce/
│   └── page.tsx                          # 🆕
└── map/
    └── page.tsx                          # 🆕

components/ui/
├── dashboard/                            # ✅ Exists — cleanup needed
│   ├── MetricCard.tsx                    # ✅ Keep, rename labels
│   ├── CompetencyRadar.tsx               # ✅ Keep, rename heading
│   ├── ActiveGapCard.tsx                 # ✅ Keep, simplify
│   ├── NextBestActionCard.tsx            # ✅ Rewrite to match backend NBA shape
│   ├── AgentActivityStrip.tsx            # ❌ DELETE (no backend endpoint)
│   ├── DashboardContext.tsx              # ✅ Keep
│   ├── SandboxBadge.tsx                  # ✅ Keep, change text to "DEMO DATA"
│   └── states/                           # ✅ Keep all
├── assessments/                          # 🆕
│   ├── AssessmentStatCards.tsx
│   ├── CompetencyAssessmentCard.tsx
│   ├── QuestionPanel.tsx
│   └── ResultsPanel.tsx
├── tasks/                                # 🆕
│   ├── TaskStatCards.tsx
│   ├── TaskProgressChart.tsx
│   └── TaskListTable.tsx
├── workforce/                            # 🆕
│   ├── WorkforceStatCards.tsx
│   ├── StatusDistributionDonut.tsx
│   ├── CompetencyComparisonChart.tsx
│   └── CompetencyAnalyticsTable.tsx
└── map/                                  # 🆕
    ├── MapStatCards.tsx
    ├── CompetencyTree.tsx
    ├── NodeDetailPanel.tsx
    └── CoverageBarChart.tsx

lib/mock/
├── officer-jso.json                      # ✅ Exists — reshape to match API
├── officer-new.json                      # ✅ Exists — reshape to match API
├── tasks-mock.json                       # 🆕
└── workforce-mock.json                   # 🆕 (or derive from dashboard data)
```
