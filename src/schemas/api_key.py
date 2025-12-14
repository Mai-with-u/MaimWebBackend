from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

class ApiKeyBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    permissions: Optional[List[str]] = None

class ApiKeyInDBBase(ApiKeyBase):
    id: str
    tenant_id: str
    agent_id: str
    api_key: str
    status: str
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApiKey(ApiKeyInDBBase):
    pass
