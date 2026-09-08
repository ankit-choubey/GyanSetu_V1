# Implementation Plan: Live Backend Wiring & Dynamic Data Integration with Graceful Baseline Fallbacks

## Goal Description
Wire the GyanSetu frontend to the active, live FastAPI backend endpoints across all 10 identified areas (Workforce Intelligence, Evidence Modal, Competency Map Calibration, Learning Timeline, Next Best Action engine, Tasks Live/Cached indicator, and Assessment backend synchronization).

> [!IMPORTANT]
> **User Architectural Constraint: Dynamic-First with Baseline Fallback Preservation**
> As specified by the user, we must **preserve the baseline mock/seed fallbacks** (`workforce-mock.json`, `tasks-mock.json`, etc.) so that when the database is fresh, unassessed, or when privacy small-cell suppression ($N < 5$) applies, the dashboard **never looks empty or broken**. Live API data is loaded dynamically whenever available, and the system seamlessly falls back to baseline demonstration data when needed.

---

## User Review Required

> [!NOTE]
> - **Dual-Layer Data Fetching Pattern**: Every component will follow the pattern:
>   1. Initialize with sensible baseline fallback data (immediate zero-delay render, no blank flashes).
>   2. Fetch live data from backend endpoint asynchronously in `useEffect`.
>   3. If valid dynamic records are returned, re-render with live data and display a `"Live Synced"` badge.
>   4. If endpoint returns an error, 403, or empty suppressed data, gracefully retain baseline data with a `"Cached / Demonstration View"` badge.
> - **Zero Disruption to Existing Stable Flows**: Port 3000 (Next.js), Port 3003 (iGOT prototype), and Port 8000 (FastAPI) will remain fully operational.

---

## Proposed Changes by Component

---

### Component 1: Core Dashboard & AI Next Best Action Engine

#### [MODIFY] [`main/backend/app/schemas/dashboard.py`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/backend/app/schemas/dashboard.py)
- Add optional `next_best_action: dict | None = None` field to `DashboardResponse` schema matching the frontend's `NextBestActionResponse` structure.

#### [MODIFY] [`main/backend/app/routers/dashboard.py`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/backend/app/routers/dashboard.py)
- Import `NextBestActionService` from `app.services.next_best_action_service`.
- In `get_learner_dashboard`, instantiate `NextBestActionService()` and compute the personalized recommendation record for the authenticated user.
- Map the recommendation into `next_best_action` dictionary with target competency, gap reason, and selected intervention.

#### [NEW] [`main/frontend/components/ui/dashboard/LearningTimeline.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/components/ui/dashboard/LearningTimeline.tsx)
- Reusable timeline feed component that calls `GET /api/competency/timeline`.
- Renders longitudinal progression cards showing:
  - Date & time of learning milestone.
  - Competency name, observed gain, and mastery delta.
  - Retention refresher recommendations.
- Includes realistic baseline timeline items if backend has 0 longitudinal history.

#### [MODIFY] [`main/frontend/app/dashboard/page.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/app/dashboard/page.tsx)
- Connect `NextBestActionCard` to live `data.next_best_action` returned by backend.
- Embed `LearningTimeline` component below the Competency Breakdown table.
- **Post-Assessment Calibration Flash Banner**: Listen to `gyansetu:assessment_updated` event; when returning from an assessment, display an animated banner:
  *"Evidence Calibrated: Tier assessment results ingested into Bayesian competency engine. Updated mastery and confidence scores applied."*

---

### Component 2: Competency Modal & Map Node Deep Inspection

#### [NEW] [`main/frontend/components/ui/competencies/CompetencyEvidenceModal.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/components/ui/competencies/CompetencyEvidenceModal.tsx)
- Interactive slide-over drawer / modal that opens when a user clicks on any competency card or "Inspect Evidence" link.
- Fetches live evidence items from `GET /api/evidence?competency_id={id}`.
- Renders:
  - Full Evidence Pyramid Level (L1: Behavioral $\to$ L6: High-Stakes Exam).
  - Observed score, Bayesian weight, evidence source, provenance, and observation timestamp.
  - Curated baseline evidence records as graceful fallback if zero items are logged yet.

#### [MODIFY] [`main/frontend/components/ui/assessments/CompetencyAssessmentCard.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/components/ui/assessments/CompetencyAssessmentCard.tsx)
- Make the `"Evidence: X recorded items"` badge clickable with an inspection icon, opening the `CompetencyEvidenceModal`.

