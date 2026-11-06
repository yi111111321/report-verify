"""GitHub deployment helper (API side).

Token is read from the GITHUB_TOKEN environment variable and is never printed,
written to disk, or committed.

    python deploy_github.py whoami
    python deploy_github.py create   [--repo report-verify]
    python deploy_github.py pages    [--repo report-verify]
    python deploy_github.py status   [--repo report-verify]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()


def api(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    if not TOKEN:
        sys.exit("GITHUB_TOKEN is not set")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "sqi-report-verify")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read() or b"{}")
        except Exception:
            return exc.code, {}


def whoami() -> str:
    status, body = api("GET", "/user")
    if status != 200:
        sys.exit(f"token rejected (HTTP {status}): {body.get('message', '')}")
    return body["login"]


def create(repo: str) -> str:
    login = whoami()
    print(f"账号：{login}")
    status, body = api("POST", "/user/repos", {
        "name": repo,
        "private": False,
        "auto_init": False,
        "description": "检测报告在线查验（报告编号核验页）",
    })
    if status == 201:
        print(f"已创建仓库 {body['full_name']}")
    elif status == 422 and "already exists" in str(body.get("errors", "")):
        print(f"仓库已存在：{login}/{repo}")
    else:
        sys.exit(f"创建仓库失败 HTTP {status}: {body.get('message', '')}")
    return login


def pages(repo: str, path: str = "/docs") -> None:
    login = whoami()
    status, body = api("POST", f"/repos/{login}/{repo}/pages", {
        "source": {"branch": "main", "path": path},
    })
    if status in (201, 204):
        print(f"已开启 Pages，目录 {path}")
    elif status == 409:
        status2, _ = api("PUT", f"/repos/{login}/{repo}/pages", {
            "source": {"branch": "main", "path": path},
        })
        print("Pages 已存在，已更新来源" if status2 in (200, 204) else f"更新 Pages 失败 HTTP {status2}")
    else:
        print(f"开启 Pages 返回 HTTP {status}: {body.get('message', '')}")


def status(repo: str) -> None:
    login = whoami()
    code, body = api("GET", f"/repos/{login}/{repo}/pages")
    if code == 404:
        print("Pages 尚未开启")
        return
    url = body.get("html_url", "")
    print(f"站点：{url}")
    build = body.get("status") or "unknown"
    print(f"构建状态：{build}")
    if body.get("cname"):
        print(f"自定义域名：{body['cname']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["whoami", "create", "pages", "status"])
    parser.add_argument("--repo", default="report-verify")
    args = parser.parse_args()

    if args.action == "whoami":
        print(whoami())
    elif args.action == "create":
        print(create(args.repo))
    elif args.action == "pages":
        pages(args.repo)
    else:
        status(args.repo)


if __name__ == "__main__":
    main()
