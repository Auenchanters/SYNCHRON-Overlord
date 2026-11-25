# Handoff — Zero-Touch AP Auditor

**Project:** GYANSUTR | Zero-Touch AP Auditor (hackathon MVP)
**Build location:** `C:\Users\Lenovo\Desktop\folderAp\ZeroTouch-AP-Auditor`
**Entry point:** `app.py`
**Local URL:** http://127.0.0.1:7860
**Stack:** Gradio 6.32, LangGraph, LangChain Google GenAI, Gemini
**Status:** Working locally. Live Gemini audit verified; deterministic fallback verified.

---

## 1. What this app does

An accounts-payable audit workspace that:

1. Parses the contract into explicit rate rules.
2. Parses the invoice into structured line items.
3. Audits invoice line items against contracted rates.
4. Drafts a dispute email for any overcharge.

The demo data flags one issue:

| Field | Value |
|---|---|
| Contracted rate | `$120.00 / hr` |
| Invoiced rate | `$150.00 / hr` |
| Quantity | `50.0 hrs` |
| Contracted amount | `$6,000.00` |
| Invoiced amount | `$7,500.00` |
| Variance | `$1,500.00` |
| Violated clause | `MSA Sec. 7.2` |

The UI streams telemetry while the LangGraph nodes run, then shows:

- A dark red audit alert.
- Yellow/red highlights in the contract and invoice panels.
- Updated metrics (`CONTRACTED`, `BILLED`, `VARIANCE`, `STATUS`).
- A populated dispute email with a copy button.

---

## 2. Run it

### Prerequisites

- Python 3.10+
- A Gemini API key

### Install

```powershell
pip install -r requirements.txt
```

### Configure

Create `.env` in the project root:

```dotenv
GOOGLE_API_KEY=your-key-here
GEMINI_MODEL=gemini-3.5-flash
GEMINI_FALLBACK_MODEL=gemini-3.1-flash-lite
GEMINI_THINKING_BUDGET=0
```

`.env` is gitignored. Do **not** commit it or paste the key into source.

Use `.env.example` as the safe template.

### Start

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:7860
```

If port `7860` is busy:

```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
python app.py
```

---

## 3. Architecture

`app.py` contains a four-node LangGraph pipeline:

```text
START
  -> parse_contract
  -> parse_invoice
  -> audit
  -> draft_email
  -> END
```

Shared state (`AuditState`):

```python
contract_text: str
invoice_text: str
contract_rules: list[dict]
invoice_data: dict
discrepancies: list[dict]
dispute_email: str
```

### Node responsibilities

| Node | Responsibility |
|---|---|
| `parse_contract` | Extract role, max hourly rate, clause reference, and quote. |
| `parse_invoice` | Extract vendor, invoice number, total, and line items. |
| `audit` | Compare invoice rates against contract rate caps. |
| `draft_email` | Draft a professional dispute email from findings. |

Structured output uses Pydantic models with `with_structured_output`.

### Model selection

`PRIMARY_MODEL` is tried first, then `FALLBACK_MODEL`.

Both `json_schema` and `function_calling` structured-output methods are attempted. If the live path fails, the UI falls back to the deterministic mock finding and dispute email, so the demo never dead-ends.

### Guardrail

The variance is recomputed deterministically:

```text
(invoiced_rate - contract_rate) x quantity
```

This prevents a model response from inventing a different total.

---

## 4. Environment / model notes

- The supplied key could not access `gemini-2.5-flash` or `gemini-2.0-flash` (`404 — no longer available to new users`).
- `gemini-3.8-flash` returned `503` high-demand errors during testing.
- Verified working models:
  - Primary: `gemini-3.5-flash`
  - Fallback: `gemini-3.1-flash-lite`
- A live audit can take roughly **15–180 seconds** depending on model latency and queueing. The final verification run took about **2 minutes 45 seconds**.
- Telemetry streams during the wait, so the button is disabled and progress remains visible.
- If the key is absent, the app runs the deterministic mock path and shows `API : OFFLINE (MOCK)` in the sidebar.

Do not change models blindly; confirm availability with the current key first.

---

## 5. UI implementation details

The design is a dark obsidian enterprise layout:

- Palette variables: `--bg`, `--panel`, `--panel-deep`, `--line`, `--text`, `--muted`, `--faint`, `--green`, `--red`, `--amber`.
- Hairline borders; no rounded cards.
- Inter for UI, JetBrains Mono for telemetry and document panels.
- No emojis, no glow effects on the primary button.
- Gradio footer hidden.

### Gradio 6-specific notes

Gradio 6 requires CSS and theme at launch time, not in the `Blocks` constructor:

```python
demo.queue().launch(
    theme=gr.themes.Base(),
    css=CUSTOM_CSS,
    server_name="0.0.0.0",
    server_port=7860,
    ssr_mode=False,
)
```

`ssr_mode=False` is required in this environment. Gradio 6's SSR mode can print the local URL and then hang without ever binding the port on Windows. The app uses client-side rendering only, so SSR is not needed.

`show_copy_button=True` is not supported in this version. The dispute textbox uses:

```python
buttons=["copy"]
```

### Important CSS fixes already applied

These are load-bearing; do not remove them without retesting.

1. **No global label hiding**

   Do not use:

   ```css
   .gradio-container label { display: none !important; }
   ```

   In Gradio 6, the `<label>` is the textbox container, not just label text. Hiding it hides the textarea and leaves a white block behind.

2. **Transparent Gradio wrappers**

   The white-box issue was caused by `.form` and `.block` wrappers with light backgrounds. These must stay transparent:

   ```css
   .form,
   .block.telemetry,
   .block.dispute {
       background: transparent !important;
       border: none !important;
       box-shadow: none !important;
   }
   ```

3. **Telemetry fills its column**

   The telemetry textarea is stretched through its wrapper chain:

   ```css
   .telemetry .wrap,
   .telemetry label,
   .telemetry .input-container,
   .telemetry textarea {
       height: 100% !important;
   }
   ```

4. **Sticky sidebar requires visible overflow**

   `.gradio-container` defaults to `overflow: hidden`, which silently disables `position: sticky` on the sidebar. This rule is required:

   ```css
   .gradio-container {
       overflow: visible !important;
   }
   ```

5. **Execute Audit button placement**

   The button sits directly below the status row, above the metadata block, so it stays near the top of the sticky sidebar. The sidebar is:

   ```css
   .sidebar {
       position: sticky;
       top: 0;
       align-self: flex-start;
       height: 100vh;
       overflow-y: auto;
   }
   ```

   Without the overflow fix in item 4, the button scrolls off-screen even though it is marked sticky.

---

## 6. Verification checklist

Run this before a demo.

- [ ] `python app.py` starts without errors.
- [ ] Page loads at `http://127.0.0.1:7860`.
- [ ] Sidebar shows `API : CONNECTED` when the key is valid.
- [ ] Execute Audit is visible near the top of the sidebar.
- [ ] Execute Audit is enabled and at least 40 px tall.
- [ ] Clicking it disables the button and starts telemetry.
- [ ] Scrolling the page keeps the sidebar and button visible.
- [ ] Telemetry stream ends with `DONE audit complete`.
- [ ] Metrics show `$6,000.00`, `$7,500.00`, `$1,500.00`, `FLAGGED`.
- [ ] Red audit alert renders with a 4 px left border.
- [ ] Contract and invoice highlights render.
- [ ] Dispute email is populated and copyable.
- [ ] No white/light-gray blocks appear before, during, or after the audit.
- [ ] No browser console errors.

