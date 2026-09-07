"""
ml_pipeline/canonical_taxonomy.py — Canonical GyanSetu Competency & Subskill Taxonomy.

Mirrors and validates against the 4 Competency Domains, 40 Competencies, and 160 Subskills
defined in the frozen GyanSetu system of record (backend/app/seed_data/competency_taxonomy.py).
"""
from __future__ import annotations

from typing import Any

CANONICAL_DOMAINS = {
    "STATISTICAL": "Statistical Competencies",
    "TECHNICAL_DIGITAL": "Technical and Digital Skills",
    "DIGITAL_GOVERNANCE": "Digital Governance and Data Security",
    "BEHAVIOURAL_MANAGERIAL": "Behavioural and Managerial Competencies",
}

CANONICAL_COMPETENCIES: dict[str, str] = {
    # Statistical
    "Sampling Design": "STATISTICAL",
    "Data Quality": "STATISTICAL",
    "Survey Methodology": "STATISTICAL",
    "Statistical Modelling": "STATISTICAL",
    "National Accounts": "STATISTICAL",
    "Index Numbers": "STATISTICAL",
    "Time Series": "STATISTICAL",
    "Estimation": "STATISTICAL",
    "Administrative Data": "STATISTICAL",
    "SDG Indicators": "STATISTICAL",
    # Technical & Digital
    "Python for Analytics": "TECHNICAL_DIGITAL",
    "Data Pipelines": "TECHNICAL_DIGITAL",
    "Database Management": "TECHNICAL_DIGITAL",
    "Data Visualization": "TECHNICAL_DIGITAL",
    "Cloud and Infrastructure": "TECHNICAL_DIGITAL",
    "Data Science": "TECHNICAL_DIGITAL",
    "Automation": "TECHNICAL_DIGITAL",
    "AI/ML Fundamentals": "TECHNICAL_DIGITAL",
    "Statistical Computing": "TECHNICAL_DIGITAL",
    "Data Architecture": "TECHNICAL_DIGITAL",
    # Digital Governance
    "Data Privacy": "DIGITAL_GOVERNANCE",
    "Cybersecurity Awareness": "DIGITAL_GOVERNANCE",
    "Government Cloud": "DIGITAL_GOVERNANCE",
    "Open Data Standards": "DIGITAL_GOVERNANCE",
    "Digital Records Management": "DIGITAL_GOVERNANCE",
    "Data Governance": "DIGITAL_GOVERNANCE",
    "Information Security Governance": "DIGITAL_GOVERNANCE",
    "Data Ethics": "DIGITAL_GOVERNANCE",
    "Digital Service Delivery": "DIGITAL_GOVERNANCE",
    "Technology Risk Management": "DIGITAL_GOVERNANCE",
    # Behavioural & Managerial
    "Communication": "BEHAVIOURAL_MANAGERIAL",
    "Team Leadership": "BEHAVIOURAL_MANAGERIAL",
    "Project Management": "BEHAVIOURAL_MANAGERIAL",
    "Training Delivery": "BEHAVIOURAL_MANAGERIAL",
    "Stakeholder Engagement": "BEHAVIOURAL_MANAGERIAL",
    "Change Management": "BEHAVIOURAL_MANAGERIAL",
    "Strategic Planning": "BEHAVIOURAL_MANAGERIAL",
    "Policy Coordination": "BEHAVIOURAL_MANAGERIAL",
    "Performance Management": "BEHAVIOURAL_MANAGERIAL",
    "Professional Ethics": "BEHAVIOURAL_MANAGERIAL",
}

