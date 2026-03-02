"""
Patient Intake Pipeline  ·  3-Agent LangGraph Chain
====================================================
Agent 1  →  Extract name, age, needs from intake text  (JSON)
Agent 2  →  Generate a CRM support ticket from the JSON
Agent 3  →  Calculate FBT liability  (salary × 0.47)

Setup on Replit
---------------
1. Secrets  →  GROQ_API_KEY = gsk_...
2. Shell    →  pip install streamlit langchain-groq langchain-core langgraph
3. Shell    →  streamlit run main.py
"""

import os
import json
import streamlit as st
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict

# ══════════════════════════════════════════════════════════════════════════════
#  Shared state that travels through every node in the LangGraph pipeline
# ══════════════════════════════════════════════════════════════════════════════


class PipelineState(TypedDict):
    intake_text: str  # raw text the user types in
    patient_json: dict  # structured data produced by Agent 1
    crm_ticket: str  # CRM ticket text produced by Agent 2
    salary: float  # salary entered by the user
    fbt_result: dict  # FBT calculation produced by Agent 3


# ══════════════════════════════════════════════════════════════════════════════
#  Shared LLM  (cached so Streamlit doesn't rebuild it on every interaction)
# ══════════════════════════════════════════════════════════════════════════════


@st.cache_resource
def get_llm():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY secret is not set in Replit Secrets.")
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0,
        api_key=api_key,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Agent 1 — Patient Intake Extractor
# ══════════════════════════════════════════════════════════════════════════════


def agent1_extract(state: PipelineState) -> PipelineState:
    """Extract name, age, and needs from free-form intake text."""
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content=(
            "You are a medical intake assistant. "
            "Extract patient information from the user's text. "
            "Return ONLY a valid JSON object with exactly these keys:\n"
            "  - name  (string or null)\n"
            "  - age   (integer or null)\n"
            "  - needs (list of strings)\n"
            "No explanation, no markdown — JSON only.")),
        HumanMessage(content=state["intake_text"]),
    ])

    raw = response.content.strip()
    # Remove accidental markdown code fences that some models add
    raw = raw.replace("```json", "").replace("```", "").strip()
    state["patient_json"] = json.loads(raw)
    return state


# ══════════════════════════════════════════════════════════════════════════════
#  Agent 2 — CRM Ticket Generator
# ══════════════════════════════════════════════════════════════════════════════


def agent2_crm_ticket(state: PipelineState) -> PipelineState:
    """Turn the structured patient JSON into a formatted CRM support ticket."""
    llm = get_llm()

    response = llm.invoke([
        SystemMessage(content="You are a CRM assistant for a medical clinic."),
        HumanMessage(content=(
            f"Here is a patient record in JSON format:\n\n"
            f"{json.dumps(state['patient_json'], indent=2)}\n\n"
            "Write a short, professional CRM support ticket. "
            "Include: a ticket title, a one-sentence patient summary, "
            "and a bullet list of action items for the care team. "
            "Plain text only — no JSON, no markdown headers.")),
    ])

    state["crm_ticket"] = response.content.strip()
    return state


# ══════════════════════════════════════════════════════════════════════════════
#  Agent 3 — FBT Calculator  (Fringe Benefits Tax = salary × 0.47)
# ══════════════════════════════════════════════════════════════════════════════


def agent3_fbt(state: PipelineState) -> PipelineState:
    """
    Calculate FBT liability and generate a plain-English summary.
    Python handles the maths; the LLM writes the human-readable explanation.
    """
    llm = get_llm()

    salary = state["salary"]
    fbt_rate = 0.47
    fbt_amount = round(salary * fbt_rate, 2)

    response = llm.invoke([
        SystemMessage(content="You are a friendly tax assistant. Be concise."),
        HumanMessage(content=(
            f"An employee has an annual salary of ${salary:,.2f}. "
            f"The Fringe Benefits Tax (FBT) rate is 47% (0.47). "
            f"The calculated FBT liability is ${fbt_amount:,.2f}. "
            "Write exactly two sentences explaining what this means for the employee."
        )),
    ])

    state["fbt_result"] = {
        "salary": salary,
        "fbt_rate": fbt_rate,
        "fbt_amount": fbt_amount,
        "explanation": response.content.strip(),
    }
    return state


# ══════════════════════════════════════════════════════════════════════════════
#  LangGraph pipeline  —  Agent1 → Agent2 → Agent3 → END
# ══════════════════════════════════════════════════════════════════════════════


def build_pipeline():
    graph = StateGraph(PipelineState)

    graph.add_node("agent1", agent1_extract)
    graph.add_node("agent2", agent2_crm_ticket)
    graph.add_node("agent3", agent3_fbt)

    graph.set_entry_point("agent1")
    graph.add_edge("agent1", "agent2")
    graph.add_edge("agent2", "agent3")
    graph.add_edge("agent3", END)

    return graph.compile()


