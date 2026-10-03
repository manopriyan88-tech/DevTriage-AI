import json
import os
import time
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()

st.set_page_config(page_title="DevTriage-AI Demo", page_icon="🤖", layout="centered")

st.title("🤖 DevTriage-AI Live Agent")
st.caption("Autonomous L1 Customer Support Triage powered by Groq (Llama 3) & Grounded Knowledge Base")

class TriageDecision(BaseModel):
    category: str = Field(description="One of: Technical Bug, Billing, Account Access, Platform Usage")
    priority: str = Field(description="One of: Low, Medium, High, Critical")
    action: str = Field(description="Must be strictly AUTO_REPLY or ESCALATE_TO_HUMAN")
    confidence_score: float = Field(description="Float between 0.0 and 1.0")
    reasoning: str = Field(description="Why this decision was made referencing the KB")
    suggested_response: str = Field(description="Draft response or escalation note")

@st.cache_data
def get_kb():
    with open("knowledge_base.json", "r") as f:
        return json.dumps(json.load(f), indent=2)

kb_context = get_kb()

def offline_triage(text: str) -> TriageDecision:
    lowered = text.lower()
    if any(k in lowered for k in ["refund", "charged", "cancelled", "cancel", "money"]):
        return TriageDecision(
            category="Billing", priority="High", action="ESCALATE_TO_HUMAN", confidence_score=1.0,
            reasoning="Per KB-04, automated agents cannot issue refunds or handle financial cancellation disputes. Mandated escalation to billing team.",
            suggested_response="Customer is disputing a $25 charge after cancellation. Escalated to Tier-2 Billing Operations with high priority."
        )
    elif any(k in lowered for k in ["camera", "black screen", "webcam", "screening"]):
        return TriageDecision(
            category="Technical Bug", priority="High", action="AUTO_REPLY", confidence_score=0.95,
            reasoning="Matches KB-02 troubleshooting runbook for browser media permissions during proctored tests.",
            suggested_response="Please check your browser permissions:\n1. Click the lock/tune icon beside your address bar.\n2. Ensure 'Camera' is set to 'Allow'.\n3. Restart Chrome and test at app.devplatform.io/device-test."
        )
    elif any(k in lowered for k in ["invoice", "tax", "accounting"]):
        return TriageDecision(
            category="Billing", priority="Low", action="AUTO_REPLY", confidence_score=0.95,
            reasoning="Grounded on KB-01 standard self-service invoice retrieval guide.",
            suggested_response="You can download monthly invoices under Workspace Settings > Billing > Invoices. Select the desired tax period to download PDF copies."
        )
    elif any(k in lowered for k in ["grader", "test case", "compiler", "time limit", "tle"]):
        return TriageDecision(
            category="Technical Bug", priority="High", action="ESCALATE_TO_HUMAN", confidence_score=0.98,
            reasoning="Per KB-05, all potential problem specification flaws or judge discrepancy claims must escalate to Engineering.",
            suggested_response="User reports discrepancy in Problem Judge runner regarding edge case evaluation. Routed to Core Engineering team for test case audit."
        )
    else:
        return TriageDecision(
            category="Platform Usage", priority="Medium", action="AUTO_REPLY", confidence_score=0.90,
            reasoning="Standard query mapped to general platform troubleshooting documentation.",
            suggested_response="Thank you for reaching out. Please consult our developer documentation or clear browser cache before retrying."
        )

# Sidebar Configuration
st.sidebar.header("Agent Controls")
demo_mode = st.sidebar.toggle("Simulation / Offline Mode", value=False)
st.sidebar.info("Engine: **Groq API**\nModel: **Llama 3 8B**")

scenarios = {
    "Billing Dispute (Escalate)": "I was charged $25 yesterday but I cancelled last week! Refund my money immediately!",
    "Webcam Permission Error (Auto-Reply)": "My camera shows a black screen while trying to start the screening test. How do I fix it?",
    "Compiler Bug Claim (Escalate)": "Your problem statement says 0 is considered even, but my solution failed test case 3. The grader is broken.",
    "Invoice Request (Auto-Reply)": "Where can our team download the September tax invoices for accounting?"
}

preset = st.selectbox("Choose a test ticket or write your own:", ["-- Custom Ticket --"] + list(scenarios.keys()))
default_val = scenarios[preset] if preset != "-- Custom Ticket --" else ""
ticket_text = st.text_area("Ticket Message:", value=default_val, height=120)

if st.button("⚡ Triage Ticket", type="primary", use_container_width=True):
    if not ticket_text.strip():
        st.warning("Please provide a ticket message.")
    else:
        decision = None
        status_box = st.empty()

        if demo_mode:
            status_box.info("Running grounded deterministic triage in offline mode...")
            time.sleep(0.4)
            decision = offline_triage(ticket_text)
            status_box.empty()
        else:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("GROQ_API_KEY missing from Secrets! Switching to Simulation Mode.")
                decision = offline_triage(ticket_text)
            else:
                client = Groq(api_key=api_key)
                system_prompt = (
                    "You are an automated L1 Support Triage Agent for a developer SaaS platform.\n"
                    f"Knowledge Base:\n{kb_context}\n\n"
                    "Rules:\n"
                    "1. If standard fix exists in KB -> AUTO_REPLY.\n"
                    "2. If refund request, billing dispute, or test case error -> ESCALATE_TO_HUMAN.\n"
                    "3. Ground all reasoning strictly on the Knowledge Base.\n\n"
                    f"Respond strictly in valid JSON format matching this schema:\n{TriageDecision.model_json_schema()}"
                )
                
                try:
                    status_box.info("Querying Groq (Llama 3)...")
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Incoming Ticket Message:\n{ticket_text}"}
                        ],
                        model="llama3-8b-8192",
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    decision = TriageDecision.model_validate_json(chat_completion.choices[0].message.content)
                    status_box.empty()
                except Exception as e:
                    st.error(f"Groq API Error: {e}")
                    status_box.warning("Auto-falling back to deterministic Knowledge Base triage...")
                    decision = offline_triage(ticket_text)

        if decision:
            st.divider()
            c1, c2, c3 = st.columns(3)
            
            if decision.action == "AUTO_REPLY":
                c1.metric("Action", "AUTO_REPLY", delta="Resolved Autonomously")
            else:
                c1.metric("Action", "ESCALATE", delta="Human Required", delta_color="inverse")
                
            c2.metric("Category", decision.category)
            c2.caption(f"Priority: **{decision.priority}**")
            c3.metric("Confidence", f"{int(decision.confidence_score * 100)}%")
            
            st.markdown("### 🔍 Grounded Rationale")
            st.info(decision.reasoning)
            
            st.markdown("### 💬 Suggested Output")
            st.code(decision.suggested_response, language="markdown")
              
