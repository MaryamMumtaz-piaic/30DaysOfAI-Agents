// Marsa Supply Chain Intelligence App Logic - Day 17

// Global industry data presets (fallback in case API fails)
const LOCAL_PRESETS = {
  smartphone: {
    product_name: "QuantumX Smartphone",
    bom: [
      { id: "comp-1", name: "5G Snapdragon Processor", category: "Semiconductors", supplier: "Silicon Systems", cost: 45.00, lead_time: 45, origin: "Hsinchu, Taiwan" },
      { id: "comp-2", name: "AMOLED Display Module", category: "Displays", supplier: "DisplayTech Ltd", cost: 30.00, lead_time: 25, origin: "Seoul, South Korea" },
      { id: "comp-3", name: "4500mAh Li-Polymer Battery", category: "Energy", supplier: "NeXus Power", cost: 15.00, lead_time: 30, origin: "Shenzhen, China" },
      { id: "comp-4", name: "Chassis & Aluminum Enclosure", category: "Mechanical", supplier: "AluFab Corp", cost: 12.00, lead_time: 15, origin: "Ho Chi Minh City, Vietnam" },
      { id: "comp-5", name: "Camera Array (Sony Sensor)", category: "Optics", supplier: "OptoSens GmbH", cost: 22.00, lead_time: 20, origin: "Munich, Germany" }
    ],
    suppliers: [
      { name: "Silicon Systems", financial_health: "Excellent", geopolitical_risk: "High", esg_score: "A", shipping_method: "Air" },
      { name: "DisplayTech Ltd", financial_health: "Good", geopolitical_risk: "Medium", esg_score: "B", shipping_method: "Sea" },
      { name: "NeXus Power", financial_health: "Fair", geopolitical_risk: "Medium", esg_score: "B", shipping_method: "Sea" },
      { name: "AluFab Corp", financial_health: "Good", geopolitical_risk: "Low", esg_score: "C", shipping_method: "Sea" },
      { name: "OptoSens GmbH", financial_health: "Excellent", geopolitical_risk: "Low", esg_score: "A", shipping_method: "Air" }
    ]
  },
  solar: {
    product_name: "SolarMax PV Inverter",
    bom: [
      { id: "comp-1", name: "IGBT Power Transistors", category: "Semiconductors", supplier: "Semicon Alps", cost: 120.00, lead_time: 60, origin: "Kyoto, Japan" },
      { id: "comp-2", name: "Toroidal Copper Transformer", category: "Electromechanical", supplier: "Inductors Inc", cost: 85.00, lead_time: 30, origin: "Monterrey, Mexico" },
      { id: "comp-3", name: "Control Board (PCB Assembly)", category: "Electronics", supplier: "CircuitBoards Co", cost: 45.00, lead_time: 25, origin: "Guangzhou, China" },
      { id: "comp-4", name: "IP65 Weatherproof Enclosure", category: "Mechanical", supplier: "EuroSteel Ltd", cost: 60.00, lead_time: 20, origin: "Gdansk, Poland" }
    ],
    suppliers: [
      { name: "Semicon Alps", financial_health: "Good", geopolitical_risk: "Low", esg_score: "A", shipping_method: "Air" },
      { name: "Inductors Inc", financial_health: "Fair", geopolitical_risk: "Low", esg_score: "B", shipping_method: "Land" },
      { name: "CircuitBoards Co", financial_health: "Fair", geopolitical_risk: "Medium", esg_score: "C", shipping_method: "Sea" },
      { name: "EuroSteel Ltd", financial_health: "Good", geopolitical_risk: "Low", esg_score: "B", shipping_method: "Land" }
    ]
  },
  automotive: {
    product_name: "Apex EV Motor Controller",
    bom: [
      { id: "comp-1", name: "Silicon Carbide MOSFETs", category: "Power Electronics", supplier: "PowerChips", cost: 210.00, lead_time: 75, origin: "Austin, USA" },
      { id: "comp-2", name: "Liquid Cooling Plate", category: "Thermal", supplier: "CoolRun Tech", cost: 65.00, lead_time: 20, origin: "Chennai, India" },
      { id: "comp-3", name: "Neodymium Magnet Rotor", category: "Magnets", supplier: "RareEarth Supply", cost: 140.00, lead_time: 40, origin: "Baotou, China" },
      { id: "comp-4", name: "Wiring Harness & Connectors", category: "Wiring", supplier: "Connex Group", cost: 35.00, lead_time: 15, origin: "Juarez, Mexico" }
    ],
    suppliers: [
      { name: "PowerChips", financial_health: "Excellent", geopolitical_risk: "Low", esg_score: "A", shipping_method: "Air" },
      { name: "CoolRun Tech", financial_health: "Good", geopolitical_risk: "Medium", esg_score: "B", shipping_method: "Sea" },
      { name: "RareEarth Supply", financial_health: "Good", geopolitical_risk: "High", esg_score: "C", shipping_method: "Sea" },
      { name: "Connex Group", financial_health: "Excellent", geopolitical_risk: "Low", esg_score: "B", shipping_method: "Land" }
    ]
  }
};

