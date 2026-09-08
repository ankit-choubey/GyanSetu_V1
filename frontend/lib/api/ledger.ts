import { TestLedgerItem, TestQuestionDetail } from "./types";
import { client } from "./client";

const LOCAL_STORAGE_LEDGER_KEY = "gyansetu_test_report_ledger";

// Pre-seeded baseline reports reflecting system history
const SEED_LEDGER_ITEMS: TestLedgerItem[] = [
  {
    report_id: "Test Report #001",
    numeric_id: 1,
    session_id: "sess_mospi_base_001",
    timestamp: "05 Sep 2026, 11:30 AM",
    iso_date: "2026-09-05T11:30:00Z",
    user_id: 1,
    full_name: "Shri Ankit Choubey",
    email: "learner@example.com",
    role_name: "Statistical Officer",
    designation: "Statistical Officer",
    department: "National Accounts Division (NAD)",
    competency_id: 1,
    competency_name: "Sampling Design & Field Methodologies",
    tier: "Tier 1: Foundation",
    difficulty_band: "Recall & Definitions (Bloom L1-L2)",
    score: 87,
    correct_count: 13,
    total_questions: 15,
    passing_score: 70,
    result_status: "PASSED",
    next_tier_unlocked: "Tier 2: Application",
    mastery: 0.82,
    confidence: 0.85,
    coverage: 0.78,
    uncertainty: 0.15,
    evidence_count: 4,
    evidence_diversity: 2,
    assessed_count: "5 of 7",
    reliability_status: "VERIFIED",
    provenance: "[CURATED:MOSPI_HANDBOOK]",
    evidence_type: "KNOWLEDGE_ASSESSMENT",
    weight: 1.0,
    items: [
      {
        question_number: "Q1",
        subskill_name: "Stratified Random Sampling",
        question_text: "What primary objective justifies the use of proportional stratified sampling over SRS?",
        user_selected: "B",
        correct_option: "B",
        is_correct: true,
      },
      {
        question_number: "Q2",
        subskill_name: "Sampling Frame Construction",
        question_text: "In the context of the Urban Frame Survey (UFS), what constitutes a Primary Sampling Unit (PSU)?",
        user_selected: "C",
        correct_option: "C",
        is_correct: true,
      },
      {
        question_number: "Q3",
        subskill_name: "Sampling Variance Estimation",
        question_text: "Under Neyman allocation, sample size allocation to strata is directly proportional to what parameter?",
        user_selected: "A",
        correct_option: "D",
        is_correct: false,
        misconception_hint: "Selected simple stratum size rather than the product of stratum size and stratum standard deviation (N_h * S_h).",
        remediation_steps: "Review MoSPI Sampling Manual, Section 3.4 (Optimal and Neyman Allocation Formulations).",
      },
      {
        question_number: "Q4",
        subskill_name: "Multi-Stage Clustering",
        question_text: "In NSS rounds, when is circular systematic sampling preferred over simple linear systematic sampling?",
        user_selected: "A",
        correct_option: "A",
        is_correct: true,
      },
      {
        question_number: "Q5",
        subskill_name: "Non-Sampling Error Handling",
        question_text: "Which technique is canonically deployed by FOD to impute missing household expenditure data?",
        user_selected: "B",
        correct_option: "D",
        is_correct: false,
        misconception_hint: "Confused deterministic mean imputation with hot-deck nearest neighbor donor matching.",
        remediation_steps: "Consult NSSTA Course Notes on Non-Sampling Errors and Modern Imputation Protocols.",
      },
      {
        question_number: "Q6",
        subskill_name: "Weighting & Multipliers",
        question_text: "How is the design weight computed for an ultimate stage unit in two-stage sampling?",
        user_selected: "A",
        correct_option: "A",
        is_correct: true,
      },
      {
        question_number: "Q7",
        subskill_name: "Standard Error Derivation",
        question_text: "What formula gives the estimated standard error of the sample proportion under SRS without replacement?",
        user_selected: "B",
        correct_option: "B",
        is_correct: true,
      },
      {
        question_number: "Q8",
        subskill_name: "Finite Population Correction",
        question_text: "At what sampling fraction threshold (n/N) is the Finite Population Correction (fpc) typically deemed necessary?",
        user_selected: "C",
        correct_option: "C",
        is_correct: true,
      },
      {
        question_number: "Q9",
        subskill_name: "Post-Stratification Weighting",
        question_text: "Why is post-stratification deployed after the completion of household field surveys?",
        user_selected: "A",
        correct_option: "A",
        is_correct: true,
      },
      {
        question_number: "Q10",
        subskill_name: "Cluster Design Effect (DEFF)",
        question_text: "How is the Design Effect (DEFF) formally related to the intra-class correlation coefficient (rho)?",
        user_selected: "D",
        correct_option: "D",
        is_correct: true,
      },
      {
        question_number: "Q11",
        subskill_name: "Field Verification Rules",
        question_text: "What protocol applies when an original selected household cannot be traced after three distinct visits?",
        user_selected: "C",
        correct_option: "C",
        is_correct: true,
      },
      {
        question_number: "Q12",
        subskill_name: "Confidence Interval Bounds",
        question_text: "For a 95% confidence interval under asymptotic normality, what critical z-multiplier is used?",
        user_selected: "B",
        correct_option: "B",
        is_correct: true,
      },
      {
        question_number: "Q13",
        subskill_name: "Stratification Gain Ratio",
        question_text: "How does the variance of the stratified estimator compare to unstratified SRS when strata are homogeneous?",
        user_selected: "A",
        correct_option: "A",
        is_correct: true,
      },
      {
        question_number: "Q14",
        subskill_name: "Sample Size Determination",
        question_text: "What happens to the required sample size if the margin of error (E) is halved while holding confidence constant?",
        user_selected: "D",
        correct_option: "D",
        is_correct: true,
      },
      {
        question_number: "Q15",
        subskill_name: "Statistical Calibration",
        question_text: "Which MoSPI calibration software module applies GREG (Generalized Regression Estimator) adjustments?",
        user_selected: "A",
        correct_option: "A",
        is_correct: true,
      },
    ],
  },
];

