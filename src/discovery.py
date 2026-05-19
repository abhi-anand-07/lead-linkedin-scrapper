"""
Prospect Discovery Module

Supports multiple data sources:
1. Proxycurl API (real LinkedIn data)
2. Manual input (for assignments/demos)
3. JSON file import

Now with DYNAMIC mock data — randomized profiles each run.
"""
import os
import json
import random
from typing import List, Optional
from datetime import datetime, timedelta

from models import Prospect, Company, LinkedInActivity


# Expanded pool of realistic mock profiles
MOCK_PROFILE_POOL = [
    {
        "first_name": "Sarah",
        "last_name": "Chen",
        "title": "Revenue Cycle Director",
        "company": {"name": "Pacific Orthopedics Group", "industry": "Healthcare", "size": "200-500"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Just wrapped our quarterly audit. 23% increase in claim denials due to prior auth lapses. We need better systems, not more bodies.",
                "date": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "activity_type": "comment",
                "content": "Same here. Our billing team is drowning in payer portal work. Anyone found a real solution?",
                "date": (datetime.now() - timedelta(days=5)).isoformat()
            }
        ]
    },
    {
        "first_name": "Marcus",
        "last_name": "Williams",
        "title": "Practice Manager",
        "company": {"name": "Summit Neurology Associates", "industry": "Healthcare", "size": "50-200"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Excited to announce our 3rd location opening in Q3! Now the hard part: scaling ops without breaking our team's spirit.",
                "date": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "activity_type": "article",
                "content": "Shared: 'The Hidden Cost of Admin Burnout in Specialty Practices'",
                "date": (datetime.now() - timedelta(days=7)).isoformat()
            }
        ]
    },
    {
        "first_name": "Jennifer",
        "last_name": "Patel",
        "title": "Billing Manager",
        "company": {"name": "Metro Pediatrics", "industry": "Healthcare", "size": "100-500"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Hiring freeze just extended through Q4. Time to get creative with automation. Looking at RCM tools — what actually works?",
                "date": (datetime.now() - timedelta(days=3)).isoformat()
            }
        ]
    },
    {
        "first_name": "David",
        "last_name": "Rodriguez",
        "title": "Operations Manager",
        "company": {"name": "Coastal Surgery Center", "industry": "Healthcare", "size": "50-200"},
        "activities": [
            {
                "activity_type": "job_change",
                "content": "Started new position as Operations Manager at Coastal Surgery Center",
                "date": (datetime.now() - timedelta(days=14)).isoformat()
            },
            {
                "activity_type": "post",
                "content": "Day 1 priority: understanding why our prior auth turnaround is 3x the national average. This is fixable.",
                "date": (datetime.now() - timedelta(days=10)).isoformat()
            }
        ]
    },
    {
        "first_name": "Amanda",
        "last_name": "Thompson",
        "title": "Revenue Cycle Manager",
        "company": {"name": "Heartland Family Medicine", "industry": "Healthcare", "size": "500-1000"},
        "activities": [
            {
                "activity_type": "comment",
                "content": "The fax machine is still the primary interface with 40% of our payers in 2025. This is absurd.",
                "date": (datetime.now() - timedelta(days=4)).isoformat()
            },
            {
                "activity_type": "post",
                "content": "Just lost another experienced biller to burnout. 18 years of institutional knowledge walking out the door.",
                "date": (datetime.now() - timedelta(days=6)).isoformat()
            }
        ]
    },
    {
        "first_name": "Michael",
        "last_name": "O'Brien",
        "title": "Revenue Cycle Director",
        "company": {"name": "Lakeside Orthopedic Institute", "industry": "Healthcare", "size": "100-300"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Our denial rate jumped 18% after switching EHRs. The data migration exposed gaps in our auth workflow we didn't know existed.",
                "date": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "activity_type": "comment",
                "content": "We tried outsourcing prior auth to a BPO. Quality tanked. Back to square one.",
                "date": (datetime.now() - timedelta(days=8)).isoformat()
            }
        ]
    },
    {
        "first_name": "Lisa",
        "last_name": "Nakamura",
        "title": "Practice Administrator",
        "company": {"name": "Bay Area Cardiology Partners", "industry": "Healthcare", "size": "50-150"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Posted 3 RCM roles 6 weeks ago. Zero qualified applicants. Starting to think the talent pool has dried up permanently.",
                "date": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "activity_type": "article",
                "content": "Shared: 'Why Medical Billers Are Leaving the Profession in Record Numbers'",
                "date": (datetime.now() - timedelta(days=5)).isoformat()
            }
        ]
    },
    {
        "first_name": "Robert",
        "last_name": "Kim",
        "title": "Billing Operations Lead",
        "company": {"name": "Denver Children's Health", "industry": "Healthcare", "size": "300-800"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Just calculated: our team spends 4.2 hours per day on hold with payers. That's 50% of one FTE doing literally nothing productive.",
                "date": (datetime.now() - timedelta(days=3)).isoformat()
            },
            {
                "activity_type": "comment",
                "content": "Has anyone successfully automated Medicaid prior auth? Our state portal changes every 3 months and breaks everything.",
                "date": (datetime.now() - timedelta(days=6)).isoformat()
            }
        ]
    },
    {
        "first_name": "Cassandra",
        "last_name": "Wright",
        "title": "Revenue Cycle Manager",
        "company": {"name": "St. Mary's Medical Group", "industry": "Healthcare", "size": "1000+"},
        "activities": [
            {
                "activity_type": "job_change",
                "content": "Excited to join St. Mary's as Revenue Cycle Manager. Looking forward to fixing what my predecessor left behind.",
                "date": (datetime.now() - timedelta(days=10)).isoformat()
            },
            {
                "activity_type": "post",
                "content": "Week 2 reality check: 12 different payer portals, each with unique login flows. Our staff has a spreadsheet just to remember passwords. There has to be a better way.",
                "date": (datetime.now() - timedelta(days=4)).isoformat()
            }
        ]
    },
    {
        "first_name": "James",
        "last_name": "Peterson",
        "title": "Practice Manager",
        "company": {"name": "Midwest Urology Center", "industry": "Healthcare", "size": "50-200"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Opening our ASC next month. My biggest fear isn't the surgical outcomes — it's whether our billing team can handle the new payer mix without drowning.",
                "date": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "activity_type": "comment",
                "content": "The payer landscape for ASCs is completely different from office-based. Different auth rules, different fee schedules, different everything.",
                "date": (datetime.now() - timedelta(days=5)).isoformat()
            }
        ]
    },
    {
        "first_name": "Priya",
        "last_name": "Sharma",
        "title": "Operations Director",
        "company": {"name": "Austin Women's Health", "industry": "Healthcare", "size": "100-400"},
        "activities": [
            {
                "activity_type": "post",
                "content": "Quarterly numbers are in: A/R days outstanding increased from 42 to 58. CFO wants answers. I want solutions that don't require 3 new hires.",
                "date": (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                "activity_type": "comment",
                "content": "We're seeing more denials for 'lack of medical necessity' even though documentation is complete. Payers are getting more aggressive.",
                "date": (datetime.now() - timedelta(days=4)).isoformat()
            }
        ]
    },
    {
        "first_name": "Thomas",
        "last_name": "Harris",
        "title": "RCM Consultant",
        "company": {"name": "Harris Healthcare Advisors", "industry": "Healthcare Consulting", "size": "10-50"},
        "activities": [
            {
                "activity_type": "post",
                "content": "After auditing 40 practices this year, the #1 pattern is clear: practices grow to 3-4 locations and their RCM completely breaks. No systems, just heroic effort.",
                "date": (datetime.now() - timedelta(days=2)).isoformat()
            },
            {
                "activity_type": "article",
                "content": "Published: 'The $2M RCM Mistake Every Growing Practice Makes'",
                "date": (datetime.now() - timedelta(days=9)).isoformat()
            }
        ]
    },
]


