# HANDOFF.md — Handoff Templates

> With 3 people instead of 6, there's no pair-partner sitting next to you who already has context. Every handoff below exists to move context out of your head and into a file, so the other two owners (or a fresh AI coding agent session) can pick up without a live explanation from you. Copy the relevant template, fill it in, don't skip sections — "N/A" is a valid answer, silence is not.

---

## 1. Solo Builder Self-Review Checklist

Run this against your own diff before every push. This replaces the pair-review step that no longer exists (Build Guide §7 originally had Aarth review Devraj, etc. — see the Operating Reality Patch at the top of `GyanSetu_BUILD_GUIDE.md`).

```
☐ Does it run locally, from a clean pull, without manual steps I forgot to document?
☐ Did I run the relevant verification steps for my track
   (Build Guide §9/§10/§11 — "Aarth's/Mounya's/Likhita's Verification Steps")?
☐ Did I check the browser console / server logs for errors I'm ignoring?
☐ If this touches the API contract or DB schema — did I ping the other two owners
   for a quick look before merging? (Cross-owner approval still required.)
☐ Did I commit any secrets, API keys, or .env files? (git diff --cached, check before commit —
   see GIT_WORKFLOW.md §7 for the full secrets checklist and what to do if one slips through)
☐ Did I update PROJECT_STATUS.md for the task(s) I touched?
☐ If I'm stopping mid-task, did I write a Session Handoff entry (§2 below)?
```

---

## 2. End-of-Session Handoff Template

Use this every time you stop working, whether you finished the task or not. This is the Build Guide §45 task-reporting format, made fillable.

```
TASK_ID:        [e.g. ML-003]
STATUS:         [ DONE | IN_PROGRESS | BLOCKED ]
WHAT_CHANGED:   [1-3 sentences — what does this task actually do now that it didn't before]
FILES_CHANGED:  [list of files/paths]
COMMANDS_RUN:   [exact commands you ran to build/test this]
TESTS:          [what you tested, and how — "manually hit the endpoint with Postman" counts]
RESULTS:        [what actually happened when you tested — be specific, not "it works"]
KNOWN_ISSUES:   [anything you know is broken, half-done, or a shortcut you took]
ARTIFACTS:      [screenshots, sample output, logs — where are they, if anywhere]
NEXT_TASK:      [what should happen next on this thread, and who's best placed to do it]
```

**Filled example:**
```
TASK_ID:        ML-003
STATUS:         DONE
WHAT_CHANGED:   generate_mcqs() now calls Groq (llama-3.3-70b-versatile) instead of a
                stub, returns validated JSON matching the schema in Build Guide §12.
FILES_CHANGED:  ml_pipeline/mcq_generator.py, ml_pipeline/prompts/mcq_prompt.txt
COMMANDS_RUN:   python -c "from mcq_generator import generate_mcqs; print(generate_mcqs(
                'sample sampling design text', 'Sampling Design', 3, 'medium'))"
TESTS:          Ran the above 5 times with different source text. Manually checked each
                MCQ's correct_answer against the source text.
RESULTS:        4/5 runs produced 3 valid MCQs with correct grounding. 1 run produced a
                question with 2 plausible correct answers — validator caught it and
                flagged quality_score 0.4, correctly rejected.
KNOWN_ISSUES:   Haven't tested with a real NSSTA PDF yet, only a hardcoded string.
                Rate limit not yet hit in testing — unknown behavior under load
                (see ENVIRONMENT_SETUP.md §3 for current Groq free-tier limits).
ARTIFACTS:      Sample output saved to /tmp/mcq_sample_output.json (not committed)
NEXT_TASK:      Test with a real PDF via document_processor.py. Then wire into
                the Backend owner's /api/content/upload endpoint (BE-xxx).
```

---

## 3. Daily Handoff (End of Day 1 → Day 2, Day 2 → Day 3)

Fill this in at the end of each day, in addition to updating `PROJECT_STATUS.md`. This is a wider-lens summary than the per-task template above.

```
DAY COMPLETED:          [ 1 | 2 | 3 ]
INTEGRATION CHECKPOINT: [ PASS | PARTIAL | FAIL ]  (see PROJECT_STATUS.md §5 for detail)
WHAT'S WORKING END-TO-END TODAY:
  - [ ]
WHAT'S BROKEN OR MISSING:
  - [ ]
DEPLOYED URLS (if changed today):
  Frontend:
  Backend:
ENV VARS ADDED/CHANGED TODAY: [list keys only, never values, here]
GIT: today's work pushed to main repo (UtkarshSingh-09/GyanSetu-)?  [ YES / NO ]
     tag created for tonight's known-good state? (git tag day{N}-checkpoint)  [ YES / NO ]
TOMORROW'S TOP 3 PRIORITIES (per owner):
  Frontend:
  Backend:
  ML/AI:
RISKS FOR TOMORROW: [anything that could block the whole team if it goes wrong]
```