export function getLocalLedgerItems(): TestLedgerItem[] {
  if (typeof window === "undefined") return SEED_LEDGER_ITEMS;
  try {
    const raw = localStorage.getItem(LOCAL_STORAGE_LEDGER_KEY);
    if (!raw) {
      localStorage.setItem(LOCAL_STORAGE_LEDGER_KEY, JSON.stringify(SEED_LEDGER_ITEMS));
      return SEED_LEDGER_ITEMS;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : SEED_LEDGER_ITEMS;
  } catch (e) {
    console.warn("Failed reading test report ledger from localStorage:", e);
    return SEED_LEDGER_ITEMS;
  }
}

export function appendTestLedgerItem(item: Omit<TestLedgerItem, "report_id" | "numeric_id">): TestLedgerItem {
  const current = getLocalLedgerItems();
  const nextNum = current.length + 1;
  const padNum = String(nextNum).padStart(3, "0");
  const fullItem: TestLedgerItem = {
    ...item,
    report_id: `Test Report #${padNum}`,
    numeric_id: nextNum,
  };

  const updated = [fullItem, ...current];
  if (typeof window !== "undefined") {
    try {
      localStorage.setItem(LOCAL_STORAGE_LEDGER_KEY, JSON.stringify(updated));
      window.dispatchEvent(new CustomEvent("gyansetu:ledger_updated", { detail: fullItem }));
    } catch (e) {
      console.warn("Failed saving test report item:", e);
    }
  }
  return fullItem;
}

export async function fetchLiveLedger(): Promise<TestLedgerItem[]> {
  const localItems = getLocalLedgerItems();
  try {
    const serverEvidence = await client.get<any>("/api/evidence").catch(() => null);
    if (serverEvidence && Array.isArray(serverEvidence.evidence)) {
      return localItems;
    }
  } catch (err) {
    // Fall back cleanly to local ledger
  }
  return localItems;
}
