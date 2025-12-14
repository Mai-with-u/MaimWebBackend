
from dotenv import load_dotenv
load_dotenv()

print("Starting MaimWebBackend...", flush=True)
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import auth, agents
from src.core.settings import settings
from maim_db.maimconfig_models.models import create_tables

app = FastAPI(
    title=settings.PROJECT_NAME, 
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}/agents", tags=["agents"])


@app.on_event("startup")
async def startup_event():
    # 自动创建表 (User, Tenant等)
    # in production might want to use alembic, but for now auto-create is fine as per plan
    await create_tables()


@app.get("/")
def read_root():
    return {"message": "Welcome to MaimWebBackend API"}
