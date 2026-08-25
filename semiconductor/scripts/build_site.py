"""
构建半导体 Dashboard 站点:
- site/api/latest.json : 最新一期综合指数+维度分+企业数据
- site/api/series.json : 历史指数时间序列
- site/index.html      : 单页 Dashboard (Chart.js CDN)
用法: python scripts/build_site.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compute_index import compute

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import argparse
_ap = argparse.ArgumentParser(description="半导体仪表盘构建")
_ap.add_argument("--site-dir", default="site",
                 help="站点输出目录(相对本项目根, 默认 site); 聚合发布时传 e.g. ../site/semiconductor")
_args = _ap.parse_args()
SITE = os.path.join(BASE, _args.site_dir)
API = os.path.join(SITE, "api")
HIST = os.path.join(BASE, "data", "history.json")
PUB = os.path.join(BASE, "data", "companies_public.json")
PRV = os.path.join(BASE, "data", "companies_private.json")

os.makedirs(API, exist_ok=True)

with open(PUB, encoding="utf-8") as f: public = json.load(f)
with open(PRV, encoding="utf-8") as f: private = json.load(f)

res = compute()

# latest.json
latest = {
    "schema_version": 1,
    "updated": res["updated"],
    "index": res["index"],
    "mc_mean": res["mc_mean"],
    "mc_std": res["mc_std"],
    "ci_low": res["ci_low"],
    "ci_high": res["ci_high"],
    "data_confidence": res["data_confidence"],
    "n_indicators": res["n_indicators"],
    "dimensions": res["dimensions"],
    "dark_lines": res["dark_lines"],
    "public_companies": public,
    "private_companies": private,
}
with open(os.path.join(API, "latest.json"), "w", encoding="utf-8") as f:
    json.dump(latest, f, ensure_ascii=False, indent=2)

# series.json
series = []
if os.path.exists(HIST):
    with open(HIST, encoding="utf-8") as f:
        series = json.load(f)
with open(os.path.join(API, "series.json"), "w", encoding="utf-8") as f:
    json.dump(series, f, ensure_ascii=False, indent=2)

# ---------- 生成 index.html（占位符替换，避免 f-string 嵌套）----------
dim_labels = [d["name"] for d in res["dimensions"]]
dim_scores = [d["score100"] for d in res["dimensions"]]
hist_labels = [h["date"] for h in series]
hist_idx = [h["index"] for h in series]
hist_lo = [h["ci_low"] for h in series]
hist_hi = [h["ci_high"] for h in series]

def esc(s):
    return ("" + s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") if isinstance(s, str) else s

def dim_rows():
    return "".join(f'<tr><td>{esc(d["name"])}</td><td>{d["score100"]:.1f}</td><td>{d["weight"]}</td><td>{d["n"]}</td></tr>' for d in res["dimensions"])

def dl_rows():
    return "".join(f'<tr><td>{esc(dl["name"])}</td><td>{dl["value"]}</td><td>{dl["weight"]}</td></tr>' for dl in res["dark_lines"])

def pub_rows(companies, kind):
    rows = []
    for c in companies:
        if kind == "china":
            rows.append(f'<tr><td>{esc(c["name"])}</td><td><code>{esc(c.get("ticker","-"))}</code></td><td>{esc(c["sector"])}</td><td>{esc(c["market_cap_cn"])}</td><td>{esc(c["role"])}</td></tr>')
        else:
            rows.append(f'<tr><td>{esc(c["name"])}</td><td><code>{esc(c.get("ticker","-"))}</code></td><td>{esc(c["sector"])}</td><td>{esc(c["market_cap_cn"])}</td><td>{esc(c.get("note",c.get("role","")))}</td></tr>')
    return "".join(rows)

def prv_rows(companies):
    return "".join(f'<tr><td>{esc(c["name"])}</td><td>{esc(c["track"])}</td><td>{esc(c["latest_round"])}</td><td>{esc(c["valuation_cn"])}</td><td>{esc("、".join(c["backers"]))}</td><td>{esc(c["route"])}</td></tr>' for c in companies)

idx_class = "up" if res["index"] >= 55 else ("mid" if res["index"] >= 45 else "down")

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Semiconductor Tracker · 半导体产业竞争力仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0b1220;--card:#121b2e;--line:#1f2c44;--txt:#e6edf6;--sub:#9aa7bd;--accent:#4f8cff;--accent2:#36d7b7;--warn:#f4b740;--danger:#ef5350;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--txt);font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;}
header{padding:28px 24px 18px;text-align:center;border-bottom:1px solid var(--line);}
header h1{font-size:1.7rem;letter-spacing:.5px;}header p{color:var(--sub);font-size:.95rem;margin-top:6px;}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px;}
.grid{display:grid;gap:18px;}.cards{grid-template-columns:repeat(4,1fr);}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;}
.card h3{font-size:.92rem;color:var(--sub);font-weight:600;margin-bottom:8px;}
.card .num{font-size:1.9rem;font-weight:800;}.card .sub{font-size:.8rem;color:var(--sub);margin-top:4px;}
.up{color:var(--accent2);}.mid{color:var(--warn);}.down{color:var(--danger);}
section{margin-top:26px;}section h2{font-size:1.2rem;margin-bottom:12px;padding-left:10px;border-left:4px solid var(--accent);}
.chart-box{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;}canvas{width:100%!important;}
table{width:100%;border-collapse:collapse;font-size:.86rem;}th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);}
th{color:var(--sub);font-weight:600;background:#0f1830;position:sticky;top:0;}tr:hover td{background:#16213a;}
code{background:#0f1830;padding:1px 6px;border-radius:5px;font-size:.8rem;color:var(--accent2);}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;}
.tab{background:#16213a;border:1px solid var(--line);color:var(--sub);padding:6px 14px;border-radius:20px;cursor:pointer;font-size:.85rem;}
.tab.on{background:var(--accent);color:#fff;border-color:var(--accent);}.panel{display:none;}.panel.on{display:block;}
.note{color:var(--sub);font-size:.82rem;margin-top:8px;}
footer{text-align:center;color:var(--sub);font-size:.8rem;margin-top:40px;padding-top:18px;border-top:1px solid var(--line);}
@media(max-width:800px){.cards{grid-template-columns:repeat(2,1fr);}}
</style>
</head>
<body>
<header>
  <h1>🧭 Semiconductor Tracker</h1>
  <p>半导体产业竞争力仪表盘 · 基于六维耦合 + 暗线修正的 SemiCompete Composite Index</p>
  <p class="note">数据基线 __UPDATED__ · 指标 __NIND__ 项 · 数据置信度 __CONF__% · 仅供趋势研究，不构成投资建议</p>
</header>
<div class="wrap">
  <div class="grid cards">
    <div class="card"><h3>半导体综合指数</h3><div class="num __IDXCLASS__">__INDEX__</div><div class="sub">0-100，&gt;50 偏中国有利</div></div>
    <div class="card"><h3>95% 置信区间</h3><div class="num">__CILO__–__CIHI__</div><div class="sub">蒙特卡洛 N=2000 ±1σ</div></div>
    <div class="card"><h3>MC 均值 ± 标准差</h3><div class="num">__MCMEAN__±__MCSTD__</div><div class="sub">含指标来源可靠度扰动</div></div>
    <div class="card"><h3>数据置信度</h3><div class="num">__CONF__%</div><div class="sub">各指标 source_reliability 几何平均</div></div>
  </div>
  <section><h2>📈 指数趋势（历史快照）</h2><div class="chart-box"><canvas id="trendChart" height="90"></canvas></div>
    <p class="note">横轴为快照日期；蓝色为综合指数，阴影带为 95% CI。更新 data/indicators.json 后重跑 update_snapshot.py 即可追加新一期。</p></section>
  <section><h2>🎯 六维竞争力雷达</h2><div class="chart-box"><canvas id="radarChart" height="100"></canvas></div></section>
  <section><h2>📊 维度得分明细</h2><div class="chart-box"><canvas id="dimBar" height="90"></canvas></div>
    <table style="margin-top:14px;"><thead><tr><th>维度</th><th>得分(0-100)</th><th>权重</th><th>指标数</th></tr></thead><tbody>__DIMROWS__</tbody></table>
    <details class="note"><summary>暗线修正项（点击展开）</summary><table style="margin-top:8px;"><thead><tr><th>暗线</th><th>数值</th><th>权重</th></tr></thead><tbody>__DLROWS__</tbody></table></details></section>
  <section><h2>🏢 企业图谱</h2>
    <div class="tabs" id="compTabs"><div class="tab on" data-t="pub_cn">中国·上市公司</div><div class="tab" data-t="pub_ov">海外·上市公司</div><div class="tab" data-t="prv_cn">中国·一级市场</div><div class="tab" data-t="prv_ov">海外·一级市场</div></div>
    <div class="chart-box">
      <div class="panel on" id="pub_cn"><table><thead><tr><th>公司</th><th>代码</th><th>环节</th><th>市值</th><th>定位</th></tr></thead><tbody>__PUBCN__</tbody></table></div>
      <div class="panel" id="pub_ov"><table><thead><tr><th>公司</th><th>代码</th><th>环节</th><th>市值</th><th>说明</th></tr></thead><tbody>__PUBOV__</tbody></table></div>
      <div class="panel" id="prv_cn"><table><thead><tr><th>公司</th><th>赛道</th><th>最新融资</th><th>估值</th><th>主要投资方</th><th>绕行路径</th></tr></thead><tbody>__PRVCN__</tbody></table></div>
      <div class="panel" id="prv_ov"><table><thead><tr><th>公司</th><th>赛道</th><th>最新融资</th><th>估值</th><th>主要投资方</th><th>绕行路径</th></tr></thead><tbody>__PRVOV__</tbody></table></div>
    </div><p class="note">市值/估值为公开资料趋势性参考，融资信息来自公开报道，可能滞后，请以公司官方披露为准。</p></section>
  <section><h2>🧮 指数计算方法</h2><div class="chart-box note" style="font-size:.88rem;">
    <p><b>① 归一化</b>：每项指标按「对中国是否有利」方向做 0–1 归一化；</p>
    <p><b>② 维度分</b>：每维内指标取几何平均（Laplace 平滑），避免极端值主导；</p>
    <p><b>③ 加权合成</b>：六维按权重 [制程装备1.2 / 制造代工1.1 / 存储HBM1.2 / AI芯片1.3 / 先进封装1.1 / 未来范式1.1] 累加，并加五条暗线修正项；</p>
    <p><b>④ Sigmoid 映射</b>：Index = 100·sigmoid(z·4)，稳定落在 (0,100)，&gt;50 偏中国有利；</p>
    <p><b>⑤ 不确定性</b>：每项指标按 source_reliability 加高斯扰动，蒙特卡洛 N=2000 给出 ±1σ 区间。</p>
    <p>权重与数据完全分离（config/weights.json），可用 site/api/latest.json 复算。</p></div></section>
</div>
<footer>Semiconductor Tracker · 数据由公开产业资料整理 · 内容由 AI 辅助生成，不构成任何投资建议 · MIT License</footer>
<script>
const dimLabels=__DIMLABELS__;
const dimScores=__DIMSCORES__;
const hLabels=__HLABELS__;
const hIdx=__HIDX__;
const hLo=__HLO__;
const hHi=__HHI__;
const accent='#4f8cff',accent2='#36d7b7';
Chart.defaults.color='#9aa7bd';Chart.defaults.borderColor='#1f2c44';
new Chart(document.getElementById('radarChart'),{type:'radar',data:{labels:dimLabels,datasets:[{label:'维度得分',data:dimScores,backgroundColor:'rgba(79,140,255,.25)',borderColor:accent,pointBackgroundColor:accent2,borderWidth:2}]},options:{scales:{r:{min:0,max:100,ticks:{stepSize:20,color:'#9aa7bd'},grid:{color:'#1f2c44'},angleLines:{color:'#1f2c44'},pointLabels:{color:'#e6edf6',font:{size:12}}}}},plugins:{legend:{display:false}}}});
new Chart(document.getElementById('dimBar'),{type:'bar',data:{labels:dimLabels,datasets:[{label:'维度得分',data:dimScores,backgroundColor:accent,borderRadius:6}]},options:{indexAxis:'y',scales:{x:{min:0,max:100,grid:{color:'#1f2c44'}},y:{grid:{color:'#1f2c44'}}},plugins:{legend:{display:false}}}});
const ymin=Math.max(0,Math.min.apply(null,hLo.concat([40]))-5),ymax=Math.min(100,Math.max.apply(null,hHi.concat([60]))+5);
new Chart(document.getElementById('trendChart'),{type:'line',data:{labels:hLabels,datasets:[{label:'综合指数',data:hIdx,borderColor:accent,backgroundColor:'rgba(79,140,255,.15)',fill:true,borderWidth:2,tension:.3,pointRadius:3},{label:'CI下限',data:hLo,borderColor:'rgba(79,140,255,.35)',borderDash:[4,4],fill:false,pointRadius:0,borderWidth:1},{label:'CI上限',data:hHi,borderColor:'rgba(79,140,255,.35)',borderDash:[4,4],fill:'+1',backgroundColor:'rgba(79,140,255,.08)',pointRadius:0,borderWidth:1}]},options:{scales:{y:{min:ymin,max:ymax,grid:{color:'#1f2c44'}},x:{grid:{color:'#1f2c44'}}},plugins:{legend:{labels:{filter:i=>i.text==='综合指数'}}}}} });
document.querySelectorAll('#compTabs .tab').forEach(t=>t.onclick=()=>{document.querySelectorAll('#compTabs .tab').forEach(x=>x.classList.remove('on'));t.classList.add('on');document.querySelectorAll('.panel').forEach(p=>p.classList.remove('on'));document.getElementById(t.dataset.t).classList.add('on');}});
</script></body></html>"""

