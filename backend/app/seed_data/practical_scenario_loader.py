import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill
from app.models.practical import (
    EvaluatorType,
    PracticalDifficulty,
    PracticalScenarioType,
    PracticalTask,
)

PRACTICAL_TASKS_DATA: list[dict[str, Any]] = [
    {
        "task_id": "TASK-MOSPI-SAMP-01",
        "title": "PLFS Sub-Sample Non-Response Weight Adjustment",
        "competency_name": "Survey Methodology",
        "subskill_name": "Survey weighting",
        "scenario_type": PracticalScenarioType.STATISTICAL_PROCEDURE.value,
        "difficulty": PracticalDifficulty.MEDIUM.value,
        "scenario_context": (
            "Official-Statistics-aligned simulated practical scenario. In the Periodic Labour Force Survey "
            "(PLFS) quarterly round, field non-response occurs across rural and urban sampling strata. "
            "Statistical investigators must compute non-response adjustment factors and calibrate base design "
            "weights to preserve unbiased population aggregates."
        ),
        "instructions": (
            "Given the 3 strata sample counts, observed respondents, and base design weights:\n"
            "1. Calculate the response rate r_h = n_resp / n_sample for each stratum.\n"
            "2. Calculate the non-response adjustment factor f_h = 1 / r_h.\n"
            "3. Compute the final calibrated weight w_adj_h = w_base_h * f_h.\n"
            "4. Compute the estimated population total Y_hat = sum(w_adj_h * y_sample_sum_h).\n"
            "Submit your answers as JSON with keys: 'response_rates', 'adjusted_weights', 'estimated_total', "
            "and 'methodology_note'."
        ),
        "input_artifacts": {
            "description": "PLFS Stratum Sampling Summary Table",
            "strata": [
                {
                    "stratum_id": "STRATUM-RURAL-01",
                    "n_sample": 100,
                    "n_respondents": 80,
                    "base_weight": 25.0,
                    "sample_sum_income": 320000.0,
                },
                {
                    "stratum_id": "STRATUM-URBAN-01",
                    "n_sample": 150,
                    "n_respondents": 120,
                    "base_weight": 15.0,
                    "sample_sum_income": 840000.0,
                },
                {
                    "stratum_id": "STRATUM-PERIURBAN-01",
                    "n_sample": 50,
                    "n_respondents": 40,
                    "base_weight": 40.0,
                    "sample_sum_income": 200000.0,
                },
            ],
        },
        "expected_output_type": "NUMERICAL_JSON",
        "rubric": {
            "version": "v1.0-rubric",
            "dimensions": {
                "response_rates": {
                    "weight": 0.25,
                    "expected": {
                        "STRATUM-RURAL-01": 0.80,
                        "STRATUM-URBAN-01": 0.80,
                        "STRATUM-PERIURBAN-01": 0.80,
                    },
                    "tolerance": 0.01,
                },
                "adjusted_weights": {
                    "weight": 0.35,
                    "expected": {
                        "STRATUM-RURAL-01": 31.25,
                        "STRATUM-URBAN-01": 18.75,
                        "STRATUM-PERIURBAN-01": 50.0,
                    },
                    "tolerance": 0.01,
                },
                "estimated_total": {
                    "weight": 0.25,
                    "expected": 35750000.0,  # 320000*31.25 + 840000*18.75 + 200000*50.0
                    "tolerance": 100.0,
                },
                "methodology_note": {
                    "weight": 0.15,
                    "keywords": ["non-response", "weight", "unbiased", "calibration"],
                    "min_length": 20,
                },
            },
            "passing_score": 0.70,
        },
        "rubric_version": "v1.0-rubric",
        "prerequisites": ["Survey weighting fundamentals", "Sampling design basics"],
        "provenance": "[CURATED:SIMULATION]",
        "source": "MOSPI_SIMULATION",
    },
    {
        "task_id": "TASK-MOSPI-SAMP-02",
        "title": "Annual Survey of Industries Neyman Optimal Allocation",
        "competency_name": "Sampling Design",
        "subskill_name": "Stratified sampling",
        "scenario_type": PracticalScenarioType.STATISTICAL_PROCEDURE.value,
        "difficulty": PracticalDifficulty.HARD.value,
        "scenario_context": (
            "Official-Statistics-aligned simulated practical scenario. For the Annual Survey of Industries "
            "(ASI) frame stratification, sampling statisticians allocate sample sizes to minimize the variance "
            "of estimated gross output given fixed total budget n=600."
        ),
        "instructions": (
            "Given 3 manufacturing enterprise strata with population frame counts N_h and output standard deviations S_h:\n"
            "1. Calculate N_h * S_h for each stratum and compute the sum.\n"
            "2. Compute Neyman sample allocation n_h = n * (N_h * S_h) / sum(N_k * S_k) for total sample n = 600.\n"
            "3. Round each allocation to the nearest integer ensuring sum(n_h) = 600.\n"
            "Submit your answers as JSON with keys: 'stratum_products', 'allocations', and 'methodology_note'."
        ),
        "input_artifacts": {
            "description": "ASI Frame Stratification Parameters",
            "total_sample_size": 600,
            "strata": [
                {"stratum_id": "ASI-SMALL", "N_h": 4000, "S_h": 50.0},
                {"stratum_id": "ASI-MEDIUM", "N_h": 1500, "S_h": 200.0},
                {"stratum_id": "ASI-LARGE", "N_h": 500, "S_h": 1000.0},
            ],
        },
        "expected_output_type": "NUMERICAL_JSON",
        "rubric": {
            "version": "v1.0-rubric",
            "dimensions": {
                "stratum_products": {
                    "weight": 0.30,
                    "expected": {
                        "ASI-SMALL": 200000.0,
                        "ASI-MEDIUM": 300000.0,
                        "ASI-LARGE": 500000.0,
                    },
                    "tolerance": 1.0,
                },
                "allocations": {
                    "weight": 0.50,
                    "expected": {
                        "ASI-SMALL": 120,
                        "ASI-MEDIUM": 180,
                        "ASI-LARGE": 300,
                    },
                    "tolerance": 1.0,
                },
                "methodology_note": {
                    "weight": 0.20,
                    "keywords": ["neyman", "optimal allocation", "variance", "strata"],
                    "min_length": 20,
                },
            },
            "passing_score": 0.70,
        },
        "rubric_version": "v1.0-rubric",
        "prerequisites": ["Stratified sampling principles", "Variance minimization"],
        "provenance": "[CURATED:SIMULATION]",
        "source": "MOSPI_SIMULATION",
    },
    {
        "task_id": "TASK-MOSPI-CPI-01",
        "title": "All-India CPI Basket Laspeyres Index Compilation",
        "competency_name": "Index Numbers",
        "subskill_name": "Laspeyres and Paasche indices",
        "scenario_type": PracticalScenarioType.STATISTICAL_PROCEDURE.value,
        "difficulty": PracticalDifficulty.MEDIUM.value,
        "scenario_context": (
            "Official-Statistics-aligned simulated practical scenario. In the Price Statistics Division (PSD), "
            "compilation of monthly Consumer Price Index (CPI) numbers requires computing item-level price relatives "
            "and aggregating them using fixed base period expenditure weights via the Laspeyres formulation."
        ),
        "instructions": (
            "Given base period prices (p_0), current period prices (p_t), and base weights (w_0) for 4 commodity groups:\n"
            "1. Calculate group price relatives R_i = (p_t / p_0) * 100 for each commodity.\n"
            "2. Compute the weighted aggregate CPI Laspeyres index: I_L = sum(w_0 * R_i) / sum(w_0).\n"
            "3. Compute the implied percentage inflation rate = I_L - 100.\n"
            "Submit your answers as JSON with keys: 'price_relatives', 'laspeyres_index', 'inflation_rate', "
            "and 'analysis_summary'."
        ),
        "input_artifacts": {
            "description": "CPI Commodity Basket Price Schedule",
            "base_period": "2012=100",
            "groups": [
                {"group_name": "Food and Beverages", "p_0": 120.0, "p_t": 150.0, "w_0": 45.86},
                {"group_name": "Housing", "p_0": 200.0, "p_t": 220.0, "w_0": 10.07},
                {"group_name": "Fuel and Light", "p_0": 80.0, "p_t": 96.0, "w_0": 6.84},
                {"group_name": "Miscellaneous", "p_0": 150.0, "p_t": 165.0, "w_0": 37.23},
            ],
        },
        "expected_output_type": "NUMERICAL_JSON",
        "rubric": {
            "version": "v1.0-rubric",
            "dimensions": {
                "price_relatives": {
                    "weight": 0.30,
                    "expected": {
                        "Food and Beverages": 125.0,
                        "Housing": 110.0,
                        "Fuel and Light": 120.0,
                        "Miscellaneous": 110.0,
                    },
                    "tolerance": 0.05,
                },
                "laspeyres_index": {
                    "weight": 0.35,
                    "expected": 117.56,
                    "tolerance": 0.05,
                },
                "inflation_rate": {
                    "weight": 0.15,
                    "expected": 17.56,
                    "tolerance": 0.05,
                },
                "analysis_summary": {
                    "weight": 0.20,
                    "keywords": ["laspeyres", "price relative", "food", "inflation"],
                    "min_length": 20,
                },
            },
            "passing_score": 0.70,
        },
        "rubric_version": "v1.0-rubric",
        "prerequisites": ["CPI index compilation", "Laspeyres price index formula"],
        "provenance": "[CURATED:SIMULATION]",
        "source": "MOSPI_SIMULATION",
    },
    {
        "task_id": "TASK-MOSPI-QUAL-01",
        "title": "Household Expenditure Microdata Outlier & Validation Audit",
        "competency_name": "Data Quality",
        "subskill_name": "Validation rules",
        "scenario_type": PracticalScenarioType.DATA_VALIDATION.value,
        "difficulty": PracticalDifficulty.MEDIUM.value,
        "scenario_context": (
            "Official-Statistics-aligned simulated practical scenario. During National Sample Survey (NSS) "
            "microdata ingestion, Field Operations Division data files must pass validation rules: identifying "
            "negative expenditures, zero-member households, and statistical outliers using Tukey's interquartile range (IQR)."
        ),
        "instructions": (
            "Given 10 household survey records with monthly consumption expenditures (MPCE in INR):\n"
            "1. Identify records violating logical validation rules (e.g. expenditure <= 0 or household size <= 0).\n"
            "2. For remaining valid records, compute Q1 (25th percentile), Q3 (75th percentile), and IQR = Q3 - Q1.\n"
            "3. Calculate the upper fence: Q3 + 1.5 * IQR. Identify any record exceeding this fence.\n"
            "4. Compute the robust clean mean MPCE excluding invalid records and outliers.\n"
            "Submit your answers as JSON with keys: 'invalid_record_ids', 'outlier_record_ids', 'iqr', "
            "'upper_fence', 'clean_mean', and 'audit_remarks'."
        ),
        "input_artifacts": {
            "description": "Raw Household Expenditure Sample File",
            "records": [
                {"hh_id": "HH-101", "hh_size": 4, "mpce": 3200.0},
                {"hh_id": "HH-102", "hh_size": 3, "mpce": 3500.0},
                {"hh_id": "HH-103", "hh_size": 5, "mpce": -500.0},
                {"hh_id": "HH-104", "hh_size": 0, "mpce": 4000.0},
                {"hh_id": "HH-105", "hh_size": 4, "mpce": 3800.0},
                {"hh_id": "HH-106", "hh_size": 2, "mpce": 4200.0},
                {"hh_id": "HH-107", "hh_size": 6, "mpce": 4500.0},
                {"hh_id": "HH-108", "hh_size": 3, "mpce": 4800.0},
                {"hh_id": "HH-109", "hh_size": 4, "mpce": 5200.0},
                {"hh_id": "HH-110", "hh_size": 5, "mpce": 25000.0},
            ],
        },
        "expected_output_type": "NUMERICAL_JSON",
        "rubric": {
            "version": "v1.0-rubric",
            "dimensions": {
                "invalid_record_ids": {
                    "weight": 0.20,
                    "expected": ["HH-103", "HH-104"],
                    "match_type": "set_equality",
                },
                "outlier_record_ids": {
                    "weight": 0.20,
                    "expected": ["HH-110"],
                    "match_type": "set_equality",
                },
                "iqr": {
                    "weight": 0.15,
                    "expected": 1350.0,
                    "tolerance": 50.0,
                },
                "upper_fence": {
                    "weight": 0.15,
                    "expected": 7025.0,
                    "tolerance": 75.0,
                },
                "clean_mean": {
                    "weight": 0.15,
                    "expected": 4171.43,
                    "tolerance": 10.0,
                },
                "audit_remarks": {
                    "weight": 0.15,
                    "keywords": ["iqr", "tukey", "outlier", "validation", "fence"],
                    "min_length": 20,
                },
            },
            "passing_score": 0.70,
        },
        "rubric_version": "v1.0-rubric",
        "prerequisites": ["Data validation rules", "Outlier detection using IQR"],
        "provenance": "[CURATED:SIMULATION]",
        "source": "MOSPI_SIMULATION",
    },
    {
        "task_id": "TASK-MOSPI-MISC-01",
        "title": "Industrial Census Unit-Level Missing Data Imputation",
        "competency_name": "Data Quality",
        "subskill_name": "Missing data assessment",
        "scenario_type": PracticalScenarioType.DATA_ANALYSIS.value,
        "difficulty": PracticalDifficulty.MEDIUM.value,
        "scenario_context": (
            "Official-Statistics-aligned simulated practical scenario. In the Annual Survey of Unincorporated "
            "Sector Enterprises (ASUSE), missing unit turnover values occur under Missing At Random (MAR) "
            "assumptions conditional on industry stratum. Statistical officers must perform donor/mean imputation."
        ),
        "instructions": (
            "Given enterprise survey records across two industry strata ('TEXTILE' and 'FOOD_PROC'):\n"
            "1. Calculate the stratum-specific observed mean turnover for non-missing units.\n"
            "2. Impute the missing unit values using their respective stratum mean turnover.\n"
            "3. Compute the overall sample aggregate turnover after imputation.\n"
            "Submit your answers as JSON with keys: 'stratum_means', 'imputed_values', 'total_turnover', "
            "and 'methodology_note'."
        ),
        "input_artifacts": {
            "description": "ASUSE Enterprise Sample Table with Missing Turnover",
            "records": [
                {"unit_id": "U-1", "stratum": "TEXTILE", "turnover": 120.0},
                {"unit_id": "U-2", "stratum": "TEXTILE", "turnover": 160.0},
                {"unit_id": "U-3", "stratum": "TEXTILE", "turnover": None},
                {"unit_id": "U-4", "stratum": "TEXTILE", "turnover": 140.0},
                {"unit_id": "U-5", "stratum": "FOOD_PROC", "turnover": 250.0},
                {"unit_id": "U-6", "stratum": "FOOD_PROC", "turnover": None},
                {"unit_id": "U-7", "stratum": "FOOD_PROC", "turnover": 350.0},
            ],
        },
        "expected_output_type": "NUMERICAL_JSON",
        "rubric": {
            "version": "v1.0-rubric",
            "dimensions": {
                "stratum_means": {
                    "weight": 0.30,
                    "expected": {
                        "TEXTILE": 140.0,
                        "FOOD_PROC": 300.0,
                    },
                    "tolerance": 0.01,
                },
                "imputed_values": {
                    "weight": 0.35,
                    "expected": {
                        "U-3": 140.0,
                        "U-6": 300.0,
                    },
                    "tolerance": 0.01,
                },
                "total_turnover": {
                    "weight": 0.20,
                    "expected": 1460.0,
                    "tolerance": 0.01,
                },
                "methodology_note": {
                    "weight": 0.15,
                    "keywords": ["stratum", "imputation", "mean", "missing"],
                    "min_length": 20,
                },
            },
            "passing_score": 0.70,
        },
        "rubric_version": "v1.0-rubric",
        "prerequisites": ["Missing data assessment", "Stratum mean imputation"],
        "provenance": "[CURATED:SIMULATION]",
        "source": "MOSPI_SIMULATION",
    },
]


