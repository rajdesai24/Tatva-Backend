# app/services/supabase_logger.py
import asyncio
from datetime import datetime
from typing import Optional
from supabase import create_client, Client
from app.config import get_settings
import logging
import uuid

logger = logging.getLogger(__name__)

class SupabaseLogger:
    """Simple asynchronous logger for tracking service calls in Supabase."""

    def __init__(self):
        settings = get_settings()
        self.supabase: Optional[Client] = None
        self.request_id: Optional[str] = None

        # Only initialize if credentials are provided
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase logger initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.supabase = None
        else:
            logger.warning("Supabase credentials not provided, logging disabled")

    def set_request_id(self, request_id: str) -> None:
        """Set the request ID for this logging session."""
        self.request_id = request_id

    async def log(self, status: str, message: str) -> None:
        """
        Log a simple status update to Supabase.

        Args:
            status: Status of the operation (e.g., 'started', 'completed', 'error')
            message: Description of what's happening (e.g., 'analysing bias')
        """
        if not self.supabase:
            # If Supabase is not configured, just log locally
            logger.info(f"[{status}] {message}")
            return

        # Use existing request_id or generate new one
        req_id = self.request_id or str(uuid.uuid4())

        # Run the database insert in a thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._insert_log,
            req_id,
            status,
            message
        )

    def _insert_log(self, request_id: str, status: str, message: str) -> None:
        """Internal method to insert log into Supabase (runs in thread pool)."""
        try:
            log_entry = {
                "request_id": request_id,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.supabase.table("agent_logs").insert(log_entry).execute()
            logger.debug(f"Logged: [{status}] {message}")
        except Exception as e:
            # Don't fail the main process if logging fails
            logger.error(f"Failed to log to Supabase: {e}")

# Global instance
supabase_logger = SupabaseLogger()
