# 量子计算产业投资跟踪与分析体系 (quantum-invest-system)

> **一句话人话总结（CHAPTER 02）**：量子比特是群"容易摔倒的小朋友"，所以要用很多个抱团组成稳定的"逻辑比特"；qLDPC、擦除纠错就是让队伍"越大越稳"的新组队招式。四条硬件路线（超导/离子阱/中性原子/光量子）都没到终点，故**先投激光器/制冷机/测控等"卖跑道和钉鞋"的部件商（卖铲人）**，整机厂（Quantinuum/IonQ/本源等）只作期权。AI 既能帮量子实时纠错，又能与量子形成"算力—能源"飞轮。

## 快速使用

```bash
python3 build_report.py
# 生成：site/index.html（Dashboard，含六维雷达图/Top12排名/梯队切换表）
#       site/api/latest.json、site/api/series.json、REPORT.md
```

## 发布到 GitHub Pages

1. 新建仓库（如 `quantum-invest-system`），推送本目录至 `main`；
2. **Settings → Pages → Source 选 `gh-pages` 分支 / `(root)`**；
3. 首次手动跑一次 Actions（`workflow_dispatch`），之后每周一自动重建；
4. 站点：`https://<用户名>.github.io/quantum-invest-system/`。

## 目录结构

```
config/indicators.py    六维指标与权重（技术/商业化/资本/路线/供应链卖铲人/政策战略）
engine/_scorelib.py     六维评分核心库（归一化+加权+蒙特卡洛±1σ，独立可复算）
engine/scoring.py       薄壳，委托 _scorelib
engine/analysis.py      梯队划分(领跑/跟进/潜力/观察)+配置标签
data/companies.json     海内外量子计算标的池（24家，覆盖四路线+部件+软件）
data/snapshots/         跨期数据快照（2026Q2 基线）
build_report.py         一键生成报告与 Dashboard
site/                   构建产物（Dashboard + API）
.github/workflows/       自动周构建部署
```

## 标的池覆盖（24 家）

| 类别 | 代表标的 |
|---|---|
| 海外整机（离子阱/光/中性原子/超导） | Quantinuum、IonQ、PsiQuantum、Atom Computing、QuEra、IQM、Rigetti、IBM、Google Quantum(Willow)、微软 |
| 中国整机（四路线） | 本源量子(超导)、图灵量子/玻色量子(光)、华翊量子(离子阱)、中科酷原/太一量生(中性原子) |
| 核心部件/卖铲人 | 国盾量子、国仪量子、频准激光、量旋科技 |
| 软件/算法 | SandboxAQ、Riverlane、Q-CTRL、Diraq |

## 附：量子原理小学生版

见同交付内的 `quantum-primer.md`（旋转硬币=叠加态；两枚硬币心灵感应=纠缠；刚睡着被吵醒=退相干；小朋友手拉手撑起靠谱大人=逻辑比特与 qLDPC）。

*免责声明：数据为公开信息近似整理，指标原始值为主观近似，仅供趋势研究与学术探讨，不构成任何投资建议。市场有风险，投资需谨慎。*
