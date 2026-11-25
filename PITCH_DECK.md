# PROJECT OVERLORD: Financial Defense Engine (PS-BA1) — 4-Slide Pitch Deck Specification

**Track:** Business Automation (`PS-BA1`: Autonomous Three-Way Invoice, Purchase Order & Goods-Receipt Reconciliation Bot)  
**Global Design System:**
- **Canvas Background:** Obsidian Void `#0A0B0E`
- **Card / Panel Surface:** `#12141A` with `1px` hairline borders `#2A2D37`
- **Primary Accent:** Neon Emerald `#10B981` (Verified / ROI / Flow)
- **Alert Accent:** Signal Crimson `#EF4444` (Discrepancy / Bounding Box)
- **Typography:** `Inter` (Bold headlines & crisp body copy) + `JetBrains Mono` (KPIs, tags, agent telemetry, architecture labels)

---

## Slide 1: The Problem & The Hook
- **Layout:** Asymmetric 2-column split (Left 60%: bold headline, bullet stack, bottom green solution bar; Right 40%: visual graphic).
- **Headline:** Enterprises Bleed Millions to "The Fragmented Match"
- **Sub-headline:** Why Accounts Payable is broken.
- **Bullet Points (The PS-BA1 Problem):**
  - AP teams manually reconcile three disconnected documents: **Purchase Orders (PO)**, **Goods Receipts (GR)**, and **Invoices**.
  - **The Leakage:** Companies pay inflated vendor rates (hidden fees) OR pay for goods that were never delivered (short-shipments).
  - **The Cost:** Millions lost annually due to human error, slow manual workflows, and zero real-time auditing.
- **The Solution (Bottom Highlight Callout — `#10B981` left border):**
  `PROJECT OVERLORD — A fully autonomous 3-Way Match Financial Defense Engine.`
- **Designer Visual / Background Note:** Dark `#0A0B0E` grid canvas with three fractured, floating document wireframes (`PO`, `GR`, `INVOICE`) connected by broken red dashed lines (`#EF4444`) leaking glowing red dollar icons into a void, contrasted by a crisp `#10B981` laser-shield line at the bottom representing Project Overlord intercepting the bleed.

---

## Slide 2: The Architecture (How It Works)
- **Layout:** Top tech-stack pill bar, center 5-node horizontal LangGraph pipeline diagram (`#12141A` cards connected by `#10B981` glowing arrows), bottom full-width Output Banner.
- **Headline:** Zero-Touch Orchestration
- **The Tech Stack (JetBrains Mono Pill Strip):**
  `LangGraph (Multi-Agent State Machine)` + `Gemini 1.5 Pro (Long-context)` + `Gemini Vision (Multimodal)` + `Gradio (Obsidian Dark-Mode UI)`
- **The 5-Agent Swarm:**
  1. **PO Parser:** Extracts authorized rates and quantities.
  2. **Vision Agent:** Physically verifies the Goods Receipt image.
  3. **Invoice Parser:** Extracts billed line items.
  4. **Auditor Agent:** Flags the discrepancy.
  5. **Supervisor Agent:** Mathematically verifies the Auditor's work to eliminate hallucinations.
- **The Output (Bottom Card — `#10B981` Glow):**
  An instant, legally grounded vendor dispute email.
- **Designer Visual / Background Note:** Deep `#0D0F14` circuit-board / terminal grid background. Render the 5 agents as sequential dark `#12141A` state-machine nodes (`START → 01 → 02 → 03 → 04 → 05 → END`) with `JetBrains Mono` edge labels (`[STATE: ROUTING]`, `600 - 500 = 100 VERIFIED`), visually emphasizing Node 5 (`Supervisor Agent`) acting as a deterministic mathematical firewall above Node 4 (`Auditor Agent`).

---

## Slide 3: The Killer Features (Why We Win)
- **Layout:** 2×2 Obsidian Bento Grid (`#12141A` cards, `1px` `#2A2D37` borders, crisp icon + `JetBrains Mono` badge on top-right of each card).
- **Headline:** Beyond Automation: XAI, Vision, and Instant Settlement
- **Card 1 — Feature 1: Vision XAI Bounding Boxes**
  If a vendor short-ships 8 GPUs instead of 10, the AI literally draws a red bounding box over the missing inventory in the warehouse photo.
- **Card 2 — Feature 2: Chaos Mode**
  A built-in adversarial toggle that tests the Vision AI live on stage to prove it isn't hardcoded.
- **Card 3 — Feature 3: UPI Payment Gateway**
  Once the correct amount is verified, the system dynamically generates a UPI QR code for instant, automated settlement.
- **Card 4 — Feature 4: The CFO Boardroom**
  Live ROI calculator showing exactly how much money the company saves at scale.
- **Designer Visual / Background Note:** Subtle `#0A0B0E` vignette with 4 high-contrast UI micro-crops inside each Bento card: (1) warehouse receipt photo with a pulsing `#EF4444` bounding box labeled `MISSING INVENTORY: 2 OF 10 UNITS`, (2) amber-accented `CHAOS MODE` toggle emitting `[VISION ALERT]`, (3) neon-emerald `#10B981` UPI QR matrix on `#0D0F14`, and (4) Bloomberg-style green ROI projection bar reading `$900,000+ ANNUAL SAVINGS`.

---

## Slide 4: The Demo & Business Impact
- **Layout:** Left 45%: Vertical 5-step Live Demo Flow timeline; Right 55%: Large hero Mission Control screenshot + bottom full-width Closing Statement banner.
- **Headline:** Recovering $900,000+ Annually in 3 Seconds *(or "$X Million in 3 Seconds" customized to target enterprise scale)*
- **The Live Demo Flow:**
  - **01.** Load PO & Invoice.
  - **02.** Gemini Vision verifies the Goods Receipt.
  - **03.** Supervisor Agent verifies the math.
  - **04.** System drafts the dispute email.
  - **05.** One-click UPI payment.
- **The Close (Centered Hero Statement — High-Contrast `#FFFFFF` + `#10B981`):**
  > "We didn't just build a hackathon project. We built the future of Accounts Payable. We are Project Overlord."
- **Designer Visual / Background Note:** Full-bleed dark `#0A0B0E` backdrop featuring a slight perspective mock of the live **Project Overlord Mission Control** dashboard glowing with `TOTAL RECOVERED: $100.00` in `#10B981` and the `DISCREPANCY DETECTED` `#EF4444` alert card, flanked by crisp `JetBrains Mono` step indicators (`01` through `05`) and a subtle emerald radial glow behind the closing statement.