// Origin coordinate mapping (For plotting nodes on SVG layout map)
const ORIGIN_COORDS = {
  "karachi, pakistan": { x: 400, y: 280, label: "Marsa Assembly Hub (Karachi, PK)" },
  "hsinchu, taiwan": { x: 670, y: 150, label: "Hsinchu, TW" },
  "seoul, south korea": { x: 720, y: 80, label: "Seoul, KR" },
  "shenzhen, china": { x: 620, y: 170, label: "Shenzhen, CN" },
  "ho chi minh city, vietnam": { x: 630, y: 220, label: "Ho Chi Minh, VN" },
  "munich, germany": { x: 200, y: 70, label: "Munich, DE" },
  "kyoto, japan": { x: 740, y: 110, label: "Kyoto, JP" },
  "monterrey, mexico": { x: 90, y: 190, label: "Monterrey, MX" },
  "guangzhou, china": { x: 610, y: 160, label: "Guangzhou, CN" },
  "gdansk, poland": { x: 220, y: 50, label: "Gdansk, PL" },
  "austin, usa": { x: 70, y: 160, label: "Austin, US" },
  "chennai, india": { x: 470, y: 310, label: "Chennai, IN" },
  "baotou, china": { x: 570, y: 110, label: "Baotou, CN" },
  "juarez, mexico": { x: 80, y: 180, label: "Juarez, MX" }
};

// Initial state load
window.addEventListener("DOMContentLoaded", () => {
  // Try to fetch presets from server, otherwise load local
  fetch("/presets")
    .then(res => res.json())
    .then(data => {
      window.presets = data;
      loadPreset("smartphone");
    })
    .catch(() => {
      window.presets = LOCAL_PRESETS;
      loadPreset("smartphone");
    });
});

// Load Sourcing Industry Preset
function loadPreset(key) {
  const preset = window.presets ? window.presets[key] : LOCAL_PRESETS[key];
  if (!preset) return;

  // Set product name
  document.getElementById("product-name").value = preset.product_name;

  // Set active preset button styling
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.classList.remove("active");
    if (btn.innerText.toLowerCase().includes(key.substring(0, 3))) {
      btn.classList.add("active");
    }
  });

  // Re-build BOM list editor
  const bomContainer = document.getElementById("bom-list-editor");
  bomContainer.innerHTML = "";
  preset.bom.forEach(item => {
    bomContainer.appendChild(createBomRowHTML(item));
  });

  // Re-build Supplier list editor
  const supplierContainer = document.getElementById("supplier-list-editor");
  supplierContainer.innerHTML = "";
  preset.suppliers.forEach(sup => {
    supplierContainer.appendChild(createSupplierRowHTML(sup));
  });
  
  // Clear any existing graphs
  clearNetworkSVG();
}

