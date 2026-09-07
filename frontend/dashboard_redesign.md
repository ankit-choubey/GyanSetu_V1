# GyanSetu Dashboard — Authenticity Redesign Guide

> **What this file is:** A section-by-section instruction sheet to make the *already-built* dashboard stop looking AI-generated and start looking like a real, premium government data product — **without rewriting logic**. You touch classNames, markup structure, copy, and a few token values. You do **not** touch data fetching, state, hooks, or API wiring.
>
> **The prime directive (read twice):** *Keep the existing design pattern.* This is a **tightening pass**, not a new design. Same light theme, same blue accent, same card-based layout, same file structure. We are **removing noise**, not adding features. Where this guide says "change," it means a small, surgical change (a color, a radius, a font on numbers, a line of copy). Box sizes and spacing may be nudged — never overhauled.
>
> **Out of scope for now:** animations/motion (leave the existing Framer Motion as-is), backend, and new pages.
>
> **Companion files:** [`dashboard_plan.md`](dashboard_plan.md) (build spec + API contract + AI-slop list) and [`design_plan.md`](design_plan.md) (landing tokens). This file is the *design-quality* layer that sits on top of both.

---

## 0. The Verdict — Current Score

**Current dashboard design: 6.0 / 10.** It's competently built and structurally sound — good empty/loading/error states, real accessibility (sr-only tables), sensible grids. But it reads "AI-generated" because of five specific, fixable habits: **too many accent colors, gradient decoration, a display font on data, inconsistent radii/shadows, and inflated jargon copy.**

| Dimension | Now | After this redesign | Why |
|---|---|---|---|
| Layout & information hierarchy | 7 | 9 | Already good; whitespace + fewer boxes will sharpen it |
| **Color discipline** | **4** | **9** | Biggest problem: rose/amber/purple/emerald/indigo/teal/blue all at once |
| Typography (esp. numbers) | 5 | 9 | Bebas Neue on data + uppercase overuse reads "poster," not "product" |
| Consistency (radius/shadow/spacing) | 5 | 9 | 4 radii, 5 shadows, ad-hoc paddings create subtle visual noise |
| Microcopy / voice | 4 | 9 | "Processing Knowledge Engine", "semantic knowledge nodes" = slop |
| Component craft / detail | 6 | 8 | Chip/icon-tile overuse; nested cards |
| Data-viz restraint | 6 | 8 | Rainbow chart series; loud status-tinted cards |

**Target after redesign: 9.0 / 10.** That is achievable with *only* the surgical edits below — no new libraries, no motion work, no logic changes.

> **The one sentence that explains everything below:** premium dashboards (Linear, Stripe, Attio, Ramp, Vercel) look premium because of **restraint** — *one* accent color, color used **only** to mean status, calm typography with aligned numbers, and one radius + one shadow. AI output looks generic because it does the opposite: every card a different color, a gradient on everything, a big display number, and boxes nested three deep. We are converting from the second thing to the first.

---

## 1. Why It Looks "AI-Generated" — Diagnosis From the Real Code

Each item below is a concrete pattern found in *your* files, with the fix. These are the root causes; Part 3 applies them per section.

### AI-Tell #1 — Rainbow accent soup (the #1 offender)
The palette is disciplined on paper (`dashboard_plan.md §5`) but the code uses **seven** accent hues at once. Worst case: [`IngestionHub.tsx`](frontend/components/ui/dashboard/IngestionHub.tsx) gives each of the 4 upload cards its **own** color (rose / blue / amber / purple), then adds emerald "Staged" badges, then indigo/blue/teal left-borders on catalog cards. The assessments tiers add emerald/amber/purple strips ([`assessments/page.tsx:152`](frontend/app/dashboard/assessments/page.tsx)).
**Rule:** *Color = state, never decoration.* Neutral by default (white + slate). Blue = the single brand/interaction accent. Teal / amber / rose reserved **only** for high / medium / low status. Kill purple, emerald, indigo, rose-as-decoration entirely. (Emerald→teal, purple→slate or blue.)

### AI-Tell #2 — Gradients as decoration
Gradient top-stripes ([`NextBestActionCard.tsx:30`](frontend/components/ui/dashboard/NextBestActionCard.tsx) `from-blue-600 via-indigo-600 to-teal-400`), gradient card fills (`bg-gradient-to-b from-rose-50/30 via-white to-white` ×4 in IngestionHub), gradient icon tiles.
**Rule:** No decorative gradients in the app. A flat 1px colored top-border or a solid `bg-blue-600` is more premium than a 3-color gradient. Keep gradients only on the *landing page*, not the product.

