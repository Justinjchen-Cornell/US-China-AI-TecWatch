# -*- coding: utf-8 -*-
"""具身智能赛道报告构建入口：生成 REPORT.md + site/index.html + JSON API。"""
import sys, os, json as _json, datetime, argparse
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
_ap = argparse.ArgumentParser(description="Embodied AI dashboard builder")
_ap.add_argument("--site-dir", default="site",
                 help="site output dir relative to project root; e.g. ../site/embodied for monorepo")
_args = _ap.parse_args()
SITE_DIR = os.path.join(_HERE, _args.site_dir)
from engine._scorelib import load_companies as load, dim_means, score_all as _score_all_all
comps = load()
W = _json.load(open(os.path.join(_HERE, "config/weights.json"), encoding="utf-8"))
DIMS = {d["key"]:d["w"] for d in W["dims"]}
def score(c):
    return round(c["mass"]*DIMS["mass"]+c["comm"]*DIMS["comm"]+c["tech"]*DIMS["tech"]
               +c["cap"]*DIMS["cap"]+c["supply"]*DIMS["supply"]+c["policy"]*DIMS["policy"],1)
for c in comps: c["score"]=score(c)
comps_sorted=sorted(comps,key=lambda x:-x["score"])
composite=round(sum(c["score"] for c in comps_sorted)/len(comps_sorted),1)
MEANS=dim_means(comps_sorted)
lead=[c for c in comps_sorted if c["score"]>=7.5]
follow=[c for c in comps_sorted if 6.5<=c["score"]<7.5]
pot=[c for c in comps_sorted if c["score"]<6.5]

