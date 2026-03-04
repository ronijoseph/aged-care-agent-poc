"""
Requirements -> Scope -> Epics/Stories -> Jira  |  SPA Module Builder
======================================================================
- Select individual user stories to demo
- Module analyser plans screens + navigation
- All screens built as single SPA with JS router
- Rendered inline in Streamlit - no new tab needed
- Full ACFS design system applied via Python (no f-strings = no brace errors)
"""

import os, json, re, textwrap
import requests as req
import streamlit as st
import streamlit.components.v1 as components
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, List, Dict, Any
from datetime import datetime

# =====================================================================
#  Pipeline State
# =====================================================================


class PipelineState(TypedDict):
    requirements: str
    scope: str
    epics: List[Dict]
    jira_results: List[Dict]
    screens: List[Dict]


# =====================================================================
#  LLM
# =====================================================================


@st.cache_resource
def get_llm():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY secret is not set.")
    from langchain_groq import ChatGroq
    return ChatGroq(model="llama-3.3-70b-versatile",
                    temperature=0.3,
                    api_key=key)


def llm_call(system, user):
    llm = get_llm()
    resp = llm.invoke([
        {
            "role": "system",
            "content": system
        },
        {
            "role": "user",
            "content": user
        },
    ])
    raw = resp.content.strip()
    raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return raw.strip()


def safe_json(text):
    try:
        return json.loads(text)
    except Exception as e:
        raise ValueError("Invalid JSON: " + str(e) + "\n\nRaw:\n" + text[:500])


# =====================================================================
#  Agent 1
# =====================================================================


def agent1_scope(state):
    state["scope"] = llm_call(
        "You are a senior business analyst. Expand requirements into a structured "
        "scope document: Overview, Objectives, Functional Requirements, "
        "Non-Functional Requirements, Out of Scope, Assumptions.",
        state["requirements"],
    )
    return state


# =====================================================================
#  Agent 2
# =====================================================================


def agent2_stories(state):
    raw = llm_call(
        'Return ONLY a JSON array, no markdown:\n'
        '[{"epic":"title","description":"one sentence","stories":['
        '{"title":"As a...","acceptance_criteria":["ac1"],"priority":"High|Medium|Low","story_points":3}]}]',
        state["scope"],
    )
    state["epics"] = safe_json(raw)
    return state


# =====================================================================
#  Agent 3A - Jira
# =====================================================================


def agent3a_jira(state):
    url = os.environ.get("JIRA_URL", "").rstrip("/")
    email = os.environ.get("JIRA_EMAIL", "")
    token = os.environ.get("JIRA_TOKEN", "")
    proj = os.environ.get("JIRA_PROJECT", "")
    if not all([url, email, token, proj]):
        raise ValueError("Jira config incomplete.")
    auth = (email, token)
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    results = []
    for epic in state["epics"]:
        er = req.post(url + "/rest/api/3/issue",
                      json={
                          "fields": {
                              "project": {
                                  "key": proj
                              },
                              "summary": epic["epic"],
                              "description": {
                                  "type":
                                  "doc",
                                  "version":
                                  1,
                                  "content": [{
                                      "type":
                                      "paragraph",
                                      "content": [{
                                          "type":
                                          "text",
                                          "text":
                                          epic.get("description", "")
                                      }]
                                  }]
                              },
                              "issuetype": {
                                  "name": "Epic"
                              },
                          }
                      },
                      auth=auth,
                      headers=hdrs,
                      timeout=15)
        if er.status_code not in (200, 201):
            results.append({"epic": epic["epic"], "status": "error"})
            continue
        ek = er.json()["key"]
        sr_list = []
        for s in epic.get("stories", []):
            sr = req.post(
                url + "/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {
                            "key": proj
                        },
                        "summary": s["title"],
                        "description": {
                            "type":
                            "doc",
                            "version":
                            1,
                            "content": [{
                                "type":
                                "paragraph",
                                "content": [{
                                    "type":
                                    "text",
                                    "text":
                                    "AC:\n" +
                                    "".join("- " + c + "\n" for c in s.get(
                                        "acceptance_criteria", []))
                                }]
                            }]
                        },
                        "issuetype": {
                            "name": "Story"
                        },
                        "priority": {
                            "name": s.get("priority", "Medium")
                        },
                        "customfield_10014": ek,
                    }
                },
                auth=auth,
                headers=hdrs,
                timeout=15)
            created = sr.status_code in (200, 201)
            sr_list.append({
                "title": s["title"],
                "key": sr.json().get("key", "-") if created else "-",
                "status": "created" if created else "error"
            })
        results.append({
            "epic": epic["epic"],
            "epic_key": ek,
            "stories": sr_list
        })
    state["jira_results"] = results
    return state


# =====================================================================
#  Module Analyser
# =====================================================================


