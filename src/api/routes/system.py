from typing import Any, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from src.core.maim_config_client import client as maim_config_client
from src.api import deps
from src.schemas.user import User

router = APIRouter()

@router.get("/models")
async def get_system_models(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get system defined models (Proxy to MaimConfig)
    """
    try:
        resp = await maim_config_client.get_system_models()
        if not resp.get("success"):
            raise HTTPException(status_code=500, detail=resp.get("message"))
        return resp["data"]
    except Exception as e:
        print(f"ERROR get_system_models: {e}")
        raise HTTPException(status_code=503, detail=f"MaimConfig service unavailable: {str(e)}")


@router.get("/bot-defaults")
async def get_bot_defaults(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get bot default configuration (Proxy to MaimConfig)
    """
    try:
        resp = await maim_config_client.get_bot_defaults()
        if not resp.get("success"):
            raise HTTPException(status_code=500, detail=resp.get("message"))
        return resp["data"]
    except Exception as e:
        print(f"ERROR get_bot_defaults: {e}")
        raise HTTPException(status_code=503, detail=f"MaimConfig service unavailable: {str(e)}")
