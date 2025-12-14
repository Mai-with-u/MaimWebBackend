from typing import Any, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from src.api import deps
from src.schemas import api_key as api_key_schema
from maim_db.maimconfig_models.models import User, Agent, AgentStatus, Tenant, ApiKey, ApiKeyStatus
import secrets
from datetime import datetime
import logging

router = APIRouter()


# 简单的 Schema 定义，实际项目中应放在 schemas/agent.py
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
    Retrieve agents.
    Only returns agents belonging to tenants owned by the current user.
    """
    # 查找属于用户的所有 tenants
    user_tenants_query = select(Tenant.id).where(Tenant.owner_id == current_user.id)
    result = await db.execute(user_tenants_query)
    tenant_ids = result.scalars().all()
    
    if not tenant_ids:
        return []

    # 查找这些 tenants 下的 agents
    query = select(Agent).where(Agent.tenant_id.in_(tenant_ids)).offset(skip).limit(limit)
    result = await db.execute(query)
    agents = result.scalars().all()
    return agents


@router.post("/", response_model=AgentOut)
async def create_agent(
    *,
    db: AsyncSession = Depends(deps.get_db),
    agent_in: AgentCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create new agent.
    Currently defaults to the user's first tenant (Personal Tenant).
    TODO: Support specifying which tenant to create in.
    """
    # 获取用户的默认 Tenant
    # 简单逻辑：取第一个
    result = await db.execute(select(Tenant).where(Tenant.owner_id == current_user.id))
    tenant = result.scalars().first()
    
    if not tenant:
        raise HTTPException(status_code=400, detail="User has no tenant to create agent in")
        
    # ...
    now = datetime.utcnow()
    agent_id = str(uuid.uuid4())
    db_agent = Agent(
        id=agent_id,
        tenant_id=tenant.id,
        name=agent_in.name,
        description=agent_in.description,
        config=agent_in.config,
        template_id=agent_in.template_id,
        status=AgentStatus.ACTIVE,
        created_at=now,
        updated_at=now
    )
    
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    return db_agent


@router.put("/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: str,
    agent_in: AgentUpdate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Update an agent.
    """
    query = select(Agent).join(Tenant).where(
        Agent.id == agent_id,
        Tenant.owner_id == current_user.id
    )
    result = await db.execute(query)
    agent_obj = result.scalars().first()
    
    if not agent_obj:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    update_data = agent_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent_obj, field, value)
    
    agent_obj.updated_at = datetime.utcnow()
        
    db.add(agent_obj)
    await db.commit()
    await db.refresh(agent_obj)
    return agent_obj


@router.get("/{agent_id}", response_model=AgentOut)
async def read_agent(
    agent_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Get agent by ID.
    """
    # 获取 Agent，并检查是否属于用户的租户
    query = select(Agent).join(Tenant).where(
        Agent.id == agent_id,
        Tenant.owner_id == current_user.id
    )
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found or permission denied")
    return agent


@router.post("/{agent_id}/api_keys", response_model=api_key_schema.ApiKey)
async def create_agent_api_key(
    agent_id: str,
    api_key_in: api_key_schema.ApiKeyCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Create a new API key for an agent.
    """
    # Verify agent ownership
    query = select(Agent).join(Tenant).where(
        Agent.id == agent_id,
        Tenant.owner_id == current_user.id
    )
    result = await db.execute(query)
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Delegate to MaimConfig Service
    import httpx
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://localhost:8000/api/v2/api-keys",
                json={
                    "tenant_id": agent.tenant_id,
                    "agent_id": agent.id,
                    "name": api_key_in.name,
                    "description": api_key_in.description,
                    "permissions": api_key_in.permissions
                },
                timeout=10.0
            )
            
            if resp.status_code != 200:
                logger = logging.getLogger(__name__)
                logger.error(f"MaimConfig error: {resp.text}")
                try:
                    error_detail = resp.json().get("message", resp.text)
                except:
                    error_detail = resp.text
                raise HTTPException(status_code=resp.status_code, detail=f"Failed to create key: {error_detail}")
                
            resp_data = resp.json()
            if not resp_data.get("success", False):
                logger = logging.getLogger(__name__)
                logger.error(f"MaimConfig business error: {resp_data}")
                raise HTTPException(status_code=400, detail=resp_data.get("message", "Unknown MaimConfig error"))

            key_data = resp_data["data"]
            if not key_data:
                raise HTTPException(status_code=500, detail="MaimConfig returned no data")
            
            # Map api_key_id to id
            key_data["id"] = key_data.pop("api_key_id")
            
            return key_data
            
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"MaimConfig service unavailable: {e}")


@router.get("/{agent_id}/api_keys", response_model=List[api_key_schema.ApiKey])
async def read_agent_api_keys(
    agent_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    List API keys for an agent.
    """
    # Verify agent ownership
    query = select(Agent).join(Tenant).where(
        Agent.id == agent_id,
        Tenant.owner_id == current_user.id
    )
    result = await db.execute(query)
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get Keys
    keys_query = select(ApiKey).where(ApiKey.agent_id == agent_id)
    result = await db.execute(keys_query)
    return result.scalars().all()


@router.delete("/{agent_id}/api_keys/{key_id}", status_code=204)
async def delete_agent_api_key(
    agent_id: str,
    key_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """
    Revoke (delete) an API key.
    """
    # Verify agent ownership
    query = select(Agent).join(Tenant).where(
        Agent.id == agent_id,
        Tenant.owner_id == current_user.id
    )
    result = await db.execute(query)
    agent = result.scalars().first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Find and delete key
    key_query = select(ApiKey).where(ApiKey.id == key_id, ApiKey.agent_id == agent_id)
    result = await db.execute(key_query)
    api_key = result.scalars().first()
    
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key not found")
        
    await db.delete(api_key)
    await db.commit()
    return None
