"""AI Supply Chain Risk & Optimizer Agents — Day 17

Multi-Agent Supply Chain Intelligence Engine:
  1. Supplier Risk Assessment  — Evaluates financial, geopolitical, and ESG risks.
  2. Lead Time Optimizer       — Suggests optimal routes and transit modes to avoid bottlenecks.
  3. Cost Reduction Analyst    — Identifies alternative sourcing and negotiating opportunities.
  4. Demand Forecaster         — Projects seasonal demand and calculates safety stock points.
  5. Disruption Alert Agent    — Scans simulated/real global events to flag shipping risks.
"""

from __future__ import annotations

import json
import os
import random
import asyncio
from typing import Awaitable, Callable, Any, Dict, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup OpenAI Client
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key.strip() and not api_key.startswith("your_"):
    client = AsyncOpenAI(api_key=api_key)
else:
    client = None

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

ProgressFn = Callable[[str, str], Awaitable[None]]

async def _noop(stage: str, message: str) -> None:
    pass

# Industry pre-sets for demo/fallback purposes
INDUSTRY_PRESETS = {
    "smartphone": {
        "product_name": "QuantumX Smartphone",
        "bom": [
            {"id": "comp-1", "name": "5G Snapdragon Processor", "category": "Semiconductors", "supplier": "Silicon Systems", "cost": 45.0, "lead_time": 45, "origin": "Hsinchu, Taiwan"},
            {"id": "comp-2", "name": "AMOLED Display Module", "category": "Displays", "supplier": "DisplayTech Ltd", "cost": 30.0, "lead_time": 25, "origin": "Seoul, South Korea"},
            {"id": "comp-3", "name": "4500mAh Li-Polymer Battery", "category": "Energy", "supplier": "NeXus Power", "cost": 15.0, "lead_time": 30, "origin": "Shenzhen, China"},
            {"id": "comp-4", "name": "Chassis & Aluminum Enclosure", "category": "Mechanical", "supplier": "AluFab Corp", "cost": 12.0, "lead_time": 15, "origin": "Ho Chi Minh City, Vietnam"},
            {"id": "comp-5", "name": "Camera Array (Sony Sensor)", "category": "Optics", "supplier": "OptoSens GmbH", "cost": 22.0, "lead_time": 20, "origin": "Munich, Germany"}
        ],
        "suppliers": [
            {"name": "Silicon Systems", "financial_health": "Excellent", "geopolitical_risk": "High", "esg_score": "A", "shipping_method": "Air"},
            {"name": "DisplayTech Ltd", "financial_health": "Good", "geopolitical_risk": "Medium", "esg_score": "B", "shipping_method": "Sea"},
            {"name": "NeXus Power", "financial_health": "Fair", "geopolitical_risk": "Medium", "esg_score": "B", "shipping_method": "Sea"},
            {"name": "AluFab Corp", "financial_health": "Good", "geopolitical_risk": "Low", "esg_score": "C", "shipping_method": "Sea"},
            {"name": "OptoSens GmbH", "financial_health": "Excellent", "geopolitical_risk": "Low", "esg_score": "A", "shipping_method": "Air"}
        ]
    },
    "solar": {
        "product_name": "SolarMax PV Inverter",
        "bom": [
            {"id": "comp-1", "name": "IGBT Power Transistors", "category": "Semiconductors", "supplier": "Semicon Alps", "cost": 120.0, "lead_time": 60, "origin": "Kyoto, Japan"},
            {"id": "comp-2", "name": "Toroidal Copper Transformer", "category": "Electromechanical", "supplier": "Inductors Inc", "cost": 85.0, "lead_time": 30, "origin": "Monterrey, Mexico"},
            {"id": "comp-3", "name": "Control Board (PCB Assembly)", "category": "Electronics", "supplier": "CircuitBoards Co", "cost": 45.0, "lead_time": 25, "origin": "Guangzhou, China"},
            {"id": "comp-4", "name": "IP65 Weatherproof Enclosure", "category": "Mechanical", "supplier": "EuroSteel Ltd", "cost": 60.0, "lead_time": 20, "origin": "Gdansk, Poland"}
        ],
        "suppliers": [
            {"name": "Semicon Alps", "financial_health": "Good", "geopolitical_risk": "Low", "esg_score": "A", "shipping_method": "Air"},
            {"name": "Inductors Inc", "financial_health": "Fair", "geopolitical_risk": "Low", "esg_score": "B", "shipping_method": "Land"},
            {"name": "CircuitBoards Co", "financial_health": "Fair", "geopolitical_risk": "Medium", "esg_score": "C", "shipping_method": "Sea"},
            {"name": "EuroSteel Ltd", "financial_health": "Good", "geopolitical_risk": "Low", "esg_score": "B", "shipping_method": "Land"}
        ]
    },
    "automotive": {
        "product_name": "Apex EV Motor Controller",
        "bom": [
            {"id": "comp-1", "name": "Silicon Carbide (SiC) MOSFETs", "category": "Power Electronics", "supplier": "PowerChips", "cost": 210.0, "lead_time": 75, "origin": "Austin, USA"},
            {"id": "comp-2", "name": "Liquid Cooling Plate", "category": "Thermal", "supplier": "CoolRun Tech", "cost": 65.0, "lead_time": 20, "origin": "Chennai, India"},
            {"id": "comp-3", "name": "Neodymium Magnet Rotor", "category": "Magnets", "supplier": "RareEarth Supply", "cost": 140.0, "lead_time": 40, "origin": "Baotou, China"},
            {"id": "comp-4", "name": "Wiring Harness & Connectors", "category": "Wiring", "supplier": "Connex Group", "cost": 35.0, "lead_time": 15, "origin": "Juarez, Mexico"}
        ],
        "suppliers": [
            {"name": "PowerChips", "financial_health": "Excellent", "geopolitical_risk": "Low", "esg_score": "A", "shipping_method": "Air"},
            {"name": "CoolRun Tech", "financial_health": "Good", "geopolitical_risk": "Medium", "esg_score": "B", "shipping_method": "Sea"},
            {"name": "RareEarth Supply", "financial_health": "Good", "geopolitical_risk": "High", "esg_score": "C", "shipping_method": "Sea"},
            {"name": "Connex Group", "financial_health": "Excellent", "geopolitical_risk": "Low", "esg_score": "B", "shipping_method": "Land"}
        ]
    }
}

