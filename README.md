# DevTriage-AI

An automated L1 Support Triage Agent for developer SaaS platforms. Grounded on an internal Knowledge Base with strict Pydantic validation, ultra-fast Groq LPU inference (Llama 3), and deterministic offline fallback handling.

## Tech Stack
- **Inference Engine:** Groq Cloud API (Llama 3)
- **Validation & Data Contract:** Pydantic (Structured JSON Schema)
- **Framework & UI:** Streamlit
- **Grounding Source:** Internal SOP Knowledge Base (`knowledge_base.json`)
- **Fault Tolerance:** Deterministic rule-based offline triage mode
