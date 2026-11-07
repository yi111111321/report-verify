"""DNSPod 记录管理（可选）。

需要环境变量 DNSPOD_TOKEN，格式为 "ID,Token"（在 https://console.dnspod.cn/account/token 创建）。

    python dns_dnspod.py list   --domain ffuf.cn
    python dns_dnspod.py create --domain ffuf.cn --sub verify --type CNAME --value yi111111321.github.io
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://dnsapi.cn/"
TOKEN = os.environ.get("DNSPOD_TOKEN", "").strip()


def call(path: str, **params) -> dict:
    if not TOKEN:
        sys.exit("DNSPOD_TOKEN 未设置（格式：ID,Token）")
    data = {"login_token": TOKEN, "format": "json", "lang": "cn", **params}
    req = urllib.request.Request(
        API + path,
        data=urllib.parse.urlencode(data).encode(),
        headers={"User-Agent": "sqi-report-verify/1.0"},
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["list", "create"])
    parser.add_argument("--domain", required=True)
    parser.add_argument("--sub", default="verify")
    parser.add_argument("--type", default="CNAME")
    parser.add_argument("--value", default="yi111111321.github.io")
    parser.add_argument("--ttl", default="600")
    args = parser.parse_args()

    if args.action == "list":
        res = call("Record.List", domain=args.domain)
        status = res.get("status", {})
        print(f"status: {status.get('code')} {status.get('message')}")
        for rec in res.get("records", []):
            print(f"  {rec.get('name'):12s} {rec.get('type'):6s} {rec.get('value')}  ttl={rec.get('ttl')}")
        return

    res = call(
        "Record.Create",
        domain=args.domain,
        sub_domain=args.sub,
        record_type=args.type,
        record_line="默认",
        value=args.value,
        ttl=args.ttl,
    )
    status = res.get("status", {})
    print(f"status: {status.get('code')} {status.get('message')}")
    print(json.dumps(res.get("record", {}), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