// ---------------------------------------------------------------------------
// BOM Editor Elements
// ---------------------------------------------------------------------------
function createBomRowHTML(item = {}) {
  const row = document.createElement("div");
  row.className = "list-item-row bom-item-row";
  
  row.innerHTML = `
    <input type="text" placeholder="Component Name" class="bom-name" value="${item.name || ''}" required>
    <input type="number" placeholder="Cost ($)" class="bom-cost" value="${item.cost || ''}" style="width:100%" step="0.01" required>
    <input type="number" placeholder="Lead Time (days)" class="bom-lt" value="${item.lead_time || ''}" style="width:100%" required>
    <button class="delete-btn" onclick="this.parentElement.remove(); checkListsEmpty();" title="Remove row">×</button>
    <div style="grid-column: span 4; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.2rem; margin-top: 0.15rem;">
      <input type="text" placeholder="Category" class="bom-category" value="${item.category || ''}">
      <input type="text" placeholder="Supplier Assigned" class="bom-supplier" value="${item.supplier || ''}" required>
      <input type="text" placeholder="Sourcing Origin (e.g. Shenzhen, China)" class="bom-origin" value="${item.origin || ''}" required>
    </div>
  `;
  return row;
}

function addBomRow() {
  const container = document.getElementById("bom-list-editor");
  container.appendChild(createBomRowHTML());
}

// ---------------------------------------------------------------------------
// Supplier Editor Elements
// ---------------------------------------------------------------------------
function createSupplierRowHTML(sup = {}) {
  const row = document.createElement("div");
  row.className = "list-item-row supplier-item-row";
  
  const fh = sup.financial_health || "Good";
  const gp = sup.geopolitical_risk || "Low";
  const esg = sup.esg_score || "B";
  const mode = sup.shipping_method || "Sea";

  row.innerHTML = `
    <input type="text" placeholder="Supplier Name" class="sup-name" value="${sup.name || ''}" required>
    <select class="sup-fh" title="Financial Health">
      <option value="Excellent" ${fh === 'Excellent' ? 'selected' : ''}>Fin: Excellent</option>
      <option value="Good" ${fh === 'Good' ? 'selected' : ''}>Fin: Good</option>
      <option value="Fair" ${fh === 'Fair' ? 'selected' : ''}>Fin: Fair</option>
      <option value="Poor" ${fh === 'Poor' ? 'selected' : ''}>Fin: Poor</option>
    </select>
    <select class="sup-gp" title="Geopolitical Risk">
      <option value="Low" ${gp === 'Low' ? 'selected' : ''}>Geo: Low Risk</option>
      <option value="Medium" ${gp === 'Medium' ? 'selected' : ''}>Geo: Med Risk</option>
      <option value="High" ${gp === 'High' ? 'selected' : ''}>Geo: High Risk</option>
    </select>
    <button class="delete-btn" onclick="this.parentElement.remove(); checkListsEmpty();" title="Remove row">×</button>
    <div style="grid-column: span 4; display: grid; grid-template-columns: 1fr 1fr; gap: 0.2rem; margin-top: 0.15rem;">
      <select class="sup-esg" title="ESG Score">
        <option value="A" ${esg === 'A' ? 'selected' : ''}>ESG Rating: A</option>
        <option value="B" ${esg === 'B' ? 'selected' : ''}>ESG Rating: B</option>
        <option value="C" ${esg === 'C' ? 'selected' : ''}>ESG Rating: C</option>
      </select>
      <select class="sup-mode" title="Logistics Mode">
        <option value="Sea" ${mode === 'Sea' ? 'selected' : ''}>Shipping: Sea Cargo</option>
        <option value="Air" ${mode === 'Air' ? 'selected' : ''}>Shipping: Air Freight</option>
        <option value="Land" ${mode === 'Land' ? 'selected' : ''}>Shipping: Overland</option>
      </select>
    </div>
  `;
  return row;
}

function addSupplierRow() {
  const container = document.getElementById("supplier-list-editor");
  container.appendChild(createSupplierRowHTML());
}

function checkListsEmpty() {
  // Standard check to ensure clean styles when empty
}

// ---------------------------------------------------------------------------
// SVG Network Map Rendering
// ---------------------------------------------------------------------------
function clearNetworkSVG() {
  const svg = document.getElementById("network-svg");
  svg.innerHTML = "";
  document.getElementById("map-placeholder").style.display = "flex";
}

