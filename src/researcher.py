"""
Research Agent Module

Analyzes prospect activity and enriches with REAL company news via Gemini Search Grounding.
"""
import os
import re
from typing import List, Optional, Dict
from datetime import datetime

from models import Prospect, LinkedInActivity
from gemini_client import GeminiClient


class ResearchAgent:
    """Researches prospect activity and company context."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()
        self.use_llm = self.gemini.is_available()
    
    def research_prospect(self, prospect: Prospect) -> Dict:
        """Full research pipeline for a single prospect."""
        # Step 1: Score and rank recent activities
        ranked_activities = self._rank_activities(prospect.activities)
        
        # Step 2: Extract pain signals from top activity
        top_activity = ranked_activities[0] if ranked_activities else None
        pain_signals = self._extract_pain_signals(top_activity) if top_activity else []
        
        # Step 3: Research REAL company news via Gemini Search Grounding
        company_news = self._research_company_news_gemini(prospect.company.name)
        
        # Step 4: Generate research summary
        research = {
            "top_activity": top_activity,
            "pain_signals": pain_signals,
            "company_news": company_news,
            "hook_recommendation": self._generate_hook(top_activity, pain_signals, company_news),
            "research_timestamp": datetime.now().isoformat()
        }
        
        # Update prospect
        prospect.pain_signals = pain_signals
        
        return research
    
    def _rank_activities(self, activities: List[LinkedInActivity]) -> List[LinkedInActivity]:
        """Rank activities by relevance for outreach."""
        scored = []
        for activity in activities:
            score = 0
            content_lower = activity.content.lower()
            
            # Recency bonus (within 7 days = highest)
            try:
                activity_date = datetime.fromisoformat(activity.date.replace('Z', '+00:00'))
                days_ago = (datetime.now() - activity_date).days
                if days_ago <= 3:
                    score += 30
                elif days_ago <= 7:
                    score += 20
                elif days_ago <= 14:
                    score += 10
            except:
                pass
            
            # Pain signal keywords
            pain_keywords = [
                "denial", "prior auth", "burnout", "hiring", "staffing",
                "automation", "payer", "claim", "reimbursement", "admin",
                "billing", "fax", "portal", "shortage", "freeze", "growth",
                "scale", "new location", "turnaround", "backlog"
            ]
            for keyword in pain_keywords:
                if keyword in content_lower:
                    score += 15
            
            # Activity type weight
            type_weights = {
                "post": 25,
                "job_change": 30,
                "article": 20,
                "comment": 15
            }
            score += type_weights.get(activity.activity_type, 10)
            
            scored.append((score, activity))
        
        scored.sort(reverse=True, key=lambda x: x[0])
        return [a for _, a in scored]
    
    def _extract_pain_signals(self, activity: LinkedInActivity) -> List[str]:
        """Extract pain signals from activity content."""
        content = activity.content.lower()
        signals = []
        
        signal_map = {
            "staffing shortage": ["hiring", "staffing", "shortage", "losing", "walk", "burnout", "quit"],
            "hiring freeze": ["hiring freeze", "no budget", "headcount", "can't hire"],
            "high admin burden": ["admin", "drowning", "buried", "paperwork", "manual"],
            "prior authorization delays": ["prior auth", "authorization", "turnaround", "approval"],
            "claim denials": ["denial", "denied", "rejected claim", "denied claim"],
            "slow reimbursement": ["reimbursement", "cash flow", "revenue cycle", "days outstanding"],
            "burnout": ["burnout", "exhausted", "overwhelmed", "mental health", "leaving"],
            "payer portal issues": ["portal", "fax", "website", "system down"],
            "growth scaling": ["new location", "expansion", "scaling", "growth", "opening"],
        }
        
        for pain, keywords in signal_map.items():
            for kw in keywords:
                if kw in content:
                    signals.append(pain)
                    break
        
        # Use Gemini for deeper analysis if available
        if self.use_llm and len(signals) < 2:
            signals.extend(self._llm_extract_pains(activity.content))
        
        return list(set(signals)) if signals else ["high admin burden"]
    
    def _llm_extract_pains(self, content: str) -> List[str]:
        """Use Gemini to extract pain signals from content."""
        try:
            system_prompt = """You are an expert B2B sales researcher. Analyze the following LinkedIn activity 