def analyse_module(selected_stories):
    raw = llm_call(
        'You are a UX architect. Return ONLY a JSON object (no markdown):\n'
        '{"module_name":"short name","app_name":"short product name",'
        '"shared_state":["camelCaseKey"],'
        '"screens":[{"id":"kebab-id","name":"Screen Name","description":"what it does",'
        '"entry_point":true,"key_elements":["el1","el2"],'
        '"navigates_to":["other-id"],"receives_state":["key"],"sets_state":["key"]}]}\n'
        'Rules: one entry_point:true, navigates_to refs valid ids, max 6 screens.',
        "Selected stories:\n" + json.dumps(selected_stories, indent=2),
    )
    return safe_json(raw)


# =====================================================================
#  ACFS CSS - plain string, never inside an f-string
# =====================================================================

ACFS_CSS = (
    "*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }\n"
    "html, body { height: 100%; font-family: 'Roboto', sans-serif; background: #F3F6F8; color: #272B30; font-size: 14px; }\n"
    ".top-nav { position: fixed; top: 0; left: 0; right: 0; height: 48px; background: #0D1B2E; display: flex; align-items: center; justify-content: space-between; padding: 0 16px; z-index: 300; box-shadow: 0 1px 4px rgba(0,0,0,0.4); }\n"
    ".nav-left { display: flex; align-items: center; gap: 14px; }\n"
    ".nav-right { display: flex; align-items: center; gap: 16px; }\n"
    ".hamburger { display: flex; flex-direction: column; gap: 4px; cursor: pointer; padding: 4px; }\n"
    ".hamburger span { display: block; width: 18px; height: 2px; background: #fff; border-radius: 2px; }\n"
    ".logo { display: flex; align-items: center; gap: 10px; text-decoration: none; }\n"
    ".logo-wordmark { font-family: 'Montserrat',sans-serif; font-weight: 800; font-size: 13px; color: #fff; letter-spacing: 0.04em; line-height: 1.15; }\n"
    ".logo-wordmark small { display: block; font-weight: 400; font-size: 9px; color: #ADB5BD; letter-spacing: 0.1em; text-transform: uppercase; }\n"
    ".nav-bell { color: #fff; font-size: 17px; cursor: pointer; position: relative; }\n"
    ".notif-dot { position: absolute; top: -1px; right: -2px; width: 7px; height: 7px; background: #C92A2A; border-radius: 50%; border: 1.5px solid #0D1B2E; }\n"
    ".user-chip { display: flex; align-items: center; gap: 8px; cursor: pointer; }\n"
    ".avatar { width: 28px; height: 28px; border-radius: 50%; background: #1068EB; display: flex; align-items: center; justify-content: center; font-family: 'Roboto',sans-serif; font-weight: 500; font-size: 10px; color: #fff; }\n"
    ".user-name { font-family: 'Roboto',sans-serif; font-size: 13px; color: #fff; }\n"
    ".caret { font-size: 9px; color: #ADB5BD; }\n"
    ".icon-sidebar { position: fixed; left: 0; top: 48px; bottom: 0; width: 56px; background: #fff; border-right: 1px solid #E9ECEF; display: flex; flex-direction: column; align-items: center; padding: 8px 0; gap: 2px; z-index: 200; overflow-y: auto; }\n"
    ".icon-item { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; cursor: pointer; font-size: 18px; color: #6A7178; transition: all 0.15s; position: relative; }\n"
    ".icon-item:hover { background: #F3F6F8; color: #272B30; }\n"
    ".icon-item.active { background: #EEF4FF; color: #005BC9; }\n"
    ".icon-tooltip { display: none; position: absolute; left: 48px; top: 50%; transform: translateY(-50%); background: #272B30; color: #fff; font-family: 'Roboto',sans-serif; font-size: 11px; padding: 4px 8px; border-radius: 4px; white-space: nowrap; z-index: 999; pointer-events: none; }\n"
    ".icon-item:hover .icon-tooltip { display: block; }\n"
    ".tab-bar { position: fixed; top: 48px; left: 56px; right: 0; height: 48px; background: #fff; border-bottom: 2px solid #E9ECEF; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; z-index: 100; }\n"
    ".tabs { display: flex; gap: 4px; height: 100%; align-items: center; }\n"
    ".tab { display: flex; align-items: center; padding: 0 16px; height: 48px; font-family: 'Roboto',sans-serif; font-size: 13px; color: #6A7178; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.15s; white-space: nowrap; user-select: none; }\n"
    ".tab:hover { color: #272B30; }\n"
    ".tab.active { font-family: 'Montserrat',sans-serif; font-weight: 600; color: #005BC9; border-bottom-color: #005BC9; }\n"
    ".tab-meta { font-family: 'Roboto',sans-serif; font-size: 12px; color: #4F575E; display: flex; align-items: center; gap: 6px; white-space: nowrap; }\n"
    ".main-wrap { margin-left: 56px; margin-top: 96px; min-height: calc(100vh - 136px); background: #F3F6F8; }\n"
    ".screen-panel { display: none; padding: 24px; }\n"
    ".screen-panel.active { display: block; }\n"
    ".footer { margin-left: 56px; height: 40px; background: #fff; border-top: 1px solid #E9ECEF; display: flex; align-items: center; justify-content: space-between; padding: 0 24px; font-family: 'Roboto',sans-serif; font-size: 12px; color: #6A7178; }\n"
    ".footer a { color: #005BC9; text-decoration: none; }\n"
    ".footer-brand { font-family: 'Montserrat',sans-serif; font-weight: 600; font-size: 11px; color: #4F575E; letter-spacing: 0.05em; }\n"
    ".page-title { font-family:'Montserrat',sans-serif; font-weight:700; font-size:20px; color:#101213; margin-bottom:16px; }\n"
    ".section-heading { font-family:'Montserrat',sans-serif; font-weight:700; font-size:14px; color:#101213; margin-bottom:4px; }\n"
    ".section-sub { font-family:'Roboto',sans-serif; font-size:13px; color:#6A7178; margin-bottom:16px; }\n"
    ".filter-row { display:flex; align-items:center; gap:10px; margin-bottom:20px; flex-wrap:wrap; }\n"
    ".ds-select { height:36px; padding:0 10px; background:#fff; border:1px solid #CED4DA; border-radius:4px; font-family:'Roboto',sans-serif; font-size:13px; color:#272B30; cursor:pointer; min-width:140px; }\n"
    ".ds-select:focus { outline:none; border-color:#1068EB; box-shadow:0 0 0 3px rgba(16,104,235,0.12); }\n"
    ".ds-input { height:36px; padding:0 12px; background:#fff; border:1px solid #CED4DA; border-radius:4px; font-family:'Roboto',sans-serif; font-size:13px; color:#272B30; width:100%; }\n"
    ".ds-input:focus { outline:none; border-color:#1068EB; box-shadow:0 0 0 3px rgba(16,104,235,0.12); }\n"
    ".ds-textarea { padding:10px 12px; background:#fff; border:1px solid #CED4DA; border-radius:4px; font-family:'Roboto',sans-serif; font-size:13px; color:#272B30; width:100%; resize:vertical; min-height:80px; }\n"
    ".form-label { display:block; font-family:'Montserrat',sans-serif; font-weight:500; font-size:12px; color:#4F575E; margin-bottom:4px; }\n"
    ".form-group { margin-bottom:14px; }\n"
    ".form-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:14px; }\n"
    ".btn-primary { height:36px; padding:0 20px; background:#005BC9; color:#fff; border:none; border-radius:4px; font-family:'Montserrat',sans-serif; font-weight:600; font-size:13px; cursor:pointer; white-space:nowrap; }\n"
    ".btn-primary:hover { background:#004aad; }\n"
    ".btn-outline { height:36px; padding:0 16px; background:#fff; color:#4F575E; border:1px solid #CED4DA; border-radius:4px; font-family:'Montserrat',sans-serif; font-weight:600; font-size:13px; cursor:pointer; }\n"
    ".btn-outline:hover { border-color:#4F575E; }\n"
    ".btn-danger { height:36px; padding:0 16px; background:#DC2020; color:#fff; border:none; border-radius:4px; font-family:'Montserrat',sans-serif; font-weight:600; font-size:13px; cursor:pointer; }\n"
    ".btn-sm { height:28px; padding:0 12px; font-size:11px; }\n"
    ".card { background:#fff; border:1px solid #CED4DA; border-radius:4px; padding:16px 20px; margin-bottom:16px; }\n"
    ".card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }\n"
    ".card-title { font-family:'Montserrat',sans-serif; font-weight:700; font-size:14px; color:#101213; }\n"
    ".view-report { font-family:'Roboto',sans-serif; font-weight:500; font-size:12px; color:#005BC9; cursor:pointer; display:inline-flex; align-items:center; gap:4px; text-decoration:none; background:none; border:none; padding:0; }\n"
    ".kpi-strip { display:flex; border:1px solid #CED4DA; border-radius:4px; overflow:hidden; margin-bottom:14px; }\n"
    ".kpi-cell { flex:1; padding:12px 16px; border-right:1px solid #CED4DA; }\n"
    ".kpi-cell:last-child { border-right:none; }\n"
    ".kpi-label { font-family:'Roboto',sans-serif; font-size:11px; color:#6A7178; margin-bottom:4px; }\n"
    ".kpi-value { font-family:'Montserrat',sans-serif; font-weight:700; font-size:26px; color:#005BC9; }\n"
    ".kpi-value.green { color:#087F5B; }\n"
    ".kpi-value.red { color:#C92A2A; }\n"
    ".kpi-value.dark { color:#101213; }\n"
    ".kpi-value.amber { color:#E9A100; }\n"
    ".stat-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px; margin-bottom:16px; }\n"
    ".stat-card { background:#fff; border:1px solid #CED4DA; border-radius:4px; padding:14px 16px; }\n"
    ".stat-label { font-family:'Roboto',sans-serif; font-size:11px; color:#6A7178; margin-bottom:6px; }\n"
    ".stat-value { font-family:'Montserrat',sans-serif; font-weight:700; font-size:26px; color:#101213; }\n"
    ".stat-sub { display:flex; gap:16px; margin-top:8px; flex-wrap:wrap; }\n"
    ".stat-sub-item { display:flex; flex-direction:column; }\n"
    ".stat-sub-val { font-family:'Roboto',sans-serif; font-weight:500; font-size:13px; color:#005BC9; }\n"
    ".stat-sub-val.green { color:#087F5B; }\n"
    ".stat-sub-val.red { color:#C92A2A; }\n"
    ".stat-sub-lbl { font-family:'Roboto',sans-serif; font-size:10px; color:#6A7178; }\n"
    ".tag { display:inline-flex; align-items:center; padding:3px 10px; border-radius:55px; font-family:'Roboto',sans-serif; font-weight:500; font-size:11px; white-space:nowrap; }\n"
    ".tag-blue { background:#1068EB; color:#fff; }\n"
    ".tag-teal { background:#087F5B; color:#fff; }\n"
    ".tag-amber { background:#F59F00; color:#fff; }\n"
    ".tag-red { background:#C92A2A; color:#fff; }\n"
    ".tag-grey { background:#E9ECEF; color:#4F575E; }\n"
    ".tag-green { background:#61CE70; color:#fff; }\n"
    ".tag-dark { background:#272B30; color:#fff; }\n"
    ".ds-table { width:100%; border-collapse:collapse; }\n"
    ".ds-table th { font-family:'Montserrat',sans-serif; font-weight:600; font-size:12px; color:#272B30; padding:10px 16px; text-align:left; background:#fff; border-bottom:2px solid #CED4DA; white-space:nowrap; }\n"
    ".ds-table td { font-family:'Roboto',sans-serif; font-size:13px; color:#272B30; padding:10px 16px; border-bottom:1px solid #E9ECEF; }\n"
    ".ds-table tbody tr:hover td { background:#F8FAFE; cursor:pointer; }\n"
    ".ds-table tbody tr:last-child td { border-bottom:none; }\n"
    ".table-wrap { background:#fff; border:1px solid #CED4DA; border-radius:4px; overflow:auto; margin-bottom:16px; }\n"
    ".alert { padding:12px 16px; border-radius:4px; margin-bottom:16px; font-family:'Roboto',sans-serif; font-size:13px; display:flex; align-items:center; gap:10px; }\n"
    ".alert-success { background:#EDF7EE; border-left:3px solid #087F5B; color:#087F5B; }\n"
    ".alert-warning { background:#FFF9EC; border-left:3px solid #F59F00; color:#856404; }\n"
    ".alert-danger  { background:#FDECEA; border-left:3px solid #C92A2A; color:#C92A2A; }\n"
    ".alert-info    { background:#EEF4FF; border-left:3px solid #1068EB; color:#1068EB; }\n"
    ".detail-row { display:flex; gap:8px; padding:10px 0; border-bottom:1px solid #E9ECEF; }\n"
    ".detail-label { font-family:'Montserrat',sans-serif; font-weight:500; font-size:12px; color:#6A7178; min-width:140px; }\n"
    ".detail-value { font-family:'Roboto',sans-serif; font-size:13px; color:#272B30; flex:1; }\n"
    ".row-2col { display:grid; grid-template-columns:1fr 1fr; gap:16px; }\n"
    ".row-3col { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }\n"
    ".row-aside { display:grid; grid-template-columns:1fr 320px; gap:16px; }\n"
    ".accent-red   { border-left:3px solid #C92A2A; padding-left:12px; }\n"
    ".accent-blue  { border-left:3px solid #1068EB; padding-left:12px; }\n"
    ".accent-green { border-left:3px solid #087F5B; padding-left:12px; }\n"
    ".scheduled-bg   { background:#EDF7EE !important; }\n"
    ".unscheduled-bg { background:#FDECEA !important; }\n"
    ".divider { border:none; border-top:1px solid #E9ECEF; margin:16px 0; }\n"
    ".breadcrumb { font-family:'Roboto',sans-serif; font-size:12px; color:#6A7178; margin-bottom:12px; }\n"
    ".bc-active { color:#272B30; font-weight:500; }\n"
    ".back-link { font-family:'Roboto',sans-serif; font-size:13px; color:#005BC9; cursor:pointer; display:inline-flex; align-items:center; gap:4px; background:none; border:none; padding:0; margin-bottom:12px; }\n"
    ".empty-state { text-align:center; padding:48px 24px; color:#6A7178; }\n"
    ".empty-icon { font-size:40px; margin-bottom:12px; }\n")

