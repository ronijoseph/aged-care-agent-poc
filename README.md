# aged-care-agent-poc
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Aged Care Intake Agent — Product Spec</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root {
--sage: #4a7c59;
--sage-light: #d4e6da;
--sage-pale: #f0f7f2;
--charcoal: #1c2b22;
--stone: #8a9b8e;
--cream: #faf9f6;
--amber: #c9822a;
--red: #c0392b;
--blue: #2c5f8a;
--border: #d0dbd3;
}

- { margin: 0; padding: 0; box-sizing: border-box; }

body {
font-family: 'DM Sans', sans-serif;
background: var(--cream);
color: var(--charcoal);
font-size: 13px;
line-height: 1.6;
print-color-adjust: exact;
-webkit-print-color-adjust: exact;
}

.page {
width: 210mm;
min-height: 297mm;
margin: 0 auto;
padding: 14mm 16mm 14mm 16mm;
background: white;
box-shadow: 0 4px 40px rgba(0,0,0,0.08);
}

/* ── HEADER ── */
header {
display: grid;
grid-template-columns: 1fr auto;
align-items: start;
border-bottom: 2.5px solid var(--sage);
padding-bottom: 10px;
margin-bottom: 14px;
}
.doc-label {
font-family: 'DM Mono', monospace;
font-size: 9px;
letter-spacing: 0.12em;
color: var(--stone);
text-transform: uppercase;
margin-bottom: 4px;
}
h1 {
font-family: 'DM Serif Display', serif;
font-size: 22px;
color: var(--charcoal);
line-height: 1.15;
}
h1 em {
color: var(--sage);
font-style: italic;
}
.meta {
text-align: right;
font-family: 'DM Mono', monospace;
font-size: 9px;
color: var(--stone);
line-height: 1.8;
}

/* ── OVERVIEW STRIP ── */
.overview {
background: var(--sage-pale);
border-left: 3px solid var(--sage);
padding: 8px 12px;
margin-bottom: 14px;
font-size: 12px;
color: var(--charcoal);
}
.overview strong { color: var(--sage); }

/* ── GRID LAYOUT ── */
.grid-2 {
display: grid;
grid-template-columns: 1fr 1fr;
gap: 12px;
margin-bottom: 12px;
}
.grid-3 {
display: grid;
grid-template-columns: 1fr 1fr 1fr;
gap: 10px;
margin-bottom: 12px;
}

/* ── SECTION ── */
.section { margin-bottom: 12px; }
.section-title {
font-family: 'DM Mono', monospace;
font-size: 9px;
letter-spacing: 0.12em;
text-transform: uppercase;
color: var(--stone);
border-bottom: 1px solid var(--border);
padding-bottom: 3px;
margin-bottom: 8px;
}

/* ── AGENT CARDS ── */
.agent-card {
border: 1px solid var(--border);
border-radius: 6px;
overflow: hidden;
}
.agent-header {
padding: 7px 10px;
display: flex;
align-items: center;
gap: 8px;
}
.agent-num {
font-family: 'DM Serif Display', serif;
font-size: 18px;
opacity: 0.25;
line-height: 1;
}
.agent-title {
font-weight: 500;
font-size: 12px;
}
.agent-subtitle {
font-size: 10px;
opacity: 0.7;
}
.agent-body {
padding: 7px 10px;
background: white;
font-size: 11px;
}
.agent-body ul { padding-left: 12px; }
.agent-body li { margin-bottom: 2px; }
.tag {
display: inline-block;
font-family: 'DM Mono', monospace;
font-size: 9px;
padding: 1px 5px;
border-radius: 3px;
margin-right: 3px;
margin-top: 4px;
}