# ══════════════════════════════════════════════════════════════════════════════
#  Streamlit UI helpers
# ══════════════════════════════════════════════════════════════════════════════


def check_api_key():
    """Stop early with a clear error if the secret is missing."""
    try:
        get_llm()
    except ValueError as e:
        st.error(f"❌ {e}")
        st.stop()


def show_agent1(state):
    st.subheader("🤖 Agent 1 — Extracted Patient Data")
    p = state["patient_json"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Name", p.get("name") or "Not found")
    c2.metric("Age", p.get("age") or "Not found")
    c3.metric("# Needs", len(p.get("needs", [])))
    needs = p.get("needs", [])
    if needs:
        for n in needs:
            st.write(f"• {n}")
    with st.expander("Raw JSON"):
        st.json(p)


def show_agent2(state):
    st.subheader("🎫 Agent 2 — CRM Ticket")
    st.text_area("CRM Ticket",
                 value=state["crm_ticket"],
                 height=200,
                 disabled=True)


def show_agent3(state):
    st.subheader("📊 Agent 3 — FBT Calculation")
    fbt = state["fbt_result"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Salary", f"${fbt['salary']:,.2f}")
    c2.metric("FBT Rate", f"{int(fbt['fbt_rate'] * 100)}%")
    c3.metric("FBT Payable", f"${fbt['fbt_amount']:,.2f}")
    st.info(fbt["explanation"])


def empty_state(intake_text, salary):
    return {
        "intake_text": intake_text,
        "patient_json": {},
        "crm_ticket": "",
        "salary": salary,
        "fbt_result": {},
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Page layout
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Patient Intake Pipeline",
                   page_icon="🏥",
                   layout="wide")
st.title("🏥 Patient Intake Pipeline")
st.caption("3-Agent LangGraph chain: Extract → CRM Ticket → FBT Calculator")
st.divider()

# ── Inputs ─────────────────────────────────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    st.subheader("📋 Patient Intake Text")
    intake_text = st.text_area(
        label="intake",
        label_visibility="collapsed",
        placeholder=(
            "Example: Hi, I'm James O'Brien, 52 years old. "
            "I've had persistent chest tightness for a week and need an ECG. "
            "I'd also like a referral to a cardiologist."),
        height=180,
    )

with right:
    st.subheader("💰 FBT Salary Input")
    salary = st.number_input(
        "Annual salary ($)",
        min_value=0.0,
        value=80000.0,
        step=1000.0,
        format="%.2f",
        help="Agent 3 calculates Fringe Benefits Tax as salary × 0.47",
    )

st.divider()

# ── Buttons ────────────────────────────────────────────────────────────────────
st.subheader("▶  Run Agents")
b1, b2, b3, b4 = st.columns(4)
run_all = b1.button("🚀 Run Full Pipeline",
                    type="primary",
                    use_container_width=True)
run_agent1 = b2.button("1️⃣  Agent 1 Only", use_container_width=True)
run_agent2 = b3.button("2️⃣  Agents 1 + 2", use_container_width=True)
run_agent3 = b4.button("3️⃣  FBT Only", use_container_width=True)

st.divider()

# ══════════════════════════════════════════════════════════════════════════════
#  Button handlers
# ══════════════════════════════════════════════════════════════════════════════

if run_all:
    if not intake_text.strip():
        st.warning("⚠️ Please enter some patient intake text first.")
        st.stop()
    check_api_key()
    with st.spinner("Running full 3-agent pipeline…"):
        result = build_pipeline().invoke(empty_state(intake_text, salary))
    st.success("✅ Pipeline complete!")
    show_agent1(result)
    st.divider()
    show_agent2(result)
    st.divider()
    show_agent3(result)

elif run_agent1:
    if not intake_text.strip():
        st.warning("⚠️ Please enter some patient intake text first.")
        st.stop()
    check_api_key()
    with st.spinner("Running Agent 1…"):
        result = agent1_extract(empty_state(intake_text, salary))
    st.success("✅ Agent 1 done!")
    show_agent1(result)

elif run_agent2:
    if not intake_text.strip():
        st.warning("⚠️ Please enter some patient intake text first.")
        st.stop()
    check_api_key()
    with st.spinner("Running Agents 1 + 2…"):
        state = agent1_extract(empty_state(intake_text, salary))
        state = agent2_crm_ticket(state)
    st.success("✅ Agents 1 & 2 done!")
    show_agent1(state)
    st.divider()
    show_agent2(state)

elif run_agent3:
    check_api_key()
    with st.spinner("Running Agent 3 (FBT)…"):
        state = agent3_fbt(empty_state("", salary))
    st.success("✅ Agent 3 done!")
    show_agent3(state)