# =====================================================================
#  build_chrome_html  -- pure string concatenation, zero f-strings
# =====================================================================


def build_chrome_html(module, screen_panels_html, js_code):
    today = datetime.now().strftime("%a, %d %b %Y")
    year = str(datetime.now().year)
    app_name = module.get("app_name", "Enterprise Portal")
    mod_name = module.get("module_name", "Module")
    screens = module.get("screens", [])
    entry_id = next((s["id"] for s in screens if s.get("entry_point")),
                    screens[0]["id"] if screens else "s0")
    icon_chars = [
        "\u25a6", "\u2302", "\u25ce", "\u25b6", "\u2605", "\u25c6", "\u25aa",
        "\u2022", "\u25cf", "\u2665", "\u2660", "\u2663"
    ]

    sidebar_parts = []
    for idx, s in enumerate(screens):
        ic = icon_chars[idx % len(icon_chars)]
        sid = s["id"]
        nm = s["name"]
        sidebar_parts.append('<div class="icon-item" id="icon-' + sid +
                             '" onclick="showScreen(\'' + sid +
                             '\')" title="' + nm + '">' +
                             '<span style="font-size:16px;">' + ic +
                             '</span>' + '<span class="icon-tooltip">' + nm +
                             '</span>' + '</div>')
    sidebar_html = "\n".join(sidebar_parts)

    tab_parts = []
    for s in screens:
        tab_parts.append('<div class="tab" id="tab-' + s["id"] +
                         '" onclick="showScreen(\'' + s["id"] + '\')">' +
                         s["name"] + '</div>')
    tabs_html = "\n".join(tab_parts)

    state_keys = ", ".join('"' + k + '": null'
                           for k in module.get("shared_state", []))
    screen_ids = json.dumps([s["id"] for s in screens])

    js_router = (
        "var AppState = {" + state_keys + "};\n"
        "var SCREENS = " + screen_ids + ";\n"
        "var ENTRY = '" + entry_id + "';\n\n"
        "function showScreen(id) {\n"
        "  SCREENS.forEach(function(sid) {\n"
        "    var panel = document.getElementById('screen-' + sid);\n"
        "    var tab   = document.getElementById('tab-'    + sid);\n"
        "    var icon  = document.getElementById('icon-'   + sid);\n"
        "    if (panel) panel.className = sid===id ? 'screen-panel active' : 'screen-panel';\n"
        "    if (tab)   tab.className   = sid===id ? 'tab active'          : 'tab';\n"
        "    if (icon)  icon.className  = sid===id ? 'icon-item active'    : 'icon-item';\n"
        "  });\n"
        "  window.scrollTo(0, 0);\n"
        "}\n\n"
        "function navigate(screenId, stateUpdates) {\n"
        "  if (stateUpdates) Object.keys(stateUpdates).forEach(function(k){ AppState[k]=stateUpdates[k]; });\n"
        "  showScreen(screenId);\n"
        "  var fn = window['onEnter_' + screenId.replace(/-/g,'_')];\n"
        "  if (typeof fn === 'function') fn();\n"
        "}\n\n"
        "function showToast(msg, type) {\n"
        "  type = type||'success';\n"
        "  var c={success:'#087F5B',error:'#C92A2A',info:'#1068EB',warning:'#E9A100'};\n"
        "  var t=document.createElement('div');\n"
        "  t.style.cssText='position:fixed;top:64px;right:20px;z-index:9999;background:'+(c[type]||c.success)+';color:#fff;padding:10px 18px;border-radius:4px;font-family:Roboto,sans-serif;font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.2);';\n"
        "  t.textContent=msg;\n"
        "  document.body.appendChild(t);\n"
        "  setTimeout(function(){t.remove();},3000);\n"
        "}\n\n")

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "<title>" + mod_name + " \u2014 " + app_name + "</title>\n"
        "<link href=\"https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&family=Roboto:wght@300;400;500;700&display=swap\" rel=\"stylesheet\">\n"
        "<style>\n" + ACFS_CSS + "</style>\n"
        "</head>\n<body>\n\n"
        "<!-- TOP NAV -->\n"
        "<nav class=\"top-nav\">\n"
        "  <div class=\"nav-left\">\n"
        "    <div class=\"hamburger\"><span></span><span></span><span></span></div>\n"
        "    <a class=\"logo\" href=\"#\">\n"
        "      <svg width=\"30\" height=\"20\" viewBox=\"0 0 30 20\" fill=\"none\">\n"
        "        <path d=\"M0 10 L8 1 L15 7 L22 1 L30 10 L22 19 L15 13 L8 19 Z\" fill=\"#ffffff\" opacity=\"0.85\"/>\n"
        "        <path d=\"M7 10 L13 4 L19 10 L13 16 Z\" fill=\"#1068EB\"/>\n"
        "      </svg>\n"
        "      <div class=\"logo-wordmark\">" + app_name.upper() +
        "<small>Enterprise Portal</small></div>\n"
        "    </a>\n"
        "  </div>\n"
        "  <div class=\"nav-right\">\n"
        "    <div class=\"nav-bell\">&#128276;<div class=\"notif-dot\"></div></div>\n"
        "    <div class=\"user-chip\">\n"
        "      <div class=\"avatar\">JS</div>\n"
        "      <span class=\"user-name\">John Smith</span>\n"
        "      <span class=\"caret\">&#9660;</span>\n"
        "    </div>\n"
        "  </div>\n"
        "</nav>\n\n"
        "<!-- ICON SIDEBAR -->\n"
        "<aside class=\"icon-sidebar\">\n" + sidebar_html + "\n</aside>\n\n"
        "<!-- TAB BAR -->\n"
        "<div class=\"tab-bar\">\n"
        "  <div class=\"tabs\">" + tabs_html + "</div>\n"
        "  <div class=\"tab-meta\">&#128197;&nbsp;" + today + "</div>\n"
        "</div>\n\n"
        "<!-- SCREENS -->\n"
        "<div class=\"main-wrap\">\n" + screen_panels_html + "\n</div>\n\n"
        "<!-- FOOTER -->\n"
        "<footer class=\"footer\">\n"
        "  <span>Copyright &copy; " + year +
        " &nbsp;&middot;&nbsp; <a href=\"#\">Privacy Policy &#8599;</a></span>\n"
        "  <span class=\"footer-brand\">" + app_name.upper() + "</span>\n"
        "</footer>\n\n"
        "<script>\n" + js_router + (js_code or "") +
        "\ndocument.addEventListener('DOMContentLoaded', function(){ showScreen(ENTRY); });\n"
        "</script>\n"
        "</body>\n</html>")


