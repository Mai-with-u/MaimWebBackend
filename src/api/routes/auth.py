from datetime import timedelta, datetime
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
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # 查询用户 by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=user_schema.User)
async def register_new_user(
    *,
    db: AsyncSession = Depends(deps.get_db),
    user_in: user_schema.UserCreate,
) -> Any:
    """
    Create new user. Also creates a default Personal Tenant.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    
    # Create user
    now = datetime.utcnow()
    user_id = str(uuid.uuid4())
    db_user = User(
        id=user_id,
        username=user_in.username,
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        is_active=user_in.is_active,
        created_at=now,
        updated_at=now,
    )
    
    # Create Personal Tenant
    try:
        tenant_id = str(uuid.uuid4())
        personal_tenant = Tenant(
            id=tenant_id,
            tenant_name=f"{user_in.username}'s Tenant",
            tenant_type=TenantType.PERSONAL,
            description=f"Personal tenant for {user_in.username}",
            owner_id=user_id,
            status=TenantStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        
        db.add(db_user)
        db.add(personal_tenant)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