### AI-Tell #3 — A display font on data
Bebas Neue (`font-heading`) is a condensed **poster** font. It's used for KPI numbers (`text-4xl/5xl`) in [`MetricCard.tsx:72`](frontend/components/ui/dashboard/MetricCard.tsx) and stat values in [`ActiveGapCard.tsx:90`](frontend/components/ui/dashboard/ActiveGapCard.tsx). Display fonts don't align numerically and scream "marketing."
**Rule (highest-impact typographic change):** Use Bebas Neue **only** for card/section *titles* (brand continuity). Render every **number** (KPI values, %, table figures, scores, counts) in **Inter with `tabular-nums`**, weight 600–700, tight tracking. This single change does more for "authentic data product" than anything else. See §2.3.

### AI-Tell #4 — Uppercase + mono everywhere
`uppercase tracking-wider` is sprinkled on labels, badges, statuses, table headers, sublabels. Overuse flattens hierarchy and feels templated.
**Rule:** Uppercase micro-labels allowed in **one** role only — the tiny eyebrow/section label. Everywhere else use sentence case. Reserve `font-mono` for genuinely machine values (IDs, tokens), not human labels like "Conf: High".

### AI-Tell #5 — Boxes inside boxes inside boxes
Cards contain bordered sub-cards containing bordered chips. E.g. ActiveGapCard: a bordered card → a 2×2 grid of bordered `bg-slate-50` stat boxes → each with its own border. IngestionHub: bordered section → bordered dropzone card → bordered inner file chip.
**Rule:** Max **one** level of border nesting. Inside a card, separate content with **whitespace and hairline dividers** (`border-slate-100`), not more bordered boxes. A stat inside a card needs a label + number, not its own border+background.

### AI-Tell #6 — Inconsistent radius, shadow, spacing scales
Radii in use: `rounded-md`, `rounded-lg`, `rounded-xl`, `rounded-2xl`, `rounded-[28px]`, `rounded-full`. Shadows: `shadow-2xs`, `shadow-xs`, `shadow-sm`, `shadow-md`, `shadow-xl`, plus a custom 2-layer string. Paddings hop between `p-3/3.5/4/5/6/7`.
**Rule:** One card radius (`rounded-xl` = 12px), one control radius (`rounded-lg` = 8px), pills only for true pills. One resting shadow token, one hover shadow token (§2.5). Spacing on the 4-based scale only (`p-4`, `p-5`, `p-6`, `gap-4`, `gap-6`).

### AI-Tell #7 — Status-tinted whole cards
MetricCard tints its **entire** background/border by value (teal-50/amber-50/rose-50). A wall of pastel-tinted cards looks toylike.
**Rule:** KPI cards stay **white**. Encode status with a small colored number, a 2px value-colored underline, or a single dot — not a full card tint.

### AI-Tell #8 — Chip & icon-tile overload
Every row gets a colored rounded icon tile (`w-9 h-9 rounded-xl bg-x-100`) and multiple pill badges ("Staged", type, "Conf: High" with a shield, difficulty, status…).
**Rule:** One icon tile per card *header* max. At most one status chip visible per element at rest. Icons are `text-slate-400` (neutral) unless they carry status meaning.

### AI-Tell #9 — Numbered "walkthrough" section headers
Colored number circles ("1", "2") before section titles in IngestionHub ([`:192`, `:517`](frontend/components/ui/dashboard/IngestionHub.tsx)) are a classic AI-tutorial look.
**Rule:** Replace with a plain title + one-line subtitle (a small neutral icon is fine). Steps belong in a flow, not as decoration on panels.

### AI-Tell #10 — Inflated jargon copy ("AI slop")
"Processing Knowledge Engine…", "Segmenting into Semantic Knowledge Chunks", "Cross-Modal Deduplication", "Vector Store Indexing & 3-Tier Generation", "semantic knowledge nodes indexed", "Ingestion & Calibration Complete". `dashboard_plan.md §2` already flagged much of this — it's still in the code.
**Rule:** Plain, confident, government-grade language. "Processing", "Extracting text", "Indexing content", "Ready". See the rewrite table in §4.

