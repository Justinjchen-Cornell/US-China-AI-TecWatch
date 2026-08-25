#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 Dashboard 站点: 计算最新快照指数 -> 写入 site/api/*.json -> 渲染 index.html。"""
import argparse, json, os, glob, datetime
from string import Template
from compute_index import compute, load_json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT,"site")
API  = os.path.join(SITE,"api")

# 行业专项注册表: (子目录, 中文名, 简述)
INDUSTRIES = [
    ("semiconductor", "半导体", "SemiCompete 综合指数"),
    ("ai-models",     "AI模型", "ModelCompete 综合指数"),
    ("quantum",       "量子计算", "QuantumCompete 综合指数"),
    ("fusion",        "可控核聚变", "FusionCompete 综合指数"),
    ("bio",           "AI生命科学", "BioCompete 综合指数"),
    ("embodied",      "具身智能", "EmbodiedCompete 综合指数"),
]

def main():
    snap_dir = os.path.join(ROOT,"data","snapshots")
    files = sorted(glob.glob(os.path.join(snap_dir,"*.json")))
    if not files:
        raise SystemExit("未找到快照，请先运行 update_snapshot.py")
    latest = files[-1]
    weights_cfg = load_json(os.path.join(ROOT,"config","weights.json"))
    defs = load_json(os.path.join(ROOT,"data","indicators.json"))
    defs_by_id = {i["id"]: i for i in defs["indicators"]}

    # 计算最新
    snap = load_json(latest)
    res = compute(snap, weights_cfg, defs_by_id)
    res["snapshot_date"] = snap.get("date") or snap.get("updated") or ""

    # 历史序列 (每个快照一个指数点)
    series = []
    for f in files:
        s = load_json(f)
        r = compute(s, weights_cfg, defs_by_id)
        series.append({"date": s.get("date") or s.get("updated") or "",
                       "index": r["index"], "low": r["index_low"], "high": r["index_high"]})

    os.makedirs(API, exist_ok=True)
    with open(os.path.join(API,"latest.json"),"w",encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    with open(os.path.join(API,"series.json"),"w",encoding="utf-8") as f:
        json.dump({"series": series}, f, ensure_ascii=False, indent=2)
    print(f"[build_site] latest={res['index']} (95%区间 {res['index_low']}-{res['index_high']}, 置信度 {res['confidence']})")
    print(f"[build_site] 历史序列点数: {len(series)}")

    # 行业专项: 读取各行业子站 latest.json (存在即上线)
    industries = []
    for sub, name, blurb in INDUSTRIES:
        pj = os.path.join(SITE, sub, "api", "latest.json")
        rec = {"sub": sub, "name": name, "blurb": blurb, "index": None,
               "ci": None, "conf": None, "date": None}
        if os.path.exists(pj):
            try:
                d = load_json(pj)
                idx = d.get("index")
                if idx is None:
                    idx = d.get("composite")
                if idx is None:
                    for k, v in d.items():
                        if k.endswith("_index") and isinstance(v, (int, float)):
                            idx = v
                            break
                rec["index"] = idx
                rec["ci"] = d.get("ci_low")
                rec["ci2"] = d.get("ci_high")
                rec["conf"] = d.get("data_confidence")
                rec["date"] = (d.get("updated") or d.get("snapshot_date")
                               or d.get("period") or d.get("date") or d.get("as_of"))
            except Exception:
                pass
        industries.append(rec)

    # 渲染 HTML
    html = render_html(res, series, weights_cfg, industries)
    with open(os.path.join(SITE,"index.html"),"w",encoding="utf-8") as f:
        f.write(html)
    print(f"[build_site] 已生成 {os.path.join(SITE,'index.html')}")

def render_html(res, series, weights_cfg, industries=None):
    dims = weights_cfg["dimensions"]
    dim_labels = json.dumps([dims[d]["label"] for d in dims], ensure_ascii=False)
    dim_label_map = dict((d, dims[d]["label"]) for d in dims)
    dim_label_map["talent"] = "人才流向(暗线)"
    dim_scores = [round(res["dimension_scores"].get(d) if res["dimension_scores"].get(d) is not None else 0,3) for d in dims]
    dim_colors = json.dumps([dims[d]["color"] for d in dims])
    sdates = json.dumps([p["date"] for p in series])
    sidx   = json.dumps([p["index"] for p in series])
    slow   = json.dumps([p["low"] for p in series])
    shigh  = json.dumps([p["high"] for p in series])
    indicator_rows = ""
    for ind in res["indicators"]:
        norm = ind.get("norm"); norm_s = f"{norm:.2f}" if norm is not None else "—"
        direction = "正向" if ind.get("direction",1)==1 else "反向"
        indicator_rows += (
            "<tr><td>" + ind['name'] + "</td><td>" + dim_label_map.get(ind.get('dim',''), ind.get('dim','')) + "</td>"
            "<td class='num'>" + str(ind.get('value')) + "</td><td>" + ind.get('unit','') + "</td>"
            "<td class='num'>" + norm_s + "</td><td>" + direction + "</td>"
            "<td class='num'>" + str(ind.get('source_reliability',0.7)) + "</td>"
            "<td class='src'>" + ind.get('source','') + "</td></tr>")
    lat_cfg = weights_cfg.get("latent_factors", {})
    lat_scores = res.get("latent_scores", {})
    lat_rel = res.get("latent_reliability", {})
    lat_rows = ""
    for k, cfg in lat_cfg.items():
        sc = lat_scores.get(k)
        rel = lat_rel.get(k, 0.7)
        lat_rows += ("<tr><td>" + cfg['label'] + "</td>"
                     "<td class='num'>" + str(round(sc,3) if sc is not None else '—') + "</td>"
                     "<td class='num'>" + str(cfg['weight']) + "</td>"
                     "<td class='num'>" + str(round(rel*100)) + "%</td></tr>")
    dim_rows = ""
    for d in dims:
        sc = res["dimension_scores"].get(d)
        dim_rows += ("<tr><td><span class='dot' style='background:" + dims[d]['color'] + "'></span>" + dims[d]['label'] + "</td>"
                     "<td class='num'>" + str(round(sc,3) if sc is not None else '—') + "</td>"
                     "<td class='num'>" + str(dims[d]['weight']) + "</td></tr>")

    ind_rows = ""
    for r in (industries or []):
        if r.get("index") is not None:
            ci = ("<td class='num'>" + str(r['ci']) + "–" + str(r['ci2']) + "</td>"
                  if r.get("ci") is not None and r.get("ci2") is not None
                  else "<td class='num' style='color:var(--muted)'>—</td>")
            conf = ("<td class='num'>" + str(r['conf']) + "%</td>"
                    if r.get("conf") is not None else "<td class='num' style='color:var(--muted)'>—</td>")
            ind_rows += (
                "<tr><td><a href='" + r['sub'] + "/' style='color:var(--accent);text-decoration:none'>"
                + r['name'] + "</a></td><td>" + r['blurb'] + "</td>"
                "<td class='num'><b>" + str(r['index']) + "</b></td>"
                + ci + conf +
                "<td class='src'>" + str(r['date'] or '') + "</td></tr>")
        else:
            ind_rows += (
                "<tr><td>" + r['name'] + "</td><td>" + r['blurb'] + "</td>"
                "<td class='num' colspan='4' style='color:var(--muted)'>待建中</td></tr>")

    tpl = Template("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>中美AI竞争 Tracker · AICompete Index</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0b1220;--card:#121b2e;--ink:#e6edf6;--muted:#9aa7b8;--accent:#38bdf8;--good:#34d399;--bad:#f87171;--line:#1f2b44;}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);}
header{padding:28px 24px 14px;max-width:1180px;margin:0 auto;}
header h1{font-size:26px;margin:0 0 6px;letter-spacing:.3px}header p{color:var(--muted);margin:0;font-size:14px}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px 40px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-top:18px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.metric{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.metric .v{font-size:28px;font-weight:700;color:var(--accent)}.metric .l{font-size:12px;color:var(--muted);margin-top:4px}
canvas{max-height:340px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px 6px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--muted);font-weight:600;position:sticky;top:0;background:var(--card)}td.num{text-align:right;font-variant-numeric:tabular-nums}
td.src{color:var(--muted);font-size:12px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;vertical-align:middle}
.legend{font-size:12px;color:var(--muted)}.foot{color:var(--muted);font-size:12px;margin-top:18px;line-height:1.6}
@media(max-width:760px){.grid{grid-template-columns:repeat(2,1fr)}}
</style></head>
<body>
<header>
 <h1>中美 AI 全维竞争 Tracker</h1>
 <p>AICompete Index · 六维耦合 + 五条暗线综合指数 · 数据截至 <b id="dt">$snapshot_date</b> · 自动更新</p>
</header>
<div class="wrap">
 <div class="grid">
  <div class="metric"><div class="v" id="mIdx">$index</div><div class="l">综合指数 (0-100，越高=中国相对优势越强)</div></div>
  <div class="metric"><div class="v" id="mLow">$index_low–$index_high</div><div class="l">95% 置信区间 (蒙特卡洛)</div></div>
  <div class="metric"><div class="v" id="mConf">$conf_pct%</div><div class="l">数据置信度 (加权平均来源可靠度)</div></div>
  <div class="metric"><div class="v" id="mN">$n_ind</div><div class="l">监测指标数 (六维+暗线)</div></div>
 </div>
 <div class="card"><div class="legend" style="margin-bottom:8px">综合指数历史趋势 (每期快照)</div>
  <canvas id="trendChart"></canvas></div>
 <div class="card"><div class="legend" style="margin-bottom:8px">六维得分 (归一化几何平均，0-1)</div>
  <canvas id="dimChart"></canvas></div>
 <div class="card"><div class="legend" style="margin-bottom:8px">行业专项 · 六大硬科技 (点击进入子站)</div>
  <table><thead><tr><th>行业</th><th>指数体系</th><th style="text-align:right">最新指数</th><th style="text-align:right">95% 区间</th><th style="text-align:right">置信度</th><th>数据截至</th></tr></thead>
  <tbody>$ind_rows</tbody></table></div>
 <div class="card"><div class="legend" style="margin-bottom:8px">五条暗线信号 (数据驱动/配置回退)</div>
  <table><thead><tr><th>暗线</th><th style="text-align:right">信号(0-1)</th><th style="text-align:right">权重</th><th style="text-align:right">可靠度</th></tr></thead>
  <tbody>$lat_rows</tbody></table></div>
 <div class="card"><div class="legend" style="margin-bottom:8px">维度分明细</div>
  <table><thead><tr><th>维度</th><th style="text-align:right">得分</th><th style="text-align:right">权重</th></tr></thead>
  <tbody>$dim_rows</tbody></table></div>
 <div class="card"><div class="legend" style="margin-bottom:8px">指标明细 (norm=归一化值，direction=对中国有利方向)</div>
  <div style="max-height:460px;overflow:auto">
  <table><thead><tr><th>指标</th><th>维度</th><th style="text-align:right">值</th><th>单位</th><th style="text-align:right">norm</th><th>方向</th><th style="text-align:right">可靠度</th><th>来源</th></tr></thead>
  <tbody>$indicator_rows</tbody></table></div></div>
 <div class="card foot">
  <b>方法说明：</b>每指标按方向 0-1 归一化；每维内几何平均得维度分；六维按权重加权后经 sigmoid 合成综合指数；暗线(能源约束/战场数据/货币分叉/开源地缘化/人才流向)作为修正项参与合成。全部原始值/权重/可靠度随 <code>site/api/latest.json</code> 发布，可复算。<br>
  <b>免责声明：</b>数据基线来自公开学术报告与权威研究，仅作趋势研究/学术讨论，不构成任何投资建议。数值会随公开数据持续修订。
 </div>
</div>
<script>
const dimLabels=$dim_labels, dimScores=$dim_scores_json, dimColors=$dim_colors;
new Chart(document.getElementById('dimChart'),{type:'bar',data:{labels:dimLabels,datasets:[{label:'维度得分',data:dimScores,backgroundColor:dimColors,borderRadius:6}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:1,ticks:{color:'#9aa7b8'}},x:{ticks:{color:'#9aa7b8'}}}}});
const sdates=$sdates, sidx=$sidx, slow=$slow, shigh=$shigh;
new Chart(document.getElementById('trendChart'),{type:'line',data:{labels:sdates,datasets:[{label:'综合指数',data:sidx,borderColor:'#38bdf8',backgroundColor:'rgba(56,189,248,.18)',fill:true,tension:.3,pointRadius:4},{label:'下界',data:slow,borderColor:'rgba(248,113,113,.7)',borderDash:[4,4],fill:false,pointRadius:2},{label:'上界',data:shigh,borderColor:'rgba(52,211,153,.7)',borderDash:[4,4],fill:false,pointRadius:2}]},options:{responsive:true,plugins:{legend:{labels:{color:'#9aa7b8'}}},scales:{y:{min:0,max:100,ticks:{color:'#9aa7b8'}},x:{ticks:{color:'#9aa7b8'}}}}});
</script></body></html>""")
    return tpl.substitute(
        snapshot_date=res.get('snapshot_date',''),
        index=res['index'], index_low=res['index_low'], index_high=res['index_high'],
        conf_pct=int(res['confidence']*100), n_ind=len(res['indicators']),
        dim_rows=dim_rows, lat_rows=lat_rows, ind_rows=ind_rows, indicator_rows=indicator_rows,
        dim_labels=dim_labels, dim_scores_json=json.dumps(dim_scores), dim_colors=dim_colors,
        sdates=sdates, sidx=sidx, slow=slow, shigh=shigh)

if __name__=="__main__":
    main()