replacements = {
    "__UPDATED__": res["updated"] or "-",
    "__NIND__": str(res["n_indicators"]),
    "__CONF__": f'{res["data_confidence"]:.1f}',
    "__IDXCLASS__": idx_class,
    "__INDEX__": f'{res["index"]:.1f}',
    "__CILO__": f'{res["ci_low"]:.1f}',
    "__CIHI__": f'{res["ci_high"]:.1f}',
    "__MCMEAN__": f'{res["mc_mean"]:.1f}',
    "__MCSTD__": f'{res["mc_std"]:.2f}',
    "__DIMROWS__": dim_rows(),
    "__DLROWS__": dl_rows(),
    "__PUBCN__": pub_rows(public.get("china", []), "china"),
    "__PUBOV__": pub_rows(public.get("overseas", []), "overseas"),
    "__PRVCN__": prv_rows(private.get("china", [])),
    "__PRVOV__": prv_rows(private.get("overseas", [])),
    "__DIMLABELS__": json.dumps(dim_labels, ensure_ascii=False),
    "__DIMSCORES__": json.dumps(dim_scores),
    "__HLABELS__": json.dumps(hist_labels),
    "__HIDX__": json.dumps(hist_idx),
    "__HLO__": json.dumps(hist_lo),
    "__HHI__": json.dumps(hist_hi),
}
for k, v in replacements.items():
    HTML = HTML.replace(k, v)

with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"[build] index.html + api/latest.json + api/series.json 已生成")
print(f"[build] 综合指数={res['index']:.1f}  CI={res['ci_low']:.1f}-{res['ci_high']:.1f}  历史{len(hist_labels)}期")
