from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app  # noqa: E402

SCENARIO_B = "Scenario B: Short-Delivery GPU Fraud ($2,000 Overcharge)"
SCENARIO_C = "Scenario C: Clean 3-Way Match ($0.00 Variance)"


def test_dynamic_edited_invoice_parsing():
    custom_po = (
        "PURCHASE ORDER NO.: PO #7711\n"
        "VENDOR: Meridian Labs\n"
        "01. 1x Cloud Audit Node ........ $1,000.00\n"
        "MAXIMUM AUTHORIZED AMOUNT: $1,000.00\n"
    )
    custom_inv = (
        "INVOICE NO.: INV-7711\n"
        "01. 1x Cloud Audit Node ........ $1,000.00\n"
        "02. Rush Onboarding Fee ........ $250.00\n"
        "TOTAL DUE: $1,250.00\n"
    )
    steps = list(
        app.run_audit(
            app.DEFAULT_SCENARIO,
            "3-Way Match",
            po_text_input=custom_po,
            inv_text_input=custom_inv,
            gr_image=None,
            chaos_mode=False,
            apply_tax=False,
        )
    )
    last = steps[-1]
    assert last[0]["interactive"] is True
    assert "Total recovered" in last[1] and "$250.00" in last[1]
    assert "Discrepancy detected: $250.00 overcharge" in last[4]
    assert "INV-7711" in last[5]
    assert "PO #7711" in last[5]

    # The Goods Receipt is what separates a 3-Way from a 2-Way match.
    three_way = list(app.run_audit(SCENARIO_B, "3-Way Match"))[-1]
    assert "Discrepancy detected: $2,000.00 overcharge" in three_way[4]
    assert "Pay</span><span class=\"ov-fig-value\">$8,000.00" in three_way[4]
    assert "Hold</span><span class=\"ov-fig-value\">$2,000.00" in three_way[4]
    assert "10000 - 8000 = 2000. Calculations mathematically verified." in three_way[3]
    assert three_way[9]["payable"] == 8000.00
    two_way = list(app.run_audit(SCENARIO_B, "2-Way Match"))[-1]
    assert "Cleared for payment" in two_way[4]

    # Tax is applied to both sides in a 3-Way match, but the 4-Way tax document makes the delivery exempt.
    taxed_three = list(app.run_audit(SCENARIO_C, "3-Way Match", apply_tax=True))[-1]
    assert "Cleared for payment" in taxed_three[4]
    taxed_four = list(app.run_audit(SCENARIO_C, "4-Way Match (Tax Verification)", apply_tax=True))[-1]
    assert "Discrepancy detected: $120.00 overcharge" in taxed_four[4]

    # A renamed fee is still caught: anything outside the PO schedule is non-billable.
    renamed = custom_inv.replace("Rush Onboarding Fee", "Onboarding Retainer")
    renamed_last = list(app.run_audit(app.DEFAULT_SCENARIO, "3-Way Match", po_text_input=custom_po, inv_text_input=renamed))[-1]
    assert "Total recovered" in renamed_last[1] and "$250.00" in renamed_last[1]


def test_pdf_extraction_via_pymupdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        pdf_path = f.name
    try:
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((72, 72), "PURCHASE ORDER NO.: PO #5555\n01. 1x GPU Cluster ........ $2,000.00")
        doc.save(pdf_path)
        doc.close()
        text = app.extract_uploaded_document_text(pdf_path)
        parsed = app.parse_po_document(text)
        assert parsed["po_number"] == "PO #5555"
        assert parsed["authorized_amount"] == 2000.00
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


