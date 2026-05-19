# 🎯 VoiceCare AI — Scalable Lead Personalization Agent

> **Assignment:** Build an agent that researches and contacts healthcare prospects at scale without sounding like a bot.

## What's New in v2.0

✅ **Web UI Dashboard** — Clean FastAPI interface with real-time results  
✅ **Gemini 2.0 Flash Lite** — Google's fast, cost-efficient LLM for message generation  
✅ **Manual Run Button** — No scheduler; trigger pipeline on-demand  
✅ **Approve/Pass Actions** — Human-in-the-loop review built into the UI  
✅ **Export CSV/JSON** — Download results for CRM import  

---

## What This Does

This agent automates the entire outreach research and personalization workflow:

1. **Discovers** 5 high-value prospects (Practice Managers, RCM Owners)
2. **Researches** their recent LinkedIn activity and company news
3. **Identifies** specific pain signals (staffing, denials, burnout, etc.)
4. **Generates** unique, activity-referenced outreach messages via **Gemini**
5. **Maps** every message to a specific VoiceCare AI value proposition
6. **Displays** results in a web dashboard with approve/pass buttons

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   DISCOVERY     │────▶│    RESEARCH     │────▶│  PERSONALIZE    │
│                 │     │                 │     │                 │
│ • Proxycurl API │     │ • Activity rank │     │ • Gemini LLM    │
│ • JSON import   │     │ • Pain extract  │     │ • Hook + Body   │
│ • Mock fallback │     │ • Company news  │     │ • Value mapping │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │   Target    │        │   Hook +    │        │  Message    │
   │   Profile   │        │   Pain      │        │  Ready      │
   └─────────────┘        └─────────────┘        └─────────────┘
                                                          │
                              ┌──────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │   FASTAPI UI    │
                    │                 │
                    │ • Run Button    │
                    │ • Review Cards  │
                    │ • Approve/Pass  │
                    │ • CSV/JSON      │
                    └─────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Framework | FastAPI + Uvicorn |
| Templates | Jinja2 |
| Styling | Custom CSS |
| LLM | Google Gemini 2.0 Flash Lite |
| LinkedIn Data | Proxycurl API (optional) |
| Data Models | Pydantic v2 |

---

## Quick Start

### 1. Install Dependencies

```bash
cd lead-personalisation-agnet
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure (Optional)

```bash
# For AI-powered messages (recommended)
export GEMINI_API_KEY=your-key-here
export GEMINI_MODEL=gemini-2.0-flash-lite

# For real LinkedIn enrichment (optional)
export PROXYCURL_API_KEY=your-key-here
```

> **Note:** The app works perfectly without any API keys using the template fallback system.

### 3. Launch the Web App

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open your browser: **http://localhost:8000**

### 4. Generate Outreach

Click the **"⚡ Run Agent"** button. The pipeline will:
- Discover 5 demo prospects
- Research their recent activity
- Generate personalized messages
- Display them in review cards

---

## Web UI Features

### Dashboard Stats
- Total generated, pending review, approved, sent

### Prospect Cards
Each card shows:
- **Prospect info** — Name, title, company
- **Pain signals** — Detected pain points (color-coded tags)
- **Referenced activity** — The exact post/comment used as hook
- **Generated message** — Ready-to-send LinkedIn message
- **VoiceCare angle** — Which value prop was mapped
- **Confidence score** — Message quality score
- **Actions** — ✓ Approve / ✕ Pass

### Export Buttons
- **CSV** — Review spreadsheet for sales team
- **JSON** — Structured data for CRM integration

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /` | — | Dashboard UI |
| `POST /api/run` | Form | Trigger pipeline |
| `GET /api/results` | — | Get JSON results |
| `POST /api/status/{id}` | Form | Update prospect status |
| `GET /api/download/csv` | — | Download review sheet |
| `GET /api/download/json` | — | Download results JSON |
| `GET /health` | — | Health check |

---

## Example Output

### Sarah Chen — Revenue Cycle Director
**Her Post:** *"23% increase in claim denials due to prior auth lapses"*

**Generated Message:**
> Hi Sarah, your post on the spike in denials hit home — 23% increase is brutal. VoiceCare eliminates the human errors that cause systemic denials and logs every call for audit. Want to see how we reduced denial rates for a Healthcare group?

### Marcus Williams — Practice Manager
**His Share:** *"'The Hidden Cost of Admin Burnout in Specialty Practices'"*

**Generated Message:**
> Hi Marcus, read your share on admin burnout in specialty practices. 28 hrs/week of admin work is staggering. Joy automates payer calls and portal work, giving your team 5x capacity without new hires. Curious if you've explored voice AI for RCM?

### Jennifer Patel — Billing Manager
**Her Post:** *"Hiring freeze just extended through Q4. Looking at RCM tools — what actually works?"*

