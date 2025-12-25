
from dotenv import load_dotenv
load_dotenv()

print("Starting MaimWebBackend...", flush=True)
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.routes import auth, agents, plugins, tenants, api_keys, admin, system
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
app.include_router(plugins.router, prefix=f"{settings.API_V1_STR}/plugins", tags=["plugins"])
app.include_router(tenants.router, prefix=f"{settings.API_V1_STR}/tenants", tags=["tenants"])
app.include_router(api_keys.router, prefix=f"{settings.API_V1_STR}/api-keys", tags=["api-keys"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(system.router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])


@app.on_event("startup")
async def startup_event():
    # 自动创建表 (User, Tenant等)
    # in production might want to use alembic, but for now auto-create is fine as per plan
    # await create_tables()
    pass


@app.get("/")
def read_root():
    return {"message": "Welcome to MaimWebBackend API"}