# =====================================================================
#  Screen panel content generator
# =====================================================================

PANEL_SYSTEM = (
    "You are an expert enterprise UI developer. Generate HTML for ONE screen panel.\n\n"
    "OUTPUT: Raw HTML only - the inner content for this screen.\n"
    "Do NOT output <html>, <head>, <body>, nav, sidebar, footer, <style>, or wrapping divs.\n"
    "You MAY include a <script> block at the END for screen-specific interactivity only.\n\n"
    "AVAILABLE CSS CLASSES (do not write new CSS unless essential for layout):\n"
    "  .row-2col .row-3col .row-aside .filter-row .form-row .stat-grid\n"
    "  .card .card-header .card-title .view-report\n"
    "  .kpi-strip .kpi-cell .kpi-label .kpi-value (.green .red .dark .amber)\n"
    "  .stat-card .stat-label .stat-value .stat-sub .stat-sub-item .stat-sub-val .stat-sub-lbl\n"
    "  .table-wrap > table.ds-table\n"
    "  .form-group .form-label .ds-input .ds-select .ds-textarea\n"
    "  .btn-primary .btn-outline .btn-danger .btn-sm\n"
    "  .tag .tag-blue .tag-teal .tag-amber .tag-red .tag-grey .tag-green\n"
    "  .alert .alert-success .alert-warning .alert-danger .alert-info\n"
    "  .detail-row .detail-label .detail-value\n"
    "  .back-link .breadcrumb .bc-active\n"
    "  .divider .empty-state .accent-red .accent-blue .accent-green\n"
    "  .scheduled-bg .unscheduled-bg\n\n"
    "NAVIGATION: navigate('target-screen-id', {stateKey: value})\n"
    "  Example: onclick=\"navigate('order-detail', {selectedOrderId: '1042'})\"\n"
    "  Back button: onclick=\"navigate('orders-list')\"\n\n"
    "SHARED STATE: read with AppState.keyName\n"
    "  On-enter hook: window.onEnter_screen_id = function() { ... }\n"
    "  (replace hyphens with underscores)\n\n"
    "TOAST: showToast('Saved successfully', 'success')\n\n"
    "RULES:\n"
    "1. First element must be <div class=\"page-title\">SCREEN NAME</div>\n"
    "2. Include a .filter-row with relevant controls\n"
    "3. Use realistic domain-specific placeholder data, no [placeholder] text\n"
    "4. Clickable table rows should navigate to detail screens\n"
    "5. Form save buttons call showToast then navigate back\n"
    "6. Keep output under 150 lines\n")