def test_xai_chatbot_guardrail_and_exact_reply():
    steps = list(app.run_audit(app.DEFAULT_SCENARIO, "3-Way Match"))
    ctx = steps[-1][9]
    po_text = app.SCENARIOS[app.DEFAULT_SCENARIO]["po_text"]
    inv_text = app.SCENARIOS[app.DEFAULT_SCENARIO]["inv_text"]

    about_hist, _ = app.chat_with_auditor("What is the invoice about?", [], ctx, po_text, inv_text)
    about_reply = about_hist[-1]["content"]
    assert "600" in about_reply and "can only answer" not in about_reply.lower()

    why_hist, _ = app.chat_with_auditor("Why did you flag this?", [], ctx, po_text, inv_text)
    assert "100" in why_hist[-1]["content"]

    memo_hist, _ = app.chat_with_auditor(
        "Draft a 2-sentence internal memo approving the base $500 payment but rejecting the $100 fee.",
        [], ctx, po_text, inv_text,
    )
    assert "500" in memo_hist[-1]["content"] and "100" in memo_hist[-1]["content"]

    hypo_hist, _ = app.chat_with_auditor(
        "Explain what the system would do if the invoice was $450 instead of $600. Would it pass or fail?",
        [], ctx, po_text, inv_text,
    )
    assert "pass" in hypo_hist[-1]["content"].lower()

    refusal_hist, _ = app.chat_with_auditor("What is the capital of France?", [], ctx, po_text, inv_text)
    refusal = refusal_hist[-1]["content"].lower()
    assert "paris" not in refusal
    assert "specialized financial auditor" in refusal

    # Replies are grounded in the executed audit, not in Scenario A constants.
    ctx_b = list(app.run_audit(SCENARIO_B, "3-Way Match"))[-1][9]
    why_b, _ = app.chat_with_auditor("Why did you flag this?", [], ctx_b, "", "")
    assert "2,000.00" in why_b[-1]["content"] and "8,000.00" in why_b[-1]["content"]
    hypo_b, _ = app.chat_with_auditor("What if the invoice was $9,000 instead?", [], ctx_b, "", "")
    assert "fail" in hypo_b[-1]["content"].lower()


def test_chaos_mode_and_certificate_export():
    steps = list(app.run_audit("Scenario C: Clean 3-Way Match ($0.00 Variance)", "3-Way Match", chaos_mode=True))
    last = steps[-1]
    assert "[VISION ALERT]" in last[3]
    assert "ov-vision-badge--alert" in last[8]
    # A Vision hold must block settlement.
    col_upd, *_ = app.open_upi_checkout(last[9])
    assert col_upd["visible"] is False
    cert_path = app.export_audit_certificate(last[9])
    assert cert_path is not None and Path(cert_path).is_file()


def test_mega_update_modules():
    # 1. Supervisor Agent 5th node on Scenario A
    steps_a = list(app.run_audit(app.DEFAULT_SCENARIO, "3-Way Match"))
    logs_a = steps_a[-1][3]
    assert "[SUPERVISOR AGENT] Verifying Auditor's math..." in logs_a
    assert "[SUPERVISOR AGENT] 600 - 500 = 100. Calculations mathematically verified. Routing to Dispute." in logs_a

    # 2. Vision XAI Bounding Box on Scenario B
    steps_b = list(app.run_audit("Scenario B: Short-Delivery GPU Fraud ($2,000 Overcharge)", "3-Way Match"))
    logs_b = steps_b[-1][3]
    bbox_img_path = steps_b[-1][15]
    assert "[VISION XAI] Bounding box drawn over missing inventory." in logs_b
    assert bbox_img_path and Path(bbox_img_path).is_file()
    assert Path(bbox_img_path).name.startswith(app.XAI_IMAGE_PREFIX)
    # Re-running on the annotated image audits the clean scan, not a box drawn on a box.
    rerun = list(app.run_audit(SCENARIO_B, "3-Way Match", gr_image=bbox_img_path))[-1]
    assert "8 of 10 units" in rerun[2]

    # 3. UPI QR Checkout & Simulate Payment Success
    col_upd, qr_upd, _fb, _st = app.open_upi_checkout(steps_a[-1][9])
    assert col_upd["visible"] is True
    assert qr_upd["value"] and Path(qr_upd["value"]).is_file()
    pay_banner, _rows, _kpi = app.simulate_payment_success(steps_a[-1][9])
    assert "Payment of $500.00 successful. Ledger updated." in pay_banner

    # 4. CFO ROI Calculator & Popup Flex
    roi_md = app.calculate_cfo_roi(5000, 600, 2.5)
    assert "Project Overlord will save you **$900,000** annually." in roi_md
    toasts: list[str] = []
    app.gr.Info = lambda msg: toasts.append(msg)
    app.send_dispute_to_vendor(steps_a[-1][5], steps_a[-1][9])
    assert any("Dispute sent. You just saved $100. At your current scale, this amounts to $120,000 saved this year." in t for t in toasts)

    # 5. Nothing to dispute on a clean match; payment settles the verified payable, not a fixed $500.
    clean = list(app.run_audit(SCENARIO_C, "3-Way Match"))[-1]
    banner, _btn = app.send_dispute_to_vendor(clean[5], clean[9])
    assert "No dispute needed" in banner
    steps_b_ctx = steps_b[-1][9]
    pay_b, _rows, _kpi = app.simulate_payment_success(steps_b_ctx)
    assert "Payment of $8,000.00 successful." in pay_b

    # 6. Motion layer: the intro script and its vendored libraries are served as JavaScript modules.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    client = TestClient(app.gr.mount_gradio_app(FastAPI(**app.APP_KWARGS), app.demo, path="/", head=app.OVERLORD_HEAD))
    config = client.get("/config", headers={"Accept-Encoding": "gzip"})
    assert "overlord_motion.js" in config.text and config.headers.get("content-encoding") == "gzip"
    script = app.MOTION_SCRIPT_URL.split("?")[0]
    for url in (script, script.replace("overlord_motion.js", "vendor/three.min.js"),
                script.replace("overlord_motion.js", "vendor/gsap.min.js")):
        resp = client.get(url)
        assert resp.status_code == 200 and "javascript" in resp.headers["content-type"], url


