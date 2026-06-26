#!/usr/bin/env python3
"""Minimal web UI server for Fitting AI."""
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app" / "index.html"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from replicate_client import load_dotenv, run, token_configured  # noqa: E402

HOST = os.environ.get("FITTING_AI_HOST", "127.0.0.1")
PORT = int(os.environ.get("FITTING_AI_PORT", "8765"))


class StableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionAbortedError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)

def _parse_multipart(body: bytes, content_type: str) -> dict[str, dict]:
    """ponytail: minimal multipart parser (cgi removed in Python 3.13)."""
    m = re.search(r'boundary=(?:"([^"]+)"|([^\s;]+))', content_type)
    if not m:
        raise ValueError("multipart boundary missing")
    boundary = (m.group(1) or m.group(2)).encode()
    fields: dict[str, dict] = {}
    for part in body.split(b"--" + boundary):
        if not part or part in (b"--\r\n", b"--", b"\r\n"):
            continue
        chunk = part.lstrip(b"\r\n")
        if chunk.endswith(b"\r\n"):
            chunk = chunk[:-2]
        head, _, data = chunk.partition(b"\r\n\r\n")
        if data.endswith(b"\r\n"):
            data = data[:-2]
        name = filename = None
        for line in head.decode("utf-8", "replace").split("\r\n"):
            if "content-disposition" not in line.lower():
                continue
            for seg in line.split(";"):
                seg = seg.strip()
                if seg.startswith("name="):
                    name = seg[5:].strip('"')
                elif seg.startswith("filename="):
                    filename = seg[9:].strip('"')
        if name:
            fields[name] = {"data": data, "filename": filename}
    return fields


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            if not APP.is_file():
                self._send(404, b"index.html not found", "text/plain; charset=utf-8")
                return
            self._send(200, APP.read_bytes(), "text/html; charset=utf-8")
            return

        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/download":
            qs = urllib.parse.parse_qs(parsed.query)
            url = (qs.get("url") or [""])[0]
            if not url.startswith("https://replicate.delivery/") and not url.startswith(
                "https://pbxt.replicate.delivery/"
            ):
                self._send(400, b"invalid url", "text/plain; charset=utf-8")
                return
            try:
                with urllib.request.urlopen(url, timeout=60) as remote:
                    data = remote.read()
                    ctype = remote.headers.get("Content-Type", "image/jpeg")
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Disposition", 'attachment; filename="fitting-ai-result.jpg"')
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as exc:  # noqa: BLE001
                self._send(500, str(exc).encode(), "text/plain; charset=utf-8")
            return

        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/try-on":
            self._send(404, b'{"error":"Not found"}', "application/json")
            return

        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._send(400, b'{"error":"multipart/form-data required"}', "application/json")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            form = _parse_multipart(body, ctype)
        except ValueError as exc:
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode()
            self._send(400, body, "application/json; charset=utf-8")
            return

        human_field = form.get("human")
        garment_field = form.get("garment")
        if not human_field or not human_field.get("data") or not garment_field or not garment_field.get("data"):
            body = json.dumps({"error": "human, garment images required"}, ensure_ascii=False).encode()
            self._send(400, body, "application/json; charset=utf-8")
            return

        category = form.get("category", {}).get("data", b"upper_body").decode() or "upper_body"

        try:
            human_bytes = human_field["data"]
            garment_bytes = garment_field["data"]
            url = run(
                human_bytes,
                garment_bytes,
                human_name=human_field.get("filename"),
                garment_name=garment_field.get("filename"),
                category=category,
            )
            body = json.dumps({"imageUrl": url}, ensure_ascii=False).encode()
            self._send(200, body, "application/json; charset=utf-8")
        except Exception as exc:  # noqa: BLE001
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode()
            self._send(500, body, "application/json; charset=utf-8")


def main() -> None:
    load_dotenv()
    if token_configured():
        print("REPLICATE_API_TOKEN: OK")
    else:
        print("경고: REPLICATE_API_TOKEN 없음 — src/.env 확인 후 서버 재시작")
    server = StableThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"Fitting AI: {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n종료")
        server.server_close()


if __name__ == "__main__":
    main()
