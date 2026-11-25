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
