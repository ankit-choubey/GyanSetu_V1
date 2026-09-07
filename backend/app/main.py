from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.assessment import router as assessment_router
from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.chatbot import router as chatbot_router
from app.routers.competency import router as competency_router
from app.routers.content import router as content_router
from app.routers.dashboard import router as dashboard_router
from app.routers.diagnostic import router as diagnostic_router
from app.routers.ecosystem import router as ecosystem_router
from app.routers.evidence import router as evidence_router
from app.routers.intervention import router as intervention_router
from app.routers.misconception import router as misconception_router
from app.routers.monitoring import router as monitoring_router
from app.routers.users import router as users_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GyanSetu backend foundation for competency-driven learning platform.",
    debug=settings.debug,
)


@app.on_event("startup")
def on_startup() -> None:
    from sqlmodel import SQLModel
    from app.database import engine, SessionLocal
    import app.models  # noqa: F401
    SQLModel.metadata.create_all(engine)

    # Ensure SQLite interventions columns exist on existing databases
    try:
        with engine.begin() as conn:
            cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(interventions)").fetchall()}
            if cols:
                if "provider" not in cols:
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN provider VARCHAR(100) DEFAULT 'INTERNAL' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN modality VARCHAR(50) DEFAULT 'ONLINE_SELF_PACED' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN duration_minutes INTEGER DEFAULT 60")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN difficulty VARCHAR(20) DEFAULT 'intermediate' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN prerequisites_json VARCHAR")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN availability VARCHAR(50) DEFAULT 'ALWAYS_AVAILABLE' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN status VARCHAR(50) DEFAULT 'ACTIVE' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN source VARCHAR(100) DEFAULT 'SYSTEM' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN source_id VARCHAR(100)")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN source_url VARCHAR(500)")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN provenance VARCHAR(100) DEFAULT '[CURATED]' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN version VARCHAR(20) DEFAULT 'v1.0' NOT NULL")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN last_verified_at DATETIME")
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN target_misconception_pattern VARCHAR(255)")
                if "integration_mode" not in cols:
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN integration_mode VARCHAR(20) DEFAULT 'REPLAY' NOT NULL")
                if "external_metadata_json" not in cols:
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN external_metadata_json VARCHAR")
                if "mapping_status" not in cols:
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN mapping_status VARCHAR(50) DEFAULT 'CURATED' NOT NULL")
                if "mapping_confidence" not in cols:
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN mapping_confidence FLOAT DEFAULT 1.0 NOT NULL")
                if "last_synced_at" not in cols:
                    conn.exec_driver_sql("ALTER TABLE interventions ADD COLUMN last_synced_at DATETIME")

            outcome_cols = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(intervention_outcomes)").fetchall()}
            if outcome_cols:
                if "provider" not in outcome_cols:
                    conn.exec_driver_sql("ALTER TABLE intervention_outcomes ADD COLUMN provider VARCHAR(100)")
                if "provider_resource_id" not in outcome_cols:
                    conn.exec_driver_sql("ALTER TABLE intervention_outcomes ADD COLUMN provider_resource_id VARCHAR(100)")
                if "provider_activity_id" not in outcome_cols:
                    conn.exec_driver_sql("ALTER TABLE intervention_outcomes ADD COLUMN provider_activity_id VARCHAR(128)")
                if "integration_mode" not in outcome_cols:
                    conn.exec_driver_sql("ALTER TABLE intervention_outcomes ADD COLUMN integration_mode VARCHAR(20)")
                if "started_at" not in outcome_cols:
                    conn.exec_driver_sql("ALTER TABLE intervention_outcomes ADD COLUMN started_at DATETIME")
                if "completed_at" not in outcome_cols:
                    conn.exec_driver_sql("ALTER TABLE intervention_outcomes ADD COLUMN completed_at DATETIME")
    except Exception:
        pass

    try:
        from app.seed_data.intervention_catalog_loader import seed_intervention_catalog
        db = SessionLocal()
        try:
            seed_intervention_catalog(db)
        finally:
            db.close()
    except Exception:
        pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(competency_router, prefix="/api")
app.include_router(assessment_router, prefix="/api")
app.include_router(diagnostic_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(misconception_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(intervention_router, prefix="/api")
app.include_router(ecosystem_router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }


@app.get("/")
def root() -> dict[str, str]:
    return {"message": f"Welcome to {settings.app_name}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug and settings.environment == "development")