def test_photo_documents_parse_and_audit():
    """A bill read from a photo is written in the preset layout, so the normal parsers and the 3-way check run on it."""
    po = app.format_document_text(
        {"number": "7310", "vendor": "Cafe Lido", "lines": [{"qty": 4, "description": "Veg thali", "amount": 48}], "total": 48},
        "po",
    )
    bill = app.format_document_text(
        {"number": "0931", "vendor": "Cafe Lido", "lines": [{"qty": 4, "description": "Veg thali", "amount": "48.00"}], "tax": 0, "total": 52.8},
        "invoice",
    )
    assert "PO #7310" in po and "MAXIMUM AUTHORIZED AMOUNT: $48.00" in po
    inv = app.parse_invoice_document(bill)
    assert inv["invoice_number"] == "INV-0931" and inv["billed_total"] == 52.80
    last = list(app.run_audit(app.DEFAULT_SCENARIO, "3-Way Match", po, bill))[-1]
    assert last[9]["variance"] == 4.80
    assert "Charges outside the itemised lines" in last[9]["reason"]
    # Offline there is no vision model: a photo yields no text, and the editor keeps what it had.
    assert app.transcribe_document_image("samples/synthetic/set1_restaurant_bill_cafe_lido.jpg", "invoice") == ""
    assert app.format_document_text({"lines": []}, "invoice") == ""


def _verdict(po_text, inv_text, gr_data=None):
    po, inv = app.parse_po_document(po_text), app.parse_invoice_document(inv_text)
    gr = gr_data or {"delivered_qty": app.primary_goods_line(po["line_items"])["qty"]}
    d = app.reconcile_three_way(po, gr, inv)
    return d["pay_amount"], d["variance"], d


