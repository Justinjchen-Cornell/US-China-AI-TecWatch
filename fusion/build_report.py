# -*- coding: utf-8 -*-
"""构建核聚变投资分析报告 + Dashboard (index.html)。"""
import json, os, statistics, argparse, sys as _sys
from engine.analysis import analyze

ROOT = os.path.dirname(os.path.abspath(__file__))
_ap = argparse.ArgumentParser(description="Fusion investment dashboard builder")
_ap.add_argument("--site-dir", default="site",
                 help="site output dir relative to project root; e.g. ../site/fusion for monorepo")
_args = _ap.parse_args()
SITE_DIR = os.path.join(ROOT, _args.site_dir)

DATA = json.load(open(os.path.join(ROOT, "data/companies.json"), encoding="utf-8"))
SNAP = json.load(open(os.path.join(ROOT, "data/snapshots/2026Q2.json"), encoding="utf-8"))
SCORED = analyze(DATA)

os.makedirs(os.path.join(SITE_DIR, "api"), exist_ok=True)

# ---- latest.json ----
def ser(s):
    out = {k: s.get(k) for k in ["id","name","country","route","role","tier","config","market","score","lo","hi"]}
    orig = next((x for x in DATA if x.get("id") == s.get("id")), {})
    for k in ["thesis","moat","risks","catalysts","track_points"]:
        out[k] = orig.get(k)
    return out

