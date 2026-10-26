#!/usr/bin/env python3
"""Servidor local que imita el API del SICEE (POST getCargosElecciones) y su servidor de descargas."""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
ROOT = Path(sys.argv[1]); PORT = int(sys.argv[2])
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if not self.path.endswith("/getCargosElecciones") or body.get("tipo") != "FEDERALES_":
            self.send_response(404); self.end_headers(); return
        d = ROOT / f"FEDERALES_{body['anio']}"
        items = [{"anio": body["anio"], "tipo_ambito": "FEDERALES_", "nombre": z.stem.replace("_", " ").title(), "ruta_zip": z.name}
                 for z in sorted(d.glob("*.zip"))] if d.exists() else []
        b = json.dumps(items).encode(); self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        pre = "/ACTASSICEEN2024/download/"
        p = ROOT / unquote(self.path[len(pre):]) if self.path.startswith(pre) else None
        if not p or not p.is_file(): self.send_response(404); self.end_headers(); return
        b = p.read_bytes(); self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
