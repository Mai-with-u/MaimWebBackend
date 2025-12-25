from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from src.core.maim_config_client import client

router = APIRouter()

@router.post("/", summary="Create API Key")
async def create_api_key(request: dict):
    try:
        return await client.create_api_key(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", summary="List API Keys")
async def list_api_keys(
    tenant_id: str = Query(...),
    agent_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1),
    status: Optional[str] = Query(None)
):
    try:
        return await client.list_api_keys(
            tenant_id=tenant_id, 
            agent_id=agent_id, 
            page=page, 
            page_size=page_size,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{api_key_id}", summary="Get API Key")
async def get_api_key(api_key_id: str):
    try:
        return await client.get_api_key(api_key_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{api_key_id}", summary="Update API Key")
async def update_api_key(api_key_id: str, request: dict):
    try:
        return await client.update_api_key(api_key_id, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{api_key_id}", summary="Delete API Key")
async def delete_api_key(api_key_id: str):
    try:
        return await client.delete_api_key(api_key_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