def generate_screen_panel(screen, module):
    nav_targets = "\n".join(
        "  - navigate to '" + s["id"] + "' (" + s["name"] + ")"
        for s in module["screens"] if s["id"] != screen["id"]
        and s["id"] in screen.get("navigates_to", [])) or "  none"

    return llm_call(
        PANEL_SYSTEM, "Screen ID:       " + screen["id"] + "\n"
        "Screen name:     " + screen["name"] + "\n"
        "Description:     " + screen["description"] + "\n"
        "Key elements:    " + ", ".join(screen.get("key_elements", [])) + "\n"
        "Entry point:     " + str(screen.get("entry_point", False)) + "\n"
        "Navigate to:\n" + nav_targets + "\n"
        "Reads AppState:  " +
        (", ".join(screen.get("receives_state", [])) or "none") + "\n"
        "Writes AppState: " +
        (", ".join(screen.get("sets_state", [])) or "none") + "\n"
        "Module:          " + module["module_name"] + " / " +
        module["app_name"] + "\n"
        "All screens:     " + ", ".join(s["id"] + "(" + s["name"] + ")"
                                        for s in module["screens"]))


# =====================================================================
#  Streamlit UI
# =====================================================================

st.set_page_config(page_title="Requirements Pipeline",
                   page_icon="=",
                   layout="wide")