# ---------------------------------------------------------------------------
# Local Heuristic Fallbacks (Runs when API key is missing or calls fail)
# ---------------------------------------------------------------------------

def calculate_supplier_risk_score(sup: dict) -> float:
    # Local scoring logic:
    fh_map = {"Excellent": 10, "Good": 30, "Fair": 60, "Poor": 90}
    gp_map = {"Low": 15, "Medium": 50, "High": 85}
    esg_map = {"A": 15, "B": 45, "C": 80}
    
    fh_val = fh_map.get(sup.get("financial_health"), 40)
    gp_val = gp_map.get(sup.get("geopolitical_risk"), 40)
    esg_val = esg_map.get(sup.get("esg_score"), 40)
    
    # Weighted average risk score
    return round((fh_val * 0.4) + (gp_val * 0.4) + (esg_val * 0.2), 1)

def run_local_risk_analysis(bom: List[dict], suppliers: List[dict]) -> List[dict]:
    risk_results = []
    sup_map = {s["name"]: s for s in suppliers}
    for item in bom:
        sname = item["supplier"]
        sup = sup_map.get(sname, {"name": sname, "financial_health": "Good", "geopolitical_risk": "Low", "esg_score": "B", "shipping_method": "Sea"})
        
        score = calculate_supplier_risk_score(sup)
        
        if score < 35:
            level = "Low"
            desc = f"Supplier {sname} displays solid financial buffers and is located in a stable administrative zone. ESG standards are high, indicating low disruption probability."
        elif score < 65:
            level = "Medium"
            geo_msg = f"Geopolitical volatility in {item['origin']}" if sup.get("geopolitical_risk") == "Medium" else "Financial reserves are somewhat tight"
            desc = f"Supplier {sname} has moderate exposure. {geo_msg}. Dual-sourcing recommended as a precaution."
        else:
            level = "High"
            desc = f"Critical Risk! Supplier {sname} has elevated risk profile. Geopolitical tension in {item['origin']} combined with weaker operational markers poses high supply chain fragility."
            
        risk_results.append({
            "component": item["name"],
            "supplier": sname,
            "origin": item["origin"],
            "financial_health": sup.get("financial_health"),
            "geopolitical_risk": sup.get("geopolitical_risk"),
            "esg_score": sup.get("esg_score"),
            "risk_score": score,
            "risk_level": level,
            "analysis": desc
        })
    return risk_results

