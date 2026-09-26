"""Serve QUANTGEN as a web app on 127.0.0.1:8552 without opening a browser,
so the Browser pane can screenshot each page. Dev-only launcher: Flet's
exported ASGI app under uvicorn."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import flet as ft
import uvicorn
import main

app = ft.run(main.main, export_asgi_app=True, assets_dir=os.path.join(ROOT, "assets"))
uvicorn.run(app, host="127.0.0.1", port=8552, log_level="info")
