import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Client initialization
api_key = os.getenv("OPENAI_API_KEY")
model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

client = AsyncOpenAI(api_key=api_key) if api_key else None

def get_client() -> AsyncOpenAI:
    if not client:
        raise ValueError("OPENAI_API_KEY is missing. Please set it in your environment or .env file.")
    return client

# ---------------------------------------------------------
# Agent 1: Social & Web Sentiment Tracker Agent
# ---------------------------------------------------------
async def social_sentiment_tracker_agent(brand_name: str, incident_context: str) -> Dict[str, Any]:
    """Simulates real-time social media & community web sentiment tracking across X, Reddit, LinkedIn, forums."""
    prompt = f"""
    You are an expert Social Sentiment Tracker Agent for brand crisis management.
    Brand Name: {brand_name}
    Incident Context / Crisis Description: {incident_context}

    Analyze social platforms (X/Twitter, Reddit, Tech/Industry Forums, LinkedIn) and simulate real-time metrics and community posts/tweets.

    Respond STRICTLY with valid JSON in this structure:
    {{
        "overall_sentiment_score": float between -1.0 (extremely negative) and 1.0 (very positive),
        "total_mentions_24h": integer (e.g. 14200),
        "negative_mention_percentage": float (e.g. 78.5),
        "trending_hashtags": ["list of string hashtags"],
        "simulated_feed": [
            {{
                "platform": "X (Twitter)" or "Reddit" or "LinkedIn" or "HackerNews",
                "author": "@handle or u/user",
                "content": "Realistic simulated post text highlighting concern, outrage, or query",
                "engagement": "e.g. 1.2k Retweets, 4.5k Likes",
                "sentiment": "Negative" or "Critical" or "Neutral"
            }},
            ... (at least 4 realistic posts across platforms)
        ],
        "viral_risk_assessment": "Short 2-sentence summary of how fast this is spreading"
    }}
    """
    try:
        cli = get_client()
        response = await cli.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output JSON only. Do not use markdown code blocks or additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data
    except Exception as e:
        # Fallback structured response
        return {
            "overall_sentiment_score": -0.75,
            "total_mentions_24h": 12400,
            "negative_mention_percentage": 82.4,
            "trending_hashtags": [f"#{brand_name.replace(' ', '')}Outage", f"#{brand_name.replace(' ', '')}Issue", "#TechFail"],
            "simulated_feed": [
                {
                    "platform": "X (Twitter)",
                    "author": "@TechWatcher",
                    "content": f"Is {brand_name} down right now or experiencing a major incident? Services failing across regions.",
                    "engagement": "850 Retweets, 2.3k Likes",
                    "sentiment": "Negative"
                },
                {
                    "platform": "Reddit",
                    "author": "u/sysadmin_guru",
                    "content": f"Detailed log analysis showing massive degradation on {brand_name}. Customers waiting for official statement.",
                    "engagement": "1.4k Upvotes, 320 Comments",
                    "sentiment": "Critical"
                }
            ],
            "viral_risk_assessment": "High viral velocity detected across X and Reddit with exponential mention growth in past 2 hours."
        }

# ---------------------------------------------------------
# Agent 2: News Alert & Media Agent
# ---------------------------------------------------------
async def news_alert_agent(brand_name: str, incident_context: str) -> Dict[str, Any]:
    """Monitors news outlets, industry publications, and tech journals for media coverage."""
    prompt = f"""
    You are an AI News Alert & Media Monitoring Agent.
    Brand: {brand_name}
    Incident: {incident_context}

    Simulate press coverage, media sentiment, top headline picks from TechCrunch, Bloomberg, Reuters, WSJ, Forbes, etc.

    Respond STRICTLY with valid JSON in this structure:
    {{
        "media_coverage_level": "High" or "Medium" or "Low" or "Severe",
        "journalists_contacted_count": integer,
        "top_news_articles": [
            {{
                "outlet": "e.g. TechCrunch / Bloomberg",
                "headline": "Realistic news headline",
                "summary": "Brief summary of article angle",
                "perceived_tone": "Hostile" or "Critical" or "Neutral" or "Balanced",
                "published_ago": "e.g. 35 mins ago"
            }},
            ... (at least 3 news articles)
        ],
        "key_media_narrative": "What is the mainstream news story angle right now?"
    }}
    """
    try:
        cli = get_client()
        response = await cli.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output JSON only. Do not use markdown code blocks or additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "media_coverage_level": "High",
            "journalists_contacted_count": 14,
            "top_news_articles": [
                {
                    "outlet": "TechCrunch",
                    "headline": f"{brand_name} Faces Unexpected Service Disruption Affecting Enterprise Clients",
                    "summary": f"Major outage reported as {brand_name} engineers investigate root cause. PR statement pending.",
                    "perceived_tone": "Critical",
                    "published_ago": "20 mins ago"
                },
                {
                    "headline": f"Security & Operational Concerns Raised Over Recent {brand_name} Incident",
                    "outlet": "Bloomberg",
                    "summary": "Industry analysts comment on brand reliability and customer trust impact.",
                    "perceived_tone": "Hostile",
                    "published_ago": "45 mins ago"
                }
            ],
            "key_media_narrative": "Media focus is heavily centered on transparency, operational reliability, and time-to-resolution."
        }

