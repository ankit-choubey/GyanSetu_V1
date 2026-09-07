from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionBankRecord:
    competency_name: str
    subskill_name: str
    question_text: str
    options: tuple[str, str, str, str]
    correct_option: str
    difficulty: str


def _question(
    competency_name: str,
    subskill_name: str,
    question_text: str,
    options: tuple[str, str, str, str],
    correct_option: str,
    difficulty: str,
) -> QuestionBankRecord:
    return QuestionBankRecord(
        competency_name=competency_name,
        subskill_name=subskill_name,
        question_text=question_text,
        options=options,
        correct_option=correct_option,
        difficulty=difficulty,
    )


QUESTION_BANK: tuple[QuestionBankRecord, ...] = (
    _question(
        "Data Quality",
        "Validation rules",
        "Which action best implements a dataset validation rule before publication?",
        (
            "Release the file as soon as collection ends",
            "Check that coded values fall within the allowed range",
            "Delete records that look unusual without review",
            "Replace all missing values with zero",
        ),
        "B",
        "easy",
    ),
    _question(
        "Data Quality",
        "Missing data assessment",
        "What is the first step when a survey variable has a high item non-response rate?",
        (
            "Impute every gap with the sample mean",
            "Drop the variable from all future collections",
            "Assess the pattern and possible causes of missingness",
            "Fill missing cells from a neighbouring country",
        ),
        "C",
        "medium",
    ),
    _question(
        "Sampling Design",
        "Probability sampling",
        "Why is probability sampling preferred for official statistics estimates?",
        (
            "It always costs less than a census",
            "Every unit has a known, non-zero chance of selection",
            "Interviewers can choose convenient respondents",
            "It removes the need for weighting",
        ),
        "B",
        "medium",
    ),
    _question(
        "Sampling Design",
        "Stratified sampling",
        "What is the main purpose of stratification in a sample design?",
        (
            "To guarantee that every household is selected",
            "To replace the sampling frame",
            "To improve precision by grouping similar units before selection",
            "To avoid calculating design weights",
        ),
        "C",
        "easy",
    ),
    _question(
        "Survey Methodology",
        "Questionnaire design",
        "Which questionnaire practice reduces measurement error?",
        (
            "Ask two concepts in a single double-barrelled item",
            "Use leading wording that suggests the expected answer",
            "Pilot the questions and revise unclear wording",
            "Place sensitive questions without any introduction",
        ),
        "C",
        "easy",
    ),
    _question(
        "Estimation",
        "Variance estimation",
        "Why must a complex survey publish sampling variance alongside estimates?",
        (
            "Variance figures replace the need for metadata",
            "Users need a measure of sampling uncertainty for inference",
            "Variance estimation removes non-sampling error",
            "It is required only for census outputs",
        ),
        "B",
        "hard",
    ),
    _question(
        "Python for Analytics",
        "Reproducible scripts",
        "Which practice most improves reproducibility of an analysis script?",
        (
            "Hard-code machine-specific file paths and silent edits",
            "Record package versions and keep the workflow in version control",
            "Copy results from an interactive console without saving code",
            "Overwrite raw input files during cleaning",
        ),
        "B",
        "medium",
    ),
    _question(
        "Data Privacy",
        "Data minimisation",
        "What does data minimisation require when compiling a statistical product?",
        (
            "Collect every available identifier in case it is useful later",
            "Retain personal data only to the extent needed for the stated purpose",
            "Publish microdata with names to aid verification",
            "Share full administrative extracts with all contractors by default",
        ),
        "B",
        "medium",
    ),
    _question(
        "Data Governance",
        "Data ownership",
        "In a statistical organisation, who should be accountable for a key data asset?",
        (
            "An unnamed shared inbox",
            "A named data owner with defined stewardship duties",
            "Any user who last edited the file",
            "An external vendor with no internal sponsor",
        ),
        "B",
        "easy",
    ),
    _question(
        "Communication",
        "Data storytelling",
        "Which approach best communicates a statistical finding to non-specialists?",
        (
            "Lead with the decision-relevant message and support it with a clear chart",
            "Present every table from the production system without commentary",
            "Use unexplained jargon to appear more technical",
            "Omit uncertainty so the story looks simpler",
        ),
        "A",
        "easy",
    ),
    _question(
        "Professional Ethics",
        "Impartiality",
        "How should a statistical officer respond to pressure to alter an inconvenient estimate?",
        (
            "Change the figure to match the requested narrative",
            "Delay publication indefinitely without explanation",
            "Protect the integrity of the methods and explain the result transparently",
            "Delete the underlying microdata so the estimate cannot be checked",
        ),
        "C",
        "medium",
    ),
    _question(
        "Database Management",
        "SQL querying",
        "Which SQL practice reduces the risk of incorrect aggregates on large statistical tables?",
        (
            "Select star from every table and total in a spreadsheet",
            "Join on poorly documented fields without checking grain",
            "State the grain of the query and validate joins against known counts",
            "Use SELECT DISTINCT to hide duplicated keys",
        ),
        "C",
        "medium",
    ),
)
