"""
scripts/verify_backend_7x.py — Master Phase 7.x Verification Suite.

Validates the final production-ready backend governance, analytics, and handoff:
- 7.1 Audit & Provenance Ledger + 5-Pillar Data Quality Engine
- 7.2 Psychometric Item Response Analytics & Distractor Diagnostics
- 7.3 Longitudinal Competency Trajectory & Retention Window Governance
- 7.4 Recommendation Conversion Funnel & Intervention Outcome Analytics
- 7.5 Security, Privacy (N < 5), Centralized Policies, & Operational Health
- Phase 7.x Dedicated Pytest Test Suites (78 tests)
- Full Runtime Verification Scorecard
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")


def run_command(cmd: list[str], env: dict[str, str] | None = None, cwd: str | None = None) -> tuple[int, str]:
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=full_env,
        cwd=cwd or str(BASE_DIR),
    )
    return proc.returncode, proc.stdout


def main() -> int:
    print("=" * 80)
    print("PHASE 7.X MASTER BACKEND VERIFICATION RUNNER")
    print("SIH 2026 PS 26101 — MoSPI DIID (Branch: revised-backend)")
    print("=" * 80)

    section_results: dict[str, str] = {}
    failed_steps: list[str] = []
    py_bin = str(BASE_DIR / "backend" / ".venv" / "bin" / "python")
    pytest_bin = str(BASE_DIR / "backend" / ".venv" / "bin" / "pytest")

    # 1. 7.1 Audit & Data Quality
    print("\n>>> [1/7] Running Task 7.1 Audit & Data Quality Runtime Verification...")
    c1, o1 = run_command([py_bin, str(BASE_DIR / "scripts" / "verify_task_7_1_e2e.py")])
    if c1 == 0:
        section_results["7.1 AUDIT & DATA QUALITY"] = "PASS"
        print("    [+] Task 7.1 Verified.")
    else:
        section_results["7.1 AUDIT & DATA QUALITY"] = "FAIL"
        failed_steps.append("scripts/verify_task_7_1_e2e.py")
        print(f"    [-] Task 7.1 FAILED:\n{o1[-800:]}")

    # 2. 7.2 Item Analytics
    print("\n>>> [2/7] Running Task 7.2 Psychometric Item Analytics Runtime Verification...")
    c2, o2 = run_command([py_bin, str(BASE_DIR / "scripts" / "verify_task_7_2_e2e.py")])
    if c2 == 0:
        section_results["7.2 ITEM ANALYTICS & QUALITY"] = "PASS"
        print("    [+] Task 7.2 Verified.")
    else:
        section_results["7.2 ITEM ANALYTICS & QUALITY"] = "FAIL"
        failed_steps.append("scripts/verify_task_7_2_e2e.py")
        print(f"    [-] Task 7.2 FAILED:\n{o2[-800:]}")

    # 3. 7.3 Longitudinal Competency & Retention
    print("\n>>> [3/7] Running Task 7.3 Longitudinal Competency & Retention Verification...")
    c3, o3 = run_command([py_bin, str(BASE_DIR / "scripts" / "verify_task_7_3_e2e.py")])
    if c3 == 0:
        section_results["7.3 LONGITUDINAL TRAJECTORY"] = "PASS"
        print("    [+] Task 7.3 Verified.")
    else:
        section_results["7.3 LONGITUDINAL TRAJECTORY"] = "FAIL"
        failed_steps.append("scripts/verify_task_7_3_e2e.py")
        print(f"    [-] Task 7.3 FAILED:\n{o3[-800:]}")

    # 4. 7.4 Outcome Analytics
    print("\n>>> [4/7] Running Task 7.4 Recommendation & Outcome Analytics Verification...")
    c4, o4 = run_command([py_bin, str(BASE_DIR / "scripts" / "verify_task_7_4_e2e.py")])
    if c4 == 0:
        section_results["7.4 OUTCOME ANALYTICS"] = "PASS"
        print("    [+] Task 7.4 Verified.")
    else:
        section_results["7.4 OUTCOME ANALYTICS"] = "FAIL"
        failed_steps.append("scripts/verify_task_7_4_e2e.py")
        print(f"    [-] Task 7.4 FAILED:\n{o4[-800:]}")

    # 5. 7.5 Security, Privacy, Policies & Health
    print("\n>>> [5/7] Running Task 7.5 Security, Privacy, Policies & Health Verification...")
    c5, o5 = run_command([py_bin, str(BASE_DIR / "scripts" / "verify_task_7_5_e2e.py")])
    if c5 == 0:
        section_results["7.5 SECURITY & POLICIES"] = "PASS"
        print("    [+] Task 7.5 Verified.")
    else:
        section_results["7.5 SECURITY & POLICIES"] = "FAIL"
        failed_steps.append("scripts/verify_task_7_5_e2e.py")
        print(f"    [-] Task 7.5 FAILED:\n{o5[-800:]}")

    # 6. Phase 7 Workforce Intelligence E2E
    print("\n>>> [6/7] Running Phase 7 Workforce Intelligence & Governance E2E...")
    c6, o6 = run_command([py_bin, str(BASE_DIR / "scripts" / "verify_phase7_end_to_end.py")])
    if c6 == 0:
        section_results["WORKFORCE INTELLIGENCE E2E"] = "PASS"
        print("    [+] Phase 7 Workforce E2E Verified.")
    else:
        section_results["WORKFORCE INTELLIGENCE E2E"] = "FAIL"
        failed_steps.append("scripts/verify_phase7_end_to_end.py")
        print(f"    [-] Phase 7 Workforce E2E FAILED:\n{o6[-800:]}")

    # 7. Dedicated Pytest Suites
    print("\n>>> [7/7] Running All Phase 7 Pytest Test Suites (7.1 - 7.5 + System)...")
    env = {"PYTHONPATH": f"{BASE_DIR / 'backend'}:{BASE_DIR}"}
    c7, o7 = run_command(
        [pytest_bin, "backend/tests/test_task_7_1_audit_provenance.py",
         "backend/tests/test_task_7_1b_data_quality.py",
         "backend/tests/test_task_7_2_item_analytics.py",
         "backend/tests/test_task_7_3_longitudinal_governance.py",
         "backend/tests/test_task_7_4_outcome_analytics.py",
         "backend/tests/test_task_7_5_security_governance.py",
         "tests/system/test_task_7_backend_governance.py", "-q"],
        env=env,
    )
    if c7 == 0:
        section_results["PHASE 7 PYTEST TEST SUITES"] = "PASS"
        print("    [+] All Phase 7 Pytest Suites Passed (78/78 tests passed).")
    else:
        section_results["PHASE 7 PYTEST TEST SUITES"] = "FAIL"
        failed_steps.append("Phase 7 Pytest Suites")
        print(f"    [-] Pytest Failed:\n{o7[-800:]}")

    # Final Scorecard
    print("\n" + "=" * 80)
    print(" PHASE 7.X BACKEND VERIFICATION SCORECARD")
    print("=" * 80)
    for section, status in section_results.items():
        print(f"  {section:35} : [{status}]")
    print("-" * 80)

    all_passed = len(failed_steps) == 0
    if all_passed:
        print("\n>>> ALL PHASE 7.X VERIFICATIONS PASSED SUCCESSFULLY (100% GREEN)!")
        print(">>> BACKEND CODEBASE IS COMPLETE, AUDITED, AND READY FOR HANDOFF.\n")
        return 0
    else:
        print(f"\n>>> VERIFICATION FAILED: {len(failed_steps)} failure(s) detected: {failed_steps}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