CANONICAL_SUBSKILLS: dict[str, tuple[str, ...]] = {
    "Sampling Design": ("Sampling frames", "Probability sampling", "Stratified sampling", "Sample size planning"),
    "Data Quality": ("Validation rules", "Missing data assessment", "Error profiling", "Quality reporting"),
    "Survey Methodology": ("Questionnaire design", "Fieldwork protocols", "Non-response management", "Survey weighting"),
    "Statistical Modelling": ("Model specification", "Regression diagnostics", "Model validation", "Interpretation of results"),
    "National Accounts": ("Supply and use tables", "Institutional sectors", "GDP compilation", "Benchmark revisions"),
    "Index Numbers": ("Price relatives", "Weight selection", "Laspeyres and Paasche indices", "Index rebasing"),
    "Time Series": ("Trend and seasonality", "Stationarity checks", "Forecast evaluation", "Seasonal adjustment"),
    "Estimation": ("Point estimation", "Variance estimation", "Small area estimation", "Confidence intervals"),
    "Administrative Data": ("Source assessment", "Data integration", "Coverage evaluation", "Metadata documentation"),
    "SDG Indicators": ("Indicator definitions", "Disaggregation", "Reporting metadata", "Data validation"),
    "Python for Analytics": ("Data frames", "Statistical packages", "Reproducible scripts", "Package management"),
    "Data Pipelines": ("Ingestion workflows", "Transformation stages", "Pipeline monitoring", "Data lineage"),
    "Database Management": ("Relational modelling", "SQL querying", "Indexing strategies", "Backup and recovery"),
    "Data Visualization": ("Chart selection", "Dashboard composition", "Accessible visual design", "Visual quality checks"),
    "Cloud and Infrastructure": ("Compute concepts", "Storage architecture", "Service monitoring", "Infrastructure cost awareness"),
    "Data Science": ("Feature preparation", "Exploratory analysis", "Model evaluation", "Experiment tracking"),
    "Automation": ("Task automation", "Workflow scheduling", "Testing automated jobs", "Operational logging"),
    "AI/ML Fundamentals": ("Supervised learning", "Unsupervised learning", "Model limitations", "Responsible AI basics"),
    "Statistical Computing": ("Numerical methods", "Performance profiling", "Code testing", "Reproducible environments"),
    "Data Architecture": ("Data models", "Integration patterns", "Reference data", "Architecture documentation"),
    "Data Privacy": ("Personal data principles", "Purpose limitation", "Data minimisation", "Privacy impact assessment"),
    "Cybersecurity Awareness": ("Phishing awareness", "Access control", "Secure handling", "Incident reporting"),
    "Government Cloud": ("Cloud service models", "Government hosting controls", "Cloud continuity", "Shared responsibility"),
    "Open Data Standards": ("Open formats", "Metadata standards", "Data catalogues", "License awareness"),
    "Digital Records Management": ("Record classification", "Retention schedules", "Digital preservation", "Audit trails"),
    "Data Governance": ("Data ownership", "Stewardship roles", "Data policies", "Governance reviews"),
    "Information Security Governance": ("Security policies", "Risk registers", "Control assurance", "Security audits"),
    "Data Ethics": ("Fairness considerations", "Bias identification", "Transparency", "Ethical review"),
    "Digital Service Delivery": ("User-centred services", "Service standards", "Accessibility", "Service monitoring"),
    "Technology Risk Management": ("Risk identification", "Impact assessment", "Mitigation planning", "Risk monitoring"),
    "Communication": ("Technical writing", "Briefing skills", "Data storytelling", "Public communication"),
    "Team Leadership": ("Team direction", "Delegation", "Feedback practices", "Conflict resolution"),
    "Project Management": ("Scope planning", "Milestone tracking", "Risk management", "Project closure"),
    "Training Delivery": ("Learning objectives", "Facilitation", "Assessment design", "Training evaluation"),
    "Stakeholder Engagement": ("Stakeholder mapping", "Consultation planning", "Expectation management", "Engagement records"),
    "Change Management": ("Change impact analysis", "Adoption planning", "Change communication", "Benefits tracking"),
    "Strategic Planning": ("Strategic objectives", "Operational planning", "Resource alignment", "Strategy review"),
    "Policy Coordination": ("Policy analysis", "Interdepartmental coordination", "Decision briefs", "Policy follow-up"),
    "Performance Management": ("Outcome indicators", "Performance reviews", "Corrective actions", "Performance reporting"),
    "Professional Ethics": ("Integrity", "Impartiality", "Confidentiality", "Accountability"),
}


def is_canonical_competency(name: str) -> bool:
    return name in CANONICAL_COMPETENCIES


def is_canonical_subskill(competency_name: str, subskill_name: str) -> bool:
    subskills = CANONICAL_SUBSKILLS.get(competency_name)
    if subskills is None:
        return False
    return subskill_name in subskills


def validate_taxonomy_reference(competency_name: str, subskill_name: str) -> tuple[bool, str | None]:
    if competency_name not in CANONICAL_COMPETENCIES:
        return False, f"Unknown competency: '{competency_name}'. Must be one of the 40 canonical competencies."
    allowed_subskills = CANONICAL_SUBSKILLS.get(competency_name, ())
    if subskill_name not in allowed_subskills:
        return False, f"Subskill '{subskill_name}' does not belong to competency '{competency_name}'. Allowed: {allowed_subskills}"
    return True, None
