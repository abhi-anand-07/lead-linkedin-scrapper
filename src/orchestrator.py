"""
Orchestrator Module (Web-Optimized)

Manages the full pipeline:
1. Discover prospects
2. Research each prospect
3. Generate personalized messages
4. Return results for UI display
5. Export to CSV/JSON
"""
import os
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path

from models import Prospect, OutreachResult, OutreachStatus
from discovery import ProspectDiscovery
from researcher import ResearchAgent
from personalizer import PersonalizationEngine
from gemini_client import GeminiClient


class LeadPersonalizationAgent:
    """Main orchestrator for the lead personalization system."""
    
    def __init__(self, 
                 proxycurl_key: Optional[str] = None,
                 gemini_key: Optional[str] = None,
                 gemini_model: Optional[str] = None,
                 linkedin_email: Optional[str] = None,
                 linkedin_password: Optional[str] = None,
                 output_dir: str = "outputs",
                 max_daily: int = 5):
        
        self.discovery = ProspectDiscovery(
            proxycurl_api_key=proxycurl_key,
            linkedin_email=linkedin_email,
            linkedin_password=linkedin_password
        )
        
        # Shared Gemini client for both researcher and personalizer
        self.gemini = GeminiClient(api_key=gemini_key, model=gemini_model)
        self.researcher = ResearchAgent(gemini_client=self.gemini)
        self.personalizer = PersonalizationEngine(gemini_client=self.gemini)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_daily = max_daily
        self.results: List[OutreachResult] = []
    
    def run_pipeline(self, linkedin_urls: Optional[List[str]] = None,
                     prospects_file: Optional[str] = None,
                     max_leads: Optional[int] = None) -> List[OutreachResult]:
        """Run the full pipeline once and return results."""
        max_leads = max_leads or self.max_daily
        
        # Step 1: Discover
        if prospects_file:
            prospects = self.discovery.discover_from_json(prospects_file)
        elif linkedin_urls:
            prospects = self.discovery.discover_from_list(linkedin_urls)
        else:
            # Randomized demo pool — different prospects each run
            prospects = self.discovery.get_mock_pool(count=max_leads)
        
        prospects = prospects[:max_leads]
        
        # Step 2 & 3: Research + Personalize
        results = []
        for prospect in prospects:
            # Research
            research = self.researcher.research_prospect(prospect)
            
            # Attach company news to prospect for UI display
            if research.get("company_news"):
                prospect.company.recent_news = research["company_news"]
            
            # Personalize
            message = self.personalizer.generate_message(prospect, research)
            
            result = OutreachResult(
                prospect=prospect,
                message=message,
                status=OutreachStatus.PENDING_REVIEW
            )
            results.append(result)
        
        # Step 4: Save outputs
        self._save_results(results)
        self._generate_review_sheet(results)
        
        self.results = results
        return results
    
    def get_status_summary(self) -> dict:
        """Get a summary of current results for the UI."""
        if not self.results:
            return {"total": 0, "pending": 0, "approved": 0, "sent": 0, "replied": 0}
        
        statuses = [r.status.value for r in self.results]
        return {
            "total": len(self.results),
            "pending": statuses.count("pending_review"),
            "approved": statuses.count("approved"),
            "sent": statuses.count("sent"),
            "replied": statuses.count("replied"),
            "booked": statuses.count("booked"),
            "passed": statuses.count("passed"),
        }
    
    def update_status(self, prospect_id: str, new_status: str) -> bool:
        """Update the status of a prospect result."""
        for result in self.results:
            if result.prospect.id == prospect_id:
                result.status = OutreachStatus(new_status)
                return True
        return False
    
    def _save_results(self, results: List[OutreachResult]):
        """Save raw results to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"outreach_results_{timestamp}.json"
        
        data = []
        for r in results:
            data.append({
                "prospect": r.prospect.model_dump(),
                "message": r.message.model_dump(),
                "status": r.status.value,
                "generated_at": r.message.generated_at.isoformat()
            })
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _generate_review_sheet(self, results: List[OutreachResult]):
        """Generate a human-readable review CSV."""
        import csv
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"review_sheet_{timestamp}.csv"
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Name", "Title", "Company", "LinkedIn URL", 
                "Hook Type", "Referenced Activity",
                "Pain Signals", "VoiceCare Angle",
                "Message", "Confidence", "Status", "Review Notes"
            ])
            
            for r in results:
                writer.writerow([
                    f"{r.prospect.first_name} {r.prospect.last_name}",
                    r.prospect.title,
                    r.prospect.company.name,
                    r.prospect.linkedin_url or "",
                    r.message.hook,
                    r.message.referenced_activity,
                    ", ".join(r.prospect.pain_signals),
                    r.message.voicecare_angle,
                    r.message.full_message,
                    f"{r.message.confidence_score:.0%}",
                    r.status.value,
                    r.message.review_notes or ""
                ])
        
        return filepath