function plotSupplyChainNetwork(bom, riskReport, routingReport) {
  document.getElementById("map-placeholder").style.display = "none";
  const svg = document.getElementById("network-svg");
  svg.innerHTML = ""; // reset

  // Create defs for arrow marker and gradients
  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#94a3b8" />
    </marker>
    <radialGradient id="glow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#818cf8" stop-opacity="0.15" />
      <stop offset="100%" stop-color="#818cf8" stop-opacity="0" />
    </radialGradient>
  `;
  svg.appendChild(defs);

  const kNode = ORIGIN_COORDS["karachi, pakistan"];
  
  // Track node coordinates
  const nodes = {
    "karachi": { ...kNode, id: "karachi", isHub: true }
  };

  // Compile supplier nodes
  bom.forEach((item, index) => {
    const originKey = item.origin.toLowerCase();
    
    // Find pre-set coordinate or generate random city coords on boundary
    let coord = null;
    for (const key in ORIGIN_COORDS) {
      if (originKey.includes(key.split(",")[0])) {
        coord = ORIGIN_COORDS[key];
        break;
      }
    }
    
    if (!coord) {
      // Procedural generation coordinates if custom city is added
      const angle = (index / bom.length) * Math.PI * 2;
      coord = {
        x: Math.round(400 + Math.cos(angle) * 250),
        y: Math.round(200 + Math.sin(angle) * 120),
        label: item.origin
      };
    }

    const nId = `node-${index}`;
    nodes[nId] = {
      id: nId,
      name: item.supplier,
      origin: item.origin,
      component: item.name,
      x: coord.x,
      y: coord.y,
      label: coord.label,
      isHub: false
    };
  });

  // Render Connections first (underneath nodes)
  Object.keys(nodes).forEach(key => {
    const node = nodes[key];
    if (node.isHub) return;

    // Retrieve risk scoring details for color coding link
    const rInfo = riskReport.find(r => r.component === node.component);
    const score = rInfo ? rInfo.risk_score : 50;
    
    // Line coloring based on risk Index
    let linkColor = "var(--success)";
    if (score >= 65) {
      linkColor = "var(--danger)";
    } else if (score >= 35) {
      linkColor = "var(--warning)";
    }

    // Curved SVG Path calculation
    const dx = kNode.x - node.x;
    const dy = kNode.y - node.y;
    const dr = Math.sqrt(dx * dx + dy * dy) * 1.2; // curve radius multiplier
    
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", `M ${node.x} ${node.y} A ${dr} ${dr} 0 0 1 ${kNode.x} ${kNode.y}`);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", linkColor);
    path.setAttribute("stroke-width", "2");
    path.setAttribute("opacity", "0.65");
    path.setAttribute("class", "link");
    path.setAttribute("marker-end", "url(#arrow)");
    
    // Speed of dashes depends on transit times computed by Lead Time optimizer
    const rtInfo = routingReport.routes.find(r => r.component === node.component);
    const days = rtInfo ? rtInfo.optimized_lead_time : 30;
    const speed = Math.max(10, days * 0.8);
    path.style.animationDuration = `${speed}s`;

    svg.appendChild(path);
  });

  // Render Nodes
  Object.keys(nodes).forEach(key => {
    const node = nodes[key];

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("class", "node");
    
    // Attach details mapping tooltip popup
    g.addEventListener("mouseenter", (e) => showTooltip(e, node, riskReport, routingReport));
    g.addEventListener("mousemove", moveTooltip);
    g.addEventListener("mouseleave", hideTooltip);

    if (node.isHub) {
      // Draw Karachi Marsa Hub indicator (larger node with radar glow ring)
      const glow = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      glow.setAttribute("cx", node.x);
      glow.setAttribute("cy", node.y);
      glow.setAttribute("r", "24");
      glow.setAttribute("fill", "url(#glow)");
      g.appendChild(glow);

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", "9");
      circle.setAttribute("fill", "var(--primary)");
      circle.setAttribute("stroke", "#ffffff");
      circle.setAttribute("stroke-width", "2");
      g.appendChild(circle);
      
      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", node.x);
      label.setAttribute("y", node.y + 24);
      label.setAttribute("class", "node-label");
      label.setAttribute("font-weight", "800");
      label.textContent = "Marsa Hub (Karachi)";
      g.appendChild(label);
    } else {
      // Standard Supplier Circle
      const rInfo = riskReport.find(r => r.component === node.component);
      const score = rInfo ? rInfo.risk_score : 50;
      let nodeColor = "var(--success)";
      if (score >= 65) nodeColor = "var(--danger)";
      else if (score >= 35) nodeColor = "var(--warning)";

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", node.x);
      circle.setAttribute("cy", node.y);
      circle.setAttribute("r", "7");
      circle.setAttribute("fill", nodeColor);
      circle.setAttribute("stroke", "#ffffff");
      circle.setAttribute("stroke-width", "2");
      g.appendChild(circle);

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("x", node.x);
      label.setAttribute("y", node.y - 12);
      label.setAttribute("class", "node-label");
      
      // Short label city name
      const city = node.origin.split(",")[0];
      label.textContent = city;
      g.appendChild(label);
    }

    svg.appendChild(g);
  });
}

// ---------------------------------------------------------------------------
// SVG Interactive Tooltips
// ---------------------------------------------------------------------------
function showTooltip(event, node, riskReport, routingReport) {
  const tt = document.getElementById("map-tooltip");
  
  if (node.isHub) {
    tt.innerHTML = `
      <div style="font-weight:700; color:var(--primary); margin-bottom: 2px;">Marsa Sourcing Hub</div>
      <div><b>Location:</b> Karachi, Pakistan</div>
      <div>Primary assembly plant & distribution terminal.</div>
    `;
  } else {
    const rInfo = riskReport.find(r => r.component === node.component);
    const rtInfo = routingReport.routes.find(r => r.component === node.component);
    
    tt.innerHTML = `
      <div style="font-weight:700; color:var(--primary); margin-bottom: 2px;">${node.name}</div>
      <div><b>Component:</b> ${node.component}</div>
      <div><b>Origin:</b> ${node.origin}</div>
      <div><b>Transit Method:</b> ${rtInfo ? rtInfo.mode : 'Sea'}</div>
      <div><b>Risk Index:</b> <span class="risk-tag ${rInfo.risk_level.toLowerCase()}" style="font-size:9px; padding:1px 3px;">${rInfo ? rInfo.risk_score : '--'} (${rInfo ? rInfo.risk_level : '--'})</span></div>
      <div style="margin-top:4px; font-size:10px; color:#94a3b8; border-top:1px solid #334155; padding-top:4px;">
        ${rInfo ? rInfo.analysis : ''}
      </div>
    `;
  }
  tt.style.display = "block";
  moveTooltip(event);
}

function moveTooltip(event) {
  const tt = document.getElementById("map-tooltip");
  const container = document.querySelector(".map-container");
  const bounds = container.getBoundingClientRect();
  
  // Calculate relative coordinates inside map card
  const x = event.clientX - bounds.left + 15;
  const y = event.clientY - bounds.top + 15;
  
  tt.style.left = `${x}px`;
  tt.style.top = `${y}px`;
}

function hideTooltip() {
  document.getElementById("map-tooltip").style.display = "none";
}

// ---------------------------------------------------------------------------
// Execution triggers & WebSocket Pipe
// ---------------------------------------------------------------------------
function triggerOptimization() {
  const pName = document.getElementById("product-name").value.trim();
  
  // Gather BOM list data
  const bomRows = document.querySelectorAll(".bom-item-row");
  const bomList = [];
  bomRows.forEach((row, i) => {
    bomList.push({
      id: `comp-${i+1}`,
      name: row.querySelector(".bom-name").value.trim(),
      cost: parseFloat(row.querySelector(".bom-cost").value) || 0,
      lead_time: parseInt(row.querySelector(".bom-lt").value) || 0,
      category: row.querySelector(".bom-category").value.trim(),
      supplier: row.querySelector(".bom-supplier").value.trim(),
      origin: row.querySelector(".bom-origin").value.trim()
    });
  });

  // Gather Supplier profiles
  const supRows = document.querySelectorAll(".supplier-item-row");
  const supplierList = [];
  supRows.forEach(row => {
    supplierList.push({
      name: row.querySelector(".sup-name").value.trim(),
      financial_health: row.querySelector(".sup-fh").value,
      geopolitical_risk: row.querySelector(".sup-gp").value,
      esg_score: row.querySelector(".sup-esg").value,
      shipping_method: row.querySelector(".sup-mode").value
    });
  });

  // Quick inputs validation
  if (!pName || bomList.length === 0 || supplierList.length === 0) {
    alert("Please check that Product Name, BOM items and Suppliers have all details filled!");
    return;
  }

  // UI state change
  const runBtn = document.getElementById("run-btn");
  runBtn.disabled = true;
  runBtn.innerText = "Running Sourcing Agents...";
  
  const consoleBadge = document.getElementById("terminal-badge");
  consoleBadge.innerText = "Processing";
  consoleBadge.style.color = "var(--warning)";

  const consoleLog = document.getElementById("log-console");
  consoleLog.innerHTML = ""; // Reset logs
  appendConsoleLog("start", "🔌 Connecting to Marsa Sourcing Agent Hub WebSocket...");

  const loader = document.getElementById("ws-loader");
  loader.style.display = "flex";

  // Hide older dashboard until pipeline completes
  document.getElementById("results-dashboard").style.display = "none";
  clearNetworkSVG();

  // Create WebSocket Connection
  // Handles deployment environments dynamically (supporting ws/wss)
  const loc = window.location;
  const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${wsProto}//${loc.host}/ws/optimize`;
  
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    appendConsoleLog("start", "🌐 Connection open. Transmission payload initiated...");
    ws.send(JSON.stringify({
      product_name: pName,
      bom: bomList,
      suppliers: supplierList
    }));
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    
    if (msg.type === "progress") {
      appendConsoleLog(msg.stage, msg.message);
    } 
    else if (msg.type === "result") {
      appendConsoleLog("finish", "🏁 Optimization pipeline complete. Processing dashboard graphics...");
      renderDashboardResults(msg.data, msg.job_id, bomList);
      
      // Plot SVG Network
      plotSupplyChainNetwork(bomList, msg.data.risk_analysis, msg.data.routing_optimization);
      
      closePipeline();
    } 
    else if (msg.type === "error") {
      appendConsoleLog("disruption", `❌ WebSocket Error: ${msg.message}`);
      closePipeline(true);
    }
  };

  ws.onerror = (err) => {
    appendConsoleLog("disruption", "❌ Connection dropped unexpectedly. Routing failure.");
    closePipeline(true);
  };

  ws.onclose = () => {
    // console connection closed
  };

  function closePipeline(hasError = false) {
    runBtn.disabled = false;
    runBtn.innerText = "Run Sourcing Optimizer";
    loader.style.display = "none";
    
    if (hasError) {
      consoleBadge.innerText = "Error";
      consoleBadge.style.color = "var(--danger)";
    } else {
      consoleBadge.innerText = "Success";
      consoleBadge.style.color = "var(--success)";
    }
  }
}