# ---------------------------------------------------------
# Agent 3: Crisis Severity Classifier Agent
# ---------------------------------------------------------
async def crisis_severity_classifier_agent(
    brand_name: str, 
    incident_context: str, 
    social_data: Dict[str, Any], 
    news_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Evaluates combined sentiment and context to categorize threat level P0, P1, P2, or P3."""
    prompt = f"""
    You are a Chief Risk & Crisis Severity Classifier Agent.
    Brand: {brand_name}
    Incident Context: {incident_context}
    Social Data: {json.dumps(social_data)}
    News Data: {json.dumps(news_data)}

    Classify the crisis into standard Incident Levels:
    - P0: CRITICAL / EXISTENTIAL CRISIS (Data breach, major safety incident, company-wide outage, legal disaster)
    - P1: HIGH CRISIS (Significant service disruption, viral executive blunder, heavy media backlash)
    - P2: MEDIUM INCIDENT (Localized issue, minor feature break, moderate negative noise)
    - P3: LOW INCIDENT (Isolated customer complaint, low-reach rumor)

    Respond STRICTLY with valid JSON in this structure:
    {{
        "severity_level": "P0" or "P1" or "P2" or "P3",
        "severity_title": "e.g. P0 - CRITICAL EMERGENCY",
        "risk_score_100": integer from 0 to 100,
        "impacted_areas": ["e.g. Brand Reputation", "Customer Retention", "Legal Compliance", "Stock/Financial"],
        "recommended_escalation": "Who should be immediately alerted (e.g. CEO, General Counsel, Head of PR, VP Engineering)",
        "justification": "Detailed 3-4 sentence explanation of why this severity level was assigned",
        "action_priority": "Immediate 60-minute priority protocol"
    }}
    """
    try:
        cli = get_client()
        response = await cli.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output JSON only. Do not use markdown code blocks or additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "severity_level": "P1",
            "severity_title": "P1 - HIGH CRISIS INCIDENT",
            "risk_score_100": 84,
            "impacted_areas": ["Brand Reputation", "Customer Retention", "Operations"],
            "recommended_escalation": "Executive Crisis Committee, VP of PR, Chief Technology Officer",
            "justification": "Rapidly growing negative social media sentiment combined with early Tier-1 tech media reporting requires swift, transparent PR action.",
            "action_priority": "Issue official statement within 30 minutes, update status page, deploy crisis customer communications."
        }

# ---------------------------------------------------------
# Agent 4: PR Response Drafter Agent
# ---------------------------------------------------------
async def pr_response_drafter_agent(
    brand_name: str, 
    incident_context: str, 
    severity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates tailored PR communications across Press Release, X/Twitter, LinkedIn, and Executive Holding Statement."""
    prompt = f"""
    You are an elite Crisis PR Specialist & Corporate Communications Lead Agent.
    Brand Name: {brand_name}
    Incident Context: {incident_context}
    Severity Classification: {json.dumps(severity_data)}

    Draft official crisis communications that are empathetic, authoritative, transparent, and legally defensive without admitting unwarranted fault.

    Respond STRICTLY with valid JSON:
    {{
        "press_release": {{
            "headline": "Official Press Statement Headline",
            "body": "Full multi-paragraph official press release content.",
            "key_takeaways": ["Point 1", "Point 2", "Point 3"]
        }},
        "social_media_posts": {{
            "twitter_x_thread": ["Tweet 1 (under 280 chars)", "Tweet 2 (under 280 chars)", "Tweet 3 (under 280 chars)"],
            "linkedin_statement": "Professional, detailed statement for LinkedIn network & partners"
        }},
        "executive_holding_statement": "Short 2-sentence quote from CEO/Spokesperson for immediate media inquiry replies",
        "do_not_say_guidelines": ["List of phrases or pitfalls to explicitly avoid in interviews"]
    }}
    """
    try:
        cli = get_client()
        response = await cli.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output JSON only. Do not use markdown code blocks or additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "press_release": {
                "headline": f"Official Statement from {brand_name} Regarding Recent Operational Incident",
                "body": f"At {brand_name}, the safety, trust, and reliability of our services remain our absolute highest priority. We are actively investigating and addressing the incident reported today...",
                "key_takeaways": [
                    "Engineers and crisis management team are actively working on resolution.",
                    "Full root cause analysis will be published transparently.",
                    "Dedicated support lines are open for impacted users."
                ]
            },
            "social_media_posts": {
                "twitter_x_thread": [
                    f"We are aware of the issue affecting {brand_name} services. Our team is actively investigating and working on a resolution. (1/3)",
                    "We sincerely apologize for any inconvenience caused. Core systems are currently being stabilized and monitored closely. (2/3)",
                    "For real-time updates, please monitor our official channels and status center. Next update in 30 mins. (3/3)"
                ],
                "linkedin_statement": f"Dear Partners and Community, We want to address the recent incident at {brand_name}... We hold ourselves to the highest standards of operational resilience."
            },
            "executive_holding_statement": f"\"We understand the concern this situation has caused. Our entire team is focused on resolving this immediately and ensuring transparent communication throughout.\"",
            "do_not_say_guidelines": [
                "Do NOT say 'it is not a big deal' or downplay user frustration.",
                "Do NOT blame third-party vendors without verified legal clearance.",
                "Do NOT make unverified promises on exact minute-by-minute ETA until confirmed."
            ]
        }

