"""Measure Project Overlord: code quality, boot time, page weight, engine speed and Gemma 4 accuracy/latency.

    python bench/benchmark.py            # offline sections only (no network, no token)
    python bench/benchmark.py --live     # adds Gemma 4 reading/writing on samples/ (needs a Hugging Face login)

Results are printed and written to bench/results.json. The token is read in-process and never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
OFFLINE_ENV = {**os.environ, "OVERLORD_LIVE_LLM": "0", "GRADIO_ANALYTICS_ENABLED": "False", "PYTHONIOENCODING": "utf-8"}


def _median(xs: list[float]) -> float:
    return round(statistics.median(xs), 3)


def code_quality() -> dict:
    ruff = subprocess.run([PY, "-m", "ruff", "check", "."], cwd=ROOT, capture_output=True, text=True)
    t = time.perf_counter()
    tests = subprocess.run(
        [PY, "-m", "pytest", "-q", "-o", "addopts=", "--cov=app", "--cov-report=term", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, env=OFFLINE_ENV,
    )
    wall = time.perf_counter() - t
    out = tests.stdout
    passed = next((m.group(1) for m in map(re.compile(r"(\d+) passed").search, out.splitlines()) if m), "0")
    cover = next((ln.split()[-1] for ln in out.splitlines() if ln.startswith("app.py")), "?")
    return {
        "ruff_clean": ruff.returncode == 0,
        "tests_passed": int(passed),
        "coverage_app_py": cover,
        "test_wall_s": round(wall, 2),
        "app_py_lines": sum(1 for _ in open(ROOT / "app.py", encoding="utf-8")),
    }


def import_time(runs: int) -> dict:
    code = "import time;t=time.perf_counter();import app;print(time.perf_counter()-t)"
    xs = [float(subprocess.run([PY, "-c", code], cwd=ROOT, capture_output=True, text=True, env=OFFLINE_ENV).stdout.split()[-1]) for _ in range(runs)]
    return {"import_app_s": _median(xs), "runs": runs}


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url: str, gzip: bool = False) -> tuple[int, bytes, dict]:
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"} if gzip else {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, r.read(), dict(r.headers)


def boot_and_page(runs: int) -> dict:
    """Seconds from `python app.py` to the first HTTP 200, then bytes the page and its scripts cost."""
    boots, page = [], {}
    for i in range(runs):
        port = _free_port()
        env = {**OFFLINE_ENV, "GRADIO_SERVER_PORT": str(port), "PORT": str(port)}
        t = time.perf_counter()
        proc = subprocess.Popen([PY, "app.py"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        base = f"http://127.0.0.1:{port}"
        try:
            while time.perf_counter() - t < 90:
                try:
                    if _get(base + "/")[0] == 200:
                        break
                except OSError:
                    time.sleep(0.05)
            boots.append(time.perf_counter() - t)
            if i == 0:
                _, html, _ = _get(base + "/")
                raw = gz = 0
                for path in sorted((ROOT / "static").rglob("*.js")):  # every script the motion layer can load
                    url = f"{base}/gradio_api/file={quote(path.as_posix(), safe='/:')}"
                    raw += len(_get(url)[1])
                    _, body, hdr = _get(url, gzip=True)
                    gz += len(body)
                    page["static_gzip_served"] = hdr.get("Content-Encoding") == "gzip"
                t0 = time.perf_counter()
                cfg = _get(base + "/config")[1]
                html_wire = len(_get(base + "/", gzip=True)[1])
                page.update({
                    "html_kb": round(len(html) / 1024, 1),
                    "html_kb_over_wire": round(html_wire / 1024, 1),
                    "config_kb": round(len(cfg) / 1024, 1),
                    "config_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "own_static_kb": round(raw / 1024, 1),
                    "own_static_kb_over_wire": round(gz / 1024, 1),
                })
        finally:
            proc.terminate()
            proc.wait(timeout=15)
    return {"boot_to_http_200_s": _median(boots), "runs": runs, **page}


def _verdict(state: dict) -> tuple[float, float]:
    d = state["discrepancy"]
    billed = float(d["invoice_billed"])
    pay = round(min(float(d["payable_cap"]), billed), 2)
    return pay, round(billed - pay, 2)


def _state(app, scenario: str, po: str = "", inv: str = "", gr: str | None = None) -> dict:
    sc = app.SCENARIOS[scenario]
    return {
        "po_text": po or sc["po_text"], "invoice_text": inv or sc["inv_text"],
        "gr_image_path": gr or app.SCENARIO_GR_IMAGES[scenario], "discrepancy": {}, "dispute_email": "",
        "audit_mode": "3-Way Match", "apply_tax": False, "chaos_mode": False, "scenario_name": scenario,
        "po_data": {}, "gr_data": {}, "invoice_data": {}, "status": "running", "step_logs": [], "logs": [],
    }


def _timed_nodes(app, state: dict) -> tuple[dict, dict]:
    """Run the graph once; return the final state and seconds spent in each node."""
    final, nodes, t = dict(state), {}, time.perf_counter()
    for update in app.OVERLORD_GRAPH.stream(state, stream_mode="updates"):
        for name, delta in update.items():
            now = time.perf_counter()
            nodes[name] = round(now - t, 3)
            t = now
            final.update({k: v for k, v in (delta or {}).items() if k != "logs"})
    return final, nodes


def engine(runs: int) -> dict:
    """The audit graph and the full UI run (with its paced telemetry) on the offline engine."""
    os.environ["OVERLORD_LIVE_LLM"] = "0"
    import app

    out = {}
    for key, name in (("A", "Scenario A"), ("B", "Scenario B"), ("C", "Scenario C")):
        scenario = next(s for s in app.SCENARIOS if s.startswith(name))
        xs = []
        for _ in range(runs):
            t = time.perf_counter()
            final = app.OVERLORD_GRAPH.invoke(_state(app, scenario))
            xs.append(time.perf_counter() - t)
        t = time.perf_counter()
        for _ in app.run_audit(scenario):
            pass
        out[key] = {"graph_ms": round(_median(xs) * 1000, 1), "ui_run_s": round(time.perf_counter() - t, 2),
                    "pay_hold": _verdict(final)}
    return out


SAMPLES = ROOT / "samples"
READS = [  # (file, kind, expected total)
    ("synthetic/set1_handwritten_po_team_lunch.jpg", "po", 60.0),
    ("synthetic/set1_restaurant_bill_cafe_lido.jpg", "invoice", 66.0),
    ("synthetic/set2_handwritten_po_office_chairs.jpg", "po", 720.0),
    ("synthetic/set2_handwritten_invoice_office_chairs.jpg", "invoice", 760.0),
    ("real/cord_v2_test_001.jpg", "invoice", 91000.0),
    ("real/cord_v2_test_004.jpg", "invoice", 174600.0),
]
SETS = [  # (po, bill, receiving note, expected pay, expected hold)
    (0, 1, "synthetic/set1_receipt_note_lunch_all_received.jpg", 60.0, 6.0),
    (2, 3, "synthetic/set2_receipt_note_chairs_4_of_6.jpg", 480.0, 280.0),
]


def live(runs: int) -> dict:
    from huggingface_hub import get_token

    token = get_token()
    if not token:
        return {"skipped": "no Hugging Face login"}
    os.environ["HF_TOKEN"] = token
    os.environ["OVERLORD_LIVE_LLM"] = "1"
    import app

    reads, texts = [], []
    for rel, kind, expected in READS:
        lat, text = [], ""
        for _ in range(runs):
            t = time.perf_counter()
            text = app.transcribe_document_image(str(SAMPLES / rel), kind)
            lat.append(time.perf_counter() - t)
        parsed = app.parse_po_document(text) if kind == "po" else app.parse_invoice_document(text)
        got = float(parsed["authorized_amount"] if kind == "po" else parsed["billed_total"]) if text else None
        reads.append({"file": rel, "expected": expected, "read": got, "exact": got == expected, "median_s": _median(lat)})
        texts.append(text)

    sets = []
    for po_i, inv_i, note, pay, hold in SETS:
        final, nodes = _timed_nodes(app, _state(app, app.DEFAULT_SCENARIO, texts[po_i], texts[inv_i], str(SAMPLES / note)))
        got = _verdict(final)
        sets.append({"set": note.split("/")[1][:4], "expected": [pay, hold], "got": list(got), "correct": got == (pay, hold),
                     "delivered": final["gr_data"].get("delivered_qty"), "node_s": nodes})

    scen_b = next(s for s in app.SCENARIOS if s.startswith("Scenario B"))
    b_final, b_nodes = _timed_nodes(app, _state(app, scen_b))

    ctx = {"executed": True, "po_id": b_final["po_data"].get("po_number"), "inv_id": b_final["invoice_data"].get("invoice_number"),
           "po_amount": b_final["po_data"].get("authorized_amount"), "inv_total": b_final["discrepancy"]["invoice_billed"],
           "payable": b_final["discrepancy"]["payable_cap"], "variance": b_final["discrepancy"]["variance"]}
    chat_lat, reply = [], ""
    for _ in range(runs):
        t = time.perf_counter()
        hist, _ = app.chat_with_auditor("Why did you flag this?", [], ctx, b_final["po_text"], b_final["invoice_text"])
        chat_lat.append(time.perf_counter() - t)
        reply = hist[-1]["content"] if hist else ""
    return {
        "model": app.GEMMA_MODEL,
        "reads": reads,
        "reads_exact": f"{sum(r['exact'] for r in reads)}/{len(reads)}",
        "sets": sets,
        "scenario_b": {"pay_hold": list(_verdict(b_final)), "delivered": b_final["gr_data"].get("delivered_qty"), "node_s": b_nodes},
        "chat_median_s": _median(chat_lat),
        "chat_reply_chars": len(reply),
        "runs": runs,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also measure Gemma 4 on samples/ (network + HF login)")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default=str(ROOT / "bench" / "results.json"))
    args = ap.parse_args()

    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    os.environ["OVERLORD_WORKSPACE_DIR"] = tempfile.mkdtemp(prefix="overlord_bench_")  # keep the real ledger clean
    OFFLINE_ENV["OVERLORD_WORKSPACE_DIR"] = os.environ["OVERLORD_WORKSPACE_DIR"]
    results = {"code_quality": code_quality(), "import": import_time(args.runs), "boot_and_page": boot_and_page(args.runs),
               "engine_offline": engine(max(args.runs, 5))}
    if args.live:
        results["gemma_live"] = live(args.runs)
    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
