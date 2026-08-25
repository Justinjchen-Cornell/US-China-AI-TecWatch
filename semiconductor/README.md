# Semiconductor Tracker · 半导体产业竞争力仪表盘

一个可发布到 **GitHub Pages** 的半导体行业专项 Dashboard。基于公开产业资料，把「中美半导体全维竞争」量化为可复算的 **SemiCompete Composite Index（半导体综合指数）**，并配套六维雷达、趋势图、企业图谱与一级市场追踪。

> 本仪表盘是「股权财政 × 中美 AI/半导体竞争」系列的行业拆分版之一（半导体行业）。数据基线来自公开学术报告与权威研究，仅作趋势研究与学术讨论，**不构成任何投资建议**。

## 综合指数的数学方法（透明、可复算）

1. **归一化**：每指标按「对中国是否有利」方向做 0–1 归一化（正向线性 / 反向取补）；
2. **维度分**：每维内指标取**几何平均**（Laplace 平滑），避免极端值主导；
3. **加权合成**：六维权重 `[制程装备 1.2, 制造代工 1.1, 存储HBM 1.2, AI芯片 1.3, 先进封装 1.1, 未来范式 1.1]`（AI 芯片 / 存储 HBM 略高）+ 五条暗线作为修正项；
4. **Sigmoid 映射**：`Index = 100·sigmoid(z)`，稳定落在 (0,100)，>50 偏中国有利；
5. **不确定性**：每个指标带 `source_reliability`，指数附带置信度 + 蒙特卡洛（N=2000）±1σ 区间。

权重与数据**完全分离**，可在 `config/weights.json` 自由调整，任何人可用 `site/api/latest.json` 复算。

## 目录结构

```
semiconductor-tracker/
├── data/indicators.json        # 六维指标 + 暗线修正项（可手工更新）
├── data/companies_public.json  # 中国/海外上市公司基本面
├── data/companies_private.json # 一级市场未上市核心标的
├── config/weights.json         # 六维权重（与数据分离）
├── scripts/
│   ├── compute_index.py        # 综合指数计算引擎（含 MC 不确定性）
│   ├── update_snapshot.py      # 生成一期快照 → data/history.json
│   └── build_site.py           # 生成 Dashboard（index.html + api）
├── .github/workflows/update.yml# 每周自动更新 + 部署 gh-pages
└── site/                       # 构建产物（GitHub Pages 发布目录）
    ├── index.html
    └── api/{latest,series}.json
```

## 本地使用

```bash
# 1) 生成一期快照（写入 data/history.json）
python scripts/update_snapshot.py

# 2) 构建 Dashboard（生成 site/index.html + site/api/*）
python scripts/build_site.py

# 3) 本地预览：直接用浏览器打开 site/index.html
```

## 发布到 GitHub Pages

1. 新建仓库（如 `semiconductor-tracker`），把本目录文件推送到 `main` 分支；
2. **Settings → Pages → Source 选 `gh-pages` 分支 / `(root)`**，保存；
3. 首次手动跑一次 Actions（`workflow_dispatch`），之后每周一 UTC 0 点自动更新；
4. 站点地址：`https://<用户名>.github.io/semiconductor-tracker/`。

## 数据更新约定

- 更新半导体指标数值 → 编辑 `data/indicators.json` → 重跑 `update_snapshot.py` + `build_site.py`；
- 新增/调整企业 → 编辑 `data/companies_public.json` 或 `companies_private.json`；
- 调整维度权重 → 编辑 `config/weights.json`（不影响历史快照的可复算性）。

## License

MIT（数据基线见各 `source` 字段，趋势解读仅供参考）。
