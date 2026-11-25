# Project Overlord (PS-BA1) — 3-Minute Live Pitch Script

Matches `Project_Overlord_Pitch_Prep_and_Script.pdf`. Before going on stage: server live on
http://localhost:7860, Scenario A selected, Chaos Mode OFF, browser zoom 80–90%.

Open the page a minute early and leave it on the landing page. The first click anywhere dissolves it into dust and opens the workspace;
make that click as you say "Meet Project Overlord". Use `http://localhost:7860/?intro=0` to skip the landing page.

### [0:00 – 0:30] Act 1: The Hook *(no clicking)*
> "Every year, enterprises lose millions of dollars to a quiet financial leak inside Accounts Payable: uncontracted invoice creep and short-shipped deliveries. Teams still manually cross-reference PDFs, warehouse delivery slips, and vendor invoices across disconnected tools—letting phantom fees slip through under Net-30 pressure.
>
> Meet **Project Overlord**—our autonomous Financial Defense Engine for Track **PS-BA1**."

### [0:30 – 1:10] Act 2: The 3-Pillar Setup *(gesture across 01 / 02 / 03)*
> "Overlord brings all three financial pillars side by side:
> - **01 / Purchase Order**: **PO #8842**, parsed by our **Gyansutr RAG** engine, locking authorized spend at **$500.00** with an explicit **Non-Billable Extras Clause**.
> - **02 / Goods Receipt**: physical delivery proof inspected by **Gemini 3.5 Flash Vision**.
> - **03 / Vendor Invoice**: **INV-2024-001**, where the vendor is billing **$600.00**."

### [1:10 – 1:50] Act 3: The Climax *(click **Execute 3-Way Match**, pause 2s)*
> "Our **5-node LangGraph** state machine routes from the PO Parser to Gemini Vision, extracts the Invoice line items, runs the 3-Way reconciliation in the Auditor, and passes through our **Supervisor Agent**—which independently verifies `600 - 500 = 100` before routing—so there are zero math hallucinations.
>
> **$500.00** locks green on the PO, **$600.00** and the unauthorized **Setup Fee** pulse red on the Invoice, and **TOTAL RECOVERED** flashes **$100.00**."

Telemetry line to point at: `[SUPERVISOR AGENT] 600 - 500 = 100. Calculations mathematically verified. Routing to Dispute.`

### [1:50 – 2:25] Act 4: XAI Chatbot + Vision Bounding Box
1. Click **Why did you flag this?** in the XAI chatbot.
2. Switch **Demo Scenario** to **Scenario B: Short-Delivery GPU Fraud ($2,000 Overcharge)** and click **Execute 3-Way Match**.

> "Judges don't want black-box AI—they want auditability. I click 'Why did you flag this?' and get a context-grounded explanation citing the exact PO cap and unauthorized fee—while off-topic prompts are blocked by guardrails.
>
> Now physical fraud detection. Scenario B: 10 GPUs ordered and billed, only 8 delivered. Look at **02 / Goods Receipt**: Gemini Vision + Pillow draw a red XAI bounding box over the empty bays: **MISSING INVENTORY: 2 OF 10 UNITS**, saving **$2,000** instantly."

Telemetry: `[SUPERVISOR AGENT] 10000 - 8000 = 2000. Calculations mathematically verified.`
Flex: switch Audit Mode to **2-Way Match** and re-run — it clears, because a 2-way check never looks at the dock. That is why the third document matters.

### [2:25 – 3:00] Act 5: Dispute, UPI Gateway & CFO Boardroom
1. Click **Send Dispute to Vendor** → green `[SUCCESS]` banner + scale toast.
2. Click **Proceed to Payment** → live UPI QR for the verified payable → **Simulate Payment Success**.
3. Open **CFO Boardroom** → drag a slider → closing line.

> "Detection alone isn't enough—we close the loop. One click on **Send Dispute to Vendor** dispatches the clause-cited dispute, seals an immutable JSONL audit record, and projects the annual savings at enterprise scale.
>
> For verified payouts, **Proceed to Payment** generates a live UPI QR code for the approved amount only—the disputed amount stays withheld. And in the **CFO Boardroom**, executives model annual savings in real time.
>
> **We just turned a manual 3-day AP bottleneck into a 3-second autonomous defense engine. We are Project Overlord.**"

Toast figures: the toast scales the dispute by 5,000 invoices/month × 2% × 12. A $100 dispute (Scenario A) shows **$120,000 saved this year**; a $2,000 dispute (Scenario B) shows **$2,400,000**. Dispatch on Scenario A if you want to quote $120,000.

### Flex moves (20 spare seconds)
| Move | Click | Proves |
| --- | --- | --- |
| Chaos Mode | Toggle **Chaos Mode** → Execute | Vision isn't hardcoded; 38.4% confidence Short-Payment Hold, payment blocked. |
| Live Edit / PDF | Col 3 → **Edit / Upload PDF**, rename or change a fee, re-run | PyMuPDF parsing; renamed fees (e.g. "Onboarding Retainer") are still flagged. |
| Audit Certificate | **Compliance Ledger & Export** → Export JSON | `OVL-CERT-*.json` for SOC2 teams. |