with st.sidebar:
    st.markdown("## Requirements Pipeline")
    st.caption("AI-powered delivery toolkit")
    st.divider()
    st.markdown("**Pipeline Status**")
    for lbl, key in [("Agent 1 - Scope", "scope"),
                     ("Agent 2 - Epics", "epics"),
                     ("Module Builder", "built_spa"),
                     ("Agent 3A - Jira", "jira_results")]:
        icon = "OK  " if st.session_state.get(key) else "... "
        st.markdown(icon + lbl)
    st.divider()
    st.markdown("**Jira Configuration**")
    j_url = st.text_input("Jira URL",
                          value=os.environ.get("JIRA_URL", ""),
                          placeholder="https://yourco.atlassian.net")
    j_email = st.text_input("Email",
                            value=os.environ.get("JIRA_EMAIL", ""),
                            placeholder="you@company.com")
    j_token = st.text_input("API Token",
                            value=os.environ.get("JIRA_TOKEN", ""),
                            type="password")
    j_proj = st.text_input("Project Key",
                           value=os.environ.get("JIRA_PROJECT", ""),
                           placeholder="PROJ")
    if st.button("Save Jira Settings", use_container_width=True):
        os.environ.update({
            "JIRA_URL": j_url,
            "JIRA_EMAIL": j_email,
            "JIRA_TOKEN": j_token,
            "JIRA_PROJECT": j_proj
        })
        st.success("Saved")