and extract the top 2 business pain points mentioned or implied. 
Return ONLY a JSON array of strings like ["pain1", "pain2"].
Pain options: staffing shortage, hiring freeze, high admin burden, 
prior authorization delays, claim denials, slow reimbursement, 
burnout, payer portal issues, growth scaling, compliance concerns."""
            
            result = self.gemini.generate_json(
                system_prompt=system_prompt,
                user_prompt=content,
                temperature=0.2
            )
            
            # Handle both array and object responses
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                for key in result:
                    if isinstance(result[key], list):
                        return result[key]
            return []
        except Exception as e:
            print(f"Gemini extraction failed: {e}")
            return []
    
    def _research_company_news_gemini(self, company_name: str) -> List[str]:
        """Research REAL company news using Gemini Search Grounding."""
        if not self.use_llm:
            return self._mock_company_news(company_name)
        
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=self.gemini.api_key)
            
            query = f"Latest news about {company_name} healthcare company in 2025 2026. Recent developments, expansions, funding, leadership changes."
            
            response = client.models.generate_content(
                model=self.gemini.model_name,
                contents=query,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    max_output_tokens=500
                )
            )
            
            # Extract news items from grounded response
            news_text = response.text.strip()
            
            # Parse into bullet points
            news_items = []
            for line in news_text.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or len(line) > 20):
                    cleaned = line.lstrip('-• ').strip()
                    if cleaned and len(cleaned) > 10:
                        news_items.append(cleaned)
            
            # If no structured bullets, split by sentences
            if not news_items:
                sentences = [s.strip() for s in re.split(r'[.!?]+', news_text) if len(s.strip()) > 20]
                news_items = sentences[:3]
            
            return news_items[:3] if news_items else self._mock_company_news(company_name)
            
        except Exception as e:
            print(f"Gemini search grounding failed for {company_name}: {e}")
            return self._mock_company_news(company_name)
    
    def _mock_company_news(self, company_name: str) -> List[str]:
        """Fallback mock company news."""
        mock_news = {
            "Pacific Orthopedics Group": [
                "Announced expansion into sports medicine in Q2 2025",
                "Recently implemented new EHR system"
            ],
            "Summit Neurology Associates": [
                "Opening 3rd location in Q3 2025",
                "Featured in regional healthcare innovation report"
            ],
            "Metro Pediatrics": [
                "Implemented hiring freeze through Q4 2025",
                "Transitioning to value-based care contracts"
            ],
            "Coastal Surgery Center": [
                "New leadership team appointed in early 2025",
                "Planning ASC expansion to adjacent county"
            ],
            "Heartland Family Medicine": [
                "Merged with two rural practices in Q1 2025",
                "Facing staffing challenges across 12 locations"
            ],
            "Lakeside Orthopedic Institute": [
                "Opened new outpatient surgery center in March 2025",
                "Partnership with regional health network announced"
            ],
            "Bay Area Cardiology Partners": [
                "Recruiting for 3 new physician roles",
                "Expanded telehealth services to rural areas"
            ],
            "Denver Children's Health": [
                "Launched pediatric mental health initiative",
                "Received Level 1 trauma center designation"
            ],
            "St. Mary's Medical Group": [
                "Merged with two rural practices in Q1 2025",
                "Implementing new revenue cycle management platform"
            ],
            "Midwest Urology Center": [
                "Opening ASC next month",
                "Recruiting for 2 new urologists"
            ],
            "Austin Women's Health": [
                "Expanded to second location",
                "Launching midwifery program"
            ],
            "Harris Healthcare Advisors": [
                "Published annual RCM benchmark report",
                "Growing client base to 40+ practices"
            ]
        }
        return mock_news.get(company_name, [])
    
    def _generate_hook(self, activity: Optional[LinkedInActivity], 
                       pain_signals: List[str], 
                       company_news: List[str]) -> Dict:
        """Generate the outreach hook recommendation."""
        if not activity:
            return {"type": "none", "text": "No recent activity found"}
        
        # Determine hook type
        if activity.activity_type == "job_change":
            return {
                "type": "job_change",
                "text": f"Congratulations on your new role at {activity.content.split(' at ')[-1] if ' at ' in activity.content else 'their company'}",
                "reference": activity.content
            }
        elif activity.activity_type == "post":
            return {
                "type": "post_reference",
                "text": f"Saw your post about {pain_signals[0] if pain_signals else 'recent challenges'}",
                "reference": activity.content[:120] + "..." if len(activity.content) > 120 else activity.content
            }
        elif activity.activity_type == "comment":
            return {
                "type": "comment_reference",
                "text": f"Noticed your comment on the discussion about {pain_signals[0] if pain_signals else 'healthcare ops'}",
                "reference": activity.content[:120] + "..." if len(activity.content) > 120 else activity.content
            }
        else:
            return {
                "type": "content_reference",
                "text": f"Read your recent share about {pain_signals[0] if pain_signals else 'healthcare operations'}",
                "reference": activity.content[:120] + "..." if len(activity.content) > 120 else activity.content
            }
