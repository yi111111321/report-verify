"""报告查验服务（Python 标准库，无第三方依赖）。

    GET /                 查验页
    GET /?no=<编号>       手动查询
    GET /v/<编号>?k=<签名> 扫码直达（签名由签发端生成）
    GET /qr               放大显示二维码，便于手机扫屏幕
    GET /healthz          探活

运行：python app.py [--host 0.0.0.0 --port 8787]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pages
import sign

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "config.json"), encoding="utf-8") as fh:
    CONFIG = json.load(fh)
with open(os.path.join(HERE, "reports.json"), encoding="utf-8") as fh:
    REPORTS: dict[str, dict] = {k.strip().upper(): v for k, v in json.load(fh).items()}

INST = CONFIG["institution"]
SERVICE = CONFIG["service"]
SECRET = SERVICE["secret"]


def page(state: str = "idle", no: str = "", record: dict | None = None) -> bytes:
    inner = pages.form(no) + pages.result(state, no)
    if state == "found" and record:
        inner += pages.details(record)
    html = pages.shell(SERVICE["title"], INST, inner, "报告查验")
    return html.encode("utf-8")


def qr_page() -> bytes:
    """Show the generated QR images large, for scanning off the screen."""
    import base64

    folder = os.path.join(HERE, "qr")
    blocks = []
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(".png"):
                continue
            with open(os.path.join(folder, name), "rb") as fh:
                data = base64.b64encode(fh.read()).decode("ascii")
            blocks.append(
                f"<div class='qrpage'><img src='data:image/png;base64,{data}' alt='QR'>"
                f"<p>{pages.escape(name[:-4])}</p></div>"
            )
    html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>二维码 · {pages.escape(SERVICE['title'])}</title>
<style>{pages.CSS}body{{background:#f6f6f6}}</style></head>
<body><div class="page" style="background:#f6f6f6">
{''.join(blocks) or '<div class="qrpage"><p>还没有生成二维码</p></div>'}
</div></body></html>"""
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "ReportCheck/1.0"

    def _send(self, payload: bytes, status: int = 200, ctype: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/healthz":
            self._send(b"ok", 200, "text/plain; charset=utf-8")
            return

        if parsed.path == "/qr":
            self._send(qr_page())
            return

        if parsed.path == "/":
            no = (params.get("no", [""])[0] or "").strip().upper()
            if not no:
                self._send(page())
                return
            record = REPORTS.get(no)
            self._send(page("found" if record else "missing", no, record))
            return

        match = re.fullmatch(r"/v/(.+)", parsed.path)
        if match:
            no = unquote(match.group(1)).strip().upper()
            key = params.get("k", [""])[0]
            if not sign.verify(SECRET, no, key):
                self._send(page("badlink", no))
                return
            record = REPORTS.get(no)
            self._send(page("found" if record else "missing", no, record))
            return

        self._send(page(), 404)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=SERVICE.get("listen_host", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(SERVICE.get("listen_port", 8787)))
    args = parser.parse_args()
    if SECRET.startswith("CHANGE-ME"):
        print("WARNING: placeholder secret in config.json", file=sys.stderr)
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"serving on http://{args.host}:{args.port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
