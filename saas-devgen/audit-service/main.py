"""Audit Service - Comprehensive logging and telemetry for compliance."""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from shared.config import settings
from shared.logging_utils import setup_logger
from shared.database import get_db
from shared.models import AuditLog, User, Tenant
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import json

# Initialize logger
logger = setup_logger("audit-service", "audit-service.log")

app = FastAPI(title="Audit Service", version="1.0.0")

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)


class AuditLogCreate(BaseModel):
    """Audit log creation model."""
    action: str
    entity: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[int] = None
    tenant_id: int


class AuditLogResponse(BaseModel):
    """Audit log response model."""
    id: int
    tenant_id: int
    user_id: Optional[int]
    action: str
    entity: Optional[str]
    entity_id: Optional[int]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime


class AuditLogsResponse(BaseModel):
    """Audit logs list response."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class AuditManager:
    """Manages audit logging and compliance tracking."""
    
    def __init__(self):
        self.logger = logger
    
    def log_action(self, db: Session, action: str, tenant_id: int, 
                   user_id: Optional[int] = None, entity: Optional[str] = None,
                   entity_id: Optional[int] = None, details: Optional[Dict] = None,
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuditLog:
        """Log an audit action."""
        with tracer.start_as_current_span("audit_log_action") as span:
            span.set_attribute("action", action)
            span.set_attribute("tenant_id", tenant_id)
            if user_id:
                span.set_attribute("user_id", user_id)
            if entity:
                span.set_attribute("entity", entity)
            
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action=action,
                entity=entity,
                entity_id=entity_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            self.logger.info(f"Audit log created: {action} by user {user_id} for tenant {tenant_id}")
            return audit_log
    
    def get_user_actions(self, db: Session, user_id: int, tenant_id: int,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        limit: int = 100) -> List[AuditLog]:
        """Get audit logs for a specific user."""
        query = db.query(AuditLog).filter(
            and_(AuditLog.user_id == user_id, AuditLog.tenant_id == tenant_id)
        )
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        return query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
    
    def get_tenant_actions(self, db: Session, tenant_id: int,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          action_filter: Optional[str] = None,
                          entity_filter: Optional[str] = None,
                          page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get audit logs for a tenant with pagination and filtering."""
        query = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        if action_filter:
            query = query.filter(AuditLog.action.ilike(f"%{action_filter}%"))
        if entity_filter:
            query = query.filter(AuditLog.entity == entity_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        logs = query.order_by(desc(AuditLog.timestamp)).offset(offset).limit(per_page).all()
        
        return {
            "logs": logs,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": offset + per_page < total,
            "has_prev": page > 1
        }
    
    def get_security_events(self, db: Session, tenant_id: int,
                          hours: int = 24) -> List[AuditLog]:
        """Get security-related events from the last N hours."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        security_actions = [
            "login_failed",
            "login_success",
            "logout",
            "password_change",
            "permission_denied",
            "unauthorized_access",
            "token_refresh",
            "account_locked"
        ]
        
        return db.query(AuditLog).filter(
            and_(
                AuditLog.tenant_id == tenant_id,
                AuditLog.timestamp >= start_time,
                AuditLog.action.in_(security_actions)
            )
        ).order_by(desc(AuditLog.timestamp)).all()
    
    def get_compliance_report(self, db: Session, tenant_id: int,
                            start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for a date range."""
        logs = db.query(AuditLog).filter(
            and_(
                AuditLog.tenant_id == tenant_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            )
        ).all()
        
        # Aggregate statistics
        action_counts = {}
        user_activity = {}
        entity_activity = {}
        
        for log in logs:
            # Count actions
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            
            # Count user activity
            if log.user_id:
                user_activity[log.user_id] = user_activity.get(log.user_id, 0) + 1
            
            # Count entity activity
            if log.entity:
                entity_activity[log.entity] = entity_activity.get(log.entity, 0) + 1
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_events": len(logs),
            "action_summary": action_counts,
            "user_activity": user_activity,
            "entity_activity": entity_activity,
            "security_events": len([log for log in logs if any(
                keyword in log.action.lower() 
                for keyword in ["login", "auth", "security", "unauthorized"]
            )])
        }


audit_manager = AuditManager()


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.post("/audit/log", response_model=AuditLogResponse)
async def create_audit_log(
    audit_log: AuditLogCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new audit log entry."""
    logger.info(f"Creating audit log: {audit_log.action} for tenant {audit_log.tenant_id}")
    
    try:
        log_entry = audit_manager.log_action(
            db=db,
            action=audit_log.action,
            tenant_id=audit_log.tenant_id,
            user_id=audit_log.user_id,
            entity=audit_log.entity,
            entity_id=audit_log.entity_id,
            details=audit_log.details,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent")
        )
        
        return AuditLogResponse(
            id=log_entry.id,
            tenant_id=log_entry.tenant_id,
            user_id=log_entry.user_id,
            action=log_entry.action,
            entity=log_entry.entity,
            entity_id=log_entry.entity_id,
            details=log_entry.details,
            ip_address=log_entry.ip_address,
            user_agent=log_entry.user_agent,
            timestamp=log_entry.timestamp
        )
        
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit log"
        )


@app.get("/audit/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    tenant_id: int = Query(..., description="Tenant ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    action_filter: Optional[str] = Query(None, description="Action filter"),
    entity_filter: Optional[str] = Query(None, description="Entity filter"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=1000, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get audit logs with filtering and pagination."""
    logger.info(f"Fetching audit logs for tenant {tenant_id}")
    
    try:
        result = audit_manager.get_tenant_actions(
            db=db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            action_filter=action_filter,
            entity_filter=entity_filter,
            page=page,
            per_page=per_page
        )
        
        return AuditLogsResponse(
            logs=[
                AuditLogResponse(
                    id=log.id,
                    tenant_id=log.tenant_id,
                    user_id=log.user_id,
                    action=log.action,
                    entity=log.entity,
                    entity_id=log.entity_id,
                    details=log.details,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    timestamp=log.timestamp
                ) for log in result["logs"]
            ],
            total=result["total"],
            page=result["page"],
            per_page=result["per_page"],
            has_next=result["has_next"],
            has_prev=result["has_prev"]
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@app.get("/audit/security/{tenant_id}")
async def get_security_events(
    tenant_id: int,
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: Session = Depends(get_db)
):
    """Get security events for the last N hours."""
    logger.info(f"Fetching security events for tenant {tenant_id}")
    
    try:
        events = audit_manager.get_security_events(db, tenant_id, hours)
        
        return {
            "tenant_id": tenant_id,
            "period_hours": hours,
            "events": [
                {
                    "id": event.id,
                    "action": event.action,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "timestamp": event.timestamp,
                    "details": event.details
                } for event in events
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@app.get("/audit/compliance/{tenant_id}")
async def get_compliance_report(
    tenant_id: int,
    start_date: datetime = Query(..., description="Report start date"),
    end_date: datetime = Query(..., description="Report end date"),
    db: Session = Depends(get_db)
):
    """Generate compliance report for a tenant."""
    logger.info(f"Generating compliance report for tenant {tenant_id}")
    
    try:
        report = audit_manager.get_compliance_report(db, tenant_id, start_date, end_date)
        
        return {
            "tenant_id": tenant_id,
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "audit-service",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Audit Service on port 8006")
    uvicorn.run(app, host="0.0.0.0", port=8006)
