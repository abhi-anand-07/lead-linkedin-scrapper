#!/usr/bin/env python3
"""
Lead Personalization Agent CLI

Usage:
    python src/main.py run              # Run pipeline once
    python src/main.py run --urls urls.txt   # Run with specific URLs
    python src/main.py schedule         # Start daily scheduler
    python src/main.py demo             # Run with demo data + show outputs
"""
import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from orchestrator import LeadPersonalizationAgent


def load_urls_from_file(filepath: str) -> list:
    """Load LinkedIn URLs from a text file."""
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def run_demo():
    """Run a full demo with rich output."""
    print("\n" + "="*70)
    print("   🎯 VOICECARE AI — SCALABLE LEAD PERSONALIZATION AGENT")
    print("   Assignment Demo: 5 Healthcare RCM Prospects")
    print("="*70)
    
    agent = LeadPersonalizationAgent(
        proxycurl_key=os.getenv("PROXYCURL_API_KEY"),
        openai_key=os.getenv("OPENAI_API_KEY"),
        max_daily=5
    )
    
    results = agent.run_pipeline()
    
    print("\n" + "="*70)
    print("   📤 SAMPLE OUTPUTS (Ready for LinkedIn)")
    print("="*70)
    
    for i, result in enumerate(results, 1):
        p = result.prospect
        m = result.message
        
        print(f"\n┌─ Prospect #{i}")
        print(f"│  Name:     {p.first_name} {p.last_name}")
        print(f"│  Role:     {p.title}")
        print(f"│  Company:  {p.company.name}")
        print(f"│  Pains:    {', '.join(p.pain_signals)}")
        print(f"│")
        print(f"│  📝 MESSAGE ({len(m.full_message)} chars):")
        # Word wrap the message
        words = m.full_message.split()
        lines = []
        current = "│     "
        for word in words:
            if len(current) + len(word) + 1 > 65:
                lines.append(current)
                current = "│     " + word
            else:
                current += " " + word if current != "│     " else word
        lines.append(current)
        for line in lines:
            print(line)
        print(f"│")
        print(f"│  🎯 Hook Type: {m.hook[:50]}...")
        print(f"│  🔗 Activity:  {m.referenced_activity[:50]}...")
        print(f"│  💡 Angle:     {m.voicecare_angle[:50]}...")
        print(f"│  📊 Confidence: {m.confidence_score:.0%}")
        print(f"└─ Status: {result.status.value.upper()}")
    
    print("\n" + "="*70)
    print("   ✅ DEMO COMPLETE")
    print("="*70)
    print("\n📁 Check the outputs/ directory for:")
    print("   • outreach_results_*.json    — Raw structured data")
    print("   • review_sheet_*.csv         — Human review spreadsheet")
    print("\n💡 To run with your own OpenAI key (better messages):")
    print("   export OPENAI_API_KEY=sk-...")
    print("   python src/main.py demo")
    print("\n💡 To run on a schedule:")
    print("   python src/main.py schedule --time 09:00")
    print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="VoiceCare AI Lead Personalization Agent"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run pipeline once")
    run_parser.add_argument("--urls", help="File with LinkedIn URLs (one per line)")
    run_parser.add_argument("--max", type=int, default=5, help="Max prospects per run")
    
    # Schedule command
    sched_parser = subparsers.add_parser("schedule", help="Start daily scheduler")
    sched_parser.add_argument("--time", default="09:00", help="Run time (HH:MM)")
    sched_parser.add_argument("--tz", default="America/Los_Angeles", help="Timezone")
    
    # Demo command
    subparsers.add_parser("demo", help="Run full demo with sample data")
    
    args = parser.parse_args()
    
    # Load environment
    load_dotenv()
    
    if args.command == "demo":
        run_demo()
    
    elif args.command == "run":
        agent = LeadPersonalizationAgent(
            proxycurl_key=os.getenv("PROXYCURL_API_KEY"),
            openai_key=os.getenv("OPENAI_API_KEY"),
            max_daily=args.max
        )
        
        urls = None
        if args.urls:
            urls = load_urls_from_file(args.urls)
        
        agent.run_pipeline(linkedin_urls=urls)
    
    elif args.command == "schedule":
        agent = LeadPersonalizationAgent(
            proxycurl_key=os.getenv("PROXYCURL_API_KEY"),
            openai_key=os.getenv("OPENAI_API_KEY"),
            max_daily=5
        )
        agent.schedule_daily(run_time=args.time, timezone=args.tz)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
