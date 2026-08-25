# -*- coding: utf-8 -*-
"""构建 AI生命科学 投资分析报告 + Dashboard (index.html)。"""
import json, os, statistics, argparse
from engine.analysis import analyze

ROOT = os.path.dirname(os.path.abspath(__file__))
_ap = argparse.ArgumentParser(description="AI life science dashboard builder")
_ap.add_argument("--site-dir", default="site",
                 help="site output dir relative to project root; e.g. ../site/bio for monorepo")
_args = _ap.parse_args()
SITE_DIR = os.path.join(ROOT, _args.site_dir)

DATA = json.load(open(os.path.join(ROOT, "data/companies.json"), encoding="utf-8"))
SNAP = json.load(open(os.path.join(ROOT, "data/snapshots/2026Q2.json"), encoding="utf-8"))
SCORED = analyze(DATA)

os.makedirs(os.path.join(SITE_DIR, "api"), exist_ok=True)

# ---- latest.json ----
def ser(s):
    return {k: s[k] for k in ["id","name","country","track","role","market","tier","config","score","lo","hi","dims"]}
latest = {
    "as_of": SNAP["as_of"], "note": SNAP["note"],
    "life_index": round(statistics.mean(s["score"] for s in SCORED), 1),
    "index_note": "池内均分·全池公司六维加权均值(非竞争指数)",
    "n": len(SCORED),
    "companies": [ser(s) for s in SCORED],
}
json.dump(latest, open(os.path.join(SITE_DIR, "api/latest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- series.json ----
series = {"dates": [SNAP["as_of"]], "life_index": [latest["life_index"]]}
json.dump(series, open(os.path.join(SITE_DIR, "api/series.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- Markdown 报告 ----
lines = []
lines.append("# AI生命科学产业投资跟踪报告\n")
lines.append(f"_数据快照：{SNAP['as_of']}_  \n")
lines.append(f"**LifeCompete Index = {latest['life_index']}**（{latest['n']} 家海内外标的六维加权均值，仅供趋势研究）\n")
lines.append("\n## 六维均值\n")
dims_cn = {"clinical":"临床验证度","pipeline":"管线/产品力","platform":"商业化确定性","tech":"技术壁垒","capital":"资本热度","policy":"政策/监管"}
for d, name in dims_cn.items():
    avg = statistics.mean(s["dims"][d] for s in SCORED)
    lines.append(f"- {name}：{avg:.1f}")
lines.append("\n## 综合得分 Top 12\n")
for i, s in enumerate(SCORED[:12], 1):
    lines.append(f"{i}. **{s['name']}** ({s['country']}/{s['track']}) — {s['score']} 分 · {s['tier']} · {s['config']}")
tier_cnt = {}
for s in SCORED: tier_cnt[s["tier"]] = tier_cnt.get(s["tier"], 0) + 1
lines.append("\n## 梯队分布\n")
for t in ["领跑","跟进","潜力","观察"]:
    lines.append(f"- {t}：{tier_cnt.get(t,0)} 家")
lines.append("\n## 配置建议（核心仓+期权仓）\n")
lines.append("- **核心仓(卖铲人/平台)**：晶泰控股、Schrödinger、华大智造、恒瑞医药、镁伽科技、强脑科技 —— 平台型/数据底座/已盈利或拟IPO，确定性最高。")
lines.append("- **管线期权仓(高赔率)**：英矽智能、Recursion、Isomorphic Labs、望石智慧、剂泰医药 —— 临床验证期博弈，关注III期成功率拐点。")
lines.append("- **信仰仓(远期)**：Neuralink、Precision Neuroscience、Xaira、深势科技、百图生科 —— 技术天花板最高但商业化遥远，小仓位。")
lines.append("- **监测节点**：晶泰盈利持续性/订单放量；英矽智能III期与礼来GLP-1订单里程碑；强脑科技IPO进展；脑机接口医保支付范围与年植入量。")
lines.append("\n> 免责声明：数据为公开信息近似整理，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。")
open(os.path.join(ROOT, "REPORT.md"), "w", encoding="utf-8").write("\n".join(lines))

# ---- index.html Dashboard ----
dimOrder = ["clinical","pipeline","platform","tech","capital","policy"]
dimLabels = [dims_cn[k] for k in dimOrder]
html = """<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>AI生命科学产业投资 Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>body{font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;max-width:1120px;margin:24px auto;padding:0 16px;color:#1a1a2e;background:#f5f7fb}h1{color:#0f3460}h2{color:#16213e;border-left:4px solid #0f3460;padding-left:10px;margin-top:30px}.cards{display:flex;gap:16px;flex-wrap:wrap}.card{background:#fff;border-radius:12px;padding:16px 20px;box-shadow:0 2px 10px #0001;flex:1;min-width:200px}.card b{font-size:24px;color:#0f3460}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}@media(max-width:800px){.grid{grid-template-columns:1fr}}table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px #0001}th{background:#0f3460;color:#fff;padding:8px;text-align:left}td{padding:7px 8px;border-bottom:1px solid #eee;font-size:13px}tr:nth-child(even){background:#f0f3fa}.tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;color:#fff}.领跑{background:#2e7d32}.跟进{background:#1565c0}.潜力{background:#ef6c00}.观察{background:#9e9e9e}.核心仓\\(卖铲人\\/平台\\){background:#0f3460}.核心仓\\(脑机落地\\){background:#00695c}.管线期权仓\\(高赔率\\){background:#c2185b}.信仰仓\\(远期\\){background:#4a148c}.路线\\/观察仓{background:#546e7a}.note{font-size:12px;color:#666;margin-top:24px}</style></head>
<body><h1>AI生命科学产业投资 Dashboard</h1><div class="cards">
<div class="card"><b id="idx">–</b><div>LifeCompete Index (六维均值)</div></div>
<div class="card"><b id="n">–</b><div>跟踪标的</div></div>
<div class="card"><b id="top">–</b><div>领跑/跟进合计</div></div></div>
<div class="grid"><div><h2>六维均值</h2><canvas id="dimChart" height="210"></canvas></div>
<div><h2>综合得分 Top 12</h2><canvas id="rankChart" height="210"></canvas></div></div>
<h2>全标的明细（按综合得分降序）</h2><table><thead><tr><th>#</th><th>公司</th><th>国别</th><th>赛道</th><th>角色</th><th>得分</th><th>区间</th><th>梯队</th><th>配置</th></tr></thead><tbody id="tbody"></tbody></table>
<p class="note">数据快照：__ASOF__ · 指标原始值为公开信息近似整理，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。</p>
<script>fetch("api/latest.json").then(r=>r.json()).then(d=>{document.getElementById("idx").textContent=d.life_index;document.getElementById("n").textContent=d.n;document.getElementById("top").textContent=d.companies.filter(c=>c.tier==="领跑"||c.tier==="跟进").length;const dimAvg=__DIMORD__.map(k=>{const vals=d.companies.map(c=>c.dims?c.dims[k]:null).filter(v=>typeof v==="number");return vals.length?Math.round(vals.reduce((a,b)=>a+b,0)/vals.length*10)/10:0});new Chart(document.getElementById("dimChart"),{type:"bar",data:{labels:__DIMLABEL__,datasets:[{label:"均值",data:dimAvg,backgroundColor:"#0f3460"}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{suggestedMin:20,suggestedMax:75}}}});const top=d.companies.slice(0,12);new Chart(document.getElementById("rankChart"),{type:"bar",data:{labels:top.map(c=>c.name),datasets:[{label:"综合得分",data:top.map(c=>c.score),backgroundColor:"#1565c0"}]},options:{indexAxis:"y",responsive:true,plugins:{legend:{display:false}}}});const tb=document.getElementById("tbody");d.companies.forEach((c,i)=>{const tr=document.createElement("tr");tr.innerHTML=`<td>${i+1}</td><td>${c.name}</td><td>${c.country||""}</td><td>${c.track||""}</td><td>${c.role||""}</td><td>${c.score}</td><td>${c.lo}~${c.hi}</td><td><span class="tag ${c.tier}">${c.tier}</span></td><td><span class="tag ${cssEscape(c.config)}">${c.config}</span></td>`;tb.appendChild(tr);});});function cssEscape(s){return (s||"").replace(/[()]/g,"\\\\$&")}</script></body></html>"""
html = html.replace("__ASOF__", SNAP["as_of"]).replace("__DIMORD__", json.dumps(dimOrder)).replace("__DIMLABEL__", json.dumps(dimLabels))
open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8").write(html)
print("built:", os.path.join(SITE_DIR, "index.html"))
print("life_index =", latest["life_index"], "| companies =", latest["n"])