st.title("Requirements Pipeline")
st.caption(
    "Requirements -> Scope -> Epics/Stories -> **Jira**  |  **SPA Module Builder**"
)
st.divider()

# Step 1 - Requirements
st.subheader("Step 1 - Requirements")
requirements = st.text_area(
    "req",
    label_visibility="collapsed",
    height=120,
    placeholder=
    "Describe what you need to build.\n\nExample: Build a customer portal where users can log in, view orders, track shipments, raise support tickets, and update their profile."
)
c1, c2 = st.columns([5, 1])
run_btn = c1.button("Generate Scope + Epics",
                    type="primary",
                    use_container_width=True)
clear_btn = c2.button("Clear All", use_container_width=True)

if clear_btn:
    for k in [
            "scope", "epics", "jira_results", "built_spa", "spa_module",
            "show_story_selector", "selected_story_keys"
    ]:
        st.session_state.pop(k, None)
    st.rerun()

if run_btn:
    if not requirements.strip():
        st.warning("Please enter requirements first.")
        st.stop()
    try:
        get_llm()
    except ValueError as e:
        st.error(str(e))
        st.stop()
    prog = st.progress(0, "Agent 1: Building scope...")
    state = {
        "requirements": requirements,
        "scope": "",
        "epics": [],
        "jira_results": [],
        "screens": []
    }
    state = agent1_scope(state)
    prog.progress(55, "Agent 2: Generating Epics & Stories...")
    state = agent2_stories(state)
    prog.progress(100, "Done")
    st.session_state.update({
        "scope": state["scope"],
        "epics": state["epics"],
        "jira_results": [],
        "built_spa": None,
        "spa_module": None
    })
    st.rerun()

# Scope output
if st.session_state.get("scope"):
    st.divider()
    st.subheader("Agent 1 - Scope Document")
    with st.expander("View scope", expanded=False):
        st.markdown(st.session_state["scope"])

# Epics output
if st.session_state.get("epics"):
    epics = st.session_state["epics"]
    st.divider()
    st.subheader("Agent 2 - Epics & User Stories")
    for epic in epics:
        stories = epic.get("stories", [])
        pts = sum(s.get("story_points", 0) for s in stories)
        with st.expander(epic["epic"] + "  |  " + str(len(stories)) +
                         " stories  |  " + str(pts) + " pts"):
            st.caption(epic.get("description", ""))
            for s in stories:
                dot = {
                    "High": "[HIGH]",
                    "Medium": "[MED]",
                    "Low": "[LOW]"
                }.get(s.get("priority", ""), "[---]")
                st.markdown("**" + dot + " " + s["title"] + "** `" +
                            str(s.get("story_points", "?")) + " pts`")
                for ac in s.get("acceptance_criteria", []):
                    st.markdown("  - " + ac)
                st.markdown("---")

    st.divider()
    st.subheader("Next Steps")
    ca, cb = st.columns(2)
    with ca:
        st.markdown("**Push to Jira**")
        st.caption("Create all Epics and Stories as Jira issues.")
        jira_btn = st.button("Send to Jira",
                             use_container_width=True,
                             key="jira_btn")
    with cb:
        st.markdown("**Build Demo Module**")
        st.caption(
            "Select stories, build a fully interlinked SPA rendered right here."
        )
        spa_btn = st.button("Build Demo Module",
                            type="primary",
                            use_container_width=True,
                            key="spa_open")

    if jira_btn:
        with st.spinner("Pushing to Jira..."):
            try:
                s = {
                    "requirements": "",
                    "scope": "",
                    "epics": epics,
                    "jira_results": [],
                    "screens": []
                }
                s = agent3a_jira(s)
                st.session_state["jira_results"] = s["jira_results"]
            except ValueError as e:
                st.error(str(e))
        st.rerun()

    if spa_btn:
        st.session_state["show_story_selector"] = True
        st.rerun()