---

## 4. Mid-Task Handoff — Going Offline / Stuck / Swapping Tracks

Because there's no pair-partner, if you have to stop mid-task (end of your working hours, stuck and need to sleep on it, or someone else needs to jump in), leave this so the thread isn't lost:

```
TASK_ID:
WHERE I STOPPED:        [exact function/file/line, or "the API call works but the
                          response doesn't parse"]
WHAT I TRIED:            [so the next person doesn't repeat a dead end]
WHAT I HAVEN'T TRIED YET:
CAN THIS WAIT UNTIL I'M BACK, OR DOES SOMEONE ELSE NEED TO PICK IT UP NOW?
IF SOMEONE ELSE PICKS IT UP — WHAT DO THEY NEED TO KNOW THAT ISN'T IN THE CODE:
```

---

## 5. AI Coding Agent Session Handoff

If you're using an agentic IDE (Antigravity, Claude Code, etc.), each new session starts with no memory of the last one. Before ending an agent session on a non-trivial task, make sure the agent has written a §2 handoff entry, and confirm it also did the following (per Build Guide §36):

```
☐ Updated PROJECT_STATUS.md for the task(s) it touched
☐ Did NOT redesign frozen architecture (Build Guide §22) without an explicit
  change request being logged
☐ Did NOT fabricate test results, benchmark numbers, or "it works" without
  actually running it
☐ Reported changed files, commands run, and results — not just "task complete"
☐ Did NOT commit to the wrong repo (private vs. main — see GIT_WORKFLOW.md §2)
☐ Left a clear NEXT_TASK for the next session (human or agent) to pick up
```

When *starting* a new agent session on an existing task, point it at: this file (most recent relevant entry), `PROJECT_STATUS.md`, `PROJECT_CONTEXT.md`, `GIT_WORKFLOW.md` (if the task touches git at all), and the specific Build Guide section for the task. Don't assume it will find these on its own — link them explicitly in the task prompt.

---

## 6. Final Pre-Demo Handoff (End of Day 3)

This is the package the presenter(s) actually need in hand before walking up. Fill in every field — a missing URL or password at demo time is how demos die.

```
DEMO ACCOUNT CREDENTIALS
  Officer login:      email / password (or note: seeded in DB, auto-login button)
  Admin login:        email / password

LIVE URLS
  Frontend:
  Backend:
  Backend /docs (in case a judge asks to see the API):

BACKUP PLAN (Build Guide §14)
  Backup demo video location/link:
  If internet dies at venue: [confirm ChromaDB embedded, local Whisper, seeded
  PostgreSQL, cached assessment items, and Groq's validated-response cache
  (Tier 2 of the 4-tier fallback — Build Guide §3) all work fully offline —
  Build Guide §14]
  Last known-good git commit hash on the main repo (for emergency revert):

DEMO SCRIPT (Build Guide §19)
  Who presents which segment:
    Minute 0-1 (context):
    Minute 1-3 (officer journey):
    Minute 3-5 (assessment):
    Minute 5-7 (recommendation + hero moment):
    Minute 7-9 (content ingestion + RAG + retention):
    Minute 9-10 (architecture):
  Who drives the keyboard/mouse:
  Who answers judge questions on: architecture / AI grounding / security / roadmap:

5-RUN VERIFICATION STATUS: [ link to PROJECT_STATUS.md §9 — confirm all 5 passed ]

KNOWN ISSUES TO NOT DEMO AROUND: [list any fragile flow to route around live]
```

---

## 7. Post-Hackathon / Submission Handoff

For whoever does the final push and README before submission:

```
☐ Final evidence package present (Build Guide §38 structure: artifacts/experiments,
  metrics, manifests, screenshots, demo/)
☐ README in the main repo states: project version, git commit, architecture version,
  content/model/prompt versions (Groq model IDs used — see ENVIRONMENT_SETUP.md §3),
  how to reproduce, known limitations (Build Guide §38 — the README requirement)
☐ No real sensitive government/user data anywhere in the repo
☐ No secrets committed anywhere in the repo history (see GIT_WORKFLOW.md §7)
☐ Main repo (UtkarshSingh-09/GyanSetu-) is the one actually submitted, not the
  private repo (ankit-choubey/GyanSetu_V1)
```