def run_local_lead_time_optimization(bom: List[dict], suppliers: List[dict]) -> Dict:
    routes = []
    total_original_time = 0
    total_optimized_time = 0
    bottlenecks = []
    
    sup_map = {s["name"]: s for s in suppliers}
    
    for item in bom:
        sname = item["supplier"]
        sup = sup_map.get(sname, {})
        origin = item["origin"]
        orig_lt = item["lead_time"]
        ship_mode = sup.get("shipping_method", "Sea")
        
        # Calculate an optimized shipping alternative
        opt_lt = orig_lt
        alt_route = ""
        savings_reason = ""
        
        # Optimization heuristic
        if orig_lt > 30 and ship_mode == "Sea":
            opt_lt = int(orig_lt * 0.75) # 25% faster
            alt_route = "FastSea + Direct Customs Routing"
            savings_reason = "Consolidation at regional hub and pre-clearance customs agreements."
        elif orig_lt > 20 and ship_mode == "Air":
            opt_lt = orig_lt - 5
            alt_route = "Direct Charter flight instead of multi-hub cargo"
            savings_reason = "Eliminating layout transfers in intermediate ports."
        else:
            opt_lt = max(5, orig_lt - 2)
            alt_route = "Domestic/Regional express shipping"
            savings_reason = "Minor warehouse sorting optimization."
            
        total_original_time += orig_lt
        total_optimized_time += opt_lt
        
        # Flag bottlenecks
        if orig_lt >= 35:
            bottlenecks.append({
                "component": item["name"],
                "origin": origin,
                "current_time": orig_lt,
                "reason": "Congestion in primary marine straits and custom clearance delays at the border."
            })
            
        routes.append({
            "component": item["name"],
            "supplier": sname,
            "origin": origin,
            "destination": "Karachi, Pakistan (Marsa Hub)",
            "original_lead_time": orig_lt,
            "optimized_lead_time": opt_lt,
            "mode": ship_mode,
            "suggested_alternative_route": alt_route,
            "savings_reason": savings_reason
        })
        
    return {
        "routes": routes,
        "total_original_lead_time": total_original_time,
        "total_optimized_lead_time": total_optimized_time,
        "bottlenecks": bottlenecks
    }

def run_local_cost_optimization(bom: List[dict]) -> Dict:
    total_cost = sum(item["cost"] for item in bom)
    savings = 0
    suggestions = []
    
    for item in bom:
        cost = item["cost"]
        # Alternate sourcing suggestions
        if item["category"] == "Semiconductors":
            alt_sup = "Tokyo Micro-Systems"
            alt_cost = round(cost * 0.9, 2)
            alt_lt = item["lead_time"] + 5
            desc = "Sourcing alternative from Tokyo yields 10% unit savings, but extends shipping cycles slightly. Fits well for non-urgent production batches."
        elif item["category"] == "Displays":
            alt_sup = "PanelOptics Corp"
            alt_cost = round(cost * 0.88, 2)
            alt_lt = item["lead_time"]
            desc = "Switching to PanelOptics displays reduces cost by 12% with equivalent technical specs and identical lead times."
        elif item["category"] == "Energy":
            alt_sup = "Karachi Cell Tech (Local)"
            alt_cost = round(cost * 0.85, 2)
            alt_lt = 10
            desc = "Local battery manufacturer matches quality, cuts transport costs entirely, avoiding high import custom duties."
        else:
            alt_sup = "Generic Global Supplier"
            alt_cost = round(cost * 0.95, 2)
            alt_lt = item["lead_time"] - 2
            desc = "General vendor bidding optimization."
            
        savings += (cost - alt_cost)
        
        suggestions.append({
            "component": item["name"],
            "current_supplier": item["supplier"],
            "current_cost": cost,
            "alternative_supplier": alt_sup,
            "alternative_cost": alt_cost,
            "alternative_lead_time": alt_lt,
            "estimated_savings_percentage": round(((cost - alt_cost) / cost) * 100, 1),
            "recommendation": desc
        })
        
    return {
        "total_current_bom_cost": round(total_cost, 2),
        "total_optimized_bom_cost": round(total_cost - savings, 2),
        "estimated_savings": round(savings, 2),
        "suggestions": suggestions
    }

