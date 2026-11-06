# 让全世界都能扫码打开

二维码本身只是一个网址。要做到「任何人、任何网络、用微信扫都能打开」，需要三样东西：

1. **公网域名**（例如 `verify.example.com`）
2. **有公网 IP 的服务器**（或云托管）
3. **HTTPS 证书**（微信对 `http://` 会提示不安全，正式报告必须 https）

这三样都在你的账号里，我这边无法替你申请或部署——本机没有公网 IP，运行环境也没有外网出口。

想先零成本跑通，可以先用静态站 + GitHub Pages，见 [GITHUB.md](GITHUB.md)；下面是在自己服务器上正式部署的步骤。

## 一、DNS 解析

在域名服务商添加 A 记录：

```
verify.example.com  ->  服务器公网 IP
```

中国大陆服务器用 80/443 对外提供网站需要 ICP 备案；没备案就用香港或海外服务器，或先备案再上线。

## 二、起服务（推荐 Docker + Caddy，自动 HTTPS）

把整个 `report-verify` 目录传到服务器：

```bash
scp -r report-verify root@你的服务器:/srv/
ssh root@你的服务器
cd /srv/report-verify
```

改两处再启动：

```bash
# config.json 里的 service.secret 换成长随机串
python3 -c "import secrets;print(secrets.token_urlsafe(48))"
```

```bash
export DOMAIN=verify.example.com
docker compose up -d
docker compose logs -f caddy     # 看到 certificate obtained 即成功
```

自检：

```bash
curl https://verify.example.com/healthz      # 返回 ok
```

## 三、生成指向公网域名的二维码

在服务器上（或任意装了 Python 的机器上）：

```bash
python make_qr.py --base-url https://verify.example.com
```

`qr/` 下的 PNG 就是要印到报告上的码。换域名或换报告后重跑这一条即可。

## 四、验收

1. 手机关掉 WiFi，只用移动数据；
2. 微信扫 `qr/` 里的二维码；
3. 应直接打开 `https://verify.example.com/v/<报告编号>?k=...` 并显示查验结果。

用移动数据是关键——连 WiFi 测不出公网是否真的通。

## 没有服务器怎么办

**临时测试**：内网穿透，能扫但不适合印在报告上（地址会变）。

```bash
# 在跑着 app.py 的机器上
cloudflared tunnel --url http://localhost:8787
# 会得到一个 https://xxx.trycloudflare.com 的地址
python make_qr.py --base-url https://xxx.trycloudflare.com
```

**云托管**：腾讯云 CloudBase、阿里云函数计算、Vercel 都能跑，需要把 `reports.json` 换成数据库或对象存储，`app.py` 的 Handler 逻辑可以直接复用。

## 打不开的排查顺序

| 现象 | 原因 |
|---|---|
| 微信提示「已停止访问该网页」 | 域名被拦截或未备案 |
| 一直转圈 | 安全组/防火墙没放行 443 |
| 打开是 404 或旧页面 | 二维码还是旧 `base_url` 生成的，重跑 `make_qr.py` |
| https 证书报错 | Caddy 没拿到证书，检查 80 端口是否放行 |
| 手机能开、别人不能 | 你用的是内网 IP 或穿透地址 |
