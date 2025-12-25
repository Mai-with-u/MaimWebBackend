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
        return await self._request("POST", "/tenants", json=tenant_data)

    async def list_tenants(self, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """List tenants"""
        return await self._request("GET", "/tenants", params={"page": page, "size": size})

    async def get_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant details"""
        return await self._request("GET", f"/tenants/{tenant_id}")

    async def update_tenant(self, tenant_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update tenant"""
        return await self._request("PUT", f"/tenants/{tenant_id}", json=update_data)

    async def delete_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Delete tenant"""
        return await self._request("DELETE", f"/tenants/{tenant_id}")

    async def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an agent in MaimConfig"""
        return await self._request("POST", "/agents", json=agent_data)

    async def get_agents(self, tenant_id: str) -> Dict[str, Any]:
        """List agents for a tenant"""
        return await self._request("GET", "/agents", params={"tenant_id": tenant_id})

    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details"""
        return await self._request("GET", f"/agents/{agent_id}")

    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent"""
        return await self._request("PUT", f"/agents/{agent_id}", json=update_data)
        
    async def create_api_key(self, api_key_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create API Key"""
        return await self._request("POST", "/api-keys", json=api_key_data)

    async def list_api_keys(self, tenant_id: str, agent_id: Optional[str] = None, page: int = 1, page_size: int = 20, status: Optional[str] = None) -> Dict[str, Any]:
        """List API Keys"""
        params = {"tenant_id": tenant_id, "page": page, "page_size": page_size}
        if agent_id:
            params["agent_id"] = agent_id
        if status:
            params["status"] = status
        return await self._request("GET", "/api-keys", params=params)

    async def get_api_key(self, api_key_id: str) -> Dict[str, Any]:
        """Get API Key details"""
        return await self._request("GET", f"/api-keys/{api_key_id}")

    async def update_api_key(self, api_key_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update API Key"""
        return await self._request("PUT", f"/api-keys/{api_key_id}", json=update_data)

    async def delete_api_key(self, api_key_id: str) -> Dict[str, Any]:
        """Delete API Key"""
        return await self._request("DELETE", f"/api-keys/{api_key_id}")

    async def upsert_plugin_setting(self, tenant_id: str, agent_id: str, setting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert plugin setting (Using v1 API)"""
        # POST /api/v1/plugins/settings
        # Hack to switch version since base_url defaults to v2
        base_v1 = self.base_url.replace("/v2", "/v1")
        url = f"{base_v1}/plugins/settings"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, params={"tenant_id": tenant_id, "agent_id": agent_id}, json=setting_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                try:
                    error_data = e.response.json()
                    raise Exception(f"MaimConfig Error: {error_data.get('message', str(e))}")
                except Exception:
                    raise Exception(f"MaimConfig Error: {str(e)}")
            except Exception as e:
                raise Exception(f"MaimConfig Connection Error: {str(e)}")

            except Exception as e:
                raise Exception(f"MaimConfig Connection Error: {str(e)}")

    async def get_bot_defaults(self) -> Dict[str, Any]:
        """Get bot default configuration"""
        return await self._request("GET", "/system/bot-defaults")

    async def get_system_models(self) -> Dict[str, Any]:
        """Get system defined models"""
        return await self._request("GET", "/system/models")

client = MaimConfigClient()
