import os
import sys
from pathlib import Path

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
    fastapi_app, demo, path="/", theme=OVERLORD_THEME, css=OVERLORD_CSS, head=OVERLORD_HEAD, ssr_mode=False
)
