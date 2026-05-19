"""
VoiceCare AI Lead Personalization Agent — Web UI
FastAPI + Jinja2 application with manual run trigger.
"""
import os
import sys
import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestrator import LeadPersonalizationAgent
from models import OutreachStatus

# Load environment
load_dotenv()

app = FastAPI(title="VoiceCare AI Lead Agent", version="2.0")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global agent instance
_agent: Optional[LeadPersonalizationAgent] = None

def get_agent() -> LeadPersonalizationAgent:
    """Get or create the agent singleton."""
    global _agent
    if _agent is None:
        _agent = LeadPersonalizationAgent(
            proxycurl_key=os.getenv("PROXYCURL_API_KEY"),
            gemini_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
            linkedin_email=os.getenv("LINKEDIN_EMAIL"),
            linkedin_password=os.getenv("LINKEDIN_PASSWORD"),
            max_daily=int(os.getenv("MAX_DAILY_LEADS", "5"))
        )
    return _agent


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    agent = get_agent()
    summary = agent.get_status_summary()
    results = agent.results
    
    gemini_ready = bool(os.getenv("GEMINI_API_KEY"))
    linkedin_scraper_ready = bool(os.getenv("LINKEDIN_EMAIL") and os.getenv("LINKEDIN_PASSWORD"))
    proxycurl_ready = bool(os.getenv("PROXYCURL_API_KEY"))
    
    return templates.TemplateResponse(request, "index.html", {
        "summary": summary,
        "results": results,
        "gemini_ready": gemini_ready,
        "linkedin_scraper_ready": linkedin_scraper_ready,
        "proxycurl_ready": proxycurl_ready,
        "model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    })


@app.post("/api/run")
async def run_pipeline(max_leads: int = Form(5), use_demo: bool = Form(True)):
    """Trigger the pipeline run with demo/mock data."""
    agent = get_agent()
    
    try:
        results = agent.run_pipeline(max_leads=max_leads)
        
        return JSONResponse({
            "success": True,
            "generated": len(results),
            "summary": agent.get_status_summary()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.post("/api/run-real")
async def run_real_pipeline(urls: List[str] = Form(...), max_leads: int = Form(5)):
    """Trigger the pipeline with REAL LinkedIn profile URLs."""
    agent = get_agent()
    
    try:
        results = agent.run_pipeline(linkedin_urls=urls[:max_leads], max_leads=max_leads)
        
        return JSONResponse({
            "success": True,
            "generated": len(results),
            "summary": agent.get_status_summary()
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@app.get("/api/results")
async def get_results():
    """Get current results as JSON."""
    agent = get_agent()
    
    data = []
    for r in agent.results:
        data.append({
            "prospect": {
                "id": r.prospect.id,
                "name": f"{r.prospect.first_name} {r.prospect.last_name}",
                "first_name": r.prospect.first_name,
                "title": r.prospect.title,
                "company": r.prospect.company.name,
                "linkedin_url": r.prospect.linkedin_url,
                "pain_signals": r.prospect.pain_signals,
            },
            "message": {
                "hook": r.message.hook,
                "full_message": r.message.full_message,
                "referenced_activity": r.message.referenced_activity,
                "voicecare_angle": r.message.voicecare_angle,
                "confidence_score": r.message.confidence_score,
                "generated_at": r.message.generated_at.isoformat(),
            },
            "status": r.status.value
        })
    
    return JSONResponse({
        "results": data,
        "summary": agent.get_status_summary()
    })


@app.post("/api/status/{prospect_id}")
async def update_status(prospect_id: str, status: str = Form(...)):
    """Update prospect status (approve, pass, etc.)."""
    agent = get_agent()
    
    valid_statuses = [s.value for s in OutreachStatus]
    if status not in valid_statuses:
        return JSONResponse({
            "success": False,
            "error": f"Invalid status. Must be one of: {valid_statuses}"
        }, status_code=400)
    
    success = agent.update_status(prospect_id, status)
    return JSONResponse({
        "success": success,
        "summary": agent.get_status_summary()
    })


@app.get("/api/download/csv")
async def download_csv():
    """Download the latest review sheet CSV."""
    output_dir = Path("outputs")
    csv_files = sorted(output_dir.glob("review_sheet_*.csv"), reverse=True)
    
    if not csv_files:
        raise HTTPException(status_code=404, detail="No CSV file found")
    
    return FileResponse(
        csv_files[0],
        media_type="text/csv",
        filename=f"voicecare_outreach_{csv_files[0].name}"
    )


@app.get("/api/download/json")
async def download_json():
    """Download the latest results JSON."""
    output_dir = Path("outputs")
    json_files = sorted(output_dir.glob("outreach_results_*.json"), reverse=True)
    
    if not json_files:
        raise HTTPException(status_code=404, detail="No JSON file found")
    
    return FileResponse(
        json_files[0],
        media_type="application/json",
        filename=f"voicecare_outreach_{json_files[0].name}"
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "linkedin_scraper_configured": bool(os.getenv("LINKEDIN_EMAIL") and os.getenv("LINKEDIN_PASSWORD")),
        "proxycurl_configured": bool(os.getenv("PROXYCURL_API_KEY")),
        "model": os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