### AI-Tell #11 — Decorative hardcoded numbers
"Target: 80%" / "Benchmark (80%)" appear as literals in several places, presented like data.
**Rule:** If it's a real target, source it once and label it "Role target"; if it's illustrative, keep it but don't dress it as a measured metric. (Consistent with `design_plan.md §2.9`.)

### AI-Tell #12 — Everything the same visual weight
Because every block is a white card with the same border/shadow, nothing leads. Eye-tracking shows users scan top-left first and want 3–7 primary things above the fold.
**Rule:** Establish weight: the hero row (KPIs) and the primary chart are visually dominant; tables and secondary panels recede (lighter borders, no shadow, more whitespace).

---

## 2. The Tightened Design System (apply globally, then per section)

> Put these as literal rules at the top of your mental model. Where practical, encode them as small shared components (§2.8) so every section inherits them instead of re-deriving colors.

### 2.1 Negative constraints (what NOT to do — the part AI skips)
- ❌ No more than **one** accent color (blue) in any non-status context.
- ❌ No gradients anywhere in `/dashboard`.
- ❌ No purple, emerald, or indigo in the app UI. (Charts: see §2.6.)
- ❌ No `rounded-2xl`, `rounded-[Npx]`, `border-2` on cards, or multi-stop shadows.
- ❌ No Bebas Neue on numbers.
- ❌ No card-background tinting by status.
- ❌ No `uppercase tracking-wider` except the single eyebrow label role.
- ❌ No bordered box inside a bordered box inside a bordered box.

### 2.2 Color = state (the whole color system in five lines)
| Meaning | Token | Where it may appear |
|---|---|---|
| Neutral / surface | white card, `slate-50` page, `slate-100/200` borders, `slate-400/500/900` text | everywhere by default |
| Brand / interactive | `blue-600` (actions), `blue-50`+`blue-200` (active/selected) | buttons, links, active nav, focus |
| High / good | `teal-600` text, `teal-500` bar, `teal-50`/`teal-200` chip | status only |
| Medium / developing | `amber-600` text, `amber-500` bar, `amber-50`/`amber-200` chip | status only |
| Low / needs work | `rose-600` text, `rose-500` bar, `rose-50`/`rose-200` chip | status only |
| Unassessed | `slate-500` text, `slate-100`/`slate-200` chip | the "no evidence" state |

That's it. If a color isn't communicating one of these states, it shouldn't be there.

### 2.3 Typography
- **Titles** (card headings, section headings): keep `font-heading` (Bebas Neue), sentence case, `tracking-normal`. Sizes: page/section title `text-xl`–`text-2xl`; card title `text-lg`.
- **Numbers / data**: `font-body` (Inter), `font-semibold`/`font-bold`, add `tabular-nums`, `tracking-tight`. KPI hero number `text-3xl`–`text-4xl` (down from `5xl` — smaller + tabular reads more precise). Table/stat numbers `text-sm`–`text-base`.
- **Body / labels**: Inter, sentence case, `text-slate-600`/`text-slate-500`. Labels `text-xs`.
- **Eyebrow label** (the *one* uppercase role): `text-[11px] font-medium uppercase tracking-wider text-slate-400`. Use for the small label above a title only.
- **Mono** (`font-mono`): only IDs/tokens (session id, codes), never human labels.
- Add `tabular-nums` globally to numeric cells so figures align in columns.

