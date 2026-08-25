# -*- coding: utf-8 -*-
"""
AI 大模型生态投资体系 · 报告构建器
====================================
生成：
  site/api/latest.json  —— 机器可读 API（综合得分/维度分/梯队/配置建议）
  site/api/series.json  —— 跨期趋势序列
  site/index.html       —— 单页 Dashboard（Chart.js 雷达+柱状+梯队表）
"""
import os, json, argparse
from engine.analysis import analyze
from engine.data import build_series

BASE = os.path.dirname(os.path.abspath(__file__))
_ap = argparse.ArgumentParser(description="AI 大模型生态投资体系报告构建")
_ap.add_argument("--site-dir", default="site",
                 help="站点输出目录(相对项目根, 默认 site); 聚合发布时传 e.g. ../site/ai-models")
_args = _ap.parse_args()
SITE = os.path.join(BASE, _args.site_dir, "api")
os.makedirs(SITE, exist_ok=True)

def build():
    a = analyze()
    # latest.json
    _all = [it for t in a["tiers"].values() for it in t]
    _cn = [it["score"] for it in _all if it.get("camp") == "中国"]
    _us = [it["score"] for it in _all if it.get("camp") == "海外"]
    payload = {
        "period": a["period"],
        "index": round(sum(_cn) / len(_cn), 1) if _cn else None,
        "index_note": "中国阵营公司综合得分均值 (0-100)",
        "camp_avg": {"中国": round(sum(_cn)/len(_cn), 1) if _cn else None,
                     "海外": round(sum(_us)/len(_us), 1) if _us else None},
        "dim_avg": a["dim_avg"],
        "tiers": {k: v for k, v in a["tiers"].items()},
        "items": a["items"],
        "recommend": {
            "core": [{"id": i["id"],"name": i["name"],"score": round(i["score"],1)}
                     for i in a["core"]],
            "option": [{"id": i["id"],"name": i["name"],"score": round(i["score"],1)}
                       for i in a["option"]],
        },
    }
    with open(os.path.join(SITE, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # series.json
    series = build_series()
    with open(os.path.join(SITE, "series.json"), "w", encoding="utf-8") as f:
        json.dump(series, f, ensure_ascii=False, indent=2)
    # HTML
    html = render_html(a)
    with open(os.path.join(os.path.dirname(SITE), "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("[build] 报告已生成")
    print("  -", os.path.join(SITE, "latest.json"))
    print("  -", os.path.join(SITE, "series.json"))
    print("  -", os.path.join(os.path.dirname(SITE), "index.html"))

def render_html(a):
    items = a["items"]
    dim_avg = a["dim_avg"]
    dims = [{"key":"model_capability","label":"模型能力"},
            {"key":"commercialization","label":"商业化兑现"},
            {"key":"open_source","label":"开源生态"},
            {"key":"compute_efficiency","label":"算力成本效率"},
            {"key":"embodiment","label":"具身/物理AI"}]
    labels = json.dumps([d["label"] for d in dims], ensure_ascii=False)
    dimdata = json.dumps([dim_avg.get(d["key"]) for d in dims])
    names = json.dumps([i["name"] for i in items], ensure_ascii=False)
    scores = json.dumps([round(i["score"],1) for i in items])
    core = ", ".join(f'{i["name"]}({i["score"]:.1f})' for i in a["core"])
    opt = ", ".join(f'{i["name"]}({i["score"]:.1f})' for i in a["option"])
    rows = ""
    for it in items:
        rows += (f'<tr><td>{it["name"]}</td><td>{it["camp"]}</td>'
                 f'<td>{it["sector"]}</td><td>{it["tier"]}</td>'
                 f'<td>{it["score"]:.1f}</td>'
                 f'<td>{it["ci_low"]:.1f}–{it["ci_high"]:.1f}</td>'
                 f'<td>{it["confidence"]:.0%}</td></tr>')
    return f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<title>AI 大模型生态投资体系 · Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;margin:0;background:#0f1626;color:#e8ecf3}}
header{{padding:28px 32px 12px;background:linear-gradient(135deg,#18253f,#0f1626);border-bottom:1px solid #243047}}
h1{{margin:0 0 6px;font-size:22px;color:#7cc4ff}} .sub{{color:#8a97ad;font-size:13px}}
main{{max-width:1180px;margin:0 auto;padding:20px}}
.card{{background:#172234;border:1px solid #243047;border-radius:12px;padding:18px;margin-bottom:20px}}
canvas{{max-height:340px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:#1f2d44;color:#9fb3d1;text-align:left;padding:8px}}
td{{padding:8px;border-top:1px solid #243047}}
tr:hover td{{background:#1c2940}}
.tag{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px}}
.领跑梯队{{background:#1f6f54;color:#b8f5d8}} .跟进梯队{{background:#2f4a6f;color:#bcd2f5}}
.潜力梯队{{background:#5a4a2a;color:#f5dcae}} .观察梯队{{background:#4a3030;color:#f5c4c4}}
.rec{{font-size:13px;line-height:1.9;color:#c7d2e6}}
footer{{text-align:center;color:#5b6677;font-size:11px;padding:16px}}
</style></head>
<body>
<header><h1>AI 大模型生态投资体系 · Dashboard</h1>
<div class="sub">数据期次：{a['period']}　|　综合评分区间 0-100（越高=生态/投资综合禀赋越强）　|　仅供趋势研究，不构成投资建议</div></header>
<main>
  <section class="card"><h3>五维生态雷达</h3><canvas id="radar"></canvas></section>
  <section class="card"><h3>公司综合得分排名</h3><canvas id="bar"></canvas></section>
  <section class="card"><h3>梯队排名明细</h3>
    <table><thead><tr><th>公司</th><th>阵营</th><th>赛道</th><th>梯队</th><th>得分</th><th>95%CI</th><th>数据置信</th></tr></thead>
    <tbody>{rows}</tbody></table></section>
  <section class="card"><h3>配置含义（投资体系观点）</h3>
    <div class="rec"><b>确定性核心（已上市/有流动性）：</b>{core}<br>
    <b>高弹性期权（一级市场/Pre-IPO）：</b>{opt}<br>
    <span style="color:#8a97ad">说明：核心仓买“商业化兑现+生态位确定性”，期权仓买“开源/端侧/视频等非对称赛道的高弹性”。</span></div></section>
</main>
<footer>数据基线来自公开研究与报告，指标原始值为近似整理，会随公开数据持续修订。</footer>
<script>
const labels={labels}; const dimdata={dimdata};
new Chart(document.getElementById('radar'),{{type:'radar',data:{{labels,datasets:[{{label:'五维平均得分',data:dimdata,backgroundColor:'rgba(124,196,255,.25)',borderColor:'#7cc4ff',borderWidth:2,pointBackgroundColor:'#7cc4ff'}}]}},options:{{scales:{{r:{{min:0,max:100,ticks:{{color:'#5b6677'}},grid:{{color:'#243047'}},angleLines:{{color:'#243047'}},pointLabels:{{color:'#9fb3d1'}}}}}},plugins:{{legend:{{display:false}}}}}} }});
const names={names}; const scores={scores};
new Chart(document.getElementById('bar'),{{type:'bar',data:{{labels:names,datasets:[{{label:'综合得分',data:scores,backgroundColor:names.map(()=>'#4f8fd6')}}]}},options:{{indexAxis:'y',scales:{{x:{{min:0,max:100,grid:{{color:'#243047'}},ticks:{{color:'#5b6677'}}}},y:{{grid:{{color:'#243047'}},ticks:{{color:'#9fb3d1'}}}}}},plugins:{{legend:{{display:false}}}}}} }});
</script></body></html>"""

if __name__ == "__main__":
    build()