def run_local_demand_forecast(bom: List[dict]) -> Dict:
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # Base seasonal demand multiplier
    seasonality = [1.0, 0.95, 1.1, 1.05, 1.15, 1.2, 1.1, 1.0, 1.15, 1.3, 1.45, 1.5] # holiday spike in Q4
    
    # Calculate a baseline average demand of 5000 units/month
    base_demand = 5000
    monthly_forecast = [int(base_demand * mult) for mult in seasonality]
    
    stock_analysis = []
    for item in bom:
        daily_usage = base_demand / 30
        lead_time = item["lead_time"]
        
        # Calculations:
        # Safety Stock = Daily Usage * Lead Time * Z-score factor (usually 1.5 for 95% service level)
        safety_stock = int(daily_usage * 0.5 * lead_time)
        reorder_point = int((daily_usage * lead_time) + safety_stock)
        
        stock_analysis.append({
            "component": item["name"],
            "daily_demand": round(daily_usage, 1),
            "lead_time_days": lead_time,
            "recommended_safety_stock_units": safety_stock,
            "reorder_point_units": reorder_point,
            "stockout_risk_level": "High" if lead_time > 30 else ("Medium" if lead_time > 15 else "Low")
        })
        
    return {
        "forecast_period": "Next 12 Months",
        "monthly_demand": [{"month": m, "units": val} for m, val in zip(months, monthly_forecast)],
        "reorder_logic": stock_analysis,
        "forecasting_notes": "Demand exhibits standard Q4 seasonal holiday volume surges. Ensure pre-orders of lead-time critical semiconductor components by late July."
    }

def run_local_disruption_alerts(bom: List[dict]) -> List[dict]:
    origins = list(set(item["origin"] for item in bom))
    sample_alerts = [
        {"title": "Customs Port Backlog", "location": "Hsinchu, Taiwan", "impact": "High", "category": "Logistics", "details": "Customs clearance experiencing 5-day backlog due to regional IT updates. Electronics shipments delayed."},
        {"title": "Suez Canal Congestion", "location": "Suez, Egypt", "impact": "Medium", "category": "Shipping", "details": "Increased maritime freight traffic causing 48-hour routing queues for Sea shipments destined for Middle-East/Karachi."},
        {"title": "Shenzhen Super Typhoon Warning", "location": "Shenzhen, China", "impact": "High", "category": "Weather", "details": "Category 4 storm approaching the Guangdong coast. Port operations halted for 72 hours starting tomorrow."},
        {"title": "Vietnam Local Labor Shortage", "location": "Ho Chi Minh City, Vietnam", "impact": "Low", "category": "Production", "details": "Factory staffing levels lower by 8% due to agricultural harvesting season, impacting manufacturing throughput."},
        {"title": "Munich Cargo Strike", "location": "Munich, Germany", "impact": "Medium", "category": "Labor", "details": "Lufthansa cargo handlers announce a 24-hour warning strike. High-priority air-freight will face handling delays."}
    ]
    
    alerts = []
    # Match alerts with origins in the BOM
    for alert in sample_alerts:
        for orig in origins:
            if orig.split(",")[0].lower() in alert["location"].lower():
                alerts.append(alert)
                break
                
    # Add a generic global supply chain alert if list is small
    if not alerts:
        alerts.append({
            "title": "Global Container Shortage",
            "location": "Global Routes",
            "impact": "Medium",
            "category": "Equipment",
            "details": "Lack of empty 40ft containers at Asian manufacturing hubs is raising spot pricing by 12%."
        })
        
    return alerts

# ---------------------------------------------------------------------------
# LLM-Based Multi-Agent Execution (Runs when client is configured)
# ---------------------------------------------------------------------------

