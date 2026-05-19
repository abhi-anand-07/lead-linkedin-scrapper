"""
Personalization Engine — 2-Step LLM Pipeline

Step 1: Research Agent analyzes activity → outputs hook + pain point
Step 2: Copy Agent writes message using Voicecare value props

Now powered by Gemini 3.1 Flash Lite.
"""
import os
import re
from typing import Optional, Dict
from datetime import datetime

from models import Prospect, PersonalizedMessage
from voicecare_props import build_context_package
from gemini_client import GeminiClient


class PersonalizationEngine:
    """Generates hyper-personalized outreach messages."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini = gemini_client or GeminiClient()
        self.use_llm = self.gemini.is_available()
    
    def generate_message(self, prospect: Prospect, research: Dict) -> PersonalizedMessage:
        """Generate a personalized message for a prospect."""
        hook = research.get("hook_recommendation", {})
        pain_signals = research.get("pain_signals", [])
        company_news = research.get("company_news", [])
        top_activity = research.get("top_activity")
        
        # Build strategic context
        activity_type = top_activity.activity_type if top_activity else "post"
        context = build_context_package(
            prospect_title=prospect.title,
            activity_type=activity_type,
            company_news=company_news
        )
        
        # Merge research pains with context
        all_pains = list(dict.fromkeys(pain_signals + context["target_pains"]))
        
        if self.use_llm:
            message_data = self._generate_with_gemini(
                prospect=prospect,
                hook=hook,
                pains=all_pains,
                value_props=context["value_props"],
                company_news=company_news
            )
        else:
            message_data = self._generate_with_templates(
                prospect=prospect,
                hook=hook,
                pains=all_pains,
                value_props=context["value_props"]
            )
        
        return PersonalizedMessage(
            prospect_id=prospect.id,
            hook=message_data["hook"],
            body=message_data["body"],
            full_message=message_data["full_message"],
            referenced_activity=hook.get("reference", ""),
            voicecare_angle=message_data["voicecare_angle"],
            confidence_score=message_data["confidence"]
        )
    
    def _parse_confidence(self, raw) -> float:
        """Parse confidence value from various formats and normalize to 0-1."""
        val = 0.75
        if isinstance(raw, (int, float)):
            val = float(raw)
        elif isinstance(raw, str):
            raw = raw.strip().lower()
            mapping = {
                "high": 0.9, "very high": 0.95, "medium": 0.7,
                "low": 0.5, "very low": 0.3
            }
            if raw in mapping:
                val = mapping[raw]
            else:
                try:
                    val = float(raw)
                except ValueError:
                    pass
        # Normalize if given as percentage (e.g. 100, 95)
        if val > 1.0:
            val = val / 100.0
        return round(max(0.0, min(1.0, val)), 2)
    
    def _generate_with_gemini(self, prospect: Prospect, hook: Dict, 
                               pains: list, value_props: list, company_news: list) -> Dict:
        """Use Gemini Flash Lite to generate a personalized message."""
        
        system_prompt = """You are an expert B2B SaaS sales copywriter specializing in healthcare technology.
You write LinkedIn connection messages for VoiceCare AI, an AI agent called "Joy" that automates revenue cycle 
management tasks like prior authorization calls, benefit verification, and claims follow-up.

CRITICAL RULES:
1. Message MUST be under 300 characters
2. MUST reference a SPECIFIC recent activity or post with real details from it
3. MUST connect their exact pain to ONE specific VoiceCare value prop
4. Tone: warm, professional, conversational — like a peer, not a vendor
5. NEVER use generic openers like "I hope this finds you well" or "I came across your profile"
6. End with ONE soft, specific question — not a meeting request
7. Use their first name once, naturally
8. Mention "Joy" or "VoiceCare" once max
9. Vary your sentence structure. Don't start every message the same way
10. If company news is provided, weave it in naturally

BE NATURAL: Avoid formulaic patterns. Mix up how you reference posts. Sometimes lead with empathy, sometimes curiosity, sometimes a shared frustration. Make each message feel uniquely written for this person.

Return valid JSON with exactly these keys: hook, body, full_message, voicecare_angle, confidence"""
        
        user_prompt = f"""
Write a personalized LinkedIn message for:

Name: {prospect.first_name} {prospect.last_name}
Role: {prospect.title}
Company: {prospect.company.name} ({prospect.company.size or 'unknown size'})

THEIR RECENT ACTIVITY (use specific details from this):
{hook.get('reference', 'No recent activity')}
Type: {hook.get('type', 'general')}

THEIR BUSINESS PAINS:
{chr(10).join(f'- {p}' for p in pains[:3])}

VOICECARE VALUE PROPS (pick ONE that best matches their pain):
{chr(10).join(f'- {vp}' for vp in value_props[:3])}

COMPANY NEWS (weave in if relevant):
{chr(10).join(f'- {n}' for n in company_news) if company_news else 'None available'}

INSTRUCTIONS:
- Reference something SPECIFIC from their activity
- Match their pain to ONE VoiceCare value prop
- Be conversational and warm
- Under 300 characters
- End with one soft question
- Return as JSON

