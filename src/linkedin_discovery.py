"""
Real LinkedIn Discovery using linkedin_scraper

Requires:
  - LINKEDIN_EMAIL and LINKEDIN_PASSWORD env vars
  - Playwright browser installed

Falls back to mock data if credentials are not provided.
"""
import os
import asyncio
from typing import List, Optional

from playwright.async_api import async_playwright
from linkedin_scraper import PersonScraper, login_with_credentials

from models import Prospect, Company, LinkedInActivity


class LinkedInDiscovery:
    """Discovers real LinkedIn profiles using linkedin_scraper + Playwright."""
    
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.email = email or os.getenv("LINKEDIN_EMAIL")
        self.password = password or os.getenv("LINKEDIN_PASSWORD")
        self.use_real = bool(self.email and self.password)
    
    async def discover_profiles(self, profile_urls: List[str]) -> List[Prospect]:
        """Scrape real LinkedIn profiles."""
        if not self.use_real:
            raise RuntimeError("LinkedIn credentials not configured. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD.")
        
        prospects = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Login
            await login_with_credentials(page, self.email, self.password, warm_up=True)
            
            # Scrape each profile
            for url in profile_urls:
                try:
                    prospect = await self._scrape_profile(page, url)
                    prospects.append(prospect)
                except Exception as e:
                    print(f"Failed to scrape {url}: {e}")
                    continue
            
            await browser.close()
        
        return prospects
    
    async def _scrape_profile(self, page, url: str) -> Prospect:
        """Scrape a single LinkedIn profile."""
        scraper = PersonScraper()
        person = await scraper.scrape(page, url)
        
        # Extract company from current experience
        company_name = "Unknown"
        if person.experiences:
            company_name = person.experiences[0].company_name or "Unknown"
        
        # Extract activities from posts if available
        activities = []
        if hasattr(person, 'posts') and person.posts:
            for post in person.posts[:3]:
                activities.append(LinkedInActivity(
                    activity_type="post",
                    content=post.content or "",
                    date=post.posted_date if hasattr(post, 'posted_date') else None,
                    url=post.link if hasattr(post, 'link') else None
                ))
        
        company = Company(name=company_name)
        
        return Prospect(
            first_name=person.first_name or "",
            last_name=person.last_name or "",
            title=person.headline or "",
            company=company,
            linkedin_url=url,
            activities=activities
        )
    
    def discover_sync(self, profile_urls: List[str]) -> List[Prospect]:
        """Synchronous wrapper for discover_profiles."""
        return asyncio.run(self.discover_profiles(profile_urls))
