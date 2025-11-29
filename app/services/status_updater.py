from supabase import create_client, Client
from app.config import get_settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StatusUpdater:
    def __init__(self):
        settings = get_settings()
        self.supabase: Client = create_client("https://rcqqpufeygnnzrplohyx.supabase.co","eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJjcXFwdWZleWdubnpycGxvaHl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NDM1MTQ4MiwiZXhwIjoyMDc5OTI3NDgyfQ.Zt-Rz7vEM3j9bCt3-4CVsOuFZ1obX2m4jN68qBaaVEc "   )

    async def update_analysis(
        self, 
        analysis
    ):
        """Update processing status in Supabase."""
                    
        clerk_user_id = "user_367vrvxLc30byC5Ai3btLJA5HNG"

        # 1. Look for existing report
        existing = (
            self.supabase
                .table("reports")
                .select("report_id")
                .eq("clerk_user_id", clerk_user_id)
                .limit(1)
                .execute()
        )

            # 2a. Update existing
        report_id = existing.data[0]["report_id"]
        result = (
            self.supabase
                .table("reports")
                .update( {"analysis":analysis})
                .eq("report_id", report_id)
                .execute()
        )

        return result
            
    async def update_status(
        self, 
        logs
    ):
        """Update processing status in Supabase."""
        try:
                        
            clerk_user_id = "user_367vrvxLc30byC5Ai3btLJA5HNG"

            # 1. Look for existing report
            existing = (
                self.supabase
                    .table("reports")
                    .select("report_id")
                    .eq("clerk_user_id", clerk_user_id)
                    .limit(1)
                    .execute()
            )

            if existing.data:
                # 2a. Update existing
                report_id = existing.data[0]["report_id"]
                result = (
                    self.supabase
                        .table("reports")
                        .update( {"logs":logs})
                        .eq("report_id", report_id)
                        .execute()
                )
            else:
                # 2b. Create new
                result = (
                    self.supabase
                        .table("reports")
                        .insert(
                            { "logs":logs,"clerk_user_id":clerk_user_id}
                        ).execute()
                )
            return result
                
        except Exception as e:
                logger.error(f"Failed to update status: {e}")
                # Don't fail the entire process if status update fails
                return None
    async def update_separate_key(
        self, 
        key,
        value
    ):
        """Update processing status in Supabase."""
        try:
                        
            clerk_user_id = "user_367vrvxLc30byC5Ai3btLJA5HNG"

            # 1. Look for existing report
            existing = (
                self.supabase
                    .table("reports")
                    .select("report_id")
                    .eq("clerk_user_id", clerk_user_id)
                    .limit(1)
                    .execute()
            )

            if existing.data:
                # 2a. Update existing
                report_id = existing.data[0]["report_id"]
                result = (
                    self.supabase
                        .table("reports")
                        .update( {key:value})
                        .eq("report_id", report_id)
                        .execute()
                )
                return result
                
        except Exception as e:
                logger.error(f"Failed to update status: {e}")
                # Don't fail the entire process if status update fails
                return None
