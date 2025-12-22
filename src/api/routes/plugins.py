from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.api import deps
from src.core.maim_config_client import client as maim_config_client
from maim_db.maimconfig_models.models import User, Tenant

router = APIRouter()

class PluginSettingIn(BaseModel):
    plugin_name: str
    enabled: bool
    config: Dict[str, Any]

@router.post("/settings")
async def upsert_plugin_setting(
    setting: PluginSettingIn,
    agent_id: str = Query(..., description="Agent ID"),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Upsert plugin setting via Proxy.
    """
    try:
        # 1. Get Agent from MaimConfig to find tenant_id
        agent_resp = await maim_config_client.get_agent(agent_id)
        if not agent_resp.get("success"):
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = agent_resp["data"]
        tenant_id = agent_data["tenant_id"]
        
        # 2. Verify Ownership
        stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(status_code=403, detail="Permission denied")

        # 3. Call MaimConfig
        resp = await maim_config_client.upsert_plugin_setting(
            tenant_id=tenant_id,
            agent_id=agent_id,
            setting_data=setting.dict()
        )
        return resp
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
