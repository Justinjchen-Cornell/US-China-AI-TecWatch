# -*- coding: utf-8 -*-
"""构建量子计算投资跟踪 Dashboard：生成 API(json) + index.html（六维雷达+梯队）。"""
import json
import sys as _sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_sys.path.insert(0, str(ROOT))

from engine.analysis import build_report
from engine.scoring import score_snapshot, DIMENSIONS
from config.indicators import DIM_LABEL

_ap = argparse.ArgumentParser(description="Quantum investment dashboard builder")
_ap.add_argument("--site-dir", default="site",
                 help="site output dir relative to project root; e.g. ../site/quantum for monorepo")
_args = _ap.parse_args()

DATA = ROOT / "data"
OUT = ROOT / _args.site_dir / "api"
SITE = ROOT / _args.site_dir
OUT.mkdir(parents=True, exist_ok=True)

snapshot = json.load(open(DATA / "snapshots" / "2026Q2.json", encoding="utf-8"))
companies = json.load(open(DATA / "companies.json", encoding="utf-8"))

report = build_report(snapshot, companies)

# latest.json
_sys.path.insert(0, str(ROOT.parent / "scripts"))
from industry_index import compute as _obj_compute
_obj = _obj_compute(json.load(open(ROOT / "data" / "industry_indicators.json", encoding="utf-8"))["indicators"])
report["pool_avg"] = report["composite"]
report["composite"] = _obj["index"]
report["index"] = _obj["index"]
report["ci_low"] = _obj["index_low"]
report["ci_high"] = _obj["index_high"]
report["confidence"] = _obj["confidence"]
report["index_note"] = "国家层客观指标(逻辑比特/物理比特/专利/论文/政府投入)"
(OUT / "latest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

# series.json：跨期趋势（当前仅一期，预留结构）
series = [{"date": snapshot["date"], "composite": report["composite"],
           "ci_low": report["ci_low"], "ci_high": report["ci_high"],
           "dim_average": report["dim_average"]}]
(OUT / "series.json").write_text(json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8")

# ---- 生成 index.html ----
def tier_rows(tier_list):
    rows = []
    for r in tier_list:
        tags = " / ".join(r["tags"])
        rows.append(
            f"<tr><td>{r['name']}</td><td>{r['country']}</td><td>{r['route']}</td>"
            f"<td>{r['role']}</td><td>{r['market']}</td><td>{r['valuation']}</td>"
            f"<td><b>{r['score']}</b><br><small>{r['ci_low']}-{r['ci_high']}</small></td>"
            f"<td>{tags}</td></tr>"
        )
    return "\n".join(rows)

tier_html = ""
for tname, tlist in [("领跑", report["tiers"].get("领跑", [])),
                      ("跟进", report["tiers"].get("跟进", [])),
                      ("潜力", report["tiers"].get("潜力", [])),
                      ("观察", report["tiers"].get("观察", []))]:
    if not tlist:
        continue
    tier_html += f"<h3>{tname}（{len(tlist)}）</h3><table class='tbl'><thead><tr>" \
                 f"<th>公司</th><th>国别</th><th>路线</th><th>环节</th><th>市场</th><th>估值/市值</th><th>得分(95%CI)</th><th>配置标签</th></tr></thead>" \
                 f"<tbody>{tier_rows(tlist)}</tbody></table>"

# 六维雷达数据（当前一期）
dim_labels = [DIM_LABEL[d] for d in DIMENSIONS]
dim_vals = [report["dim_average"][d] for d in DIMENSIONS]

# Top12 横向排名
top12 = report["companies"][:12]
top_labels = [r["name"] for r in top12]
top_scores = [r["score"] for r in top12]

dim_rows = "".join(
    f"<tr><td>{DIM_LABEL[d]}</td><td>{report['dim_average'][d]}</td></tr>"
    for d in DIMENSIONS
)

comp_table = "".join(
    f"<tr><td>{i+1}</td><td>{r['name']}</td><td>{r['country']}</td><td>{r['route']}</td>"
    f"<td>{r['role']}</td><td><b>{r['score']}</b></td></tr>"
    for i, r in enumerate(report["companies"][:15])
)

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>量子计算产业投资跟踪体系</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
body{{font-family:"WenQuanYi Micro Hei","PingFang SC",sans-serif;max-width:1120px;margin:24px auto;padding:0 16px;color:#1a2233;background:#f7f9fc}}
h1{{font-size:1.6em;color:#0d3b66}}h2{{color:#0d3b66;border-left:5px solid #0d3b66;padding-left:10px;margin-top:30px}}
.card{{background:#fff;border-radius:10px;padding:18px 20px;box-shadow:0 2px 10px #0001;margin:14px 0}}
.metric{{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-end}}
.metric .num{{font-size:2.4em;font-weight:800;color:#0d3b66}}
.metric .sub{{color:#666;font-size:.95em}}
canvas{{max-height:360px}}
.tbl{{width:100%;border-collapse:collapse;font-size:.88em;margin-top:8px}}
.tbl th{{background:#0d3b66;color:#fff;padding:8px}}.tbl td{{border-bottom:1px solid #e3e8ef;padding:7px}}
.tbl tr:nth-child(even){{background:#f2f5fa}}
.note{{font-size:.85em;color:#7a7a7a;margin-top:6px}}
.charts{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
@media(max-width:800px){{.charts{{grid-template-columns:1fr}}}}
</style></head>
<body>
<h1>量子计算产业投资跟踪与分析体系</h1>
<div class='note'>数据基线来自公开研究与行业报告，指标原始值为近似整理，仅供趋势研究与学术探讨，不构成任何投资建议。数值会随公开数据持续修订。</div>
<div class='card metric'>
  <div><div class='num'>{report['composite']}</div><div class='sub'>QuantumCompete Index（综合得分，0-100）</div></div>
  <div><div class='num' style='font-size:1.3em;color:#3a7'>{report['ci_low']}–{report['ci_high']}</div><div class='sub'>95% 置信区间（蒙特卡洛 N={2000} ±1σ）</div></div>
  <div><div class='num' style='font-size:1.3em;color:#c0392b'>{snapshot['date']}</div><div class='sub'>快照日期</div></div>
</div>
<div class='charts'>
<div class='card'><h2>六维平均得分</h2><table class='tbl'><thead><tr><th>维度</th><th>平均分(0-100)</th></tr></thead><tbody>{dim_rows}</tbody></table>
<canvas id='radar' style='margin-top:10px'></canvas></div>
<div class='card'><h2>综合趋势（历史序列）</h2><canvas id='trend'></canvas><div class='note'>当前仅含 2026Q2 一期基线；后续新增快照后自动扩展。</div>
<h2 style='margin-top:18px'>Top 12 横向排名</h2><canvas id='barrank'></canvas></div>
</div>
<div class='card'><h2>公司综合得分排名（Top 15）</h2><table class='tbl'><thead><tr><th>#</th><th>公司</th><th>国别</th><th>路线</th><th>环节</th><th>得分</th></tr></thead><tbody>{comp_table}</tbody></table></div>
<div class='card'><h2>梯队明细与配置建议</h2>
<div class='note'>配置：核心仓 = {", ".join(report["allocation"]["核心仓(已上市/卖铲人)"])}；期权仓 = {", ".join(report["allocation"]["期权仓(一级/整机前沿)"])}</div>
{tier_html}
</div>
<script>
const series={json.dumps(series)};
const ctx=document.getElementById('trend').getContext('2d');
new Chart(ctx,{{type:'line',data:{{labels:series.map(s=>s.date),datasets:[
{{label:'综合指数',data:series.map(s=>s.composite),borderColor:'#0d3b66',fill:false,tension:.3}},
{{label:'CI上界',data:series.map(s=>s.ci_high),borderColor:'#3a7',borderDash:[4,4],fill:false}},
{{label:'CI下界',data:series.map(s=>s.ci_low),borderColor:'#c0392b',borderDash:[4,4],fill:false}}
]}},options:{{scales:{{y:{{min:0,max:100}}}}}}}});
new Chart(document.getElementById('radar').getContext('2d'),{{type:'radar',data:{{labels:{json.dumps(dim_labels)},datasets:[{{label:'六维均值',data:{json.dumps(dim_vals)},backgroundColor:'rgba(13,59,102,.25)',borderColor:'#0d3b66',pointBackgroundColor:'#0d3b66'}}]}},options:{{scales:{{r:{{min:0,max:100}}}}}}}}}});
new Chart(document.getElementById('barrank').getContext('2d'),{{type:'bar',data:{{labels:{json.dumps(top_labels)},datasets:[{{label:'综合得分',data:{json.dumps(top_scores)},backgroundColor:'#0d3b66'}}]}},options:{{indexAxis:'y',scales:{{x:{{min:0,max:100}}}}}}}}}});
</script>
</body></html>"""

(SITE / "index.html").write_text(html, encoding="utf-8")
print("composite =", report["composite"], "| dim_avg =", report["dim_average"])
print("companies scored:", len(report["companies"]))
print("OK ->", SITE / "index.html")