def seed_practical_tasks(db: Session) -> dict[str, int]:
    """Idempotently seed authentic MoSPI practical scenarios."""
    counts = {"created": 0, "updated": 0, "total": len(PRACTICAL_TASKS_DATA)}

    # Fetch competency and subskill lookup maps
    competencies = {c.name.strip(): c for c in db.execute(select(Competency)).scalars().all()}
    subskills = {s.name.strip(): s for s in db.execute(select(SubSkill)).scalars().all()}

    for data in PRACTICAL_TASKS_DATA:
        task_id = data["task_id"]
        comp = competencies.get(data["competency_name"])
        sub = subskills.get(data["subskill_name"])

        if not comp:
            continue

        existing = db.execute(
            select(PracticalTask).where(PracticalTask.task_id == task_id)
        ).scalar_one_or_none()

        if existing:
            existing.title = data["title"]
            existing.competency_id = comp.id
            existing.subskill_id = sub.id if sub else None
            existing.scenario_type = data["scenario_type"]
            existing.difficulty = data["difficulty"]
            existing.scenario_context = data["scenario_context"]
            existing.instructions = data["instructions"]
            existing.input_artifacts_json = json.dumps(data["input_artifacts"])
            existing.expected_output_type = data["expected_output_type"]
            existing.rubric_json = json.dumps(data["rubric"])
            existing.rubric_version = data["rubric_version"]
            existing.prerequisites_json = json.dumps(data["prerequisites"])
            existing.provenance = data["provenance"]
            existing.source = data["source"]
            existing.updated_at = datetime.now(timezone.utc)
            counts["updated"] += 1
        else:
            task = PracticalTask(
                task_id=task_id,
                title=data["title"],
                competency_id=comp.id,
                subskill_id=sub.id if sub else None,
                scenario_type=data["scenario_type"],
                difficulty=data["difficulty"],
                scenario_context=data["scenario_context"],
                instructions=data["instructions"],
                input_artifacts_json=json.dumps(data["input_artifacts"]),
                expected_output_type=data["expected_output_type"],
                rubric_json=json.dumps(data["rubric"]),
                rubric_version=data["rubric_version"],
                prerequisites_json=json.dumps(data["prerequisites"]),
                provenance=data["provenance"],
                source=data["source"],
                status="ACTIVE",
            )
            db.add(task)
            counts["created"] += 1

    db.commit()
    return counts
