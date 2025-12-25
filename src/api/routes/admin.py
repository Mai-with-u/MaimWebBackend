import json
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from maim_db.core.models.business import ChatHistory, ChatLogs, FileUpload, SystemMetrics
from maim_db.core.context_manager import set_current_agent_id

# We need to temporarily set agent_id to allow querying business models regardless of specific agent constraint if we want full admin view.
# However, business models enforce agent_id in 'select'. 
# We might need a way to bypass this for Admin, or iterate/filter by tenant logic.
# For now, let's assume we pass agent_id or handle it. 
# Re-reading business.py: `select` calls `get_current_agent_id()`. If it returns None, it doesn't filter.
# So if we don't set the context, we should be able to see all data?
# Let's verify `business.py`:
# query = query.where(cls.agent_id == current_id) if current_id else query.
# Yes! So if we don't set the context, we get everything. Good for Admin.

router = APIRouter()

def parse_json(content):
    if not content:
        return None
    try:
        return json.loads(content)
    except:
        return content

@router.get("/chat-history", summary="List Chat History")
async def list_chat_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    agent_id: Optional[str] = None
):
    try:
        # If agent_id is provided, we can either use context or just filter.
        # Filtering is safer for read-only admin view without messing with global context.
        query = ChatHistory.select()
        if agent_id:
            query = query.where(ChatHistory.agent_id == agent_id)
            
        total = query.count()
        logs = query.order_by(ChatHistory.created_at.desc()).paginate(page, size)
        
        items = []
        for log in logs:
            items.append({
                "id": str(log.id),
                "agent_id": log.agent_id,
                "session_id": log.session_id,
                "user_message": log.user_message,  # Might be JSON or text
                "assistant_message": log.assistant_message,
                "user_id": log.user_id,
                "created_at": log.created_at.isoformat() if log.created_at else None
                # Parse messages if needed, but keeping raw is fine for admin list
            })
            
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files", summary="List Files")
async def list_files(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    agent_id: Optional[str] = None
):
    try:
        query = FileUpload.select()
        if agent_id:
            query = query.where(FileUpload.agent_id == agent_id)
            
        total = query.count()
        files = query.order_by(FileUpload.created_at.desc()).paginate(page, size)
        
        items = []
        for f in files:
            items.append({
                "id": str(f.id),
                "agent_id": f.agent_id,
                "original_filename": f.original_filename,
                "file_path": f.file_path,
                "file_size": f.file_size,
                "mime_type": f.mime_type,
                "created_at": f.created_at.isoformat() if f.created_at else None
            })
            
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", summary="List System Metrics")
async def list_metrics(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    metric_name: Optional[str] = None
):
    try:
        query = SystemMetrics.select()
        if metric_name:
            query = query.where(SystemMetrics.metric_name == metric_name)
            
        total = query.count()
        metrics = query.order_by(SystemMetrics.created_at.desc()).paginate(page, size)
        
        items = []
        for m in metrics:
            items.append({
                "id": str(m.id),
                "agent_id": m.agent_id,
                "metric_name": m.metric_name,
                "metric_value": m.metric_value,
                "metric_unit": m.metric_unit,
                "tags": parse_json(m.tags),
                "created_at": m.created_at.isoformat() if m.created_at else None
            })
            
        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