### Useful browser checks

Find light-background blocks:

```js
[...document.querySelectorAll('*')]
  .filter(e => {
    const c = getComputedStyle(e).backgroundColor.match(/rgba?\((\d+), (\d+), (\d+)/);
    if (!c) return false;
    const [r, g, b] = c.slice(1).map(Number);
    const r0 = e.getBoundingClientRect();
    return (r * 299 + g * 587 + b * 114) / 1000 > 180 && r0.width > 50 && r0.height > 50;
  })
  .map(e => ({ tag: e.tagName, cls: e.className, bg: getComputedStyle(e).backgroundColor }));
```

Check button position:

```js
const b = [...document.querySelectorAll('button')]
  .find(x => (x.innerText || '').toUpperCase().includes('EXECUTE AUDIT'));
b.getBoundingClientRect();
```

Check sidebar stickiness by scrolling, then re-running the button check. `y` should remain near the top of the viewport.

---

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| White boxes where textareas should be | A `.form`/`.block` wrapper has a light background, or a label rule hid the textarea | Keep the transparency rules in section 5. |
| Execute Audit off-screen | `.gradio-container` has `overflow: hidden`, breaking sticky | Keep `overflow: visible !important`. |
| Execute Audit does nothing | API call still running; button disabled | Wait for `DONE audit complete`; check telemetry. |
| Live audit takes a long time | Gemini latency / queueing | Expected; telemetry streams. Fallback engages on failure. |
| `404 model no longer available` | Model unavailable to this key | Use `gemini-3.5-flash`; keep `gemini-3.1-flash-lite` fallback. |
| `503` from Gemini | Provider high demand | Retry; fallback path still produces a demo result. |
| Sidebar scrolls away | `overflow: hidden` ancestor, or sticky CSS removed | Reapply section 5 items 4 and 5. |
| Footer visible | Footer CSS removed | Keep `footer { display: none !important; }`. |
| Launch prints the local URL but the port never opens | Gradio 6 SSR mode hangs during startup | Keep `ssr_mode=False` in `launch()`. |
| Startup stalls for 30–60s before the URL appears | Gradio analytics/network check | Optional: set `GRADIO_ANALYTICS_ENABLED=False` before launching. |

---

## 8. File map

| File | Purpose |
|---|---|
| `app.py` | Full application: schemas, prompts, graph, render helpers, CSS, UI, launch. |
| `.env` | Local secrets and model configuration. Gitignored. Never commit. |
| `.env.example` | Safe template for environment setup. |
| `.gitignore` | Excludes `.env`, `.env.*`, caches, virtualenvs. |
| `requirements.txt` | `gradio`, `langgraph`, `langchain-google-genai`, `python-dotenv`. |
| `handoff.md` | This document. |

---

## 9. Security notes

- The Gemini key lives only in `.env`.
- `.env` is gitignored via `.env` and `.env.*`.
- Source code contains no hardcoded API key.
- Telemetry and prompts treat contract/invoice text as data, not instructions.
- The dispute email is a draft and explicitly marked pending human review.

---

## 10. Known limitations / next steps

- Single hardcoded contract and invoice pair; no upload flow yet.
- One demo discrepancy; the audit UI assumes a single primary finding.
- No persistence or audit history.
- No authentication; intended for local demo use only.
- The deterministic fallback is intentionally optimistic for demo safety; it is not a real OCR or pricing engine.
- For production, add file ingestion, validation, retries, audit logging, and human approval before sending any dispute email.

---

## 11. Current verified state

- Live Gemini audit completed end-to-end with the correct `$1,500.00` variance.
- Deterministic fallback verified with no key and with a simulated API failure.
- White-box regression fixed and rechecked.
- Execute Audit button verified visible at the top of the sticky sidebar, enabled before execution, disabled during execution, and still visible after page scroll.
- Server starts reliably with `python app.py` once `ssr_mode=False` is set.
- No light-background blocks detected before or during an audit run.

**Last verified:** November 24, 2026