### 2.4 Radius & border
- Cards / panels / modals / chart containers: `rounded-xl` (12px), `border border-slate-200`.
- Buttons / inputs / dropzones / chips-that-aren't-pills: `rounded-lg` (8px).
- True pills (status chips): `rounded-full`.
- Dropzones: `border border-dashed` (not `border-2`).
- Inner dividers: `border-slate-100` (lighter than the card's `slate-200`).

### 2.5 Shadow (only two tokens)
- Resting card: `shadow-sm` **or** no shadow (prefer border-only for secondary panels).
- Interactive hover: `hover:shadow-md`.
- Delete every `shadow-2xs`, `shadow-xs`, `shadow-xl`, and custom shadow strings from `/dashboard`. Modals may use `shadow-lg`.
- Premium tip: **borders over shadows.** Lean on `border-slate-200` and whitespace; use shadow sparingly for genuine elevation (modals, hover).

### 2.6 Data-viz rules (charts)
- Primary series: `blue-600`. Comparison/benchmark: `slate-400` dashed. That's the default — two colors.
- When a chart legitimately needs multiple categorical series, use a **single-hue sequential blue ramp** (`blue-700 → blue-500 → blue-300 → slate-300`), not a rainbow. Only use teal/amber/rose in a chart when the segments **mean** high/med/low.
- Gridlines muted (`slate-200`, dashed ok), no chart drop-shadows, no gradient fills. Radar keeps its current calm blue fill (`fillOpacity ~0.18`) — that one's already right.
- Tooltips: dark `slate-900` card is fine (already used) — keep it consistent everywhere.

### 2.7 Density & spacing
- Page content already uses full width (`p-4 sm:p-8`) — good, keep it.
- Section rhythm: `space-y-6` (down from `space-y-8` where it feels sparse; pick one and use it everywhere — recommend `space-y-6`).
- Inside cards: `p-5` for stat cards, `p-6` for panels/charts/tables. One divider between header and body (`border-slate-100`).
- Let panels breathe: reduce oversized min-heights (e.g. IngestionHub dropzones `min-h-[220px]` → `~min-h-[176px]`; ActiveGapCard `min-h-[360px]` is fine to match the radar).

### 2.8 Standardize into shared primitives (do this first — it fixes most tells at once)
Create/adopt these tiny wrappers and use them **everywhere** so no section re-invents colors. (Pure presentational; no logic.)
- `Card` — `bg-white border border-slate-200 rounded-xl` (+ optional `shadow-sm`, `hover:shadow-md`). One place that owns card styling.
- `StatCell` — label (eyebrow) + big `tabular-nums` number + optional sublabel + optional status color. No border, no bg (lives inside a Card).
- `StatusChip` — `size` + `status: high|med|low|unassessed|info`; renders the exact §2.2 colors as a `rounded-full` pill. Replaces every ad-hoc badge.
- `IconTile` — `w-8 h-8 rounded-lg bg-slate-100 text-slate-500` by default; a `tone="brand"` variant = `bg-blue-50 text-blue-600`. One tile per card header.
- `SectionHeader` — eyebrow + title + subtitle + optional right-aligned action. Replaces numbered-circle headers.
- `Divider` — `border-t border-slate-100`.

If you standardize these six, ~70% of the "AI look" disappears before you touch individual pages.

---

## 3. Section-by-Section Redesign

Each section: **Keep** (don't break it), **Change** (surgical fixes), **Box/size nudges** (the small dimensional tweaks the brief allows).

### 3.1 The Shell — Sidebar + Collapse + Top Bar  ([`app/dashboard/layout.tsx`](frontend/app/dashboard/layout.tsx))
This is the frame around everything, so fixing it lifts the whole product. The user specifically called out the **top bar** and the **sidebar collapse** — here's exactly how to make both feel intentional.

**Keep:** the fixed left sidebar, the collapse-to-`w-20` behavior, the mobile drawer, the sticky top bar, the persona switcher, the auth gate.

**Change (sidebar):**
- The collapse toggle currently lives in the footer labeled "Collapse Sidebar" with a `Menu` (hamburger) icon — a hamburger doesn't read as "collapse." Move a **single chevron toggle** (`PanelLeftClose` / `PanelLeftOpen`, or `ChevronsLeft`/`ChevronsRight`) to the **top-right of the brand header**, so collapse control sits where users expect it. Keep it in the footer too if you like, but use the chevron icon, not the hamburger.
- Collapsed state polish: when `isCollapsed`, center every icon, hide labels (already done), and ensure the active item's left accent bar (`border-l-[3px] border-blue-600`) still shows. Add `title=` tooltips on every collapsed item (already present — good).
- Active item: keep `bg-blue-50 text-blue-700` + left accent. Remove the `pl-[9px]` magic number; use consistent padding and let the 3px border sit inside.
- The "Admin" badge on Workforce: make it a `StatusChip status="info"` (neutral slate), not blue-on-active — it's a role tag, not a state.
- Footer: three actions (collapse / home / sign-out) stacked is fine. Sign-out stays the only colored (rose) item — that's correct (destructive = the one place rose-as-action is allowed).
- **Motion of content:** the main container already shifts `lg:pl-20 ↔ lg:pl-60` with `transition-all` — keep. Just confirm the top bar spans the content area (it does, since it's inside the shifted container).

**Change (top bar / "bar two"):**
- It currently mixes: hamburger (mobile), user name as an `h1` in Bebas Neue, an "OFFICIAL SESSION" `SandboxBadge`, role•dept subtitle, a persona segmented control, an avatar, and a duplicate logout. That's a lot competing at 56px tall.
- Hierarchy fix: **left** = page/context title (not the user's name — the user is shown by the avatar). Put the **current section name** here (e.g. "Dashboard", "Data Ingestion") in `font-heading text-lg`, with a light breadcrumb/subtitle if useful. Move the user's name+role into an avatar menu on the right.
- **Right cluster order:** persona switcher → a thin `Divider` (vertical `w-px h-6 bg-slate-200`) → avatar (opens a small menu containing name, role, dept, and Sign out). Remove the standalone logout icon button (it duplicates the sidebar and the future avatar menu).
- Persona switcher: keep the segmented control but neutralize it — inactive `text-slate-500`, active `bg-white text-slate-900 shadow-sm` inside a `bg-slate-100 rounded-lg` track. Label it quietly ("View as") so judges know it's a demo tool without it shouting.
- `SandboxBadge` "OFFICIAL SESSION": keep a badge, but if data is mock, it should honestly read a calm `Demo data` (`StatusChip status="info"`), per the honesty rule — not "OFFICIAL SESSION," which overclaims.
- Backdrop: `bg-white/95 backdrop-blur` border-bottom is fine (this is the one acceptable glass surface). Keep it subtle.

**Box/size nudges:** sidebar `w-60` / `w-20` are good. Top bar: keep ~`h-14`/`py-3`. Ensure brand header height matches the top-bar height (currently `h-[61px]` vs top bar `py-3` — align both to the same value, e.g. 60px, so the sidebar top and content top edges line up perfectly — misaligned header seams are a subtle "unfinished" tell).

### 3.2 Learner Dashboard  ([`app/dashboard/page.tsx`](frontend/app/dashboard/page.tsx), `MetricCard`, `CompetencyRadar`, `ActiveGapCard`, `NextBestActionCard`)

**Keep:** the 4-KPI row → radar(7)+gap(5) → NBA → breakdown table structure. It's a textbook, correct hierarchy. Keep the empty/loading/error states and the sr-only radar table.

**Change — KPI row (`MetricCard`):**
- **Un-tint the cards.** All four KPI cards are white (`bg-white border-slate-200`), always. Delete the `statusColor` background/border logic. Encode status three calmer ways instead: (a) the number's text color (teal/amber/rose per §2.2), (b) a 2px status-colored rule under the number, or (c) a tiny status dot by the label. Pick one and use it for all four.
- **Numbers → Inter `tabular-nums`.** Replace `font-heading text-4xl/5xl` on the value with `font-body font-bold text-3xl tabular-nums tracking-tight`. Keep "Unassessed" as a smaller sentence-case label with the neutral state, not a giant Bebas word.
- Drop the shield-icon "Conf: High" chip clutter; if you show confidence on a card, use a plain `StatusChip`. Remove the hardcoded "Target: 80%" sublabel unless it's a real, sourced target (then label it "Role target").
- Confidence/Coverage as % is fine — keep the derived values; just render them tabular.

**Change — Competency Radar:** it's the best-looking component already. Only: make the header title Bebas but the legend/labels sentence case (they are), keep the calm blue fill, and change the footer's "Primary Attention: Lowest Mastery Axis" to plain "Focus: lowest-scoring area." Ensure the container radius/shadow match the token (`rounded-xl shadow-sm`). Leave the chart itself alone.

**Change — ActiveGapCard:**
- Remove the top accent strip (or make it a single flat `blue-500`/`rose-500` 2px line, not a decoration). Better: drop it and show priority via a single `StatusChip`.
- The 2×2 stat grid uses four bordered `bg-slate-50` boxes — flatten to a borderless 2×2 of `StatCell`s separated by a hairline divider, or a simple label/value list. Numbers → tabular Inter (not `font-heading text-2xl`).
- Keep the copy honest and plain (it mostly is): "No baseline evidence recorded" / "Below the role target."

**Change — NextBestActionCard:**
- **Delete the 3-color gradient stripe** (`from-blue-600 via-indigo-600 to-teal-400`). Replace with a flat `border-l-4 border-blue-600` on the card, or nothing. That gradient alone is a giant AI tell on the most important card.
- Reduce chips: keep the "Recommended action" chip (brand), drop the indigo type-pill or make it neutral slate. Keep the two reason panels but make them one tone (both `bg-slate-50 border-slate-100`) instead of blue vs teal boxes — the *content* differentiates them, not the color.
- `dashboard_plan.md` notes the backend returns a compact NBA, and the "12 explainability fields" are the target. Present what exists cleanly now (title, why, expected outcome); when the 12 fields arrive, use a "Why this?" expander (progressive disclosure) rather than 12 colored boxes.

**Change — Breakdown table:** already close to Stripe-style. Just: right-align numeric columns, add `tabular-nums`, make the header row sentence-case-ish (or keep the single uppercase eyebrow style consistently), keep the thin mastery bar but use the §2.2 status colors only. Row hover `bg-slate-50` is good.

**Change — modals:** fine and calm already. Match radius (`rounded-xl`) and use one shadow (`shadow-lg`). Keep copy plain ("Start Assessment").

**Box/size nudges:** KPI `min-h-[140px]` good. Consider `gap-4` for the KPI row (tighter, more "dashboard") and keep `gap-6` for the big rows. Hero number down to `text-3xl` (precision > size).

### 3.3 Data Ingestion Hub  ([`components/ui/dashboard/IngestionHub.tsx`](frontend/components/ui/dashboard/IngestionHub.tsx)) — **the biggest visual offender**
This screen has the most "AI" in it: 4 differently-colored dropzones, gradient fills, emerald badges, numbered circles, and jargon copy.

**Keep:** the 3-part flow (upload sources → pick curriculum modules → action bar), the processing stepper, the staged/ingested states, all the logic and refs.

**Change — the 4 upload cards (do this exactly):**
- Make all four cards **identical and neutral**: `bg-white border border-slate-200 rounded-xl`, hover `border-slate-300 hover:shadow-sm`. **Remove** the per-type accent colors and gradient fills (rose/blue/amber/purple → all neutral).
- The type icon tile: neutral `IconTile` (`bg-slate-100 text-slate-500`). The *icon glyph* still differs per type (Youtube/FileText/MonitorPlay/FileAudio) — that's enough differentiation; the color doesn't need to.
- Selected/staged state: this is a real state, so it may use the brand accent — `border-blue-300 ring-1 ring-blue-500/15 bg-blue-50/30` (one accent, subtle), and the "Staged" chip becomes `StatusChip status="high"` (teal) — one chip, not emerald+green mixed.
- Footer line of each card ("Transcribed & Indexed" / "Active"/"Optional"): keep, but neutral; "Active" in teal only when staged.

**Change — numbered section headers:** replace the `1` / `2` colored circles with `SectionHeader` (eyebrow "Step 1" in slate + Bebas title + subtitle). Or a small neutral icon. No colored number chips.

**Change — curriculum catalog cards:** drop the per-category left-border colors (indigo/blue/teal). Use one neutral card; show category as a neutral chip; show difficulty with the §2.2 status scale **only if** difficulty maps to a real risk (otherwise neutral chips). Selected = the blue accent, same as everywhere.

**Change — action bar + stepper copy (rewrite, see §4):** "Ingest & Process Data" → "Process materials"; "Processing Knowledge Engine…" → "Processing…"; the 4 steps → "Extracting text & transcribing", "Segmenting content", "Removing duplicates", "Indexing & building questions"; "semantic knowledge nodes indexed" → "content chunks indexed"; "Ingestion & Calibration Complete" → "Processing complete". Session id stays in `font-mono` (it's a real machine value) — good.

**Box/size nudges:** dropzone `min-h-[220px]` → `min-h-[176px]`; `border-2` → `border`; unify all radii to `rounded-xl`. Grid stays 4-up on `lg`, 2-up on `sm`.

### 3.4 Assessments (3-Tier)  ([`app/dashboard/assessments/page.tsx`](frontend/app/dashboard/assessments/page.tsx), `AssessmentRunner`, `components/ui/assessments/*`)

**Keep:** the 3 gated tier cards, lock/complete states, the runner, session-id header.

**Change:**
- Tier top strips are emerald/amber/purple ([`:152`](frontend/app/dashboard/assessments/page.tsx)). Difficulty **does** map to a scale, so this is a *legit* use of status color — but switch to the §2.2 set: **teal (easy) → amber (medium) → rose (hard)**, and make the strip a thin 2px line, not `h-1.5`. Drop purple entirely.
- The tier name badge (`text-emerald-600 bg-emerald-50 …`) → `StatusChip`. Locked cards: keep `opacity-60` + lock icon; that's a good, honest affordance.
- Numbers (scores, %) → tabular Inter. "Session ID" chip stays mono.
- Titles Bebas, descriptions sentence-case Inter (already are).

**Box/size nudges:** 3-up grid on `md` is right. Equalize card heights (`h-full` already). One radius/shadow token.

### 3.5 Tasks  ([`app/dashboard/tasks/page.tsx`](frontend/app/dashboard/tasks/page.tsx), `TaskStatCards`, `TaskListTable`, `TaskBreakdownCard`, `TaskProgressChart`)
Apply the same primitives; specifics:
**Keep:** stat row + table/breakdown + progress chart pattern.
**Change:** stat cards → white, tabular numbers, status via number color/chip (§3.2 rules). Table → right-aligned tabular numeric columns, `slate-50` hover, hairline row dividers, status as `StatusChip`. Progress chart → single blue series (or teal/amber/rose only if segments mean status), muted gridlines, no gradient/shadow. Task type/priority → neutral or status chips, never a new color per type.

### 3.6 Workforce / Admin Analytics  ([`app/dashboard/workforce/page.tsx`](frontend/app/dashboard/workforce/page.tsx), `WorkforceStatCards`, `CompetencyAnalyticsTable`, `StatusDistributionDonut`, `CompetencyComparisonChart`)
This is where rainbow charts are most tempting.
**Keep:** KPI row → donut + comparison chart → analytics table (a strong exec-overview layout).
**Change:**
- **Donut** (status distribution): use the §2.2 *state* colors mapped to their meaning — Assessed = teal, Unassessed = slate, Conflicting = amber. That's meaningful, not decorative. No third decorative hue. Center label number tabular.
- **Comparison chart** (avg mastery by competency): single blue series with the value-color rule only if you're encoding high/med/low; otherwise all `blue-600`. Muted axes. No gradient bars.
- **Analytics table:** the Stripe pattern — dense, right-aligned tabular numbers, muted gridlines, status chips. Make this the primary surface (largest), charts as summaries above it.
- Stat cards: white, tabular, calm (same as §3.2).

### 3.7 Competency Map  ([`app/dashboard/map/page.tsx`](frontend/app/dashboard/map/page.tsx), `CompetencyTree`, `NodeDetailPanel`, `MapStatCards`, `CoverageBarChart`)
**Keep:** tree/graph + detail panel + coverage chart.
**Change:** node colors encode **state only** (mastery high/med/low via §2.2; unassessed = slate). Edges/links neutral `slate-300`. Selected node = blue ring (the one accent). Detail panel = one Card, stat list not bordered sub-boxes, tabular numbers. Coverage bar chart = single blue (or status scale). No rainbow node categories.

---

## 4. Microcopy Rewrite Table (kill the "AI slop")
Plain, confident, government-appropriate. (Extends `dashboard_plan.md §2`.)

| Current (slop) | Replace with |
|---|---|
| "Processing Knowledge Engine…" | "Processing…" |
| "Segmenting into Semantic Knowledge Chunks" | "Segmenting content" |
| "Cross-Modal Deduplication" | "Removing duplicates" |
| "Vector Store Indexing & 3-Tier Generation" | "Indexing & building questions" |
| "semantic knowledge nodes indexed" | "content chunks indexed" |
| "Ingestion & Calibration Complete" | "Processing complete" |
| "Ingest & Process Data" (button) | "Process materials" |
| "Upload Custom Study Materials" | "Upload materials" (subtitle can explain) |
| "Curriculum Competencies Catalog" | "Curriculum modules" |
| "Ready to extract semantics and calibrate 3-tier adaptive assessment" | "Ready to build your assessment" |
| "OFFICIAL SESSION" (top-bar badge) | "Demo data" (when mock) / real session label (when live) |
| "Primary Attention: Lowest Mastery Axis" | "Focus: lowest-scoring area" |
| "3-Tier Gated Assessment" | "Assessment" (subtitle: "Three levels, unlocked in order") |
| Any "AI-powered / Intelligence Engine / Knowledge Engine" flourish | remove the flourish; name the actual action |

**Voice rule:** name the *action or the fact*, not the technology. A government officer trusts "Indexing content" more than "Vector Store Indexing." Never brag in the UI.

---

## 5. Execution Order & Acceptance Checklist

**Do it in this order (fastest path to the score jump):**
1. Build the six shared primitives (§2.8). *(Half the AI-look gone.)*
2. Global find-and-replace passes: remove gradients; collapse radii to `xl`/`lg`/`full`; collapse shadows to `sm`/`md`; purge purple/emerald/indigo from UI; add `tabular-nums` + Inter to all numbers.
3. Shell (sidebar collapse + top bar) — §3.1.
4. Learner Dashboard — §3.2.
5. Ingestion Hub — §3.3 (biggest visual win).
6. Assessments, Tasks, Workforce, Map — §3.4–3.7.
7. Microcopy pass — §4.

**Acceptance checklist (the redesign is "done" when all true):**
- [ ] Only blue appears as a non-status accent; teal/amber/rose appear **only** as high/med/low status; purple/emerald/indigo appear nowhere in the app UI.
- [ ] Zero gradients under `/dashboard`.
- [ ] Every number is Inter + `tabular-nums`; Bebas Neue appears only on titles.
- [ ] One card radius (`rounded-xl`), one control radius (`rounded-lg`); one resting shadow, one hover shadow.
- [ ] No card tints its whole background by status; KPI cards are white.
- [ ] No bordered box nested inside a bordered box inside a bordered box.
- [ ] `uppercase tracking-wider` appears only on the single eyebrow-label role.
- [ ] Top bar leads with the section/context, not the user's name; one logout path; honest data badge.
- [ ] Sidebar collapse toggled by a chevron in the brand header; active item + tooltips intact when collapsed.
- [ ] No "Knowledge Engine / semantic nodes / calibration" jargon remains (see §4).
- [ ] At `375 / 768 / 1024 / 1440` px: no horizontal scroll; grids collapse cleanly.
- [ ] Re-score against §0 table — target 9/10.

**Definition of "fantastic" (your word):** a stranger looking at the dashboard should be unable to tell it was AI-assisted — it should read as a calm, confident, single-accent government analytics product where **color always means something**, numbers align, and nothing decorative competes with the data.

---

## 6. References (where these principles come from)

**Why AI UI looks generic + how to fix it:**
- [Why Your AI-Generated UI Looks Like Everyone Else's (Medium)](https://medium.com/@Rythmuxdesigner/why-your-ai-generated-ui-looks-like-everyone-elses-and-how-to-break-the-pattern-7a3bf6b070be)
- [Spot the Slop: Fixing AI Defaults (Mania Design)](https://www.mania.design/blog/spot-the-slop-a-ui-designers-guide-to-fixing-ai-defaults/)
- [How to Fix AI-Generated UI: Anti-Patterns Guide (BSWEN)](https://docs.bswen.com/blog/2026-03-20-ai-generated-ui-anti-patterns/)
- [Why Your AI Keeps Building the Same Purple Gradient (prg.sh)](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website)
- [Design Systems for AI Coding: Stop Getting Purple Gradients (Braingrid)](https://www.braingrid.ai/blog/design-system-optimized-for-ai-coding)

**Premium dashboard / CRM references to study (restraint, tables, tabular numbers):**
- [Best Dashboard Design Patterns 2026: 4 Layouts to Steal](https://artofstyleframe.com/blog/dashboard-design-patterns-web-apps/) — Linear (slim chrome, density from type), Stripe (dense tables + tabular numerals + status chips), Attio/Twenty (spreadsheet-fast tables), folk (calm, editorial, skip the wall of charts)
- [How We Designed a CRM Inspired by Linear and Attio (SalesSheet)](https://salessheets.ai/blog/mobile-crm-linear-attio-design/)
- [9 Best CRM Dashboard Examples (AdminLTE)](https://adminlte.io/blog/crm-dashboard-examples/) · [35 SaaS Dashboard Examples (925studios)](https://www.925studios.co/blog/saas-dashboard-design-examples-2026)
- Look directly at: **linear.app**, **stripe.com/dashboard**, **attio.com**, **ramp.com**, **vercel.com/dashboard** — and Dribbble searches for "Linear dashboard", "Attio", "analytics dashboard neutral".

**Dashboard information hierarchy / KPI layout:**
- [Brand.dev — Dashboard Design Best Practices](https://www.brand.dev/blog/dashboard-design-best-practices) · [Setproduct — Dashboard UI: KPIs to layouts](https://www.setproduct.com/blog/dashboard-ui-design)

**Internal:** current code under `frontend/app/dashboard/**` and `frontend/components/ui/**`; [`dashboard_plan.md`](dashboard_plan.md) (§2 AI-slop list, §5 color system) and [`design_plan.md`](design_plan.md) (tokens, `§2.9` data honesty).
