from __future__ import annotations

from dataclasses import dataclass

from app.models.competency import CompetencyDomain


@dataclass(frozen=True)
class TaxonomyCompetency:
    name: str
    domain: CompetencyDomain
    subskills: tuple[str, ...]


@dataclass(frozen=True)
class TaxonomyRole:
    name: str
    competency_names: tuple[str, ...]



def _subskills(name: str, *items: str) -> TaxonomyCompetency:
    return TaxonomyCompetency(name=name, domain=DOMAIN_BY_COMPETENCY[name], subskills=tuple(items))


DOMAIN_BY_COMPETENCY: dict[str, CompetencyDomain] = {
    "Sampling Design": CompetencyDomain.STATISTICAL,
    "Data Quality": CompetencyDomain.STATISTICAL,
    "Survey Methodology": CompetencyDomain.STATISTICAL,
    "Statistical Modelling": CompetencyDomain.STATISTICAL,
    "National Accounts": CompetencyDomain.STATISTICAL,
    "Index Numbers": CompetencyDomain.STATISTICAL,
    "Time Series": CompetencyDomain.STATISTICAL,
    "Estimation": CompetencyDomain.STATISTICAL,
    "Administrative Data": CompetencyDomain.STATISTICAL,
    "SDG Indicators": CompetencyDomain.STATISTICAL,
    "Python for Analytics": CompetencyDomain.TECHNICAL_DIGITAL,
    "Data Pipelines": CompetencyDomain.TECHNICAL_DIGITAL,
    "Database Management": CompetencyDomain.TECHNICAL_DIGITAL,
    "Data Visualization": CompetencyDomain.TECHNICAL_DIGITAL,
    "Cloud and Infrastructure": CompetencyDomain.TECHNICAL_DIGITAL,
    "Data Science": CompetencyDomain.TECHNICAL_DIGITAL,
    "Automation": CompetencyDomain.TECHNICAL_DIGITAL,
    "AI/ML Fundamentals": CompetencyDomain.TECHNICAL_DIGITAL,
    "Statistical Computing": CompetencyDomain.TECHNICAL_DIGITAL,
    "Data Architecture": CompetencyDomain.TECHNICAL_DIGITAL,
    "Data Privacy": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Cybersecurity Awareness": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Government Cloud": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Open Data Standards": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Digital Records Management": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Data Governance": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Information Security Governance": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Data Ethics": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Digital Service Delivery": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Technology Risk Management": CompetencyDomain.DIGITAL_GOVERNANCE,
    "Communication": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Team Leadership": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Project Management": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Training Delivery": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Stakeholder Engagement": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Change Management": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Strategic Planning": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Policy Coordination": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Performance Management": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
    "Professional Ethics": CompetencyDomain.BEHAVIOURAL_MANAGERIAL,
}


_SUBSKILL_SETS: dict[str, tuple[str, ...]] = {
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

COMPETENCIES: tuple[TaxonomyCompetency, ...] = tuple(
    TaxonomyCompetency(name=name, domain=DOMAIN_BY_COMPETENCY[name], subskills=subskills)
    for name, subskills in _SUBSKILL_SETS.items()
)


ROLES: tuple[TaxonomyRole, ...] = (
    TaxonomyRole("Statistical Officer", ("Sampling Design", "Data Quality", "Survey Methodology", "Estimation", "SDG Indicators", "Communication", "Professional Ethics")),
    TaxonomyRole("Senior Statistical Officer", ("Sampling Design", "Data Quality", "Survey Methodology", "Statistical Modelling", "Time Series", "Estimation", "Training Delivery", "Stakeholder Engagement")),
    TaxonomyRole("Assistant Director", ("Survey Methodology", "Statistical Modelling", "National Accounts", "Index Numbers", "Administrative Data", "Project Management", "Team Leadership", "Policy Coordination")),
    TaxonomyRole("Deputy Director", ("National Accounts", "Index Numbers", "Time Series", "Administrative Data", "SDG Indicators", "Strategic Planning", "Performance Management", "Data Governance")),
    TaxonomyRole("Director", ("Statistical Modelling", "National Accounts", "SDG Indicators", "Data Governance", "Data Ethics", "Technology Risk Management", "Strategic Planning", "Policy Coordination", "Stakeholder Engagement", "Change Management", "Professional Ethics")),
    TaxonomyRole("Statistical Investigator", ("Sampling Design", "Data Quality", "Survey Methodology", "Administrative Data", "Python for Analytics", "Data Visualization", "Communication")),
    TaxonomyRole("Data Analyst", ("Data Quality", "Python for Analytics", "Data Pipelines", "Database Management", "Data Visualization", "Data Science", "Statistical Computing", "Automation", "AI/ML Fundamentals", "Data Privacy", "Open Data Standards")),
    TaxonomyRole("IT Officer", ("Database Management", "Data Pipelines", "Cloud and Infrastructure", "Automation", "Data Architecture", "Cybersecurity Awareness", "Government Cloud", "Open Data Standards", "Digital Records Management", "Digital Service Delivery", "Information Security Governance", "Technology Risk Management")),
)


def taxonomy_counts() -> tuple[int, int, int, int]:
    return len(ROLES), len({competency.domain for competency in COMPETENCIES}), len(COMPETENCIES), sum(len(competency.subskills) for competency in COMPETENCIES)
