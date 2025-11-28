# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.input_models import TattvaInput
from app.models.output_models import TattvaOutput
from app.agents.tattva_agent import TattvaAgent
import asyncio

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

@app.post("/api/v1/fact-check", response_model=TattvaOutput)
async def fact_check(input_data: TattvaInput):
    """
    Main fact-checking endpoint.
    
    Accepts normalized content and returns comprehensive fact-check analysis.
    """
    try:
        if input_data.status != "Success":
            raise HTTPException(
                status_code=400,
                detail=f"Input status is {input_data.status}, expected 'Success'"
            )
        
        if not input_data.transcript.text:
            raise HTTPException(
                status_code=400,
                detail="Transcript text is empty"
            )
        
        result = await tattva_agent.process(input_data)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Processing error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)