from typing import Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from src.core.maim_config_client import client

router = APIRouter()

@router.post("/", summary="Create Tenant")
async def create_tenant(request: dict):
    try:
        return await client.create_tenant(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", summary="List Tenants")
async def list_tenants(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1)
):
    try:
        return await client.list_tenants(page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{tenant_id}", summary="Get Tenant")
async def get_tenant(tenant_id: str):
    try:
        return await client.get_tenant(tenant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{tenant_id}", summary="Update Tenant")
async def update_tenant(tenant_id: str, request: dict):
    try:
        return await client.update_tenant(tenant_id, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tenant_id}", summary="Delete Tenant")
async def delete_tenant(tenant_id: str):
    try:
        return await client.delete_tenant(tenant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
