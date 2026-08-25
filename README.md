# US-China AI Competition Tracker

一个数据驱动、可自动更新、带综合指数（Composite Index）的中美 AI 全维竞争监测 Dashboard，可一键发布到 GitHub Pages。

## 项目定位

把公开报告《中美 AI 全维竞争》中"双核六维耦合"框架，翻译成一个可持续维护的观测仪表盘：

- **六个维度**：能源(Energy) · 算力(Compute) · 智能(Intelligence) · 生命(Life) · 暴力(Violence) · 金融(Finance)
- **五条暗线**：能源约束 · 战场数据 · 货币分叉 · 开源地缘化 · 人才流向
- **一个综合指数**：`AICompete Index ∈ [0,100]`，数值越高代表该体系（默认中国）相对优势越强；50 为均势。

## 综合指数数学方法

综合指数不是简单平均，而是**可复现、可审计、带不确定性**的合成：

1. **指标归一化**：对每个指标按其性质做 0-1 归一化。归一化使用**指标定义中的绝对校准区间 `ref_min/ref_max`**（跨快照稳定、单指标维度不失真、任何人可复算）；规模/交易量类指标（投资额、市值、日调用量）启用对数缩放 `log(1+x)/log(1+x_max)`；反向指标（direction=-1）取补。未配置参考区间的指标回退到维度内 min/max（min==max 时取中性 0.5）。
2. **维度得分**：每维内指标取**几何平均**（对零值做 Laplace 平滑 `log(x+ε)`），避免个别极端值主导。
3. **维度权重**：六维权重 `[1.0, 1.2, 1.3, 0.9, 1.0, 1.1]`（智能/算力略高，生命略低），暗线作为修正项权重 0.4。权重与数据完全分离，可在 `config/weights.json` 调整。
4. **暗线信号（数据驱动）**：带 `latent` 标签的指标（如人才流向 3 项）先归一化，再取几何平均得到该暗线的信号值；无对应指标的暗线回退到 `config/weights.json` 中 `latent_signals` 的配置值。暗线信号与可靠度随 API 一并发布，可复算。
5. **合成**：`Index = 100 * sigmoid( z )`，其中 `z = Σ w_i·(s_i - 0.5)` 经标准化，`sigmoid` 保证输出稳定落在 (0,100)。
6. **不确定性**：对每个指标给一个 `source_reliability ∈ [0,1]`（官方=1.0 / 行业研究=0.8 / 媒体=0.6），指数附带 `confidence = 加权平均可靠度`，并给出 `index_low / index_high`（±1σ 蒙特卡洛扰动，N=2000）。
> 设计原则：**透明优先**。所有原始值、归一化值、维度分、权重、可靠度、置信区间全部随 JSON API 一并发布，任何人可复算。

## 目录结构

```
us-china-ai-tracker/
├── README.md
├── config/
│   └── weights.json          # 维度/指标权重与方向配置
├── data/
│   ├── indicators.json       # 指标定义（名称/单位/方向/维度/可靠度/来源）
│   └── snapshots/            # 每期观测快照（按 YYYY-MM-DD.json）
├── scripts/
│   ├── compute_index.py      # 核心：归一化+维度分+综合指数+置信区间
│   ├── update_snapshot.py    # 从 indicators.json 生成本期 snapshot
│   └── build_site.py         # 渲染 index.html + 写入 api/*.json
├── site/
│   ├── index.html             # 单页 Dashboard（Chart.js 图表）
│   └── api/
│       ├── latest.json        # 最新一期数据+指数（供外部调用）
│       └── series.json        # 历史指数序列（供趋势图）
└── .github/workflows/
    └── update.yml             # 每周自动重算并部署 GitHub Pages
```

## 本地使用

```bash
python scripts/compute_index.py --snapshot data/snapshots/2026-08-24.json
python scripts/build_site.py
# 打开 site/index.html 查看 Dashboard
```

## 自动更新（GitHub Actions）

`.github/workflows/update.yml` 每周一 UTC 00:00 自动运行：重新计算最新快照的指数、构建站点并部署到 GitHub Pages（分支 `gh-pages`）。如需手动触发，在仓库 Actions 页点 "Run workflow"。

## 数据来源与免责声明

数据基线来自公开学术报告与权威研究（Stanford AI Index、ATOM Report、OpenRouter、CIFER、中金研究、行业公开数据）。本项目**仅做趋势研究与学术讨论**，不构成任何投资建议。指标数值会随公开数据持续修订，请以最新快照为准。
