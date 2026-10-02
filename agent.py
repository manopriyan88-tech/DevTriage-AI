import json
import os
import time
import pandas as pd
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. Load Environment Variables & Initialize Client
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file! Check your .env setup.")

client = genai.Client(api_key=api_key)

# 2. Structured Output Schema
class TriageDecision(BaseModel):
    ticket_id: str
    category: str = Field(description="One of: Technical Bug, Billing, Account Access, Platform Usage")
    priority: str = Field(description="One of: Low, Medium, High, Critical")
    action: str = Field(description="Must be strictly AUTO_REPLY or ESCALATE_TO_HUMAN")
    confidence_score: float = Field(description="Float between 0.0 and 1.0 indicating confidence")
    reasoning: str = Field(description="Why this decision was made referencing the KB")
    suggested_response: str = Field(description="Client reply if AUTO_REPLY, or internal escalation note if ESCALATE_TO_HUMAN")

# 3. Load Knowledge Base
def load_knowledge_base(filepath: str = "knowledge_base.json") -> str:
    with open(filepath, "r") as f:
        kb_data = json.load(f)
    return json.dumps(kb_data, indent=2)

# 4. Triage Ticket with Extended Backoff
def triage_ticket(ticket: dict, kb_context: str, max_retries: int = 8) -> TriageDecision:
    prompt = (
        "You are an automated L1 Support Triage Agent for a developer SaaS platform.\n"
        "Analyze the incoming user ticket strictly against our internal Knowledge Base.\n\n"
        f"Internal Knowledge Base:\n{kb_context}\n\n"
        "Incoming Ticket:\n"
        f"- Ticket ID: {ticket['ticket_id']}\n"
        f"- Subject: {ticket['subject']}\n"
        f"- User Message: {ticket['message']}\n\n"
        "Rules:\n"
        "1. If the exact answer or standard troubleshooting steps exist in the Knowledge Base, set action to AUTO_REPLY.\n"
        "2. If the issue involves refund requests, billing disputes, or alleged compiler/test case errors (as specified in KB policies), you MUST set action to ESCALATE_TO_HUMAN.\n"
        "3. Ground all suggested responses purely on the provided Knowledge Base. Do NOT invent policies.\n"
    )

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TriageDecision,
                    temperature=0.1,
                ),
            )
            return TriageDecision.model_validate_json(response.text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"   [!] Rate limit reached. Waiting 60s for quota window reset (Attempt {attempt}/{max_retries})...")
                time.sleep(60)
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                wait_time = attempt * 8
                print(f"   [!] Server busy (503). Waiting {wait_time}s (Attempt {attempt}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"   [!] API Error: {err_str}")
                if attempt == max_retries:
                    raise e
                time.sleep(5)

    raise RuntimeError("Max retries exceeded.")

# 5. Batch Pipeline Execution
def run_triage_batch(csv_filepath: str = "tickets.csv"):
    kb_context = load_knowledge_base()
    df = pd.read_csv(csv_filepath)
    
    results = []
    total = len(df)
    print(f"[*] Processing {total} tickets using gemini-3.8-flash...\n")
    
    for count, (_, row) in enumerate(df.iterrows(), 1):
        ticket = row.to_dict()
        print(f"[{count}/{total}] Triaging {ticket['ticket_id']} - \"{ticket['subject']}\"...")
        decision = triage_ticket(ticket, kb_context)
        results.append(decision.model_dump())
        print(f"   +-- Status: {decision.action} | {decision.category} (Conf: {decision.confidence_score})")
        
        if count < total:
            print("   +-- Waiting 15s to respect free-tier RPM limits...")
            time.sleep(15)

    results_df = pd.DataFrame(results)
    results_df.to_csv("triage_results.csv", index=False)
    print("\n[+] Batch complete! Saved outputs to triage_results.csv")
    return results_df

if __name__ == "__main__":
    run_triage_batch()
