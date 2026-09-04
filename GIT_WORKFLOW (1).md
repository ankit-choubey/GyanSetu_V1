# GIT_WORKFLOW.md — Two-Repo, Two-Account Git Model

> Read this before your first commit. The Build Guide's original git section (§7 "GitHub & Version Control Checkpoints") assumed one shared repo from Day 1 — that's superseded. This file is the actual workflow. See the Operating Reality Patch at the top of `GyanSetu_BUILD_GUIDE.md` for the one-paragraph summary of *why* this changed; this file is the *how*.

---

## 1. The Two Repos

| | Private repo | Main repo |
|---|---|---|
| **URL** | `https://github.com/ankit-choubey/GyanSetu_V1.git` | `https://github.com/UtkarshSingh-09/GyanSetu-.git` |
| **Owner account** | `ankit-choubey` | `UtkarshSingh-09` |
| **Purpose** | Pre-hackathon scaffolding, solo practice, throwaway experiments, learning the stack | The repo actually built in during the 3-day hackathon window. This is what gets demoed and submitted. |
| **Judged?** | No | Yes |
| **Commit history matters?** | No — messy WIP history is fine, this repo is scratch space | Yes — this history should read as "3 days of real work," not as history imported wholesale from somewhere else |
| **When to stop using it** | The moment Day 1 of the hackathon starts | N/A — this is where you live from Day 1 onward |

**The one rule that matters more than any command below: once the hackathon clock starts, all real work happens in the main repo.** The private repo's job is done at that point except as a reference you can copy *specific* working code out of (see §5).

---

## 2. Who Pushes Where — Recommended Setup (do this, not the SSH-alias version in §8 unless you hit a specific blocker)

The simplest model, and the one to default to: **each of the 3 owners uses their own personal GitHub account as a collaborator on both repos.** You do not need to "become" `ankit-choubey` or `UtkarshSingh-09` to push to their repos — GitHub lets any invited collaborator push to a repo they don't own, authenticated as themselves. This avoids all multi-account credential juggling on a personal laptop.

1. **Repo owner adds the other two as collaborators:**
   - `ankit-choubey` → Settings → Collaborators → Add people → invite Utkarsh's and the Frontend owner's GitHub usernames, on the **private repo**.
   - `UtkarshSingh-09` → Settings → Collaborators → Add people → invite Ankit's and the Frontend owner's GitHub usernames, on the **main repo**.
2. **Each invited person accepts the invite** (email or github.com/notifications).
3. **Each person clones with their own credentials**, using whichever auth method they already use for GitHub (SSH key or HTTPS + Personal Access Token). If you don't have GitHub auth set up on your machine yet:
   ```bash
   # SSH (recommended) — generate a key if you don't have one
   ssh-keygen -t ed25519 -C "you@example.com"
   # then paste the contents of ~/.ssh/id_ed25519.pub into
   # GitHub → Settings → SSH and GPG keys → New SSH key
   ```
4. **Local commit identity** — set this once per machine (or per-repo if your name differs across projects):
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "the-email-linked-to-your-github-account@example.com"
   ```
   This is what shows up as the commit author — separate from whichever account's credentials authenticated the push.
5. **Clone both repos:**
   ```bash
   git clone git@github.com:ankit-choubey/GyanSetu_V1.git
   git clone git@github.com:UtkarshSingh-09/GyanSetu-.git
   ```

If GitHub's collaborator model doesn't work for your situation (e.g., you genuinely need one laptop to push as two different GitHub identities), skip to §8 for the SSH host-alias method — but try this section first, it's simpler.

---

## 3. `.gitignore` — Set This Up Before Your First Commit, in Both Repos

Create `.gitignore` at the root of each repo before you commit anything:

```gitignore
# Secrets — never commit these
.env
.env.local
.env.*.local
*.pem
*.key

# Python
__pycache__/
*.pyc
.venv/
venv/
env/
*.egg-info/

# Node / Next.js
node_modules/
.next/
out/
.vercel/

# Vector store / local model caches
chroma_db/
chroma_data/
*.sqlite3
.cache/
models/

# OS / editor
.DS_Store
Thumbs.db
.vscode/
.idea/

