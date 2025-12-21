import httpx
from typing import Optional, Dict, List, Any
from src.core.settings import settings

class MaimConfigClient:
    def __init__(self, base_url: str = settings.MAIMCONFIG_API_URL):
        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Try to get error details from response
                try:
                    error_data = e.response.json()
                    raise Exception(f"MaimConfig Error: {error_data.get('message', str(e))}")
                except Exception:
                    raise Exception(f"MaimConfig Error: {str(e)}")
            except Exception as e:
                raise Exception(f"MaimConfig Connection Error: {str(e)}")

    async def create_tenant(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a tenant in MaimConfig"""
        # MaimConfig POST /tenants expects:
        # tenant_name, tenant_type, etc.
        # But MaimConfig generates ID? Or assumes we pass one?
        # MaimConfig `POST /tenants` (from tenant_api.py):
        # class TenantCreateRequest(BaseModel):
        #     tenant_name: str
        #     tenant_type: str = "personal"
        #     contact_email: Optional[EmailStr] = None
        #     description: Optional[str] = None
        # It RETURNS tenant_id.
        return await self._request("POST", "/tenants", json=tenant_data)

    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an agent in MaimConfig"""
        # POST /agents
        return await self._request("POST", "/agents", json=agent_data)

    async def get_agents(self, tenant_id: str) -> Dict[str, Any]:
        """List agents for a tenant"""
        # GET /agents?tenant_id=...
        return await self._request("GET", "/agents", params={"tenant_id": tenant_id})

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details"""
        # GET /agents/{agent_id}
        return await self._request("GET", f"/agents/{agent_id}")

    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent"""
        # PUT /agents/{agent_id}
        return await self._request("PUT", f"/agents/{agent_id}", json=update_data)
        
    async def create_api_key(self, api_key_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create API Key"""
        # POST /api-keys
        return await self._request("POST", "/api-keys", json=api_key_data)

    async def get_api_keys(self, tenant_id: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """List API Keys"""
        params = {"tenant_id": tenant_id}
        if agent_id:
            params["agent_id"] = agent_id
        return await self._request("GET", "/api-keys", params=params)

    async def delete_api_key(self, api_key_id: str) -> Dict[str, Any]:
        """Delete API Key"""
        # DELETE /api-keys/{api_key_id}
        return await self._request("DELETE", f"/api-keys/{api_key_id}")

client = MaimConfigClient()