async def llm_agent_supplier_risk(client: AsyncOpenAI, bom: List[dict], suppliers: List[dict], progress: ProgressFn) -> List[dict]:
    await progress("risk", "🕵️ Supplier Risk Agent is querying international risk index...")
    
    prompt = f"""
    You are the Supplier Risk Assessment Agent.
    Evaluate the overall risk index for each component's supplier in the given Bill of Materials (BOM) and Supplier profiles.
    
    BOM Data:
    {json.dumps(bom, indent=2)}
    
    Supplier Profiles:
    {json.dumps(suppliers, indent=2)}
    
    Perform a multi-dimensional risk scoring (0-100 scale) for each component supplier, analyzing:
    1. Financial risk based on health rating.
    2. Geopolitical risk based on geographical origin and risk zones.
    3. Environmental, Social, and Governance (ESG) rating.
    
    Format the response as a valid JSON array of objects, with NO surrounding markdown or text, like this:
    [
      {{
        "component": "Component Name",
        "supplier": "Supplier Name",
        "origin": "Origin City/Country",
        "financial_health": "Health",
        "geopolitical_risk": "Risk Level",
        "esg_score": "ESG Score",
        "risk_score": 45.5,
        "risk_level": "Low/Medium/High",
        "analysis": "Brief 1-2 sentence detailed professional description of risk status."
      }}
    ]
    """
    
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        # Handle if the LLM wrapped it under a key
        if isinstance(data, dict):
            # Try to find list
            for key, val in data.items():
                if isinstance(val, list):
                    return val
            return list(data.values())[0] if data else run_local_risk_analysis(bom, suppliers)
        return data
    except Exception as e:
        await progress("risk", f"⚠️ LLM Error: {str(e)}. Switched to local heuristic risk modeling.")
        return run_local_risk_analysis(bom, suppliers)


async def llm_agent_lead_time_optimizer(client: AsyncOpenAI, bom: List[dict], suppliers: List[dict], progress: ProgressFn) -> Dict:
    await progress("leadtime", "🔀 Lead Time Optimizer Agent is calculating shipping routes to Karachi...")
    
    prompt = f"""
    You are the Lead Time Optimizer Agent.
    Your destination for all materials is Karachi, Pakistan (Marsa Hub).
    Analyze lead times and routes for the following components:
    
    BOM Data:
    {json.dumps(bom, indent=2)}
    
    Supplier Data:
    {json.dumps(suppliers, indent=2)}
    
    Your task:
    1. Calculate transit bottlenecks for components with high lead times.
    2. Suggest alternative logistics routes or transportation modes (e.g. Air, Sea, Rail).
    3. Generate optimized transit times.
    4. Provide the total original transit time and the optimized transit time.
    
    Format the response as a valid JSON object with NO surrounding markdown or text:
    {{
      "routes": [
        {{
          "component": "Component Name",
          "supplier": "Supplier Name",
          "origin": "Origin",
          "destination": "Karachi, Pakistan (Marsa Hub)",
          "original_lead_time": 45,
          "optimized_lead_time": 35,
          "mode": "Sea/Air/Land",
          "suggested_alternative_route": "Routing path",
          "savings_reason": "Why transit is shorter"
        }}
      ],
      "total_original_lead_time": 120,
      "total_optimized_lead_time": 95,
      "bottlenecks": [
        {{
          "component": "Component Name",
          "origin": "Origin",
          "current_time": 45,
          "reason": "Specific logistics roadblock description"
        }}
      ]
    }}
    """
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        await progress("leadtime", f"⚠️ LLM Error: {str(e)}. Switched to local heuristic routing optimizer.")
        return run_local_lead_time_optimization(bom, suppliers)


async def llm_agent_cost_reduction(client: AsyncOpenAI, bom: List[dict], progress: ProgressFn) -> Dict:
    await progress("cost", "💰 Cost Reduction Analyst Agent is evaluating component costs...")
    
    prompt = f"""
    You are the Cost Reduction Analyst Agent.
    Analyze the pricing of materials and suggest alternative sourcing opportunities, local manufacturing switches, or volume pricing deals.
    
    BOM Data:
    {json.dumps(bom, indent=2)}
    
    Your task:
    1. Identify parts that are expensive or have high shipping overhead.
    2. Propose alternate suppliers (e.g. local manufacturer in Karachi, Pakistan or major global distributor) with a lower cost.
    3. Estimate total savings and return a list of recommendations.
    
    Format the response as a valid JSON object with NO surrounding markdown or text:
    {{
      "total_current_bom_cost": 234.50,
      "total_optimized_bom_cost": 195.20,
      "estimated_savings": 39.30,
      "suggestions": [
        {{
          "component": "Component Name",
          "current_supplier": "Supplier A",
          "current_cost": 45.0,
          "alternative_supplier": "Supplier B (Local/Global alternative)",
          "alternative_cost": 38.0,
          "alternative_lead_time": 30,
          "estimated_savings_percentage": 15.5,
          "recommendation": "Brief rationale outlining cost benefits vs risks."
        }}
      ]
    }}
    """
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        await progress("cost", f"⚠️ LLM Error: {str(e)}. Switched to local cost heuristics.")
        return run_local_cost_optimization(bom)