# Logs and local artifacts
*.log
/tmp/
```

Run `git status` right after creating this and before your first `git add .` — if you see `.env`, `node_modules`, or `venv` listed as untracked-and-about-to-be-added, the `.gitignore` isn't catching it yet; fix that before committing, not after.

---

## 4. Day-to-Day Branch & Commit Workflow (Main Repo, Hackathon Days 1–3)

With 3 people owning 3 mostly-disjoint folders (`frontend/`, `backend/`, `ml_pipeline/`), heavy branching overhead usually isn't worth it for a 3-day sprint. Use this tiered approach:

**Tier 1 — inside your own track's folder, low collision risk:**
Commit directly to `main`, frequently (every 30–60 minutes of real progress, not once a day). Small commits are easier to `git revert` individually if one breaks something.
```bash
git add ml_pipeline/mcq_generator.py
git commit -m "[ML-003] generate_mcqs() now calls Groq, returns validated JSON"
git push origin main
```
Prefix every commit message with the Task ID from `PROJECT_STATUS.md` §3 (`[FE-001]`, `[BE-002]`, `[ML-003]`, etc.) — this is what makes a commit and a status-board row traceable to each other later.

**Tier 2 — anything touching shared surface area (API contract / OpenAPI schema, DB schema, `.env.example`, `docker-compose.yml`, root README, CI config):**
Use a short-lived branch and get a quick look from the affected owner(s) before merging — this is the "cross-owner approval" step the Self-Review Checklist in `HANDOFF.md` refers to.
```bash
git checkout -b api-contract/add-retention-endpoint
# make the change
git push origin api-contract/add-retention-endpoint
# ping the other owner(s), get a thumbs up in chat, then:
git checkout main
git pull origin main
git merge api-contract/add-retention-endpoint
git push origin main
git branch -d api-contract/add-retention-endpoint
```

**Always pull before you push**, especially first thing after a break, to avoid unnecessary conflicts:
```bash
git pull --rebase origin main
```

**If a merged commit breaks `main`:** don't scramble to hand-patch it live. Per Build Guide §7's original rollback discipline (still correct, unchanged by this patch):
```bash
git revert <bad-commit-hash>
git push origin main
```

**End of each day:** tag the known-good state so there's an instant rollback point if Day 3 polish breaks something late (this feeds `HANDOFF.md` §3's "known-good state" field):
```bash
git tag day1-checkpoint
git push origin day1-checkpoint
```

---

## 5. Migrating Code Out of the Private Repo, Into the Main Repo (Start of Day 1)

You built scaffolding in the private repo before the clock started. Two ways to bring it into the main repo — **pick the first one unless you have a specific reason not to:**

### Option A (recommended) — Fresh history, copy files only
Keeps the main repo's commit history honest as "written during the hackathon," and avoids a judge asking why the repo history predates the event. The private repo still exists on GitHub as your own proof of prior practice if anyone asks.
```bash
# From a fresh clone of the main repo
git clone git@github.com:UtkarshSingh-09/GyanSetu-.git
cd GyanSetu-

# Copy only the working files you want to keep (not .git) from your local
# private-repo checkout — adjust paths to whatever you actually built
cp -r ../GyanSetu_V1/ml_pipeline ./ml_pipeline
cp -r ../GyanSetu_V1/frontend ./frontend
# etc.

git add .
git commit -m "[DAY1] Bring in pre-hackathon scaffolding: ML pipeline skeleton, frontend shell"
git push origin main
```

### Option B — Carry full history
Only do this if you specifically want the private repo's commit history visible in the main repo (e.g., to show iteration). This drags in every WIP commit, including any that may have contained something you didn't mean to keep.
```bash
cd GyanSetu-
git remote add scaffolding git@github.com:ankit-choubey/GyanSetu_V1.git
git fetch scaffolding
git merge scaffolding/main --allow-unrelated-histories
# resolve any conflicts, then:
git push origin main
git remote remove scaffolding
```

**Before either option:** check your hackathon's specific rules on reusing pre-built code — some hackathons (including many SIH-style formats) restrict how much pre-hackathon code can count toward the judged submission. This two-repo split exists to keep that boundary auditable regardless of what the exact rule turns out to be; it doesn't by itself guarantee compliance with a rule you haven't checked.

---

## 6. Commit Message Convention

```
[TASK-ID] Short imperative description

