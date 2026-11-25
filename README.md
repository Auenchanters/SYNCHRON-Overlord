# Project Overlord // The Financial Defense Engine (PS-BA1)

Autonomous Three-Way Invoice, Purchase Order & Goods-Receipt Reconciliation Bot built with **LangGraph**, **Gemini 1.5 Pro**, **Gemini Vision**, **Gyansutr RAG**, and **Gradio 6**.

---

## Problem Statement (PS-BA1)
Enterprises suffer massive annual budget leakage because Accounts Payable (AP) teams manually cross-reference three disconnected records: the **Purchase Order (PO)**, the physical **Goods Receipt (GR)**, and the incoming **Vendor Invoice**. Manual reconciliation is slow, error-prone, and leads to organizations paying inflated vendor rates, hidden surcharges, or bills for undelivered goods.

---

## Architecture (LangGraph + Gemini + Gyansutr RAG)
Project Overlord orchestrates a 4-node **LangGraph `StateGraph`** inside an Obsidian Mission Control interface:

1. **`po_parser_node` (Gyansutr RAG + Gemini 1.5 Pro):** Cleans, chunks, and retrieves governing pricing caps and non-billable extras clauses from the Purchase Order (`PO #8842`).
2. **`vision_agent_node` (Gemini 1.5 Flash Vision):** Inspects uploaded Goods Receipt images (with an auto-injected dock-scan fallback so live demos never crash) to verify physical delivery quantities.
3. **`invoice_parser_node`:** Extracts line items, base fees, and hidden surcharges (`Setup Fee: $100.00`) from the vendor invoice.
4. **`auditor_node`:** Cross-references all three records, flags discrepancies or Chaos Vision exceptions, logs an fsync'd JSONL compliance receipt (`workspace/receipts/overlord_audit.jsonl`), and drafts the dispute email.

---

## Key Features
- **3-Column XAI Visual Diffing:** Highlights authorized PO caps in green (`$500.00`) and unauthorized invoice line items (`Setup Fee`, `$600.00`) in pulsing red, paired with a flashing `TOTAL RECOVERED` financial impact metric.
- **Explainable AI (XAI) Chatbot:** Memory-backed `gr.Chatbot` (`Chat with the Auditor`) with strict financial-audit domain guardrails, quick-ask chips, and clause-grounded explanations.
- **Chaos Mode (Adversarial Vision Switch):** Sidebar toggle that injects simulated real-world Vision failures (`[VISION ALERT] Logo not visible in Goods Receipt...`) to prove active anomaly detection.
- **Multi-Scenario Matrix & Audit Modes:** Switch between Unauthorized Setup Fee (`$100`), Short-Delivery GPU Fraud (`$3,000`), and Clean 3-Way Match (`$0.00`), plus `2-Way`, `3-Way`, and `4-Way (Tax Verification)` modes.
- **Send Dispute Kill Shot:** One-click `"Send Dispute to Vendor"` action firing an API toast, green confirmation banner, and immutable ledger entry.
- **Donut Challenge Hooks:** Pre-wired commented LangGraph nodes (`translate_dispute_email()`, `calculate_tax()`) at the bottom of `app.py`.

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Configure Gemini API key in .env
# GOOGLE_API_KEY=your_key_here

# 3. Launch Mission Control UI
python app.py
```

Open **http://localhost:7860** in your browser.
