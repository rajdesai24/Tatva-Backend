# app/services/supabase_logger.py
import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from supabase import create_client, Client
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

class SupabaseLogger:
    """Asynchronous logger for tracking agentic processing in Supabase."""

    def __init__(self):
        settings = get_settings()
        self.supabase: Optional[Client] = None

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

    async def log_event(
        self,
        event_type: str,
        request_id: str,
        step: str,
        data: Dict[str, Any],
        status: str = "success",
        error: Optional[str] = None
    ) -> None:
        """
        Asynchronously log an event to Supabase.

        Args:
            event_type: Type of event (e.g., 'agent_start', 'claim_extraction', 'verdict')
            request_id: Unique identifier for the request
            step: Processing step name
            data: Event data to log
            status: Status of the event ('success', 'error', 'in_progress')
            error: Error message if status is 'error'
        """
        if not self.supabase:
            # If Supabase is not configured, just log locally
            logger.info(f"[{event_type}] {step}: {status}")
            return

        # Run the database insert in a thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._insert_log,
            event_type,
            request_id,
            step,
            data,
            status,
            error
        )

    def _insert_log(
        self,
        event_type: str,
        request_id: str,
        step: str,
        data: Dict[str, Any],
        status: str,
        error: Optional[str]
    ) -> None:
        """Internal method to insert log into Supabase (runs in thread pool)."""
        try:
            log_entry = {
                "event_type": event_type,
                "request_id": request_id,
                "step": step,
                "data": json.dumps(data) if isinstance(data, dict) else str(data),
                "status": status,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }

            self.supabase.table("agent_logs").insert(log_entry).execute()
            logger.debug(f"Logged event: {event_type} - {step}")
        except Exception as e:
            # Don't fail the main process if logging fails
            logger.error(f"Failed to log event to Supabase: {e}")

    async def log_agent_start(self, request_id: str, input_data: Dict[str, Any]) -> None:
        """Log the start of agent processing."""
        await self.log_event(
            event_type="agent_start",
            request_id=request_id,
            step="initialization",
            data=input_data,
            status="in_progress"
        )

    async def log_agent_complete(
        self,
        request_id: str,
        result: Dict[str, Any],
        status: str = "success"
    ) -> None:
        """Log the completion of agent processing."""
        await self.log_event(
            event_type="agent_complete",
            request_id=request_id,
            step="finalization",
            data=result,
            status=status
        )

    async def log_step(
        self,
        request_id: str,
        step_name: str,
        step_data: Dict[str, Any],
        status: str = "success"
    ) -> None:
        """Log a processing step."""
        await self.log_event(
            event_type="processing_step",
            request_id=request_id,
            step=step_name,
            data=step_data,
            status=status
        )

    async def log_error(
        self,
        request_id: str,
        step: str,
        error_message: str,
        error_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an error during processing."""
        await self.log_event(
            event_type="error",
            request_id=request_id,
            step=step,
            data=error_data or {},
            status="error",
            error=error_message
        )

# Global instance
supabase_logger = SupabaseLogger()