os.makedirs(os.path.join(SITE_DIR, "api"), exist_ok=True)
_json.dump({"generated_at":datetime.datetime.utcnow().isoformat()+"Z","as_of":"2026Q2",
  "composite":composite,"index":round(composite*10,1),
  "index_note":"池内均分·全池公司六维加权均值(非竞争指数)",
  "index_scale":"0-100 (10x of internal 0-10 composite)","dim_means":MEANS,
  "tiers":{"领跑":[c["id"] for c in lead],"跟进":[c["id"] for c in follow],"潜力":[c["id"] for c in pot]},
  "ranking":[{"rank":i+1,"id":c["id"],"name":c["name"],"score":c["score"],"role":c["role"],"country":c["country"]} for i,c in enumerate(comps_sorted)]},
  open(os.path.join(SITE_DIR, "api/latest.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
_json.dump([{"asof":"2026-Q2","composite":composite,"count":len(comps),"dim_means":MEANS}],
  open(os.path.join(SITE_DIR, "api/series.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)

def tr(c):
    return "<tr><td>"+c['name']+"</td><td>"+(c.get('ticker') or '—')+"</td><td>"+c['country']+"</td><td>"+c['role']+"</td><td>"+c['sub']+"</td><td>"+str(c['score'])+"</td><td>"+str(c['market'])+c['unit']+"</td><td>"+c['note']+"</td></tr>"

_DIMS_JSON=_json.dumps(MEANS)
_TOP_JSON=_json.dumps([{"name":c["name"],"score":c["score"]} for c in comps_sorted[:12]])
def _tier_json(clist):
    return _json.dumps([{"n":c["name"],"t":c["ticker"] or "—","r":c["role"],"s":c["score"],"m":str(c["market"])+c["unit"],"note":c["note"]} for c in clist])
_TIER_JSON=_json.dumps({"lead":_tier_json(lead),"follow":_tier_json(follow),"pot":_tier_json(pot)})

HTML='''<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8"><title>具身智能产业投资跟踪</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;max-width:1180px;margin:0 auto;padding:24px;color:#1a2233;background:#f7f9fc}h1{font-size:26px;margin:0 0 6px}h2{font-size:18px;margin:28px 0 10px;color:#0d3b8a;border-left:4px solid #2f6bff;padding-left:10px}.meta{color:#7a8699;font-size:13px}.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:12px;color:#fff;background:#2f6bff;margin-left:6px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:14px 0}.card{background:#fff;border-radius:12px;padding:16px;box-shadow:0 2px 10px rgba(0,0,0,.06)}.card h3{margin:0 0 6px;font-size:15px}.card .num{font-size:24px;font-weight:700;color:#2f6bff}.tabs{display:flex;gap:8px;margin:10px 0 4px}button{border:1px solid #d5dbe5;background:#fff;padding:6px 14px;border-radius:8px;cursor:pointer;font-size:13px}button.on{background:#2f6bff;color:#fff;border-color:#2f6bff}table{width:100%;border-collapse:collapse;font-size:13px;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.05)}th{background:#0d3b8a;color:#fff;padding:9px;text-align:left}td{padding:8px 9px;border-bottom:1px solid #eef1f6}.tier-l{color:#c0392b;font-weight:700}.tier-f{color:#d48806;font-weight:700}.tier-p{color:#7a8699}canvas{max-height:340px}</style></head>
<body><h1>🤖 具身智能 / 物理AI 产业投资跟踪 <span class="badge">GitHub Pages</span></h1>
<div class="meta">EmbodiedCompete Index · 数据基线为公开信息近似整理（2026Q2 快照）· 仅供研究探讨，不构成投资建议</div>
<div class="grid"><div class="card"><h3>综合指数</h3><div class="num">__COMPOSITE__</div><div class="meta">25家标的六维加权平均（0-10）</div></div>
<div class="card"><h3>领跑 / 跟进 / 潜力</h3><div class="num">__LEADN__ / __FOLLOWN__ / __POTN__</div><div class="meta">按六维总分划分梯队</div></div>
<div class="card"><h3>核心逻辑</h3><div class="meta" style="font-size:13px;line-height:1.7">整机组装厂化 · 价值向"脑"与"手"集中 · 供应链卖铲人确定性最高</div></div></div>
<h2>六维均值（全标的池）</h2><div class="card"><canvas id="radar"></canvas></div>
<h2>Top 12 排名（六维总分）</h2><div class="card"><canvas id="bar"></canvas></div>
<div class="tabs"><button class="on" onclick="show('lead',this)">领跑（≥7.5）</button><button onclick="show('follow',this)">跟进（6.5–7.4）</button><button onclick="show('pot',this)">潜力（&lt;6.5）</button></div>
<div id="tbl"></div>
<h2>全标的明细（按总分降序）</h2><table><thead><tr><th>公司</th><th>代码</th><th>国别</th><th>角色</th><th>细分</th><th>分数</th><th>市值/估值</th><th>点评</th></tr></thead><tbody>__TBODY__</tbody></table>
<div class="meta" style="margin-top:24px">数据来源：公开融资披露、公司公告、行业研报整理（近似）。指标原始值为人工近似评分，仅供趋势研究。</div>
<script>const DIMS=__DIMS__;const top=__TOP__;const TIERS=__TIERS__;
new Chart(document.getElementById('radar'),{type:'radar',data:{labels:['量产确定性','商业化进度','技术壁垒','资本热度','供应链地位','政策/场景'],datasets:[{label:'六维均值',data:[DIMS.mass,DIMS.comm,DIMS.tech,DIMS.cap,DIMS.supply,DIMS.policy],backgroundColor:'rgba(47,107,255,.25)',borderColor:'#2f6bff',borderWidth:2,pointBackgroundColor:'#2f6bff'}]},options:{scales:{r:{min:0,max:10,ticks:{stepSize:2}}},plugins:{legend:{display:false}}}});
new Chart(document.getElementById('bar'),{type:'bar',data:{labels:top.map(x=>x.name),datasets:[{label:'六维总分',data:top.map(x=>x.score),backgroundColor:'#2f6bff'}]},options:{indexAxis:'y',scales:{x:{min:0,max:10}},plugins:{legend:{display:false}}}});
function show(k,b){document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');const arr=TIERS[k];let h='<table><thead><tr><th>公司</th><th>代码</th><th>角色</th><th>分数</th><th>市值/估值</th><th>点评</th></tr></thead><tbody>';for(const c of arr){h+='<tr><td>'+c.n+'</td><td>'+c.t+'</td><td>'+c.r+'</td><td class="'+(k==="lead"?"tier-l":k==="follow"?"tier-f":"tier-p")+'">'+c.s+'</td><td>'+c.m+'</td><td>'+c.note+'</td></tr>';}h+='</tbody></table>';document.getElementById('tbl').innerHTML=h;}
show('lead',document.querySelector('.tabs button'));</script></body></html>'''
HTML=(HTML.replace("__COMPOSITE__",str(composite)).replace("__LEADN__",str(len(lead)))
         .replace("__FOLLOWN__",str(len(follow))).replace("__POTN__",str(len(pot)))
         .replace("__TBODY__",''.join(tr(c) for c in comps_sorted))
         .replace("__DIMS__",_DIMS_JSON).replace("__TOP__",_TOP_JSON).replace("__TIERS__",_TIER_JSON))
open(os.path.join(SITE_DIR, "index.html"),"w",encoding="utf-8").write(HTML)

def _fmt(clist): return " · ".join(f"{c['name']}({c['score']})" for c in clist)
REPORT='''# 具身智能 / 物理AI 产业投资跟踪 · 分析报告
> EmbodiedCompete Index = **__COMPOSITE__** / 10（25家标的六维加权平均）· 数据基线为公开信息近似整理，仅供研究探讨，不构成投资建议。

## 一、 核心结论（人话版）
具身智能是 AI 从"数字世界"落地到"物理世界"的最后一公里。2026 年被定义为"量产元年"——人形机器人跨过万台门槛，成本曲线复刻新能源汽车。

投资三条核心判断：
1. **整机组装厂化**：硬件标准化+降价，整机厂利润被压缩为"富士康式组装费"。
2. **价值向"脑"与"手"集中**：上游"脑"(VLA/世界模型)与"手"(灵巧手，占整机物料约17.3%)价值密度最高。
3. **卖铲人确定性最高**：减速器/伺服/丝杠/传感等部件商只要行业扩产就持续受益。

## 二、 六维评分体系
| 维度 | 权重 | 全池均值 | 说明 |
|---|---|---|---|
| 量产确定性 | 0.22 | __MMASS__ | 万台门槛/量产交付/成本曲线 |
| 商业化进度 | 0.20 | __MCOMM__ | 付费订单/进厂部署/复购ROI |
| 技术壁垒 | 0.18 | __MTECH__ | VLA/世界模型/灵巧手/Sim2Real |
| 资本热度 | 0.16 | __MCAP__ | 融资轮次/估值/顶级机构 |
| 供应链地位 | 0.14 | __MSUPPLY__ | 核心部件卡位 |
| 政策/场景 | 0.10 | __MPOLICY__ | 工业场景/国产替代/政策支持 |

## 三、 梯队排名
### 领跑（≥7.5，__LEADN__家）
__LEADLIST__
### 跟进（6.5–7.4，__FOLLOWN__家）
__FOLLOWLIST__
### 潜力（<6.5，__POTN__家）
__POTLIST__

## 四、 风险监测
1. 量产证伪：2027年前工厂任务成功率未突破99%，"量产元年"叙事面临回调。
2. 估值透支：部分整机/灵巧手估值已隐含"成为机器人OS"预期。
3. 自研威胁：头部整机厂自研灵巧手比例上升，挤压第三方部件商。
4. 路线切换：直驱 vs 绳驱/腱绳技术路线未统一。

*免责声明：本项目为开源分析工具，数据来源于公开报告与行业研究，指标原始值为人工近似评分，仅供投资研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。*
'''
REPORT=(REPORT.replace("__COMPOSITE__",str(composite)).replace("__MMASS__",str(MEANS["mass"]))
        .replace("__MCOMM__",str(MEANS["comm"])).replace("__MTECH__",str(MEANS["tech"]))
        .replace("__MCAP__",str(MEANS["cap"])).replace("__MSUPPLY__",str(MEANS["supply"])).replace("__MPOLICY__",str(MEANS["policy"]))
        .replace("__LEADN__",str(len(lead))).replace("__FOLLOWN__",str(len(follow))).replace("__POTN__",str(len(pot)))
        .replace("__LEADLIST__",_fmt(lead)).replace("__FOLLOWLIST__",_fmt(follow)).replace("__POTLIST__",_fmt(pot)))
open("REPORT.md","w",encoding="utf-8").write(REPORT)
print("built. composite =",composite,"lead/follow/pot =",len(lead),len(follow),len(pot))