async def llm_agent_demand_forecaster(client: AsyncOpenAI, bom: List[dict], progress: ProgressFn) -> Dict:
    await progress("demand", "📈 Demand Forecaster Agent is running seasonal demand simulations...")
    
    prompt = f"""
    You are the Demand Forecaster Agent.
    Run a demand forecast over the next 12 months for the product and establish reorder thresholds for components based on their lead times.
    
    BOM Data:
    {json.dumps(bom, indent=2)}
    
    Your task:
    1. Predict 12-month demand units (e.g., base production averages around 5,000 units/month, with seasonal shifts).
    2. Calculate Reorder Point and Safety Stock for each component.
       Formula context:
       - Safety Stock = Daily Usage * Safety Buffer Days
       - Reorder Point = (Daily Usage * Lead Time) + Safety Stock
    3. Gauge the stockout risk level (Low, Medium, High).
    
    Format the response as a valid JSON object with NO surrounding markdown or text:
    {{
      "forecast_period": "Next 12 Months",
      "monthly_demand": [
        {{"month": "Jan", "units": 5000}},
        {{"month": "Feb", "units": 4800}}
        // ... (12 months total)
      ],
      "reorder_logic": [
        {{
          "component": "Component Name",
          "daily_demand": 166.7,
          "lead_time_days": 30,
          "recommended_safety_stock_units": 2500,
          "reorder_point_units": 7500,
          "stockout_risk_level": "Low/Medium/High"
        }}
      ],
      "forecasting_notes": "Key seasonal takeaways or inventory management advice."
    }}
    """
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        await progress("demand", f"⚠️ LLM Error: {str(e)}. Switched to local seasonal forecasting model.")
        return run_local_demand_forecast(bom)


async def llm_agent_disruption_alerter(client: AsyncOpenAI, bom: List[dict], progress: ProgressFn) -> List[dict]:
    await progress("disruption", "🚨 Disruption Alert Agent is checking global maritime and geopolitical updates...")
    
    origins = [item["origin"] for item in bom]
    
    prompt = f"""
    You are the Disruption Alert Agent.
    Scan global news events (simulated real-time news) for regions matching the shipping origins of our supply chain parts:
    Origins to check: {', '.join(origins)}
    
    Identify any active supply chain threats (typhoons, port strikes, custom logjams, raw material embargoes) in those regions.
    For each issue:
    1. Title of disruption.
    2. Specific location.
    3. Impact level (Low, Medium, High).
    4. Category (Weather, Labor, Logistics, Geopolitical).
    5. Details of the event.
    
    Format the response as a valid JSON array of objects, with NO surrounding markdown or text:
    [
      {{
        "title": "Port Delay due to Typhoons",
        "location": "Shenzhen, China",
        "impact": "High",
        "category": "Weather",
        "details": "High winds and storm surge have closed container terminals for 3 days."
      }}
    ]
    """
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        if isinstance(data, dict):
            # Handle key nesting
            for key, val in data.items():
                if isinstance(val, list):
                    return val
            return list(data.values())[0] if data else run_local_disruption_alerts(bom)
        return data
    except Exception as e:
        await progress("disruption", f"⚠️ LLM Error: {str(e)}. Using local simulated news feeds.")
        return run_local_disruption_alerts(bom)


# ---------------------------------------------------------------------------
# Master Orchestration Class
# ---------------------------------------------------------------------------

