# app/main.py
from fastapi import FastAPI, HTTPException, Response,BackgroundTasks,status
from fastapi.middleware.cors import CORSMiddleware
from app.models.input_models import TattvaInput
from app.models.output_models import TattvaOutput
from typing import Optional
from app.agents.tattva_agent import TattvaAgent
import asyncio
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

async def process_fact_check_background( input_data):
    """Background task to process fact-checking."""
    try:
        logger.info(f"Starting background processing for session")
        result = await tattva_agent.process(input_data)
        logger.info(f"Completed background processing for session")
        
    except Exception as e:
        logger.error(f"Error in background processing for session : {str(e)}")
        # Update status to failed


# app/main.py - Add this endpoint
from app.services.transcriber import transcribe_url

@app.post("/api/v1/fact-check-url",response_model=TattvaOutput)
async def fact_check_url(
    url: str,
    background_tasks: BackgroundTasks,response:Response,
    beliefs: Optional[list] = None,
    twitter_token: Optional[str] = None
):
    """
    Fact-check content from a URL.
    
    Supports:
    - YouTube videos
    - Twitter/X tweets
    - News articles
    - Blog posts
    """

    # Step 1: Transcribe URL to normalized format
    logger.info(f"Processing URL: {url}")
    transcribed_data = transcribe_url(url, beliefs)
    print(transcribed_data)
    # Check if transcription was successful
    if transcribed_data["status"] != "Success":
        raise HTTPException(
            status_code=400,
            detail=transcribed_data["metadata"].get("error", "Failed to process URL")
        )
    
    background_tasks.add_task(process_fact_check_background, transcribed_data)
    response.status_code = status.HTTP_200_OK
    return response
        

# @app.post("/api/v1/fact-check", response_model=TattvaOutput)
# async def fact_check(input_data: TattvaInput,background_tasks: BackgroundTasks,response:Response):
#     """
#     Main fact-checking endpoint.
    
#     Accepts normalized content and returns comprehensive fact-check analysis.
#     """
#     try:
#         if input_data.status != "Success":
#             raise HTTPException(
#                 status_code=400,
#                 detail=f"Input status is {input_data.status}, expected 'Success'"
#             )
        
#         if not input_data.transcript.text:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Transcript text is empty"
#             )
#         background_tasks.add_task(process_fact_check_background, input_data)
#         response.status_code = status.HTTP_200_OK
#         return response
        
        
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Processing error: {str(e)}"
    #     )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)