# Story selector
if st.session_state.get("show_story_selector") and st.session_state.get(
        "epics"):
    epics = st.session_state["epics"]
    st.divider()
    st.subheader("Step 3 - Select Stories for Demo Module")
    st.caption(
        "Tick the stories you want to demo. All selected screens will be linked together in one interactive module."
    )

    all_stories = []
    for epic in epics:
        for s in epic.get("stories", []):
            all_stories.append({
                "epic":
                epic["epic"],
                "title":
                s["title"],
                "priority":
                s.get("priority", "Medium"),
                "points":
                s.get("story_points", 0),
                "acceptance_criteria":
                s.get("acceptance_criteria", [])
            })

    default_selected = st.session_state.get(
        "selected_story_keys", set(s["title"] for s in all_stories))
    new_selected = set()
    by_epic = {}
    for s in all_stories:
        by_epic.setdefault(s["epic"], []).append(s)

    for ename, stories in by_epic.items():
        st.markdown("**" + ename + "**")
        for s in stories:
            if st.checkbox(s["title"] + "  [" + s["priority"] + " / " +
                           str(s["points"]) + " pts]",
                           value=(s["title"] in default_selected),
                           key="chk_" + str(abs(hash(s["title"])) % 999999)):
                new_selected.add(s["title"])

    st.session_state["selected_story_keys"] = new_selected
    n = len(new_selected)
    st.markdown("**" + str(n) + " of " + str(len(all_stories)) +
                " stories selected**")

    b1, b2 = st.columns([3, 1])
    build_now = b1.button("Build Module (" + str(n) + " stories)",
                          type="primary",
                          use_container_width=True,
                          key="build_spa_btn",
                          disabled=(n == 0))
    cancel_btn = b2.button("Cancel",
                           use_container_width=True,
                           key="cancel_spa")

    if cancel_btn:
        st.session_state["show_story_selector"] = False
        st.rerun()

    if build_now:
        selected_stories = [
            s for s in all_stories if s["title"] in new_selected
        ]
        st.session_state["show_story_selector"] = False

        with st.spinner("Analysing stories and planning module screens..."):
            try:
                module = analyse_module(selected_stories)
                st.session_state["spa_module"] = module
            except Exception as e:
                st.error("Module analysis failed: " + str(e))
                st.stop()

        screens = module.get("screens", [])
        st.info("Module: " + module["module_name"] + " - " +
                str(len(screens)) + " screens: " + ", ".join(s["name"]
                                                             for s in screens))

        prog = st.progress(0, "Starting build...")
        panel_parts = []
        for i, screen in enumerate(screens):
            prog.progress(
                int((i / len(screens)) * 90), "Building " + str(i + 1) + "/" +
                str(len(screens)) + ": " + screen["name"] + "...")
            try:
                content = generate_screen_panel(screen, module)
                panel_parts.append('<div class="screen-panel" id="screen-' +
                                   screen["id"] + '">\n' + content +
                                   '\n</div>')
            except Exception as e:
                panel_parts.append(
                    '<div class="screen-panel" id="screen-' + screen["id"] +
                    '"><div class="page-title">' + screen["name"] +
                    '</div><div class="alert alert-danger">Error: ' + str(e) +
                    '</div></div>')

        prog.progress(95, "Assembling SPA...")
        spa_html = build_chrome_html(
            module=module,
            screen_panels_html="\n\n".join(panel_parts),
            js_code="")
        prog.progress(100, "Done")
        st.session_state["built_spa"] = spa_html
        st.rerun()

# Render SPA
if st.session_state.get("built_spa"):
    spa_html = st.session_state["built_spa"]
    module = st.session_state.get("spa_module", {})
    screens = module.get("screens", [])
    st.divider()
    st.subheader("Demo Module - " + module.get("module_name", ""))
    st.caption(
        str(len(screens)) + " screens: " + "  ->  ".join(s["name"]
                                                         for s in screens) +
        "   |   Use sidebar icons or tabs to navigate between screens.")
    a1, a2, _ = st.columns([1, 1, 4])
    with a1:
        st.download_button(
            "Download SPA",
            data=spa_html,
            file_name=module.get("module_name", "module").replace(" ", "_") +
            "_spa.html",
            mime="text/html",
            use_container_width=True)
    with a2:
        if st.button("Rebuild Module", use_container_width=True):
            st.session_state.pop("built_spa", None)
            st.session_state["show_story_selector"] = True
            st.rerun()
    components.html(spa_html, height=780, scrolling=True)

# Jira results
if st.session_state.get("jira_results"):
    st.divider()
    st.subheader("Jira Results")
    for r in st.session_state["jira_results"]:
        icon = "OK" if r.get("epic_key") else "FAIL"
        with st.expander("[" + icon + "] " + r["epic"] + " - " +
                         r.get("epic_key", "failed")):
            for s in r.get("stories", []):
                ok = s["status"] == "created"
                st.markdown(("OK " if ok else "FAIL ") + "`" +
                            s.get("key", "-") + "` - " + s["title"])