class SupplyChainSystem:
    def __init__(self):
        pass

    async def run(
        self,
        product_name: str,
        bom: List[dict],
        suppliers: List[dict],
        progress: ProgressFn = _noop
    ) -> Dict[str, Any]:
        """Runs the 5-Agent Supply Chain Optimization Pipeline sequentially."""
        
        await progress("start", f"🚀 Initializing Supply Chain Optimization for '{product_name}'...")
        await asyncio.sleep(0.5)

        # 1. Supplier Risk Assessment
        if client:
            risk_report = await llm_agent_supplier_risk(client, bom, suppliers, progress)
        else:
            await progress("risk", "🕵️ Running Supplier Risk Assessment (Local Heuristics)...")
            await asyncio.sleep(0.8)
            risk_report = run_local_risk_analysis(bom, suppliers)
        
        # Calculate summary metrics for risk
        high_risk_count = sum(1 for r in risk_report if r.get("risk_level") == "High")
        avg_risk_score = round(sum(r.get("risk_score", 0) for r in risk_report) / len(risk_report), 1) if risk_report else 0
        await progress("risk_done", f"✅ Risk assessment complete. Avg Risk: {avg_risk_score}/100. Critical risks flagged: {high_risk_count}.")
        await asyncio.sleep(0.5)

        # 2. Lead Time Optimizer
        if client:
            lead_time_report = await llm_agent_lead_time_optimizer(client, bom, suppliers, progress)
        else:
            await progress("leadtime", "🔀 Running Lead Time Optimizer (Local Heuristics)...")
            await asyncio.sleep(0.8)
            lead_time_report = run_local_lead_time_optimization(bom, suppliers)
            
        orig_lt = lead_time_report.get("total_original_lead_time", 0)
        opt_lt = lead_time_report.get("total_optimized_lead_time", 0)
        lt_reduction = orig_lt - opt_lt
        await progress("leadtime_done", f"✅ Logistics routing optimized. Reduced total transit from {orig_lt} to {opt_lt} days (Saved {lt_reduction} days).")
        await asyncio.sleep(0.5)

        # 3. Cost Analyst
        if client:
            cost_report = await llm_agent_cost_reduction(client, bom, progress)
        else:
            await progress("cost", "💰 Running Cost Reduction Analyst (Local Heuristics)...")
            await asyncio.sleep(0.8)
            cost_report = run_local_cost_optimization(bom)
            
        savings = cost_report.get("estimated_savings", 0)
        await progress("cost_done", f"✅ Sourcing cost analysis complete. Identified ${savings} in potential BOM cost savings.")
        await asyncio.sleep(0.5)

        # 4. Demand Forecaster
        if client:
            demand_report = await llm_agent_demand_forecaster(client, bom, progress)
        else:
            await progress("demand", "📈 Running Demand Forecaster (Local Heuristics)...")
            await asyncio.sleep(0.8)
            demand_report = run_local_demand_forecast(bom)
            
        await progress("demand_done", "✅ Monthly demand projections and stock reorder triggers generated.")
        await asyncio.sleep(0.5)

        # 5. Disruption Alerts
        if client:
            alerts_report = await llm_agent_disruption_alerter(client, bom, progress)
        else:
            await progress("disruption", "🚨 Running Disruption Alert Monitor (Local Heuristics)...")
            await asyncio.sleep(0.8)
            alerts_report = run_local_disruption_alerts(bom)
            
        alert_count = len(alerts_report)
        await progress("disruption_done", f"✅ Scan complete. Found {alert_count} active geopolitical/weather warnings in logistics network.")
        await asyncio.sleep(0.5)

        await progress("finish", "🎉 Supply Chain optimization matrix successfully generated!")
        
        return {
            "metadata": {
                "product_name": product_name,
                "timestamp": asyncio.get_event_loop().time(),
                "agent_model": MODEL if client else "Local Heuristics Engine",
                "risk_summary": {
                    "average_score": avg_risk_score,
                    "critical_threats": high_risk_count
                },
                "logistics_summary": {
                    "original_days": orig_lt,
                    "optimized_days": opt_lt,
                    "savings_days": lt_reduction
                },
                "financial_summary": {
                    "original_cost": cost_report.get("total_current_bom_cost", 0),
                    "optimized_cost": cost_report.get("total_optimized_bom_cost", 0),
                    "potential_savings": savings
                }
            },
            "risk_analysis": risk_report,
            "routing_optimization": lead_time_report,
            "cost_reduction": cost_report,
            "demand_forecast": demand_report,
            "disruption_alerts": alerts_report,
            "original_bom": bom,
            "original_suppliers": suppliers
        }