**Generated Message:**
> Hi Jennifer, saw your post about staffing challenges. We've helped practices handle 5x claims volume without adding headcount — Joy automates the payer calls that eat up your team's day. Worth a 10-min conversation to see how it'd work for Metro Pediatrics?

### David Rodriguez — Operations Manager
**His Post:** *"Day 1: understanding why our prior auth turnaround is 3x the national average"*

**Generated Message:**
> Hi David, read your post about prior auth bottlenecks. Painful when patients wait because of paperwork. Joy handles end-to-end prior auth calls and portal navigation autonomously. Happy to share how we cut auth turnaround by 70% for a similar practice?

### Amanda Thompson — Revenue Cycle Manager
**Her Comment:** *"The fax machine is still the primary interface with 40% of our payers in 2025. This is absurd."*

**Generated Message:**
> Hi Amanda, saw your comment about fax machines still ruling payer comms in 2025. It's absurd. Joy navigates portals, processes faxes, and makes calls — whatever modality the payer requires. Have you found any tools that actually handle multi-payer workflows?

---

## The Message Quality Framework

Every generated message must pass these checks:

| Check | Description |
|-------|-------------|
| ✅ Activity Reference | Mentions a SPECIFIC recent post, comment, or job change |
| ✅ Pain-Value Map | Connects their pain to a specific VoiceCare capability |
| ✅ Role-Relevant | Uses pain priorities ranked by their job title |
| ✅ Under 300 chars | Fits LinkedIn connection message limits |
| ✅ No Bot Tone | Professional, empathetic, no generic fluff |
| ✅ Soft CTA | One specific question, not a hard pitch |

---

## Strategic Design Decisions

### 1. Why Gemini Flash Lite?
- **Speed:** Sub-second generation for 5 messages
- **Cost:** ~10x cheaper than GPT-4 for this use case
- **Quality:** Excellent at structured JSON output and concise copy
- **JSON mode:** Native structured output for reliable parsing

### 2. Why Template Fallback?
LLMs are great but unpredictable in interviews. The template system:
- Works 100% of the time with zero API costs
- Shows deep understanding of VoiceCare's value props
- Demonstrates you can build without crutches
- Gemini layer is additive, not required

### 3. Why Proxycurl over Scraping?
- LinkedIn scraping = immediate ban + legal risk
- Proxycurl is the industry standard for LinkedIn enrichment
- Shows you know the compliant tool stack
- Mock fallback proves the architecture is resilient

### 4. Why Web UI over CLI?
- **Interview-ready:** You can demo it live in a browser
- **Sales-friendly:** Non-technical stakeholders can review messages
- **Action-oriented:** Approve/Pass buttons show workflow thinking
- **Exportable:** CSV/JSON for CRM integration

### 5. Why Manual Run Button?
- **Quality control:** No accidental auto-sends
- **Interview-safe:** Trigger on-demand during demo
- **Future-proof:** Easy to add scheduler later via `/api/run` + cron

---

## Project Structure

```
.
├── app.py                     # FastAPI application
├── config/
│   └── settings.yaml          # VoiceCare value props, ICP, constraints
├── data/
│   └── sample_targets.json    # 5 demo prospects
├── outputs/                   # Generated CSV + JSON
├── src/
│   ├── models.py              # Pydantic data models
│   ├── voicecare_props.py     # Value prop ↔ Pain point mapping
│   ├── gemini_client.py       # Gemini API wrapper
│   ├── discovery.py           # Prospect discovery (API + mock)
│   ├── researcher.py          # Activity analysis + pain extraction
│   ├── personalizer.py        # Message generation engine
│   ├── orchestrator.py        # Pipeline orchestrator
│   └── main.py                # Legacy CLI (still works)
├── static/
│   └── style.css              # UI styles
├── templates/
│   ├── base.html              # Base layout
│   └── index.html             # Dashboard
├── .env.example               # Environment variables
├── requirements.txt
└── README.md
```

---

## Extending This

| Enhancement | How |
|-------------|-----|
| Add scheduler back | APScheduler calling `/api/run` daily at 9am PT |
| Real web search | Add SerpAPI/Perplexity to `researcher.py` |
| LinkedIn sending | n8n + browser automation or LinkedIn API |
| CRM sync | Webhook to Salesforce/HubSpot on "Approve" |
| A/B testing | Track message variants and reply rates |
| Slack alerts | Post daily results to #sales-ops |

---

## Assignment Submission Tips

1. **Launch the UI** — run `uvicorn app:app` and screen-share the dashboard
2. **Click "Run Agent"** — show real-time generation of 5 messages
3. **Walk through a card** — explain the hook, pain signal, and value prop
4. **Show the architecture** — the 4-layer pipeline + web UI
5. **Emphasize Gemini** — mention why you chose Flash Lite (speed + cost)
6. **Show compliance** — Proxycurl + human review = enterprise-ready

---

Built for VoiceCare AI interview assignment.
