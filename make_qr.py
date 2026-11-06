"""Generate signed QR images for the reports in reports.json.

    python make_qr.py                 # all reports -> qr/<报告编号>.png
    python make_qr.py --only SQI-...  # a single report
    python make_qr.py --base-url https://verify.example.org
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import quote, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import qrcodegen
import render
import sign

HERE = os.path.dirname(os.path.abspath(__file__))


def build_url(base_url: str, secret: str, report_no: str) -> str:
    return f"{base_url.rstrip('/')}/v/{quote(report_no, safe='')}?k={sign.signature(secret, report_no)}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=os.path.join(HERE, "config.json"))
    parser.add_argument("--reports", default=os.path.join(HERE, "reports.json"))
    parser.add_argument("--out", default=os.path.join(HERE, "qr"))
    parser.add_argument("--base-url", default=None, help="override service.base_url")
    parser.add_argument("--only", default=None)
    parser.add_argument("--scale", type=int, default=12)
    parser.add_argument("--no-caption", action="store_true")
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        config = json.load(fh)
    with open(args.reports, encoding="utf-8") as fh:
        reports = json.load(fh)

    secret = config["service"]["secret"]
    base_url = args.base_url or config["service"]["base_url"]
    if secret.startswith("CHANGE-ME"):
        print("WARNING: placeholder secret in config.json — regenerate before production.", file=sys.stderr)
    if "127.0.0.1" in base_url or "localhost" in base_url:
        print("WARNING: base_url points at localhost; phones will not be able to scan it.", file=sys.stderr)
    elif base_url.startswith("http://"):
        host = urlparse(base_url).hostname or ""
        private = host.startswith("192.168.") or host.startswith("10.") or host.startswith("172.")
        if not private:
            print("WARNING: base_url is not https; WeChat will warn about the page.", file=sys.stderr)

    numbers = [args.only] if args.only else list(reports)
    os.makedirs(args.out, exist_ok=True)

    for number in numbers:
        url = build_url(base_url, secret, number)
        qr = qrcodegen.QrCode.encode_text(url, qrcodegen.ECL_Q)
        path = os.path.join(args.out, f"{number}.png")
        render.render_png(
            qr.to_rows(),
            path,
            scale=args.scale,
            border=4,
            caption=None if args.no_caption else "扫码核验报告真伪",
        )
        print(f"{number}  v{qr.version}  {url}")


if __name__ == "__main__":
    main()
