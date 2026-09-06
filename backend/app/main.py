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
from app.routers.users import router as users_router
from app.routers.monitoring import router as monitoring_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="GyanSetu backend foundation for competency-driven learning platform.",
    debug=settings.debug,
)

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
app.include_router(dashboard_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")


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