def test_user_bills_found_in_testing():
    """Regressions from bills a user would send: each case was wrong before the fix."""
    # Typed PDFs: "Grand Total" / "Amount Due" are totals, not one more billed line (was billed twice: $1,500).
    po = "PO Number: PO-3310\nVendor: Northwind\n3    27in Monitor  (3 x $250.00)   $750.00\nGrand Total: $750.00"
    inv = "Invoice Number: NW-2291\n3 x 27in Monitor: $750.00\nSubtotal: $750.00\nAmount Due: $750.00"
    assert app.parse_invoice_document(inv)["billed_total"] == 750.0
    assert _verdict(po, inv)[:2] == (750.0, 0.0)

    # Rupees with lakh commas, and an invoice number with slashes (was the demo's $500 / $600 and "SL").
    po = "PO No: PO-IN-0042\n1 x Laptop ........ Rs. 1,20,000.00\nTotal: Rs. 1,20,000.00"
    inv = "Invoice No: SL/24-25/118\n1 x Laptop ........ INR 1,25,000.00\nTotal: ₹1,25,000.00"
    assert app.parse_invoice_document(inv)["invoice_number"] == "SL/24-25/118"
    assert _verdict(po, inv)[:2] == (120000.0, 5000.0)
    # A user's document without numbers never borrows the demo's PO, invoice or amounts.
    assert app.parse_po_document("Office chairs, see attached")["po_number"] == "the purchase order"
    assert app.parse_invoice_document("Thanks for your order")["billed_total"] == 0.0

    # Unit prices in the item name ("@ $12" vs "@ $14") still match the PO line: only the $100 difference is held.
    po = "PO-5521\n  01. 50x USB-C cable @ $12.00 ........ $600.00\n  MAXIMUM AUTHORIZED AMOUNT: $600.00"
    inv = "INV-7781\n  01. 50x USB-C cable @ $14.00 ........ $700.00\nTOTAL DUE: $700.00"
    assert _verdict(po, inv)[:2] == (600.0, 100.0)

    # One line over its PO price while the total is under the cap: pay the bill minus the overcharge, not the cap.
    po = "PO-6604\n  01. 1x Desk lamp ........ $100.00\n  02. 1x Filing cabinet ........ $100.00\n  MAXIMUM AUTHORIZED AMOUNT: $200.00"
    inv = "INV-5512\n  01. 1x Desk lamp ........ $150.00\n  02. 1x Filing cabinet ........ $40.00\nTOTAL DUE: $190.00"
    assert _verdict(po, inv)[:2] == (140.0, 50.0)

    # A discount line is read as negative and is not disputed.
    inv = "INV-3390\n  01. 10x Folding chair ........ $200.00\n  02. 1x Loyalty discount ........ $-20.00\nTOTAL DUE: $180.00"
    po = "PO-2207\n  01. 10x Folding chair ........ $200.00\n  MAXIMUM AUTHORIZED AMOUNT: $200.00"
    assert _verdict(po, inv)[:2] == (180.0, 0.0)

    # A receiving note counted per line: 2 of 4 mice missing is held even though every keyboard arrived.
    po = "PO-8120\n  01. 4x Keyboard ........ $200.00\n  02. 4x Wireless mouse ........ $100.00\n  MAXIMUM AUTHORIZED AMOUNT: $300.00"
    inv = "INV-0457\n  01. 4x Keyboard ........ $200.00\n  02. 4x Wireless mouse ........ $100.00\nTOTAL DUE: $300.00"
    pay, hold, d = _verdict(po, inv, {"delivered_qty": 6, "delivered_by_line": {"keyboard": 4, "wireless mouse": 2}})
    assert (pay, hold) == (250.0, 50.0) and (d["delivered_qty"], d["ordered_qty"]) == (6, 8)

    # No receipt uploaded for the user's own PO: the demo's dock scan is not counted against it (was "1 of 50 delivered").
    state = {"po_text": po, "invoice_text": inv, "gr_image_path": app.DEFAULT_GR_IMAGE_PATH, "scenario_name": app.DEFAULT_SCENARIO,
             "audit_mode": "3-Way Match", "apply_tax": False, "chaos_mode": False, "discrepancy": {}, "dispute_email": "",
             "po_data": {}, "gr_data": {}, "invoice_data": {}, "status": "running", "clause_check": None, "step_logs": [], "logs": []}
    final = app.OVERLORD_GRAPH.invoke(state)
    assert final["gr_data"]["not_checked"] and final["discrepancy"]["variance"] == 0.0
    assert "We will pay" not in final["dispute_email"] and "PO-8120" in final["dispute_email"]