# ---------------------------------------------------------
# Agent 5: Stakeholder Communicator Agent
# ---------------------------------------------------------
async def stakeholder_communicator_agent(
    brand_name: str, 
    incident_context: str, 
    severity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generates direct targeted email communication for key stakeholder segments."""
    prompt = f"""
    You are an AI Stakeholder Communications Director Agent.
    Brand: {brand_name}
    Incident Context: {incident_context}
    Severity Data: {json.dumps(severity_data)}

    Draft personalized, clear email templates tailored for 4 distinct stakeholder groups:
    1. Customers / End-Users
    2. Enterprise VIP Clients / Enterprise Account Managers
    3. Investors & Board Members
    4. Internal Staff & Team Members

    Respond STRICTLY with valid JSON:
    {{
        "customer_email": {{
            "subject": "Subject line for customers",
            "body": "Empathetic, clear email body"
        }},
        "enterprise_client_email": {{
            "subject": "Subject line for enterprise clients",
            "body": "Professional SLA-focused email body with direct contact details"
        }},
        "investor_board_email": {{
            "subject": "Subject line for investors/board",
            "body": "Strategic, financial risk mitigation and impact assessment email"
        }},
        "internal_team_email": {{
            "subject": "Subject line for internal employees",
            "body": "Internal guidance, media policy advisory, team alignment email"
        }}
    }}
    """
    try:
        cli = get_client()
        response = await cli.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You output JSON only. Do not use markdown code blocks or additional text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "customer_email": {
                "subject": f"Important Update Regarding {brand_name} Services",
                "body": f"Dear Customer,\n\nWe are reaching out to inform you about a recent incident affecting {brand_name}. Our engineering and customer care teams are working diligently to ensure full service restoration..."
            },
            "enterprise_client_email": {
                "subject": f"[Priority SLA Update] {brand_name} Operational Incident Status",
                "body": f"Dear Valued Enterprise Partner,\n\nThis is a direct status update regarding your account with {brand_name}..."
            },
            "investor_board_email": {
                "subject": f"Executive Briefing: {brand_name} Crisis Response & Status",
                "body": f"Dear Board Members & Investors,\n\nThis email provides a strategic update on the active incident and our response plan..."
            },
            "internal_team_email": {
                "subject": f"Internal Briefing: {brand_name} Crisis Action Protocol & Media Guidelines",
                "body": f"Team,\n\nAs you may be aware, we are currently managing an active operational issue. Please direct all press inquiries to pr@{brand_name.lower().replace(' ', '')}.com..."
            }
        }

# ---------------------------------------------------------
# Master Orchestrator: Multi-Agent Crisis Workflow
# ---------------------------------------------------------
async def run_crisis_communication_pipeline(brand_name: str, incident_context: str) -> Dict[str, Any]:
    """Orchestrates all 5 agents in a multi-stage crisis mitigation pipeline."""
    # Stage 1: Parallel Social & News Monitoring
    social_task = social_sentiment_tracker_agent(brand_name, incident_context)
    news_task = news_alert_agent(brand_name, incident_context)
    social_data, news_data = await asyncio.gather(social_task, news_task)

    # Stage 2: Risk Classification based on Stage 1 outputs
    severity_data = await crisis_severity_classifier_agent(
        brand_name, incident_context, social_data, news_data
    )

    # Stage 3: Parallel Response Generation (PR & Stakeholder Comms)
    pr_task = pr_response_drafter_agent(brand_name, incident_context, severity_data)
    stakeholder_task = stakeholder_communicator_agent(brand_name, incident_context, severity_data)
    pr_data, stakeholder_data = await asyncio.gather(pr_task, stakeholder_task)

    # Combined Orchestration Output
    return {
        "brand_name": brand_name,
        "incident_context": incident_context,
        "social_sentiment": social_data,
        "news_alert": news_data,
        "severity_classification": severity_data,
        "pr_responses": pr_data,
        "stakeholder_communications": stakeholder_data
    }
