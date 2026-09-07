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
from app.routers.practical import router as practical_router
from app.routers.scenarios import router as scenarios_router
from app.routers.users import router as users_router
from app.routers.workforce import router as workforce_router
from app.routers.governance import router as governance_router


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

    # Schema is managed canonically via Alembic migrations.
    # Startup performs zero runtime schema mutations.


    try:
        from app.seed_data.intervention_catalog_loader import seed_intervention_catalog
        from app.seed_data.practical_scenario_loader import seed_practical_tasks
        from app.services.governance_service import GovernanceService
        db = SessionLocal()
        try:
            seed_intervention_catalog(db)
            seed_practical_tasks(db)
            GovernanceService.initialize_governance_data(db)
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
app.include_router(practical_router, prefix="/api")
app.include_router(scenarios_router, prefix="/api")
app.include_router(workforce_router, prefix="/api")
app.include_router(governance_router, prefix="/api")


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
