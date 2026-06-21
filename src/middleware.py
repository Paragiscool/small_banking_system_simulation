import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from .database import SessionLocal
from . import models

logger = logging.getLogger(__name__)

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            process_time = (time.time() - start_time) * 1000
            
            # Autonomous Session to ensure audit logs survive rollbacks
            db = SessionLocal()
            try:
                audit_log = models.AuditLog(
                    method=request.method,
                    path=request.url.path,
                    ip_address=request.client.host if request.client else "unknown",
                    status_code=status_code,
                    response_time_ms=process_time
                )
                db.add(audit_log)
                db.commit()
            except Exception as audit_e:
                logger.error(f"Failed to save audit log: {audit_e}")
            finally:
                db.close()
                
        return response