.agent-1 .agent-header { background: #e8f3ed; }
.agent-1 .agent-num { color: var(--sage); }
.agent-2 .agent-header { background: #e8f0f7; }
.agent-2 .agent-num { color: var(--blue); }
.agent-3 .agent-header { background: #fef3e8; }
.agent-3 .agent-num { color: var(--amber); }

.tag-green { background: #d4e6da; color: var(--sage); }
.tag-blue  { background: #d4e5f2; color: var(--blue); }
.tag-amber { background: #fde8cc; color: var(--amber); }
.tag-red   { background: #fad6d3; color: var(--red); }

/* ── DIAGRAM ── */
.diagram {
background: var(--charcoal);
border-radius: 8px;
padding: 14px 12px 10px;
margin-bottom: 12px;
}
.diagram-title {
font-family: 'DM Mono', monospace;
font-size: 9px;
letter-spacing: 0.12em;
text-transform: uppercase;
color: var(--stone);
margin-bottom: 12px;
}
.flow {
display: flex;
align-items: center;
justify-content: space-between;
gap: 4px;
}
.flow-node {
flex: 1;
text-align: center;
}
.node-box {
border-radius: 6px;
padding: 8px 6px;
font-size: 10px;
font-weight: 500;
line-height: 1.3;
}
.node-label {
font-family: 'DM Mono', monospace;
font-size: 8px;
margin-top: 4px;
opacity: 0.6;
color: white;
}
.node-ui    { background: #2c5f8a; color: white; }
.node-a1    { background: #4a7c59; color: white; }
.node-a2    { background: #2c5f8a; color: white; }
.node-a3    { background: #c9822a; color: white; }
.node-out   { background: #1c2b22; color: #d4e6da; border: 1px solid #4a7c59; }

.arrow {
color: var(--stone);
font-size: 16px;
flex-shrink: 0;
display: flex;
flex-direction: column;
align-items: center;
gap: 2px;
}
.arrow-label {
font-family: 'DM Mono', monospace;
font-size: 7.5px;
color: #666;
white-space: nowrap;
}

/* ── JSON SAMPLE ── */
.json-block {
background: #0e1a12;
border-radius: 6px;
padding: 10px 12px;
font-family: 'DM Mono', monospace;
font-size: 10px;
line-height: 1.7;
color: #a8d5b5;
overflow: hidden;
}
.json-key   { color: #7ecba0; }
.json-str   { color: #f0c98a; }
.json-num   { color: #e07070; }
.json-bool  { color: #88c7e0; }
.json-null  { color: #aaa; }
.json-label { font-family: 'DM Mono', monospace; font-size: 8.5px; color: var(--stone); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 5px; }

/* ── UI WIREFRAME ── */
.wireframe {
border: 1px solid var(--border);
border-radius: 6px;
padding: 10px;
background: #fafafa;
font-size: 11px;
}
.wf-bar {
background: var(--sage);
color: white;
padding: 4px 8px;
border-radius: 4px 4px 0 0;
font-size: 10px;
margin: -10px -10px 8px -10px;
font-weight: 500;
}
.wf-field {
border: 1px solid var(--border);
background: white;
border-radius: 4px;
padding: 4px 7px;
margin-bottom: 5px;
color: #999;
font-size: 11px;
}
.wf-field span { color: #ccc; }
.wf-btn {
background: var(--sage);
color: white;
padding: 5px 12px;
border-radius: 4px;
font-size: 11px;
display: inline-block;
margin-top: 2px;
}
.wf-status {
margin-top: 7px;
padding: 5px 8px;
background: var(--sage-pale);
border-radius: 4px;
font-size: 10px;
color: var(--sage);
font-family: 'DM Mono', monospace;
}

/* ── TABLE ── */
table { width: 100%; border-collapse: collapse; font-size: 11px; }
th {
background: var(--sage-pale);
padding: 5px 8px;
text-align: left;
font-family: 'DM Mono', monospace;
font-size: 9px;
letter-spacing: 0.08em;
text-transform: uppercase;
color: var(--stone);
border: 1px solid var(--border);
}
td {
padding: 5px 8px;
border: 1px solid var(--border);
vertical-align: top;
}
tr:nth-child(even) td { background: #fafcfb; }

/* ── FOOTER ── */
footer {
border-top: 1px solid var(--border);
margin-top: 14px;
padding-top: 7px;
display: flex;
justify-content: space-between;
font-family: 'DM Mono', monospace;
font-size: 8.5px;
color: var(--stone);
}

@media print {
body { background: white; }
.page { box-shadow: none; margin: 0; }
}
</style>
</head>
<body>
<div class="page">

<!-- HEADER -->
<header>
<div>
<div class="doc-label">Product Specification · v1.0</div>
<h1>Aged Care <em>Intake Agent</em></h1>
</div>
<div class="meta">
Status: DRAFT<br>
Date: March 2026<br>
Owner: Product Team<br>
Ref: ACI-001
</div>
</header>

<!-- OVERVIEW -->
<div class="overview">
<strong>Purpose:</strong> A multi-agent AI system that accepts natural-language patient intake submissions via a web UI, validates and enriches the data, then automatically generates a <strong>CRM ticket</strong> and a <strong>FBT (Fringe Benefits Tax) compliance report</strong> — all output as structured JSON.
</div>

<!-- SYSTEM FLOW DIAGRAM -->
<div class="diagram">
<div class="diagram-title">System Architecture · Data Flow</div>
<div class="flow">
<div class="flow-node">
<div class="node-box node-ui">🖥 Web UI<br><small style="opacity:.7">Input Form</small></div>
<div class="node-label">User Entry</div>
</div>
<div class="arrow">
→
<div class="arrow-label">raw text</div>
</div>
<div class="flow-node">
<div class="node-box node-a1">Agent 1<br><small style="opacity:.8">Extract & Validate</small></div>
<div class="node-label">NLP + Rules</div>
</div>
<div class="arrow">
→
<div class="arrow-label">validated JSON</div>
</div>
<div class="flow-node">
<div class="node-box node-a2">Agent 2<br><small style="opacity:.8">CRM Ticket Gen</small></div>
<div class="node-label">Ticket Engine</div>
</div>
<div class="arrow">
→
<div class="arrow-label">ticket payload</div>
</div>
<div class="flow-node">
<div class="node-box node-a3">Agent 3<br><small style="opacity:.8">FBT Report Gen</small></div>
<div class="node-label">Compliance</div>
</div>
<div class="arrow">
→
<div class="arrow-label">report JSON</div>
</div>
<div class="flow-node">
<div class="node-box node-out">📦 Output<br><small style="opacity:.8">JSON Bundle</small></div>
<div class="node-label">Final Artifact</div>
</div>
</div>
</div>

<!-- THREE AGENT CARDS -->
<div class="section">
<div class="section-title">Agent Specifications</div>
<div class="grid-3">

```
  <div class="agent-card agent-1">
    <div class="agent-header">
      <div class="agent-num">1</div>
      <div>
        <div class="agent-title">Intake Extractor</div>
        <div class="agent-subtitle">Extract &amp; Validate</div>
      </div>
    </div>
    <div class="agent-body">
      <ul>
        <li>Parse free-text input using LLM</li>
        <li>Extract: name, DOB/age, address, care needs, GP, emergency contact</li>
        <li>Validate required fields, flag missing data</li>
        <li>Normalise dates, phone numbers, postcodes</li>
        <li>Return structured patient JSON or error list</li>
      </ul>
      <div>
        <span class="tag tag-green">Claude claude-sonnet-4-6</span>
        <span class="tag tag-green">Regex validation</span>
        <span class="tag tag-red">Halts on critical error</span>
      </div>
    </div>
  </div>

  <div class="agent-card agent-2">
    <div class="agent-header">
      <div class="agent-num">2</div>
      <div>
        <div class="agent-title">CRM Ticket Generator</div>
        <div class="agent-subtitle">Structured Ticket</div>
      </div>
    </div>
    <div class="agent-body">
      <ul>
        <li>Receives validated patient JSON from Agent 1</li>
        <li>Maps fields to CRM schema (HubSpot / Salesforce compatible)</li>
        <li>Auto-assign priority (low / medium / high / urgent)</li>
        <li>Set SLA deadline based on care urgency flags</li>
        <li>Generate ticket ID and webhook payload</li>
      </ul>
      <div>
        <span class="tag tag-blue">Template engine</span>
        <span class="tag tag-blue">Priority rules</span>
        <span class="tag tag-blue">Webhook-ready</span>
      </div>
    </div>
  </div>

  <div class="agent-card agent-3">
    <div class="agent-header">
      <div class="agent-num">3</div>
      <div>
        <div class="agent-title">FBT Report Generator</div>
        <div class="agent-subtitle">Compliance Output</div>
      </div>
    </div>
    <div class="agent-body">
      <ul>
        <li>Receives patient + ticket data from Agents 1 &amp; 2</li>
        <li>Calculates FBT-exempt care categories (ATO guidelines)</li>
        <li>Computes reportable fringe benefit amounts</li>
        <li>Attaches employee/provider benefit attribution</li>
        <li>Outputs FBT-compliant JSON report with audit trail</li>
      </ul>
      <div>
        <span class="tag tag-amber">ATO FBT rules</span>
        <span class="tag tag-amber">Financial calc</span>
        <span class="tag tag-amber">Audit log</span>
      </div>
    </div>
  </div>

</div>
```

</div>

<!-- UI WIREFRAME + JSON OUTPUT SIDE BY SIDE -->
<div class="grid-2">

```
<div class="section">
  <div class="section-title">Web UI · Input Form</div>
  <div class="wireframe">
    <div class="wf-bar">🏥 Aged Care Intake Portal</div>
    <div class="wf-field">Patient Name &nbsp;<span>e.g. Margaret Thornton</span></div>
    <div class="wf-field">Age / Date of Birth &nbsp;<span>e.g. 82 or 12/03/1942</span></div>
    <div class="wf-field">Care Needs &nbsp;<span>e.g. dementia support, mobility aid…</span></div>
    <div class="wf-field">GP / Referrer &nbsp;<span>optional</span></div>
    <div class="wf-field">Emergency Contact &nbsp;<span>optional</span></div>
    <div class="wf-btn">▶ Submit Intake</div>
    <div class="wf-status">✓ Agent 1 complete &nbsp;|&nbsp; ⟳ Agent 2 running…</div>
  </div>
  <div style="margin-top:8px; font-size:10.5px; color:#666;">
    <strong>Tech stack:</strong> React + Tailwind · REST API (FastAPI) · Real-time agent status via SSE · Mobile responsive · WCAG 2.1 AA
  </div>
</div>

<div class="section">
  <div class="section-title">Output Schema · JSON Bundle</div>
  <div class="json-label">Final output_bundle.json (abbreviated)</div>
  <div class="json-block">{
```

<span class="json-key">"patient"</span>: {
<span class="json-key">"name"</span>: <span class="json-str">"Margaret Thornton"</span>,
<span class="json-key">"age"</span>: <span class="json-num">82</span>,
<span class="json-key">"dob"</span>: <span class="json-str">"1942-03-12"</span>,
<span class="json-key">"care_needs"</span>: [<span class="json-str">"dementia"</span>, <span class="json-str">"mobility"</span>],
<span class="json-key">"validated"</span>: <span class="json-bool">true</span>
},
<span class="json-key">"crm_ticket"</span>: {
<span class="json-key">"ticket_id"</span>: <span class="json-str">"ACI-20260302-0041"</span>,
<span class="json-key">"priority"</span>: <span class="json-str">"high"</span>,
<span class="json-key">"sla_due"</span>: <span class="json-str">"2026-03-04T09:00:00Z"</span>,
<span class="json-key">"status"</span>: <span class="json-str">"open"</span>
},
<span class="json-key">"fbt_report"</span>: {
<span class="json-key">"exempt_category"</span>: <span class="json-str">"aged_care_s58P"</span>,
<span class="json-key">"reportable_amount"</span>: <span class="json-num">0.00</span>,
<span class="json-key">"fbt_year"</span>: <span class="json-str">"2025-26"</span>,
<span class="json-key">"audit_id"</span>: <span class="json-str">"FBT-A9F3C2"</span>
}
}</div>
</div>

</div>

<!-- REQUIREMENTS TABLE -->
<div class="section">
<div class="section-title">Key Requirements & Constraints</div>
<table>
<thead>
<tr><th>Area</th><th>Requirement</th><th>Priority</th><th>Notes</th></tr>
</thead>
<tbody>
<tr><td>Security</td><td>All PII encrypted in transit (TLS 1.3) and at rest (AES-256)</td><td><span class="tag tag-red">P0</span></td><td>Must, pre-launch</td></tr>
<tr><td>Compliance</td><td>Aged Care Act 1997 (AU) + Privacy Act 1988 data handling</td><td><span class="tag tag-red">P0</span></td><td>Legal review req.</td></tr>
<tr><td>Performance</td><td>End-to-end pipeline ≤ 8 seconds p95 latency</td><td><span class="tag tag-amber">P1</span></td><td>Async agent chain</td></tr>
<tr><td>Error Handling</td><td>Partial failure: complete available agents, flag failed ones</td><td><span class="tag tag-amber">P1</span></td><td>Never silent fail</td></tr>
<tr><td>Audit</td><td>Immutable audit log per intake (agent inputs/outputs timestamped)</td><td><span class="tag tag-blue">P2</span></td><td>Stored 7 years</td></tr>
</tbody>
</table>
</div>

<!-- FOOTER -->
<footer>
<span>ACI-001 · Aged Care Intake Agent · Product Spec v1.0</span>
<span>Confidential — Internal Use Only · © 2026</span>
<span>Next: Technical Design Doc → ACI-002</span>
</footer>

</div>
</body>
</html>
