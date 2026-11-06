"""Switch the site to a new domain in one step.

    python set_domain.py --domain verify.sqi.org.cn
    python set_domain.py --url https://verify.sqi.org.cn --domain verify.sqi.org.cn

What it does:
  1. rewrites service.base_url in config.json
  2. rebuilds docs/ with the new base URL
  3. writes docs/CNAME when --domain is given
  4. regenerates the QR images in qr/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=None, help="站点根地址，如 https://verify.sqi.org.cn")
    parser.add_argument("--domain", default=None, help="自定义域名，会写入 docs/CNAME")
    args = parser.parse_args()

    if not args.url and not args.domain:
        parser.error("至少给一个：--url 或 --domain")

    url = args.url or f"https://{args.domain}"
    if not re.match(r"^https://", url):
        sys.exit("url 必须是 https:// 开头，微信对 http 页面会提示不安全")
    url = url.rstrip("/")

    domain = args.domain or re.sub(r"^https://([^/]+).*$", r"\1", url)

    config_path = os.path.join(HERE, "config.json")
    with open(config_path, encoding="utf-8") as fh:
        config = json.load(fh)
    old = config["service"]["base_url"]
    config["service"]["base_url"] = url
    with open(config_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"config.json: {old} -> {url}")

    cmd = [sys.executable, os.path.join(HERE, "build_static.py"), "--base-url", url]
    if args.domain:
        cmd += ["--domain", args.domain]
    subprocess.run(cmd, check=True, cwd=HERE)

    print(f"""
下一步（只有你能做）：

1. DNS：{domain} 加 CNAME 记录 -> yi111111321.github.io
   （如果换成国内服务器，就加 A 记录指向服务器 IP）

2. GitHub：仓库 Settings → Pages → Custom domain 填 {domain}
   再勾上 Enforce HTTPS，证书通常几分钟签好

3. 提交并推送：
   git add -A && git commit -m "切换域名到 {domain}" && git push
""")


if __name__ == "__main__":
    main()