#### [MODIFY] [`main/frontend/components/ui/map/NodeDetailPanel.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/components/ui/map/NodeDetailPanel.tsx)
- Fetch detailed node telemetry from `GET /api/competency/state/{competency_id}` on node selection.
- Render the 3 missing statistical calibration parameters:
  - **Evidence Diversity**: Distinct evidence modalities collected.
  - **Uncertainty Score**: Posterior distribution variance ($\sigma$).
  - **Last Assessed**: Relative timestamp of most recent evaluation.
- Fetch longitudinal history from `GET /api/competency/history/{competency_id}` and render a mini progress sparkline.

---

### Component 3: Workforce Intelligence & Gap Triage

#### [NEW] [`main/frontend/components/ui/workforce/WorkforceGapTriage.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/components/ui/workforce/WorkforceGapTriage.tsx)
- Component connecting to `GET /api/workforce/gaps`.
- Displays prioritized cadre skill gaps:
  - Competency name & domain.
  - Severity level (`CRITICAL_DEFICIT`, `MODERATE_GAP`, `DEVELOPING`).
  - Triage decision (`ACTIONABLE` vs `NEEDS_MORE_EVIDENCE`).
  - Recommended NSSTA training intervention.
- Graceful baseline fallback with MoSPI survey administration gaps.

#### [MODIFY] [`main/frontend/app/dashboard/workforce/page.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/app/dashboard/workforce/page.tsx)
- In `useEffect`, fetch live data from `GET /api/workforce/competencies` using `client.get`.
- If dynamic data is available and unsuppressed, update state; otherwise retain `workforce-mock.json` fallback.
- Dynamic indicator:
  - When live data is active: `<SandboxBadge label="LIVE WORKFORCE SYNC" variant="success" />`
  - When baseline fallback is active: `<SandboxBadge label="DEMO CADRE BASELINE" variant="neutral" />`
- Embed `WorkforceGapTriage` component below the chart grid.

---

### Component 4: Tasks Live Sync & Assessment Backend Integration

#### [MODIFY] [`main/frontend/app/dashboard/tasks/page.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/app/dashboard/tasks/page.tsx)
- Add `isLiveSync: boolean` state.
- Set `isLiveSync = true` when `/api/practical/learner-tasks` succeeds with items.
- In header, display:
  - Live: `<span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">● Live Practical Sync</span>`
  - Cached: `<span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">○ Curriculum View (Offline)</span>`

#### [MODIFY] [`main/frontend/components/assessments/AssessmentRunner.tsx`](file:///Users/utkarshsingh/Desktop/GyanSetu/main/frontend/components/assessments/AssessmentRunner.tsx)
- On assessment submit, call backend `POST /api/assessment/runner-submit` (or `/api/competency/state`) asynchronously to register the assessment attempt in the database.
- Keep local storage and Test Report Ledger dual-persistence intact so offline / refreshed states remain 100% reliable.

---

## Verification Plan

### Automated Build & Type Checking
1. **TypeScript Typecheck**:
   ```bash
   cd main/frontend && npx tsc --noEmit
   ```
   Ensures zero type mismatches in schemas, new modal props, and API client responses.
2. **Next.js Production Route Build**:
   ```bash
   cd main/frontend && npm run build
   ```
   Ensures all routes compile cleanly with zero server/client hydration errors.

### Functional Verification
1. **Dashboard & NBA Check**:
   - Open `http://localhost:3000/dashboard`.
   - Verify that `NextBestActionCard` appears dynamically with personalized action.
   - Verify that `LearningTimeline` renders below the breakdown table.
2. **Competency Evidence Modal Check**:
   - Click "Evidence: X recorded items" on any competency card.
   - Verify modal opens and renders evidence details from `GET /api/evidence?competency_id=X`.
3. **Competency Map Calibration Check**:
   - Open `http://localhost:3000/dashboard/map`.
   - Click a node. Verify `NodeDetailPanel` shows Evidence Diversity, Uncertainty, and Last Assessed.
4. **Workforce Page & Gap Triage Check**:
   - Open `http://localhost:3000/dashboard/workforce`.
   - Verify Workforce Overview renders data (live or baseline fallback) with the appropriate badge.
   - Verify the new Gap Triage section renders below the charts.
5. **Tasks Page Sync Badge Check**:
   - Open `http://localhost:3000/dashboard/tasks`.
   - Verify header clearly displays either "Live Practical Sync" or "Curriculum View".
6. **Assessment Backend Sync & Post-Assessment Flash**:
   - Complete a Tier 1 test in `/dashboard/assessments`.
   - Navigate to `/dashboard`. Verify the Post-Assessment Calibration Flash Banner appears dynamically.