Generate the message now.
"""
        
        try:
            result = self.gemini.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7
            )
            
            full_msg = result.get("full_message", "")
            # Safety: truncate if over limit
            if len(full_msg) > 320:
                full_msg = full_msg[:317] + "..."
            
            # Robust confidence parsing
            raw_confidence = result.get("confidence", 0.85)
            confidence = self._parse_confidence(raw_confidence)
            
            return {
                "hook": result.get("hook", hook.get("text", "")),
                "body": result.get("body", ""),
                "full_message": full_msg,
                "voicecare_angle": result.get("voicecare_angle", value_props[0] if value_props else ""),
                "confidence": confidence
            }
        except Exception as e:
            print(f"Gemini generation failed: {e}. Falling back to templates.")
            return self._generate_with_templates(prospect, hook, pains, value_props)
    
    def _generate_with_templates(self, prospect: Prospect, hook: Dict,
                                  pains: list, value_props: list) -> Dict:
        """Template-based fallback when LLM is unavailable."""
        name = prospect.first_name
        hook_type = hook.get("type", "post")
        hook_text = hook.get("text", "")
        activity_ref = hook.get("reference", "")
        
        # Select primary pain and value prop
        primary_pain = pains[0] if pains else "high admin burden"
        primary_value = value_props[0] if value_props else "automates revenue cycle tasks"
        
        # Template library based on hook type and pain
        templates = {
            ("post_reference", "staffing shortage"): (
                f"Hi {name}, saw your post about staffing challenges. "
                f"We've helped practices handle 5x claims volume without adding headcount — "
                f"Joy automates the payer calls that eat up your team's day. "
                f"Worth a 10-min conversation to see how it'd work for {prospect.company.name}?"
            ),
            ("post_reference", "hiring freeze"): (
                f"Hi {name}, your post about the hiring freeze resonated — "
                f"tough to scale with fixed headcount. "
                f"VoiceCare AI essentially 'super-staffs' your RCM team by automating benefit verifications and auth calls. "
                f"Curious if you've explored AI for your backlog?"
            ),
            ("post_reference", "prior authorization delays"): (
                f"Hi {name}, read your post about prior auth bottlenecks. "
                f"Painful when patients wait because of paperwork. "
                f"Joy handles end-to-end prior auth calls and portal navigation autonomously. "
                f"Happy to share how we cut auth turnaround by 70% for a similar practice?"
            ),
            ("post_reference", "claim denials"): (
                f"Hi {name}, your post on the spike in denials hit home — "
                f"23% increase is brutal. "
                f"VoiceCare eliminates the human errors that cause systemic denials and logs every call for audit. "
                f"Want to see how we reduced denial rates for a {prospect.company.industry or 'healthcare'} group?"
            ),
            ("post_reference", "burnout"): (
                f"Hi {name}, your post about burnout really stood out. "
                f"Losing experienced billers is expensive. "
                f"Joy takes the most tedious RCM calls off your team's plate so they focus on what matters. "
                f"Would you be open to seeing how we protect institutional knowledge?"
            ),
            ("post_reference", "growth scaling"): (
                f"Hi {name}, congrats on the expansion! Scaling RCM across locations is the hard part. "
                f"VoiceCare lets you replicate your best billing ops without replicating headcount. "
                f"Interested in how we helped a multi-location practice scale smoothly?"
            ),
            ("job_change", "growth scaling"): (
                f"Hi {name}, congrats on the new role! "
                f"Fresh starts are the perfect time to fix broken RCM processes. "
                f"VoiceCare AI automates prior auth and claims follow-up from day one — "
                f"no 6-month implementation. "
                f"Worth a brief chat about quick wins for your first 90 days?"
            ),
            ("comment_reference", "payer portal issues"): (
                f"Hi {name}, saw your comment about fax machines still ruling payer comms in 2025. "
                f"It's absurd. Joy navigates portals, processes faxes, and makes calls — "
                f"whatever modality the payer requires. "
                f"Have you found any tools that actually handle multi-payer workflows?"
            ),
            ("content_reference", "staffing shortage"): (
                f"Hi {name}, read your share on admin burnout in specialty practices. "
                f"28 hrs/week of admin work is staggering. "
                f"Joy automates payer calls and portal work, giving your team 5x capacity without new hires. "
                f"Curious if you've explored voice AI for RCM?"
            ),
            ("content_reference", "burnout"): (
                f"Hi {name}, your share on admin burnout really resonated. "
                f"Losing institutional knowledge because of tedious payer calls is preventable. "
                f"Joy handles benefit verifications and auth follow-ups autonomously, "
                f"so your team focuses on patient care, not hold music. "
                f"Worth exploring how we protect team sanity while scaling volume?"
            ),
        }
        
        # Try exact match, then partial match
        key = (hook_type, primary_pain)
        if key in templates:
            full_message = templates[key]
        else:
            # Generic but still personalized
            full_message = (
                f"Hi {name}, {hook_text.lower() if not hook_text.startswith('Hi') else hook_text[3:].lower()}. "
                f"{primary_value}. "
                f"Would you be open to a brief conversation about how this might work for {prospect.company.name}?"
            )
        
        # Extract components
        sentences = [s.strip() for s in full_message.split('. ') if s.strip()]
        hook_sent = sentences[0] if sentences else hook_text
        body_sentences = sentences[1:-1] if len(sentences) > 2 else sentences[1:]
        body = '. '.join(body_sentences) + '.' if body_sentences else ""
        
        return {
            "hook": hook_sent,
            "body": body,
            "full_message": full_message,
            "voicecare_angle": primary_value,
            "confidence": 0.75
        }
