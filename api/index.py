import os
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from app import OVERLORD_CSS, OVERLORD_HEAD, OVERLORD_THEME, demo  # noqa: E402

fastapi_app = FastAPI(title="Project Overlord // Financial Defense Engine")


@fastapi_app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "project-overlord"}


# Gradio 6 applies theme/css/head at launch or mount time, not in Blocks(); without them the UI renders unstyled.
app = gr.mount_gradio_app(
    fastapi_app, demo, path="/", theme=OVERLORD_THEME, css=OVERLORD_CSS, head=OVERLORD_HEAD, ssr_mode=False,
    allowed_paths=[tempfile.gettempdir()],  # generated GR scans live in /tmp on every serverless instance
)

_gradio_asgi = app


async def app(scope, receive, send):  # noqa: F811
    """Vercel's rewrite hands every request the path /api/index.py; vercel.json passes the real one as __ovpath."""
    if scope.get("type") in ("http", "websocket"):
        pairs = parse_qsl(scope.get("query_string", b"").decode("latin-1"), keep_blank_values=True)
        original = next((v for k, v in pairs if k == "__ovpath"), None)
        if original is not None:
            rest = urlencode([(k, v) for k, v in pairs if k != "__ovpath"]).encode("latin-1")
            scope = {**scope, "path": original, "raw_path": original.encode("utf-8"), "query_string": rest}
    await _gradio_asgi(scope, receive, send)
