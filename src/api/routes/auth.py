from datetime import datetime, timedelta
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.api import deps
from src.core import security
from src.core.settings import settings
from src.schemas import token as token_schema
from src.schemas import user as user_schema
from maim_db.maimconfig_models.models import User, Tenant, TenantType, TenantStatus

router = APIRouter()


@router.post("/login", response_model=token_schema.Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # 1. Authenticate user
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    # 2. Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=user_schema.User)
async def register(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: user_schema.UserCreate,
) -> Any:
    """
    Create new user without the need to be logged in
    """
    # 1. Check if user exists
    stmt = select(User).where(User.username == user_in.username)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
        
    # Check if email exists
    if user_in.email:
        stmt = select(User).where(User.email == user_in.email)
        result = await db.execute(stmt)
        if result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )

    # 2. Create User
    now = datetime.utcnow()
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user = User(
        id=user_id,
        username=user_in.username,
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        is_active=user_in.is_active,
        created_at=now,
        updated_at=now
    )
    db.add(user)
    
    # 3. Create Default Tenant (Sync with MaimConfig)
    from src.core.maim_config_client import client as maim_config_client
    
    tenant_name = f"{user_in.username}'s Personal Tenant"
    description = "Default personal tenant created on registration"
    
    try:
        # Call MaimConfig to create tenant
        resp = await maim_config_client.create_tenant({
            "tenant_name": tenant_name,
            "tenant_type": TenantType.PERSONAL.value,
            "description": description,
            "contact_email": user_in.email
        })
        
        if not resp.get("success"):
            raise HTTPException(status_code=500, detail=f"Failed to create tenant in MaimConfig: {resp.get('message')}")
            
        real_tenant_id = resp["data"]["id"]
        
    except Exception as e:
        # If remote creation fails, we must rollback user creation?
        # Since we haven't committed yet, raising exception here will rollback the transaction (if db session context manages it).
        # But db.add(user) was called. We should catch and re-raise.
        raise HTTPException(status_code=503, detail=f"MaimConfig service unavailable or error: {str(e)}")

    # Create local mapping
    tenant = Tenant(
        id=real_tenant_id,  # Use the ID from MaimConfig
        tenant_name=tenant_name,
        tenant_type=TenantType.PERSONAL.value,
        status=TenantStatus.ACTIVE.value,
        owner_id=user_id,
        description=description,
        created_at=now,
        updated_at=now
    )
    db.add(tenant)
    
    await db.commit()
    await db.refresh(user)
    
    return user