Optional longer body if the change needs explanation that
doesn't fit in the subject line.
```
Examples: `[BE-001] Add evidence-fusion weights to competency engine`, `[FE-003] Wire assessment flow to real /api/assessment endpoint`, `[ML-004] Reject MCQs with 2+ plausible correct answers in validator`.

This isn't bureaucracy for its own sake — it's what lets anyone (including a fresh AI coding agent session) run `git log --grep="BE-001"` and see exactly what happened for a given task, instead of re-deriving it from scratch.

---

## 7. Secrets Hygiene

* **Never** commit `.env`, API keys, database connection strings, or JWT secrets. The `.gitignore` in §3 stops the obvious cases; it doesn't stop you pasting a key directly into a `.py` file "just for a quick test."
* **Before every commit**, get in the habit of `git diff --cached` and actually reading it, not just `git add . && git commit`.
* **If a secret does get committed and pushed:**
  1. Rotate the secret immediately (regenerate the Groq key, change the DB password, etc.) — assume it's compromised the second it's visible on GitHub, even in a private repo.
  2. Remove it from history, not just in a new commit on top (a new commit doesn't delete it from history — anyone can still see it in an old commit). Use `git filter-repo` (or `git filter-branch` if that's unavailable) to purge it, then force-push.
  3. Everyone with a local clone needs to re-clone or hard-reset after a history rewrite like this — a stale local clone will otherwise resurrect the old history the next time someone pushes.
* Optional but recommended if you have 10 minutes on Day 0: install a secret-scanning pre-commit hook (e.g. `gitleaks protect --staged` as a pre-commit hook) so a secret is caught before it's committed at all, not after.
* Same rule applies to `PROJECT_STATUS.md` and any screenshot you paste into a group chat: host/URL is fine, the actual key or password is not — see `PROJECT_STATUS.md` §2's note on this.

---

## 8. Appendix — SSH Multi-Account Aliases (Only If §2's Collaborator Model Doesn't Work For You)

Use this if you genuinely need one machine to push as two different GitHub identities (for example, only 2 real GitHub accounts exist across 3 people, or you're testing from a shared/borrowed laptop).

1. Generate a separate SSH key per identity:
   ```bash
   ssh-keygen -t ed25519 -C "ankit-account" -f ~/.ssh/id_ed25519_ankit
   ssh-keygen -t ed25519 -C "utkarsh-account" -f ~/.ssh/id_ed25519_utkarsh
   ```
2. Add each public key to the matching GitHub account (Settings → SSH and GPG keys).
3. Create `~/.ssh/config` with a Host alias per identity:
   ```
   Host github.com-ankit
     HostName github.com
     User git
     IdentityFile ~/.ssh/id_ed25519_ankit
     IdentitiesOnly yes

   Host github.com-utkarsh
     HostName github.com
     User git
     IdentityFile ~/.ssh/id_ed25519_utkarsh
     IdentitiesOnly yes
   ```
4. Clone using the alias instead of `github.com` directly:
   ```bash
   git clone git@github.com-ankit:ankit-choubey/GyanSetu_V1.git
   git clone git@github.com-utkarsh:UtkarshSingh-09/GyanSetu-.git
   ```
5. Set commit identity **per repo** (not `--global`) so commits from each repo are correctly attributed:
   ```bash
   cd GyanSetu_V1 && git config user.email "ankit's-email" && git config user.name "Ankit Choubey"
   cd ../GyanSetu- && git config user.email "utkarsh's-email" && git config user.name "Utkarsh [surname]"
   ```

---

## 9. Quick Reference Cheat Sheet

```
Clone both repos:        git clone git@github.com:<owner>/<repo>.git
Check what's staged:     git diff --cached
Small frequent commit:   git add <files> && git commit -m "[TASK-ID] message"
Pull safely:             git pull --rebase origin main
Push:                    git push origin main
Undo a bad merged commit git revert <hash> && git push origin main
End-of-day checkpoint:   git tag dayN-checkpoint && git push origin dayN-checkpoint
See history for a task:  git log --grep="BE-001"
```
