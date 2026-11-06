"""Build a static version of the verification site for GitHub Pages.

GitHub Pages only serves files, so instead of a lookup service every report
gets its own page at v/<报告编号>/index.html. Missing numbers fall through to
404.html.

    python build_static.py --base-url https://<user>.github.io/<repo>
    python build_static.py --base-url https://verify.example.com --domain verify.example.com

Output: docs/  (commit it, then enable Pages -> Deploy from branch -> /docs)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from urllib.parse import quote

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pages
import qrcodegen
import render

HERE = os.path.dirname(os.path.abspath(__file__))


def write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=os.path.join(HERE, "config.json"))
    parser.add_argument("--reports", default=os.path.join(HERE, "reports.json"))
    parser.add_argument("--out", default=os.path.join(HERE, "docs"))
    parser.add_argument("--base-url", required=True, help="如 https://user.github.io/report-verify")
    parser.add_argument("--domain", default=None, help="自定义域名，会写入 docs/CNAME")
    parser.add_argument("--scale", type=int, default=16)
    args = parser.parse_args()

    with open(args.config, encoding="utf-8") as fh:
        config = json.load(fh)
    with open(args.reports, encoding="utf-8") as fh:
        reports = json.load(fh)

    inst = config["institution"]
    title = config["service"]["title"]
    base = args.base_url.rstrip("/")

    if os.path.isdir(args.out):
        shutil.rmtree(args.out)
    os.makedirs(args.out, exist_ok=True)

    # 首页
    index_inner = pages.form("", static_root="./")
    write(os.path.join(args.out, "index.html"),
          pages.shell(title, inst, index_inner, "报告查验"))

    # 每个报告一个页面
    qr_dir = os.path.join(HERE, "qr")
    os.makedirs(qr_dir, exist_ok=True)
    for number, record in reports.items():
        no = number.strip().upper()
        inner = pages.form(no, static_root="../../") + pages.result("found", no) + pages.details(record)
        write(os.path.join(args.out, "v", quote(no, safe=""), "index.html"),
              pages.shell(title, inst, inner, "报告查验"))

        url = f"{base}/v/{quote(no, safe='')}/"
        qr = qrcodegen.QrCode.encode_text(url, qrcodegen.ECL_Q)
        render.render_png(qr.to_rows(), os.path.join(qr_dir, f"{no}.png"),
                          scale=args.scale, border=4, caption="扫码核验报告真伪")
        print(f"{no}  v{qr.version}  {url}")

    # 404：编号不存在
    not_found = pages.form("", static_root="./") + pages.result("missing", "")
    write(os.path.join(args.out, "404.html"),
          pages.shell("报告不存在", inst, not_found, "报告查验"))

    # GitHub Pages 需要 .nojekyll，否则下划线开头的文件会被忽略
    write(os.path.join(args.out, ".nojekyll"), "")

    if args.domain:
        write(os.path.join(args.out, "CNAME"), args.domain + "\n")
        print(f"CNAME -> {args.domain}")

    print(f"\n静态站点已生成：{args.out}")
    print("推送到 GitHub 后，Settings → Pages → Deploy from a branch → /docs")


if __name__ == "__main__":
    main()
