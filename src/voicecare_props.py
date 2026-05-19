"""
VoiceCare AI value propositions mapped to prospect pain points.
This is the strategic messaging library that ensures every outreach
is tied to a specific problem VoiceCare solves.
"""
from typing import Dict, List


# Pain point → Value prop mapping
PAIN_TO_VALUE_MAP: Dict[str, List[str]] = {
    "staffing shortage": [
        "Handle 5x claims volume with 0% staff increase",
        "Our AI agent Joy completes payer calls autonomously, freeing your team for patient care"
    ],
    "hiring freeze": [
        "Break the 1:1 link between volume and headcount",
        "Super-staff your revenue cycle without adding headcount"
    ],
    "high admin burden": [
        "Save 500 hours per 1,000 payer phone calls",
        "Clinicians spend 28 hrs/week on admin — we give that time back"
    ],
    "prior authorization delays": [
        "Automate prior auth calls and portal navigation end-to-end",
        "Reduce time-to-therapy by collapsing the auth-to-approval timeline"
    ],
    "claim denials": [
        "30% better quality by eliminating human errors that cause denials",
        "Every call is logged and audit-ready with 99.9% precision"
    ],
    "slow reimbursement": [
        "Up to 70% faster claim-to-reimbursement cycle",
        "Cash flow velocity improvements through autonomous claims follow-up"
    ],
    "burnout": [
        "Remove the most tedious part of RCM — hours on hold with payers",
        "Your team focuses on high-order work; Joy handles the repetitive calls"
    ],
    "payer portal issues": [
        "Joy navigates payer portals autonomously, across voice, fax, and web",
        "Multi-modal orchestration — uses the most efficient channel for each payer"
    ],
    "growth scaling": [
        "Scale revenue cycle operations without scaling headcount linearly",
        "New locations, same RCM team — powered by AI"
    ],
    "compliance concerns": [
        "HIPAA compliant and SOC 2 Type II attested",
        "Human-in-the-loop safety net for complex clinical exceptions"
    ],
}

# Activity signal → Pain inference
ACTIVITY_SIGNAL_MAP: Dict[str, List[str]] = {
    "post about hiring": ["staffing shortage", "hiring freeze"],
    "post about new location": ["growth scaling", "staffing shortage"],
    "post about automation": ["high admin burden", "burnout"],
    "comment on payer issues": ["prior authorization delays", "claim denials"],
    "job change to rcm": ["growth scaling", "high admin burden"],
    "job change to practice manager": ["staffing shortage", "burnout"],
    "post about patient access": ["prior authorization delays", "slow reimbursement"],
    "post about billing": ["claim denials", "slow reimbursement"],
    "article about healthcare ai": ["high admin burden", "burnout"],
    "comment on staffing": ["staffing shortage", "burnout"],
}

# Role → Primary pain focus
ROLE_PAIN_PRIORITY: Dict[str, List[str]] = {
    "Practice Manager": ["staffing shortage", "burnout", "high admin burden", "growth scaling"],
    "Revenue Cycle Manager": ["claim denials", "slow reimbursement", "prior authorization delays", "payer portal issues"],
    "Revenue Cycle Director": ["growth scaling", "slow reimbursement", "staffing shortage", "compliance concerns"],
    "Billing Manager": ["claim denials", "high admin burden", "payer portal issues"],
    "Operations Manager": ["growth scaling", "staffing shortage", "high admin burden"],
    "Administrator": ["burnout", "staffing shortage", "compliance concerns"],
}


def get_value_props_for_pain(pain: str) -> List[str]:
    """Get VoiceCare value props for a specific pain point."""
    return PAIN_TO_VALUE_MAP.get(pain.lower(), [])


def infer_pains_from_activity(activity_type: str) -> List[str]:
    """Infer pain points from LinkedIn activity type."""
    activity_lower = activity_type.lower()
    for signal, pains in ACTIVITY_SIGNAL_MAP.items():
        if signal.lower() in activity_lower:
            return pains
    return ["high admin burden"]  # default


def get_role_priority_pains(title: str) -> List[str]:
    """Get prioritized pain points based on job title."""
    title_lower = title.lower()
    for role, pains in ROLE_PAIN_PRIORITY.items():
        if role.lower() in title_lower:
            return pains
    return ["high admin burden", "burnout", "staffing shortage"]


def build_context_package(prospect_title: str, activity_type: str, company_news: List[str] = None) -> Dict:
    """Build a strategic context package for message generation."""
    role_pains = get_role_priority_pains(prospect_title)
    activity_pains = infer_pains_from_activity(activity_type)
    
    # Merge and deduplicate, prioritizing role-specific pains
    all_pains = list(dict.fromkeys(role_pains + activity_pains))
    
    # Get value props for top 2 pains
    value_props = []
    for pain in all_pains[:2]:
        value_props.extend(get_value_props_for_pain(pain))
    
    return {
        "target_pains": all_pains[:3],
        "value_props": list(dict.fromkeys(value_props))[:3],
        "company_news": company_news or []
    }
