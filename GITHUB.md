# 用 GitHub Pages 部署（不需要服务器）

GitHub Pages 只能托管静态文件，所以核验方式从“后台查询”改成“**预先给每份报告生成一个页面**”：

```
docs/
├─ index.html                    查验首页（输入编号 → 跳转）
├─ v/WB2603019335/index.html     这份报告的核验页
├─ 404.html                      编号不存在时显示
├─ .nojekyll
└─ CNAME                         （可选）自定义域名
```

扫码地址变成 `https://<用户名>.github.io/<仓库>/v/WB2603019335/`。

## 步骤

**1. 建仓库**：GitHub 新建一个仓库，例如 `report-verify`。免费账号要选 **Public**（私有仓库开 Pages 需要 Pro）。

**2. 推送代码**

```bash
cd report-verify
git init
git add .
git commit -m "report verification"
git branch -M main
git remote add origin https://github.com/<用户名>/report-verify.git
git push -u origin main
```

**3. 构建静态站**

```bash
python build_static.py --base-url https://<用户名>.github.io/report-verify
```

`docs/` 生成好，`qr/` 里的二维码也一并按这个地址重新生成。

**4. 提交并开启 Pages**

```bash
git add docs qr
git commit -m "build site"
git push
```

仓库 → **Settings → Pages** → Source 选 **Deploy from a branch** → Branch `main`、目录 `/docs` → Save。

等 1–2 分钟，访问 `https://<用户名>.github.io/report-verify/`。

**5. 验证**：手机关 WiFi，微信扫 `qr/WB2603019335.png`，应直接打开核验页。

## 加自己的域名（建议）

```bash
python build_static.py --base-url https://verify.example.com --domain verify.example.com
git add docs && git commit -m "custom domain" && git push
```

- 域名 DNS 加一条 `CNAME` 记录：`verify` → `<用户名>.github.io`
- 仓库 **Settings → Pages → Custom domain** 填 `verify.example.com`，勾选 **Enforce HTTPS**
- 证书由 GitHub 自动签发，通常几分钟生效

用自有域名后，二维码指向的就是你自己的域名，客户扫码看到的不再是 `github.io`。

## 必须知道的三个限制

| 限制 | 说明 |
|---|---|
| **国内访问不稳定** | `github.io` 在大陆经常很慢或间歇性打不开，微信有时直接提示“无法打开”。给客户、监管扫码用，这个风险很实在 |
| **没有动态查询** | 新增报告必须重跑 `build_static.py` 再 push；作废报告要把对应目录删掉 |
| **没有签名校验** | 静态页是公开文件，`?k=` 无法验证。防篡改靠“页面只存在于你的仓库”，比动态版弱 |

## 建议的用法

- **内部演示、给领导看效果**：GitHub Pages 完全够用，零成本、十分钟上线。
- **正式印在报告上**：换成国内云服务器 + 已备案的自有域名（见 [DEPLOY.md](DEPLOY.md)），或者直接用院里的官网域名，稳定性和可信度都高得多。
