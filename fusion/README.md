# 可控核聚变产业投资跟踪与分析体系 (fusion-invest-system)

> **一句话人话总结（对应本报告系列 CHAPTER 05）**：核聚变就是人类想给地球装一颗"人造小太阳"来无限发电。难点不是"能不能点着火"（2022 年 NIF 已证实 Q>1），而是"能不能 24 小时稳定烧着还不把装置烧坏"。因此投资上别去赌哪家先点亮灯泡，而要买**卖铲人**——高温超导磁体/带材、特种材料、真空室这些无论哪条路线赢都要采购的部件；整机厂（CFS、Helion、能量奇点等）只当作高赔率低胜率的"期权仓"小仓位博弈。
>
> 本体系把这套"**核心仓(卖铲人) + 整机期权**"逻辑做成可复算、可扩展的开源跟踪工具，数据(JSON) → 六维加权评分 → 梯队划分 → Dashboard + JSON API。

## 快速使用

```bash
python3 build_report.py
# 生成：site/index.html（Dashboard）、site/api/latest.json、site/api/series.json、REPORT.md
```

## 发布到 GitHub Pages

1. 新建仓库（如 `fusion-invest-system`），推送本目录至 `main`；
2. **Settings → Pages → Source 选 `gh-pages` 分支 / `(root)`**；
3. 首次手动跑一次 Actions（`workflow_dispatch`），之后每周自动重建；
4. 站点：`https://<用户名>.github.io/fusion-invest-system/`。

## 目录结构

```
config/indicators.py   六维指标与权重（科学/工程/资本/供应链/政策/AI）
engine/scoring.py      归一化+加权+线性映射+蒙特卡洛 ±1σ
engine/analysis.py     梯队划分 + 配置标签
data/companies.json    海内外标的池（六维近似原始分）
data/snapshots/        跨期数据快照
build_report.py        一键生成报告与 Dashboard
site/                  构建产物（Dashboard + API）
.github/workflows/     自动重建部署
```

## 扩展：新增一期快照

在 `data/snapshots/` 新增 JSON（如 `2026Q3.json`，含 `as_of`/`note`），并更新 `companies.json` 中原始分，重跑 `build_report.py` 即自动更新趋势序列 `series.json` 与全部图表。

---

## 附：本系列前五章"人话总结"

### CHAPTER 01 · AI 大模型（已另建项目 ai-model-invest-system）
**人话**：大模型就是个"偏科的天才文科生"，能读会写但不懂物理因果。产业正从"堆参数、刷跑分"切换到"卖电赚钱"——通用底座已被巨头垄断，真金白银在**垂直多模态（视频/3D/Agent 编程）**和**开源低成本**（DeepSeek 式）里。投资看 ARR 与盈利，别只看估值。

### CHAPTER 02 · 量子计算（已另建项目 quantum-invest-system）
**人话**：量子比特是群"容易摔倒的小朋友"，所以要用很多个抱团组成稳定的"逻辑比特"；纠错算法（qLDPC、擦除纠错）是让队伍"越大越稳"的关键。四条硬件路线（超导/离子阱/中性原子/光量子）都没到终点，故**先投激光器/制冷机/测控等"卖跑道和钉鞋"的部件商**，整机厂只作期权。

### CHAPTER 03 · 半导体（已另建项目 semiconductor-tracker）
**人话**：芯片是现代工业的"地基"，国产化替代是长坡厚雪的自主可控主线。

### CHAPTER 04 · 中美 AI 博弈（已另建项目 us-china-ai-tracker）
**人话**：算力、模型、应用三层都在"脱钩又耦合"中重构，关注各自生态内的稀缺资产。

### CHAPTER 05 · 可控核聚变（本项目）
**人话**：见顶部。核心 = **工程化倒计时 + 供应链现货(卖铲人) + 整机期权**。密集兑现期在 2027–2035（SPARC/BEST/ARC/CFEDR），AI 既消耗聚变的电，又反过来帮聚变实时控制等离子体，形成"算力—能源"飞轮。

---

*免责声明：所有数据为公开信息近似整理，指标原始值为主观近似，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。*
