from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pymupdf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app


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
    assert "TOTAL RECOVERED: $250.00" in last[1]
    assert "DISCREPANCY DETECTED: $250.00 OVERCHARGE" in last[4]
    assert "INV-7711" in last[5]
    assert "PO #7711" in last[5]


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
    why_hist, _ = app.chat_with_auditor("Why did you flag this?", [], ctx)
    assert why_hist[-1]["content"] == (
        "The Purchase Order authorized a flat fee of $500.00. "
        "The Vendor Invoice billed $600.00, citing an unauthorized 'Setup Fee'. "
        "Therefore, an overcharge of $100.00 was detected."
    )
    refusal_hist, _ = app.chat_with_auditor("What is the capital of France?", [], ctx)
    assert refusal_hist[-1]["content"] == (
        "I am a specialized Financial Auditor. I can only answer questions "
        "regarding the current PO, Invoice, and Goods Receipt."
    )


def test_chaos_mode_and_certificate_export():
    steps = list(app.run_audit("Scenario C: Clean 3-Way Match ($0.00 Variance)", "3-Way Match", chaos_mode=True))
    last = steps[-1]
    assert "[VISION ALERT]" in last[3]
    assert "ov-vision-badge--alert" in last[8]
    app.gr.Info = lambda *_a, **_kw: None
    cert_path = app.export_audit_certificate(last[9])
    assert cert_path is not None and Path(cert_path).is_file()