class ProspectDiscovery:
    """Discovers and enriches prospect profiles.
    
    Supports three modes (in priority order):
    1. Real LinkedIn scraping via linkedin_scraper (requires LINKEDIN_EMAIL/PASSWORD)
    2. Proxycurl API (requires PROXYCURL_API_KEY)
    3. Mock data (default, no credentials needed)
    """
    
    def __init__(self, proxycurl_api_key: Optional[str] = None,
                 linkedin_email: Optional[str] = None,
                 linkedin_password: Optional[str] = None):
        self.proxycurl_api_key = proxycurl_api_key or os.getenv("PROXYCURL_API_KEY")
        self.linkedin_email = linkedin_email or os.getenv("LINKEDIN_EMAIL")
        self.linkedin_password = linkedin_password or os.getenv("LINKEDIN_PASSWORD")
        
        # Determine which source to use
        if self.linkedin_email and self.linkedin_password:
            self.mode = "linkedin_scraper"
        elif self.proxycurl_api_key:
            self.mode = "proxycurl"
        else:
            self.mode = "mock"
    
    def discover_from_list(self, linkedin_urls: List[str]) -> List[Prospect]:
        """Discover prospects from a list of LinkedIn URLs."""
        if self.mode == "linkedin_scraper":
            return self._scrape_linkedin_profiles(linkedin_urls)
        elif self.mode == "proxycurl":
            prospects = []
            for url in linkedin_urls:
                prospects.append(self._api_enrich_profile(url))
            return prospects
        else:
            prospects = []
            for url in linkedin_urls:
                prospects.append(self._mock_enrich_profile(url))
            return prospects
    
    def _scrape_linkedin_profiles(self, urls: List[str]) -> List[Prospect]:
        """Scrape real LinkedIn profiles using linkedin_scraper."""
        import asyncio
        from linkedin_discovery import LinkedInDiscovery
        
        discovery = LinkedInDiscovery(
            email=self.linkedin_email,
            password=self.linkedin_password
        )
        return discovery.discover_sync(urls)
    
    def discover_from_json(self, filepath: str) -> List[Prospect]:
        """Load prospects from a JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        prospects = []
        for item in data:
            company = Company(**item.get("company", {}))
            activities = [LinkedInActivity(**a) for a in item.get("activities", [])]
            prospect = Prospect(
                first_name=item["first_name"],
                last_name=item["last_name"],
                title=item["title"],
                company=company,
                linkedin_url=item.get("linkedin_url"),
                email=item.get("email"),
                activities=activities
            )
            prospects.append(prospect)
        return prospects
    
    def get_mock_pool(self, count: int = 5) -> List[Prospect]:
        """Get a randomized selection of mock prospects."""
        selected = random.sample(MOCK_PROFILE_POOL, min(count, len(MOCK_PROFILE_POOL)))
        prospects = []
        for profile in selected:
            company = Company(**profile["company"])
            activities = [LinkedInActivity(**a) for a in profile["activities"]]
            prospect = Prospect(
                first_name=profile["first_name"],
                last_name=profile["last_name"],
                title=profile["title"],
                company=company,
                linkedin_url=f"https://linkedin.com/in/{profile['first_name'].lower()}-{profile['last_name'].lower()}",
                activities=activities
            )
            prospects.append(prospect)
        return prospects
    
    def _api_enrich_profile(self, linkedin_url: str) -> Prospect:
        """Enrich profile using Proxycurl API.
        
        In production, this makes real API calls to:
        - /v2/linkedin/person/profile
        - /v2/linkedin/person/activity
        """
        import requests
        
        headers = {"Authorization": f"Bearer {self.proxycurl_api_key}"}
        
        # Get profile
        profile_resp = requests.get(
            "https://nubela.co/proxycurl/api/v2/linkedin",
            headers=headers,
            params={"url": linkedin_url, "use_cache": "if-present"},
            timeout=30
        )
        profile = profile_resp.json()
        
        # Get recent activity
        activity_resp = requests.get(
            "https://nubela.co/proxycurl/api/v2/linkedin/person/activity",
            headers=headers,
            params={"linkedin_profile_url": linkedin_url, "page_size": "10"},
            timeout=30
        )
        activities_raw = activity_resp.json().get("activities", [])
        
        activities = []
        for act in activities_raw[:5]:
            activities.append(LinkedInActivity(
                activity_type=act.get("activity_type", "post"),
                content=act.get("title", act.get("content", "")),
                date=act.get("published_at"),
                url=act.get("url")
            ))
        
        company = Company(
            name=profile.get("experiences", [{}])[0].get("company", "Unknown"),
            industry=profile.get("industry"),
            location=profile.get("location"),
        )
        
        return Prospect(
            first_name=profile.get("first_name", ""),
            last_name=profile.get("last_name", ""),
            title=profile.get("occupation", ""),
            company=company,
            linkedin_url=linkedin_url,
            activities=activities
        )
    
    def _mock_enrich_profile(self, linkedin_url: str) -> Prospect:
        """Generate realistic mock data for demo/assignment purposes."""
        # For URL-based requests, pick deterministically but from expanded pool
        url_lower = linkedin_url.lower()
        
        # Try to match by name in URL
        for idx, profile in enumerate(MOCK_PROFILE_POOL):
            first = profile["first_name"].lower()
            last = profile["last_name"].lower()
            if first in url_lower or last in url_lower:
                selected = profile
                break
        else:
            # Random fallback for unmatched URLs
            selected = random.choice(MOCK_PROFILE_POOL)
        
        company = Company(**selected["company"])
        activities = [LinkedInActivity(**a) for a in selected["activities"]]
        
        return Prospect(
            first_name=selected["first_name"],
            last_name=selected["last_name"],
            title=selected["title"],
            company=company,
            linkedin_url=linkedin_url,
            activities=activities
        )