function appendConsoleLog(stage, msg) {
  const consoleLog = document.getElementById("log-console");
  const div = document.createElement("div");
  div.className = `log-entry stage-${stage}`;
  div.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
  consoleLog.appendChild(div);
  consoleLog.scrollTop = consoleLog.scrollHeight;
}

// ---------------------------------------------------------------------------
// Render outputs on Sourcing Dashboard
// ---------------------------------------------------------------------------
function renderDashboardResults(data, jobId, originalBom) {
  document.getElementById("results-dashboard").style.display = "block";
  
  // Set Download PDF Link
  const pdfBtn = document.getElementById("pdf-download-btn");
  pdfBtn.onclick = () => {
    window.location.href = `/report/${jobId}.pdf`;
  };

  // KPIs
  const meta = data.metadata;
  document.getElementById("kpi-risk-index").innerText = `${meta.risk_summary.average_score}/100`;
  
  // Risk Index KPI rating badge
  const rIndexBadge = document.getElementById("kpi-risk-change");
  rIndexBadge.className = "kpi-change";
  if (meta.risk_summary.average_score < 35) {
    rIndexBadge.innerText = "Low Overall Risk";
    rIndexBadge.classList.add("positive");
  } else if (meta.risk_summary.average_score < 65) {
    rIndexBadge.innerText = "Moderate Risk Profile";
    rIndexBadge.classList.add("warning");
  } else {
    rIndexBadge.innerText = "Critical Sourcing Risk";
    rIndexBadge.classList.add("danger");
  }

  document.getElementById("kpi-lead-time").innerText = `${meta.logistics_summary.optimized_days} Days`;
  document.getElementById("kpi-lead-saved").innerText = `-${meta.logistics_summary.savings_days} Days Saved`;
  
  document.getElementById("kpi-savings").innerText = `$${meta.financial_summary.potential_savings.toFixed(2)}`;
  
  const savedPct = (meta.financial_summary.potential_savings / meta.financial_summary.original_cost) * 100;
  document.getElementById("kpi-savings-pct").innerText = `${savedPct.toFixed(1)}% Saved`;
  
  document.getElementById("kpi-bom-cost").innerText = `$${meta.financial_summary.optimized_cost.toFixed(2)}`;
  document.getElementById("kpi-bom-change").innerText = `Was $${meta.financial_summary.original_cost.toFixed(2)}`;

  // Tab 1 Table: Supplier Risk
  const riskBody = document.getElementById("risk-table-body");
  riskBody.innerHTML = "";
  data.risk_analysis.forEach(r => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><b>${r.component}</b></td>
      <td>${r.supplier}</td>
      <td>${r.origin}</td>
      <td>${r.financial_health}</td>
      <td>${r.geopolitical_risk}</td>
      <td>${r.esg_score}</td>
      <td><b>${r.risk_score}</b></td>
      <td><span class="risk-tag ${r.risk_level.toLowerCase()}">${r.risk_level}</span></td>
    `;
    riskBody.appendChild(row);
  });

  // Tab 2 Table: Sourcing Routing
  const routingBody = document.getElementById("routing-table-body");
  routingBody.innerHTML = "";
  data.routing_optimization.routes.forEach(rt => {
    const row = document.createElement("tr");
    const diff = rt.original_lead_time - rt.optimized_lead_time;
    row.innerHTML = `
      <td><b>${rt.component}</b></td>
      <td>${rt.supplier}</td>
      <td>${rt.origin}</td>
      <td>${rt.mode}</td>
      <td>${rt.original_lead_time} Days</td>
      <td><b>${rt.optimized_lead_time} Days</b></td>
      <td><font color="var(--success)"><b>-${diff} Days:</b></font> ${rt.suggested_alternative_route} (${rt.savings_reason})</td>
    `;
    routingBody.appendChild(row);
  });

  // Tab 3 Table: Sourcing Cost Analyst
  const costBody = document.getElementById("cost-table-body");
  costBody.innerHTML = "";
  data.cost_reduction.suggestions.forEach(c => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><b>${c.component}</b></td>
      <td>${c.current_supplier} ($${c.current_cost.toFixed(2)})</td>
      <td>${c.alternative_supplier}</td>
      <td><b>$${c.alternative_cost.toFixed(2)}</b></td>
      <td><font color="var(--success)"><b>-${c.estimated_savings_percentage}%</b></font></td>
      <td>${c.recommendation}</td>
    `;
    costBody.appendChild(row);
  });

  // Tab 4 Table: Reorder Triggers
  const demandBody = document.getElementById("demand-table-body");
  demandBody.innerHTML = "";
  data.demand_forecast.reorder_logic.forEach(rl => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><b>${rl.component}</b></td>
      <td>${rl.recommended_safety_stock_units.toLocaleString()} units</td>
      <td><span style="font-weight:700; color:var(--primary)">${rl.reorder_point_units.toLocaleString()} units</span></td>
    `;
    demandBody.appendChild(row);
  });
  
  // Set Strategy Note
  document.getElementById("demand-forecast-strategy-note").innerText = data.demand_forecast.forecasting_notes;

  // Render Tab 4 Chart (Forecasting Canvas)
  renderForecastingChart(data.demand_forecast.monthly_demand);

  // Tab 5 List: Disruption Alerts
  const alertContainer = document.getElementById("disruption-list");
  alertContainer.innerHTML = "";
  if (data.disruption_alerts.length === 0) {
    alertContainer.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--success); font-weight:600;">✅ No active sourcing disruptions found in these corridors.</div>`;
  } else {
    data.disruption_alerts.forEach(a => {
      const card = document.createElement("div");
      card.className = `alert-banner ${a.impact.toLowerCase()}-impact`;
      card.innerHTML = `
        <div class="alert-banner-header">
          <span>🚨 ${a.title} (${a.location})</span>
          <span>${a.impact} Severity</span>
        </div>
        <div class="alert-desc">
          <b>Category:</b> ${a.category} | ${a.details}
        </div>
      `;
      alertContainer.appendChild(card);
    });
  }
}