def test_edge_case_bills_round_two(tmp_path):
    """Round 2 of user testing: edge cases that each gave a wrong verdict, explanation or upload result."""
    # European numbers (dot thousands, comma decimals) and PDF soft hyphens in document numbers.
    po = "PO No: PO­DE­311\n4 x Konferenzstuhl ........ €1.200,00\nTotal: €1.200,00"
    inv = "Invoice No: BM­2026­77\nPO: PO­DE­311\n4 x Konferenzstuhl ........ €1.250,00\nTotal: €1.250,00"
    assert app.parse_invoice_document(inv)["invoice_number"] == "BM-2026-77"
    assert _verdict(po, inv)[:2] == (1200.0, 50.0)
    assert [app._money_value(v) for v in ("£3,499.99", "€1.250", "$12.5")] == [3499.99, 1250.0, 12.5]

    # The same line billed twice is held as a repeat, not explained as "total exceeds payable".
    po = "PO-5150\n  01. 5x Standing desk ........ $500.00\n  MAXIMUM AUTHORIZED AMOUNT: $500.00"
    inv = "INV-0090 | PO REF: PO-5150\n  01. 5x Standing desk ........ $500.00\n  02. 5x Standing desk ........ $500.00\nTOTAL DUE: $1,000.00"
    pay, hold, d = _verdict(po, inv)
    assert (pay, hold) == (500.0, 500.0) and d["flagged_items"][0]["reason"].startswith("Billed again")

    # Price raised and short-shipped on one line: the disputed line carries the whole $300, both reasons named.
    po = "PO-3907\n  01. 10x 24in monitor @ $100.00 ........ $1,000.00\n  MAXIMUM AUTHORIZED AMOUNT: $1,000.00"
    inv = "INV-7781\n  01. 10x 24in monitor @ $110.00 ........ $1,100.00\nTOTAL DUE: $1,100.00"
    pay, hold, d = _verdict(po, inv, {"delivered_qty": 8})
    assert (pay, hold) == (800.0, 300.0) and d["flagged_items"][0]["excess"] == 300.0
    assert "exceeds PO line" in d["flagged_items"][0]["reason"] and "8 of 10" in d["flagged_items"][0]["reason"]

    # A partial invoice for exactly what arrived clears; an invoice for another PO is held whole for review.
    po = "PO-4410\n  01. 10x Office chair ........ $1,500.00\n  MAXIMUM AUTHORIZED AMOUNT: $1,500.00"
    assert _verdict(po, "INV-2201\n  01. 8x Office chair ........ $1,200.00\nTOTAL DUE: $1,200.00", {"delivered_qty": 8})[:2] == (1200.0, 0.0)
    pay, hold, d = _verdict(po, "INV-2201 | PO REF: PO-9753\n  01. 10x Office chair ........ $1,500.00\nTOTAL DUE: $1,500.00")
    assert (pay, hold) == (0.0, 1500.0) and "another order" in d["review"]
    assert app.parse_invoice_document("Ship to PO Box 4411\nTOTAL DUE: $5.00")["po_refs"] == []

    # Unreadable amounts never "clear": the old result was "Cleared for payment $0.00".
    pay, hold, d = _verdict(po, "Invoice No: X-1\nFolding chairs, see attached")
    assert d["detected"] and d["review"].startswith("Could not read") and pay == 0.0
    html = app.render_findings_html("done", variance=0.0, billed=0.0, payable=0.0, review=d["review"])
    assert "Needs review" in html and "Cleared" not in html

    # Uploads: a broken PDF or an unreadable binary never puts error text, server paths or raw bytes in the editor.
    (tmp_path / "broken.pdf").write_bytes(b"%PDF-1.4 broken")
    (tmp_path / "photo.heic").write_bytes(b"\x00\x01binary-not-an-image" * 20)
    assert app.extract_uploaded_document_text(str(tmp_path / "broken.pdf")) == ""
    assert app.extract_uploaded_document_text(str(tmp_path / "photo.heic")) == ""
    scanned = pymupdf.open()
    scanned.new_page().insert_image(pymupdf.Rect(0, 0, 400, 300), filename="samples/synthetic/set1_restaurant_bill_cafe_lido.jpg")
    scanned.save(tmp_path / "scan.pdf")
    assert app.extract_uploaded_document_text(str(tmp_path / "scan.pdf")) == ""  # offline: no vision model, no crash

    # "What if the invoice was $450?" is answered with exact arithmetic, not left to the model.
    ctx = {"executed": True, "po_id": "PO-4410", "inv_id": "INV-2201", "po_amount": 1500.0, "payable": 1200.0,
           "inv_total": 1200.0, "variance": 0.0}
    hist, _ = app.chat_with_auditor("What if the invoice was $450?", [], ctx, po, "")
    assert "PASS" in hist[-1]["content"] and "$450.00" in hist[-1]["content"]
