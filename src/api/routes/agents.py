from typing import Any, List, Optional
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from src.api import deps
from src.core.maim_config_client import client as maim_config_client
from src.schemas import api_key as api_key_schema
from maim_db.maimconfig_models.models import User, Tenant

router = APIRouter()

# Schema definitions (temporary, should be moved to schemas/)
class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    config: Optional[dict] = None
    template_id: Optional[str] = None

class AgentCreate(AgentBase):
    pass

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    template_id: Optional[str] = None
    status: Optional[str] = None

class AgentOut(AgentBase):
    id: str
    tenant_id: str
    status: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[AgentOut])
async def read_agents(
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve agents via MaimConfig Proxy.
    """
    # 1. Get User's Tenants
    user_tenants_query = select(Tenant.id).where(Tenant.owner_id == current_user.id)
    result = await db.execute(user_tenants_query)
    tenant_ids = result.scalars().all()
    
    if not tenant_ids:
        return []

    # 2. Fetch Agents for each Tenant from MaimConfig
    # Note: This could be optimized if MaimConfig supported bulk fetching or list by multiple tenants
    # For now, we fetch concurrently
    tasks = [maim_config_client.get_agents(tid) for tid in tenant_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    all_agents = []
    for res in results:
        if isinstance(res, dict) and res.get("success"):
             # data contains {"items": [], "total": ...} or list?
             # Checking api_docs/agent_api.py: returns items list inside data?
             # agent_api.py list_agents returns data={"items": [...], ...}
             data = res.get("data", {})
             items = data.get("items", []) if isinstance(data, dict) else []
             all_agents.extend(items)
        # Identify connection errors? user might want to know
    
    # Simple pagination in memory (inefficient for large datasets but ok for now)
    return all_agents[skip : skip + limit]


@router.post("/", response_model=AgentOut)
async def create_agent(
    *,
    db: AsyncSession = Depends(deps.get_db),
    agent_in: AgentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new agent via Proxy.
    Defaults to the user's first tenant.
    """
    # 1. Get User's First Tenant
    result = await db.execute(select(Tenant).where(Tenant.owner_id == current_user.id))
    tenant = result.scalars().first()
    
    if not tenant:
        raise HTTPException(status_code=400, detail="User has no tenant to create agent in")
        
    # 2. Call MaimConfig
    payload = agent_in.dict()
    payload["tenant_id"] = tenant.id
    
    try:
        resp = await maim_config_client.create_agent(payload)
        if not resp.get("success"):
            raise HTTPException(status_code=400, detail=resp.get("message"))
        
        # Returns {"data": {"agent_id": "...", ...}}
        # We need to fetch the full object? create_agent usually returns the object?
        # agent_api.py create_agent returns data={agent_id, tenant_id, name...}
        return resp["data"]
        
    except Exception as e:
         raise HTTPException(status_code=503, detail=str(e))


@router.get("/{agent_id}", response_model=AgentOut)
async def read_agent(
    agent_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get agent by ID via Proxy.
    """
    try:
        # 1. Get Agent from MaimConfig
        resp = await maim_config_client.get_agent(agent_id)
        if not resp.get("success"):
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = resp["data"]
        tenant_id = agent_data["tenant_id"]
        
        # 2. Verify Ownership (Check if tenant_id belongs to user)
        stmt = select(Tenant).where(Tenant.id == tenant_id, Tenant.owner_id == current_user.id)
        result = await db.execute(stmt)
        if not result.scalars().first():
            raise HTTPException(status_code=403, detail="Permission denied")
            
        return agent_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.put("/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: str,
    agent_in: AgentUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update agent via Proxy.
    """
    # 1. Check permission first? Or fetch first? Update needs tenant_id to check permission.
    # MaimConfig update endpoint doesn't return tenant_id in error if not found.
    # We fetch agent first (read_agent logic)
    await read_agent(agent_id, db, current_user) # reusing check logic
    
    try:
        resp = await maim_config_client.update_agent(agent_id, agent_in.dict(exclude_unset=True))
        if not resp.get("success"):
            raise HTTPException(status_code=400, detail=resp.get("message"))
        return resp["data"]
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# API Key Proxy Implementation (Reusing similar logic)

@router.post("/{agent_id}/api_keys", response_model=api_key_schema.ApiKey)
async def create_agent_api_key(
    agent_id: str,
    api_key_in: api_key_schema.ApiKeyCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Verify permission
    await read_agent(agent_id, db, current_user)
    
    try:
        payload = api_key_in.dict()
        # Need tenant_id? create_api_key in MaimConfig needs tenant_id AND agent_id
        # We need to fetch agent to get tenant_id first...
        agent_resp = await maim_config_client.get_agent(agent_id)
        tenant_id = agent_resp["data"]["tenant_id"]
        
        payload["tenant_id"] = tenant_id
        payload["agent_id"] = agent_id
        
        resp = await maim_config_client.create_api_key(payload)
        if not resp.get("success"):
             raise HTTPException(status_code=400, detail=resp.get("message"))
             
        # Response mapping
        data = resp["data"]
        data["id"] = data.pop("api_key_id", None) or data.get("id")
        return data
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/{agent_id}/api_keys", response_model=List[api_key_schema.ApiKey])
async def read_agent_api_keys(
    agent_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # Verify permission
    await read_agent(agent_id, db, current_user)
    
    # Get agent to get tenant_id
    # Optimization: read_agent already fetches it, we could return it? but simpler to refetch or just assume user owns agent if pass
    # Actually maim_config_client.get_api_keys needs tenant_id.
    agent_resp = await maim_config_client.get_agent(agent_id)
    tenant_id = agent_resp["data"]["tenant_id"]
    
    try:
        resp = await maim_config_client.get_api_keys(tenant_id, agent_id)
        if not resp.get("success"):
            return []
            
        items = resp["data"].get("items", [])
        for item in items:
            item["id"] = item.pop("api_key_id", None) or item.get("id")
        return items
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/{agent_id}/api_keys/{key_id}", status_code=204)
async def delete_agent_api_key(
    agent_id: str,
    key_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    # Verify permission for agent
    await read_agent(agent_id, db, current_user)
    
    try:
        await maim_config_client.delete_api_key(key_id)
        return None
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