// ---------------------------------------------------------------------------
// Custom Canvas Line Chart Renderer (Self-contained, zero-CDNs)
// ---------------------------------------------------------------------------
function renderForecastingChart(monthlyDemand) {
  const canvas = document.getElementById("demand-chart");
  const ctx = canvas.getContext("2d");

  // Reset resolution handling HighDPI displays
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);

  const width = rect.width;
  const height = rect.height;
  const padding = { top: 20, right: 20, bottom: 30, left: 45 };

  // Clear canvas
  ctx.clearRect(0, 0, width, height);

  // Min-Max values calculation
  const units = monthlyDemand.map(d => d.units);
  const maxVal = Math.max(...units) * 1.15;
  const minVal = Math.min(...units) * 0.85;

  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Grid Lines & Y Labels
  const gridSteps = 5;
  ctx.strokeStyle = "var(--border-color)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "var(--text-muted)";
  ctx.font = "10px Inter, sans-serif";
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";

  for (let i = 0; i <= gridSteps; i++) {
    const val = minVal + (maxVal - minVal) * (i / gridSteps);
    const y = padding.top + chartHeight - (chartHeight * (i / gridSteps));
    
    // Draw gridline
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();

    // Draw label
    ctx.fillText(Math.round(val).toLocaleString(), padding.left - 8, y);
  }

  // Draw X axis months
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  const stepX = chartWidth / (monthlyDemand.length - 1);

  monthlyDemand.forEach((item, index) => {
    const x = padding.left + index * stepX;
    const y = height - padding.bottom + 8;
    ctx.fillText(item.month, x, y);
  });

  // Calculate plotting paths coordinates
  const coords = monthlyDemand.map((item, index) => {
    const x = padding.left + index * stepX;
    const y = padding.top + chartHeight - (chartHeight * ((item.units - minVal) / (maxVal - minVal)));
    return { x, y };
  });

  // Render Area Gradient
  const grad = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
  grad.addColorStop(0, "rgba(79, 70, 229, 0.25)");
  grad.addColorStop(1, "rgba(79, 70, 229, 0.0)");

  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(coords[0].x, height - padding.bottom);
  coords.forEach(pt => ctx.lineTo(pt.x, pt.y));
  ctx.lineTo(coords[coords.length - 1].x, height - padding.bottom);
  ctx.closePath();
  ctx.fill();

  // Draw Line
  ctx.strokeStyle = "var(--primary)";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.moveTo(coords[0].x, coords[0].y);
  for (let i = 1; i < coords.length; i++) {
    ctx.lineTo(coords[i].x, coords[i].y);
  }
  ctx.stroke();

  // Draw circles at data indexes
  coords.forEach((pt, index) => {
    ctx.fillStyle = "var(--primary)";
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, 2, 0, Math.PI * 2);
    ctx.fill();
  });
}

// ---------------------------------------------------------------------------
// Tab Navigation Actions
// ---------------------------------------------------------------------------
function switchTab(event, tabId) {
  // Hide all contents
  const contents = document.querySelectorAll(".tab-content");
  contents.forEach(el => el.classList.remove("active"));

  // De-activate tab triggers styling
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach(el => el.classList.remove("active"));

  // Show selected content and activate tab button styling
  document.getElementById(tabId).classList.add("active");
  event.currentTarget.classList.add("active");
}
