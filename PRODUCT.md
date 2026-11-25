# Product: Project Overlord — Financial Defense Engine (PS-BA1)

## What it is
An accounts-payable audit tool that reconciles three documents before an invoice is paid: the Purchase Order (what was authorized), the Goods Receipt (what physically arrived), and the Vendor Invoice (what is billed). A 5-node LangGraph pipeline (PO Parser, Vision Agent, Invoice Parser, Auditor, Supervisor) finds overcharges and short deliveries, drafts a clause-cited dispute email, and settles the verified amount.

## Who uses it, and where
- Accounts-payable clerks and controllers at a desk, reviewing invoices in batches under Net-30 deadlines.
- Hackathon judges watching a 3-minute live demo on a projector (browser zoom 80–90%), who must read the result from across a room.

## The one job of the main screen
Show, at a glance, whether this invoice should be paid, how much, and why. Order of reading: documents in → run the check → verdict and amount → explanation → action (dispute or pay).

## Product truths (must stay accurate)
- Scenario A: PO #8842 authorizes $500.00, invoice INV-2024-001 bills $600.00, unauthorized $100.00 Setup Fee.
- Scenario B: 10 GPUs ordered and billed, 8 delivered, $2,000.00 overcharge; Vision draws a box over missing stock.
- Scenario C: clean match, $0.00 variance, eligible for UPI payment.
- Supervisor line: "600 - 500 = 100. Calculations mathematically verified."
- Dispute toast scales a dispute by 5,000 invoices/month × 2% × 12.
- Models: gemini-3.5-flash (fallback gemini-3.1-flash-lite); deterministic offline fallback.

## Brand commitments
- Name: Project Overlord. Track PS-BA1. Tone: calm, exact, financial; no hype words in the UI.
- Mode: Operate (task tool). Scanability and trust over decoration.
- Constraints: built in Gradio 6 (Python); styling is CSS over Gradio components plus HTML renderers in app.py.
