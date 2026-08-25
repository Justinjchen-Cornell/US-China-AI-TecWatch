# AI生命科学产业投资跟踪与分析体系 (ai-life-invest-system)

> **一句话人话总结（对应本报告系列 CHAPTER 06 · AI × LIFE SCIENCE ROADMAP）**：AI正在把生命科学从"靠运气和经验的手艺活"改造成"可计算、可设计、可预测的工程学科"。AlphaFold 已把蛋白质结构预测从"几年"压到"几分钟"，下一关是把 AI 设计的药真正送上病床（临床验证期），以及让脑机接口跨过医保定价的门槛。投资上别只看 Demo，要盯临床数据与商业化拐点——**平台型/卖铲人（晶泰、Schrödinger、华大智造）确定性高，管线型（英矽智能、Recursion）高赔率，侵入式脑机（Neuralink）是远期信仰仓**。
>
> 本体系把这套"**核心仓(卖铲人/平台) + 管线期权 + 信仰仓**"逻辑做成可复算、可扩展的开源跟踪工具，数据(JSON) → 六维加权评分 → 梯队划分 → Dashboard + JSON API。

## 快速使用

```bash
python3 build_report.py
# 生成：site/index.html（Dashboard）、site/api/latest.json、site/api/series.json、REPORT.md
```

## 发布到 GitHub Pages

1. 新建仓库（如 `ai-life-invest-system`），推送本目录至 `main`；
2. **Settings → Pages → Source 选 `gh-pages` 分支 / `(root)`**；
3. 首次手动跑一次 Actions（`workflow_dispatch`），之后每周自动重建；
4. 站点：`https://<用户名>.github.io/ai-life-invest-system/`。

## 目录结构

```
config/indicators.py   六维指标与权重（临床/管线/平台/技术/资本/政策）
engine/scoring.py      归一化+加权+线性映射+蒙特卡洛 ±1σ
engine/analysis.py     梯队划分 + 配置标签（核心仓/管线期权/信仰仓）
data/companies.json    海内外标的池（约25家，六维近似原始分）
data/snapshots/        跨期数据快照
build_report.py        一键生成报告与 Dashboard
site/                  构建产物（Dashboard + API）
.github/workflows/     自动重建部署
```

## 六维指标说明

| 维度 | 权重 | 含义 |
|---|---|---|
| clinical 临床验证度 | 0.22 | 管线临床阶段/获批产品/真实世界疗效——AI制药生死线 |
| platform 商业化确定性 | 0.20 | 盈利/ARR/大药企客户/订单能见度（卖铲人稳健性）|
| tech 技术壁垒 | 0.16 | 算法唯一性、数据护城河、自动化闭环能力 |
| pipeline 管线/产品力 | 0.16 | 在研管线数量质量、平台可复用性、差异化靶点 |
| capital 资本热度 | 0.14 | 累计融资、估值、顶级投资方、IPO/SPAC 进度 |
| policy 政策/监管 | 0.12 | 医保立项、审评通道、国产替代、数据合规 |

## 扩展：新增一期快照

在 `data/snapshots/` 新增 JSON（如 `2026Q3.json`，含 `as_of`/`note`），并更新 `companies.json` 中原始分，重跑 `build_report.py` 即自动更新趋势序列 `series.json` 与全部图表。

---

## 附：本系列"人话总结"

### CHAPTER 01 · AI 大模型（项目 ai-model-invest-system）
**人话**：大模型是"偏科天才文科生"，产业从"堆参数刷分"切换到"卖电赚钱"——垂直多模态+开源低成本是金矿，投资看 ARR 与盈利。

### CHAPTER 02 · 量子计算（项目 quantum-invest-system）
**人话**：量子比特是"容易摔倒的小朋友"，要抱团成"逻辑比特"；路线未收敛，**先投部件商（卖跑道和钉鞋）**，整机厂只作期权。

### CHAPTER 03 · 半导体（项目 semiconductor-tracker）
**人话**：芯片是现代工业"地基"，国产替代是长坡厚雪主线。

### CHAPTER 04 · 中美 AI 博弈（项目 us-china-ai-tracker）
**人话**：算力/模型/应用三层"脱钩又耦合"重构，关注各自生态内稀缺资产。

### CHAPTER 05 · 可控核聚变（项目 fusion-invest-system）
**人话**：核聚变是"人造小太阳"，难点在 24 小时稳定烧；**工程化倒计时 + 供应链现货(卖铲人) + 整机期权**。

### CHAPTER 06 · AI生命科学（本项目）
**人话**：AI 把生物学变工程科学。核心 = **临床验证拐点 + 卖铲人确定性 + 脑机接口医保落地**。密集兑现期在 2026–2035（英矽III期、晶泰盈利、脑机医保、虚拟细胞基准）。

---

*免责声明：所有数据为公开信息近似整理，指标原始值为主观近似，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。*