_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from industry_index import compute as _obj_compute
_obj = _obj_compute(json.load(open(os.path.join(ROOT, "data/industry_indicators.json"), encoding="utf-8"))["indicators"])
latest = {
    "as_of": SNAP["as_of"], "note": SNAP["note"],
    "index": _obj["index"],
    "ci_low": _obj["index_low"],
    "ci_high": _obj["index_high"],
    "confidence": _obj["confidence"],
    "index_note": "国家层客观指标(等离子体维持/磁体/点火/专利/投入)",
    "pool_avg": round(statistics.mean(s["score"] for s in SCORED), 1),
    "fusion_index": round(statistics.mean(s["score"] for s in SCORED), 1),
    "n": len(SCORED),
    "companies": [ser(s) for s in SCORED],
}
json.dump(latest, open(os.path.join(SITE_DIR, "api/latest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- series.json (2024Q3 → 2025Q2 → 当前) ----
_ind_cfg = json.load(open(os.path.join(ROOT, "data/industry_indicators.json"), encoding="utf-8"))
series = []
for _pt in _ind_cfg.get("series", []):
    _inds = [dict(i) | ({"value": _pt["values"][i["id"]]} if _pt["values"].get(i["id"]) is not None else {})
             for i in _ind_cfg["indicators"]]
    _r = _obj_compute(_inds)
    series.append({"date": _pt["as_of"], "index": _r["index"],
                   "ci_low": _r["index_low"], "ci_high": _r["index_high"]})
series.append({"date": _ind_cfg["as_of"], "index": latest["index"],
               "ci_low": latest["ci_low"], "ci_high": latest["ci_high"]})
json.dump(series, open(os.path.join(SITE_DIR, "api/series.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 趋势解读（方向/动量/驱动归因/观察清单）
_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from trend_analysis import analyze as _trend
_s0 = _ind_cfg.get("series", [{}])[0].get("values", {})
_inds_first = [dict(i) | ({"value": _s0.get(i["id"], i["value"])}) for i in _ind_cfg["indicators"]]
latest["trend"] = _trend(_ind_cfg["indicators"], _inds_first, series, watch=_ind_cfg.get("watch"))
latest["frontier"] = _ind_cfg.get("frontier", [])
latest["intelligence"] = json.load(open(os.path.join(ROOT, "data/industry_intelligence.json"), encoding="utf-8"))
json.dump(latest, open(os.path.join(SITE_DIR, "api/latest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 行业研判 HTML 区块
try:
    _v = latest["intelligence"].get("verdict", {})
    _vc = latest["intelligence"].get("value_chain", [])
    _inf = latest["intelligence"].get("inflections_6_18m", [])
    intel_html = "<div class='card' style='border-left:4px solid #f59e0b'>"
    intel_html += "<div style='font-size:12px;color:#7a8699'>行业研判 · 非评分 · 作者观点</div>"
    intel_html += "<h2 style='font-size:17px;margin:8px 0 10px'>" + _v.get('phase', '') + "</h2>"
    intel_html += "<table><tbody>"
    intel_html += "<tr><th style='text-align:left;width:130px'>中国位置</th><td>" + _v.get('china_position', '') + "</td></tr>"
    intel_html += "<tr><th style='text-align:left'>关键拐点</th><td>" + _v.get('key_inflection', '') + "</td></tr>"
    intel_html += "<tr><th style='text-align:left'>投资主题</th><td>" + _v.get('investment_theme', '') + "</td></tr>"
    intel_html += "</tbody></table>"
    if _vc:
        intel_html += "<div style='font-size:13px;font-weight:600;margin:12px 0 6px'>价值链判断</div><ul style='margin:0;padding-left:18px;font-size:12.5px'>"
        for seg in _vc[:3]:
            intel_html += "<li><b>" + seg.get('segment', '') + "</b>（" + seg.get('value_concentration', '') + "）：" + seg.get('logic', '') + "</li>"
        intel_html += "</ul>"
    if _inf:
        intel_html += "<div style='font-size:13px;font-weight:600;margin:12px 0 6px'>未来 6-18 个月拐点</div><ul style='margin:0;padding-left:18px;font-size:12.5px'>"
        for inf in _inf:
            intel_html += "<li><b>" + inf.get('event', '') + "</b>（概率 " + inf.get('probability', '') + "）：" + inf.get('impact', '') + "</li>"
        intel_html += "</ul>"
    intel_html += "</div>"
except Exception:
    intel_html = ""

# ---- Markdown 报告 ----
lines = []
lines.append("# 可控核聚变产业投资跟踪报告\n")
lines.append(f"_数据快照：{SNAP['as_of']}_  \n")
lines.append(f"**FusionCompete Index = {latest['fusion_index']}**（{latest['n']} 家海内外标的六维加权均值，仅供趋势研究）\n")
lines.append("\n## 六维均值\n")
dims = {"science":"科学可行性","engineering":"工程进度","capital":"资本热度","supply":"供应链地位","policy":"政策支持","ai":"AI赋能"}
for d,name in dims.items():
    avg = statistics.mean(s["dims"][d] for s in SCORED)
    lines.append(f"- {name}：{avg:.1f}")
lines.append("\n## 综合得分 Top 10\n")
for i,s in enumerate(SCORED[:10],1):
    lines.append(f"{i}. **{s['name']}** ({s['country']}/{s['route']}) — {s['score']} 分 · {s['tier']} · {s['config']}")
tier_cnt = {}
for s in SCORED: tier_cnt[s["tier"]] = tier_cnt.get(s["tier"],0)+1
lines.append("\n## 梯队分布\n")
for t in ["领跑","跟进","潜力","观察"]:
    lines.append(f"- {t}：{tier_cnt.get(t,0)} 家")
lines.append("\n## 配置建议\n")
lines.append("- **核心仓(卖铲人)**：高温超导磁体/带材与核心部件（联创光电、西部超导、永鼎股份、昱曦科技、安泰科技、国光电气）—— 无论哪条路线胜出均需采购。")
lines.append("- **整机期权仓**：海外 CFS/Helion/TAE、中国星环聚能/能量奇点/新奥科技 —— 高赔率高风险，小仓位博弈技术兑现。")
lines.append("- **监测节点**：2026 底 CFS SPARC 首次等离子体；2028 Helion 对微软 50MW PPA；中国 BEST/CFETR 工程招标与采购订单流向。")
lines.append("\n> 免责声明：数据为公开信息近似整理，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。")
open(os.path.join(ROOT, "REPORT.md"), "w", encoding="utf-8").write("\n".join(lines))

# ---- index.html Dashboard ----
html = """<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>可控核聚变产业投资 Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>body{font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#1a1a2e;background:#f5f7fb}h1{color:#0f3460}h2{color:#16213e;border-left:4px solid #0f3460;padding-left:10px;margin-top:32px}.cards{display:flex;gap:16px;flex-wrap:wrap}.card{background:#fff;border-radius:12px;padding:16px 20px;box-shadow:0 2px 10px #0001;flex:1;min-width:200px}.card b{font-size:24px;color:#0f3460}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:800px){.grid{grid-template-columns:1fr}}table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px #0001}th{background:#0f3460;color:#fff;padding:8px;text-align:left}td{padding:7px 8px;border-bottom:1px solid #eee;font-size:14px}tr:nth-child(even){background:#f0f3fa}.tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;color:#fff}.领跑{background:#2e7d32}.跟进{background:#1565c0}.潜力{background:#ef6c00}.观察{background:#9e9e9e}.核心仓\\(卖铲人\\){background:#0f3460}.整机期权仓{background:#c2185b}.路线\\/观察仓{background:#546e7a}.note{font-size:12px;color:#666;margin-top:24px}</style></head>
<body><h1>可控核聚变产业投资 Dashboard</h1>__INTEL__<div class="cards">
<div class="card"><b id="idx">–</b><div>FusionCompete Index (六维均值)</div></div>
<div class="card"><b id="n">–</b><div>跟踪标的</div></div>
<div class="card"><b id="top">–</b><div>领跑/跟进合计</div></div></div>
<div class="grid"><div><h2>六维均值</h2><canvas id="dimChart" height="200"></canvas></div>
<div><h2>综合得分 Top 12</h2><canvas id="rankChart" height="200"></canvas></div></div>
<h2>全标的明细（按综合得分降序）</h2><table><thead><tr><th>#</th><th>公司</th><th>国别</th><th>路线</th><th>角色</th><th>得分</th><th>区间</th><th>梯队</th><th>配置</th></tr></thead><tbody id="tbody"></tbody></table>
<p class="note">数据快照：__ASOF__ · 指标原始值为公开信息近似整理，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。</p>
<script>fetch("api/latest.json").then(r=>r.json()).then(d=>{document.getElementById("idx").textContent=d.fusion_index;document.getElementById("n").textContent=d.n;const lead=d.companies.filter(c=>c.tier==="领跑"||c.tier==="跟进").length;document.getElementById("top").textContent=lead;const dims={science:"科学可行性",engineering:"工程进度",capital:"资本热度",supply:"供应链地位",policy:"政策支持",ai:"AI赋能"};const dimOrder=["science","engineering","capital","supply","policy","ai"];const dimAvg=dimOrder.map(k=>{const vals=d.companies.map(c=>c.dims?c.dims[k]:null).filter(v=>typeof v==="number");return vals.length?Math.round(vals.reduce((a,b)=>a+b,0)/vals.length*10)/10:0});new Chart(document.getElementById("dimChart"),{type:"bar",data:{labels:dimOrder.map(k=>dims[k]),datasets:[{label:"均值",data:dimAvg,backgroundColor:"#0f3460"}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{suggestedMin:30,suggestedMax:80}}}});const top=d.companies.slice(0,12);new Chart(document.getElementById("rankChart"),{type:"bar",data:{labels:top.map(c=>c.name),datasets:[{label:"综合得分",data:top.map(c=>c.score),backgroundColor:"#1565c0"}]},options:{indexAxis:"y",responsive:true,plugins:{legend:{display:false}}}});const tb=document.getElementById("tbody");d.companies.forEach((c,i)=>{const tr=document.createElement("tr");tr.innerHTML=`<td>${i+1}</td><td>${c.name}</td><td>${c.country||""}</td><td>${c.route||""}</td><td>${c.role||""}</td><td>${c.score}</td><td>${c.lo}~${c.hi}</td><td><span class="tag ${c.tier}">${c.tier}</span></td><td><span class="tag ${cssEscape(c.config)}">${c.config}</span></td>`;tb.appendChild(tr);});});function cssEscape(s){return (s||"").replace(/[()]/g,"\\\\$&")}</script></body></html>"""
# 注入快照日期
html = html.replace("__ASOF__", SNAP["as_of"]).replace("__INTEL__", intel_html)
open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8").write(html)
print("built:", os.path.join(SITE_DIR, "index.html"))
print("fusion_index =", latest["fusion_index"], "| companies =", latest["n"])
