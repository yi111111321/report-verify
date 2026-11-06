"""Shared HTML for the report-check page.

Used both by the dynamic server (app.py) and the static builder
(build_static.py) so the two never drift apart.
"""

from __future__ import annotations

from html import escape

CSS = """
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:#fff;color:#222;
 font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei","PingFang SC",sans-serif;
 -webkit-font-smoothing:antialiased}
.page{max-width:480px;margin:0 auto;background:#fff;min-height:100vh;display:flex;flex-direction:column}
.masthead{display:flex;align-items:center;gap:10px;background:#fff;padding:12px 16px;
 border-bottom:1px solid #e8e8e8}
.logo{flex:none;width:44px;height:44px;border-radius:7px;background:#0b4a8f;color:#fff;
 display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;letter-spacing:.5px}
.orgnames{min-width:0}
.org-cn{font-size:15.5px;font-weight:600;line-height:1.35;letter-spacing:.2px}
.org-en{font-size:10px;color:#8b96a1;line-height:1.35;margin-top:2px;
 white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.banner{height:158px;display:flex;align-items:center;justify-content:center;
 background:linear-gradient(135deg,#37434f 0%,#1d262e 55%,#2b3945 100%);position:relative;overflow:hidden}
.banner:after{content:"";position:absolute;inset:0;
 background:radial-gradient(120px 90px at 78% 30%,rgba(255,255,255,.10),transparent 70%)}
.banner span{position:relative;z-index:1;color:#fff;font-size:20px;letter-spacing:4px;font-weight:500;
 text-shadow:0 1px 2px rgba(0,0,0,.35)}
form{padding:18px 16px 4px;margin:0}
input{width:100%;height:46px;border:1px solid #d8d8d8;border-radius:4px;background:#fff;
 padding:0 12px;font-size:15px;color:#222;outline:none;font-family:inherit}
input:focus{border-color:#1a6fc4}
button{width:100%;height:46px;margin-top:12px;border:0;border-radius:4px;background:#1a6fc4;
 color:#fff;font-size:16px;letter-spacing:4px;font-family:inherit;cursor:pointer}
button:active{background:#155a9e}
.result{padding:16px 16px 2px;font-size:15px;line-height:1.75;font-weight:600;color:#c0261c}
.result b{font-weight:700}
.result .sub{display:block;font-weight:400;font-size:13px;color:#6b737b;margin-top:6px}
.card{margin:14px 16px 0;background:#fff;border:1px solid #e9e9e9;border-radius:6px;padding:2px 14px}
.card h2{font-size:12px;font-weight:600;color:#8b96a1;letter-spacing:.6px;margin:12px 0 2px}
.row{display:flex;justify-content:space-between;gap:18px;padding:10px 0;border-bottom:1px solid #f0f0f0}
.row:last-child{border-bottom:0}
dt{color:#7a838c;font-size:13px;flex:none}
dd{margin:0;text-align:right;font-size:13.5px;font-weight:500}
.foot{margin-top:auto;text-align:center;color:#9aa3ab;font-size:12px;padding:20px 16px 24px;
 border-top:1px solid #eee;line-height:2}
.foot .fine{color:#b3bac1;font-size:11.5px}
.qrpage{padding:24px 16px;text-align:center}
.qrpage img{width:330px;max-width:100%;image-rendering:pixelated}
.qrpage p{color:#6b737b;font-size:13px;word-break:break-all}
"""


def shell(title: str, institution: dict, inner: str, service: str, head_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta name="format-detection" content="telephone=no">
<meta name="robots" content="noindex">
<title>{escape(title)}</title>
<style>{CSS}</style>{head_extra}</head>
<body><div class="page">
<div class="masthead">
  <div class="logo">{escape(institution['brand'])}</div>
  <div class="orgnames">
    <div class="org-cn">{escape(institution['name'])}</div>
    <div class="org-en">{escape(institution['full_name_en'])}</div>
  </div>
</div>
<div class="banner"><span>检测报告在线查验</span></div>
{inner}
<div class="foot">
  <div>{escape(institution['short_name'])} · {escape(service)}</div>
  <div class="fine">本页仅用于核对报告编号是否由本机构出具</div>
</div>
</div></body></html>"""


def form(no: str = "", static_root: str | None = None) -> str:
    """查询表单。static_root 为静态站里的根路径前缀（如 './' 或 '../../'）。"""
    if static_root is None:
        return f"""<form method="get" action="/">
  <input name="no" value="{escape(no)}" placeholder="请输入报告编号" autocomplete="off" autocapitalize="characters">
  <button type="submit">查 询</button>
</form>"""
    return f"""<form id="q">
  <input id="no" name="no" value="{escape(no)}" placeholder="请输入报告编号" autocomplete="off" autocapitalize="characters">
  <button type="submit">查 询</button>
</form>
<script>
document.getElementById('q').addEventListener('submit', function (e) {{
  e.preventDefault();
  var v = document.getElementById('no').value.trim().toUpperCase();
  if (v) location.href = '{static_root}v/' + encodeURIComponent(v) + '/';
}});
</script>"""


def result(state: str, no: str = "") -> str:
    if state == "found":
        return f"<div class='result'>报告编号为 <b>{escape(no)}</b> 的检测报告存在</div>"
    if state == "missing":
        if not no:
            return ("<div class='result'>未查询到该报告"
                    "<span class='sub'>请核对报告编号是否输入正确，或联系出具机构确认。</span></div>")
        return (f"<div class='result'>报告编号为 <b>{escape(no)}</b> 的检测报告不存在"
                f"<span class='sub'>请核对编号是否输入正确，或联系出具机构确认。</span></div>")
    if state == "badlink":
        return ("<div class='result'>该二维码校验未通过"
                "<span class='sub'>二维码可能被复制或篡改，请输入报告编号手动查询。</span></div>")
    return ""


def details(record: dict) -> str:
    rows = [
        ("样品名称", record.get("sample_name", "")),
        ("型号规格", record.get("model", "")),
        ("委托单位", record.get("client", "")),
        ("检验类别", record.get("category", "")),
        ("签发日期", record.get("issued", "")),
        ("检测结论", record.get("conclusion", "")),
    ]
    body = "".join(
        f"<div class='row'><dt>{escape(k)}</dt><dd>{escape(str(v))}</dd></div>"
        for k, v in rows if v
    )
    return f"<div class='card'><h2>报告信息</h2>{body}</div>"
