# app/main.py
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from app.models.input_models import TattvaInput
from app.models.output_models import TattvaOutput
from app.agents.tattva_agent import TattvaAgent
from app.services.supabase_logger import supabase_logger
import asyncio
import uuid
import json

app = FastAPI(
    title="Tattva Agent API",
    description="Transparent, source-grounded fact-checking service powered by Google Gemini",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tattva_agent = TattvaAgent()

@app.get("/")
async def root():
    return {
        "message": "Tattva Agent API - Powered by Google Gemini",
        "version": "1.0.0",
        "endpoints": {
            "fact_check": "/api/v1/fact-check",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": "gemini-2.0-flash-exp"}

@app.post("/api/v1/fact-check")
async def fact_check(input_data: TattvaInput, response: Response):
    """
    Main fact-checking endpoint.

    Accepts normalized content and returns comprehensive fact-check analysis.
    Always returns with 200 status code.
    """
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())

    try:
        # Log API request
        await supabase_logger.log_event(
            event_type="api_request",
            request_id=request_id,
            step="fact_check_endpoint",
            data={
                "content_type": input_data.content_type,
                "has_transcript": bool(input_data.transcript and input_data.transcript.text),
                "beliefs_count": len(input_data.beliefs) if input_data.beliefs else 0
            },
            status="in_progress"
        )

        if input_data.status != "Success":
            # Hardcode 200 status even for validation errors
            response.status_code = 200
            error_result = {
                "status": "error",
                "message": f"Input status is {input_data.status}, expected 'Success'",
                "request_id": request_id
            }

            await supabase_logger.log_event(
                event_type="api_response",
                request_id=request_id,
                step="validation_error",
                data=error_result,
                status="error",
                error=error_result["message"]
            )

            return error_result

        if not input_data.transcript.text:
            # Hardcode 200 status even for validation errors
            response.status_code = 200
            error_result = {
                "status": "error",
                "message": "Transcript text is empty",
                "request_id": request_id
            }

            await supabase_logger.log_event(
                event_type="api_response",
                request_id=request_id,
                step="validation_error",
                data=error_result,
                status="error",
                error=error_result["message"]
            )

            return error_result

        # Process the request
        result = await tattva_agent.process(input_data)

        # Hardcode 200 status for successful processing
        response.status_code = 200

        # Log successful API response
        await supabase_logger.log_event(
            event_type="api_response",
            request_id=request_id,
            step="fact_check_complete",
            data={
                "claims_count": len(result.claims),
                "tattva_score": result.tattva_score
            },
            status="success"
        )

        # Return result with request_id
        result_dict = result.dict()
        result_dict["request_id"] = request_id

        return result_dict

    except Exception as e:
        # Hardcode 200 status even for errors
        response.status_code = 200

        error_result = {
            "status": "error",
            "message": f"Processing error: {str(e)}",
            "request_id": request_id
        }

        await supabase_logger.log_event(
            event_type="api_response",
            request_id=request_id,
            step="processing_error",
            data=error_result,
            status="error",
            error=str(e)
        )

        return error_result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)