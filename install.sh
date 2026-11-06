#!/usr/bin/env bash
# 静态站一键部署（Ubuntu / Debian）
# 用法：sudo ./install.sh verify.sqi.org.cn
set -euo pipefail

DOMAIN="${1:-}"
if [ -z "$DOMAIN" ]; then
  echo "用法: sudo ./install.sh <域名>" >&2
  exit 1
fi

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "==> 安装 Docker"
  curl -fsSL https://get.docker.com | sh
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "缺少 docker compose 插件，请先安装：apt install docker-compose-plugin" >&2
  exit 1
fi

printf 'DOMAIN=%s\n' "$DOMAIN" > .env

echo "==> 启动 Caddy"
docker compose -f docker-compose.static.yml up -d
sleep 3
docker compose -f docker-compose.static.yml ps

echo
echo "完成。确认 DNS 已把 $DOMAIN 指向本机公网 IP，然后访问 https://$DOMAIN"
echo "证书签发日志：docker compose -f docker-compose.static.yml logs -f web"
