# 俄乌装备损失率统计分析

本项目基于 Oryx 和 WarSpotting 的开源影像验证数据，分析俄乌装备损失记录，完成损失率点估计、Poisson 置信区间、两独立 Poisson 条件检验、装备类型分层估计，以及基于 WarSpotting 日期字段的周度聚合分析。

## 研究问题

1. 如何基于开源影像验证记录估计装备损失率？
2. 俄乌双方装备损失率是否存在统计显著差异？
3. 不同装备类型的损失结构是否存在明显差异？
4. 带日期的 WarSpotting 数据能否用于时间分层和 Block Bootstrap 分析？

## 数据来源

### Oryx

Oryx 数据来自两个公开页面：

- 俄方损失页：https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html
- 乌方损失页：https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html

Oryx 只记录有照片或视频证据的装备损失，因此这里估计的是“影像验证损失率”，不是绝对真实损失率。

生成的合并文件：

```text
oryx_losses_combined.csv
```

### WarSpotting

WarSpotting 数据来自 Kaggle 同步源的公开 CSV：

```text
warspotting_losses.csv
```

该文件包含日期、装备类型、状态和地理信息，但当前数据只包含俄方损失记录。因此 WarSpotting 主要用于俄方时间序列和周度 block 分析。

## 目录结构

```text
.
├── README.md
├── data_sources.md
├── oryx_losses_combined.csv
├── oryx_russia.html
├── oryx_ukraine.html
├── warspotting_losses.csv
├── russia_losses_equipment.json
├── russia_losses_equipment_oryx.json
├── scripts
│   ├── scrape_oryx.py
│   ├── build_summary_tables.py
│   ├── build_poisson_inference.py
│   └── build_warspotting_weekly.py
└── tables
    ├── cleaned_oryx_loss_records.csv
    ├── summary_by_side.csv
    ├── summary_by_side_category.csv
    ├── summary_by_side_status.csv
    ├── summary_by_side_category_status.csv
    ├── summary_by_side_category_model.csv
    ├── category_comparison_russia_ukraine.csv
    ├── poisson_inference_overall.csv
    ├── poisson_inference_by_category.csv
    ├── warspotting_weekly_total.csv
    ├── warspotting_weekly_by_type.csv
    ├── warspotting_weekly_by_status.csv
    ├── warspotting_type_summary.csv
    ├── warspotting_weekly_block_bootstrap_bca.csv
    ├── warspotting_weekly_bootstrap_distribution.csv
    ├── warspotting_weekly_jackknife_rates.csv
    ├── warspotting_coordinate_quality.csv
    ├── warspotting_spatial_macro_region_summary.csv
    ├── warspotting_spatial_macro_region_by_type.csv
    ├── warspotting_spatial_grid_1deg_summary.csv
    ├── warspotting_location_area_summary.csv
    ├── observation_probability_sensitivity_overall.csv
    └── observation_probability_sensitivity_by_category.csv
```

## 运行顺序

### 1. 抓取并合并 Oryx 双方数据

使用已下载的 HTML 重新生成 CSV：

```bash
python3 scripts/scrape_oryx.py
```

如需重新联网抓取最新页面：

```bash
python3 scripts/scrape_oryx.py --refresh
```

输出：

```text
oryx_losses_combined.csv
```

### 2. 生成清洗后的统计表

```bash
python3 scripts/build_summary_tables.py
```

主要输出：

```text
tables/cleaned_oryx_loss_records.csv
tables/summary_by_side.csv
tables/summary_by_side_category.csv
tables/category_comparison_russia_ukraine.csv
```

说明：统计损失件数时应汇总 `item_count` 字段，不能直接数 CSV 行数。

### 3. 生成 Poisson 估计和检验表

```bash
python3 scripts/build_poisson_inference.py
```

主要输出：

```text
tables/poisson_inference_overall.csv
tables/poisson_inference_by_category.csv
```

当前观察期设定为：

```text
2022-02-24 至 2026-05-28，共 1555 天
```

### 4. 生成 WarSpotting 周度聚合表

```bash
python3 scripts/build_warspotting_weekly.py
```

主要输出：

```text
tables/warspotting_weekly_total.csv
tables/warspotting_weekly_by_type.csv
tables/warspotting_weekly_by_status.csv
tables/warspotting_type_summary.csv
```

### 5. 生成 WarSpotting 周度 Block Bootstrap / BCa 区间

```bash
python3 scripts/build_warspotting_bootstrap.py
```

主要输出：

```text
tables/warspotting_weekly_block_bootstrap_bca.csv
tables/warspotting_weekly_bootstrap_distribution.csv
tables/warspotting_weekly_jackknife_rates.csv
```

### 6. 生成 WarSpotting 坐标/地区分层表

```bash
python3 scripts/build_warspotting_spatial.py
```

主要输出：

```text
tables/warspotting_coordinate_quality.csv
tables/warspotting_spatial_macro_region_summary.csv
tables/warspotting_spatial_macro_region_by_type.csv
tables/warspotting_spatial_grid_1deg_summary.csv
tables/warspotting_location_area_summary.csv
```

宏观区域由经纬度阈值构造，不是官方行政区：

```text
East: lon >= 36
West: lon < 28
North: lat >= 50
South: lat < 47.5
Central: 其余有坐标记录
```

### 7. 生成观测概率敏感性分析表

```bash
python3 scripts/build_observation_sensitivity.py
```

主要输出：

```text
tables/observation_probability_sensitivity_overall.csv
tables/observation_probability_sensitivity_by_category.csv
```

该分析不直接估计观测概率，而是假设不同的俄乌观测概率组合：

```text
p_observed_russia, p_observed_ukraine ∈ {0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}
```

并计算：

```text
corrected_count = observed_count / p_observed
corrected_rate_ratio = corrected_russia_rate / corrected_ukraine_rate
```

## 已实现的统计方法

### MLE 点估计

设某方在观察期内的损失数为 `Y`，观察期天数为 `T`，则 Poisson 损失率的极大似然估计为：

```text
lambda_hat = Y / T
```

脚本输出了：

```text
rate_per_day
rate_per_30_days
```

### Poisson 置信区间

已实现三类区间：

```text
Wald CI
Score CI
Exact CI
```

对应字段位于：

```text
tables/poisson_inference_overall.csv
tables/poisson_inference_by_category.csv
```

### 两独立 Poisson 条件检验

用于检验：

```text
H0: lambda_Russia = lambda_Ukraine
H1: lambda_Russia != lambda_Ukraine
```

输出字段包括：

```text
rate_ratio_russia_over_ukraine
rate_ratio_ci_low
rate_ratio_ci_high
conditional_poisson_p_value
significant_0_05
```

### 分层估计

已按装备类型分层：

```text
tables/poisson_inference_by_category.csv
```

也生成了按状态和型号的汇总：

```text
tables/summary_by_side_status.csv
tables/summary_by_side_category_status.csv
tables/summary_by_side_category_model.csv
```

### 周度聚合

WarSpotting 数据具有日期字段，已按周一作为 `week_start` 聚合：

```text
tables/warspotting_weekly_total.csv
tables/warspotting_weekly_by_type.csv
tables/warspotting_weekly_by_status.csv
```

这些表可作为后续 Block Bootstrap 的输入。

### Block Bootstrap 与 BCa 区间

已基于 `warspotting_weekly_total.csv` 将每一周作为一个 block，进行 10000 次有放回重抽样，并使用 jackknife 计算 BCa 校正项。

输出文件：

```text
tables/warspotting_weekly_block_bootstrap_bca.csv
```

当前结果：

```text
theta_hat = 14.695067 件/天
percentile 95% CI = [13.214574, 16.407479]
BCa 95% CI = [13.377314, 16.656228]
```

### 坐标/地区分层

已基于 WarSpotting 的 `latitude` 和 `longitude` 字段构造空间分层。

坐标覆盖情况：

```text
records_with_coordinates = 14048 / 22939
coordinate_coverage = 61.2407%
```

宏观区域分布：

```text
East: 10171
North: 2275
South: 1514
Central: 88
Missing coordinates: 8891
```

由于约 38.76% 记录缺少坐标，空间分层结果应作为观测偏误分析，而不是完整地理分布估计。

### 观测概率敏感性分析

已构造简单观测概率敏感性分析。总体结果显示，在 49 个观测概率组合中，有 47 个组合下修正后的 `Russia / Ukraine` rate ratio 仍大于 1。

关键场景：

```text
p_Russia = 0.7, p_Ukraine = 0.7 -> corrected RR = 2.060247
p_Russia = 0.8, p_Ukraine = 0.6 -> corrected RR = 1.545186
p_Russia = 0.9, p_Ukraine = 0.5 -> corrected RR = 1.144582
p_Russia = 1.0, p_Ukraine = 0.4 -> corrected RR = 0.824099
```

这说明总体结论对中等程度的观测概率差异较稳健；只有在假设俄方损失几乎完全可观测、而乌方损失观测概率很低的极端场景下，rate ratio 才可能低于 1。

## 当前主要结果

基于 Oryx 双方数据，当前总体损失数为：

```text
Russia: 22980
Ukraine: 11154
```

总体 Poisson 损失率估计：

```text
Russia: 14.778135 件/天
Ukraine: 7.172990 件/天
```

总体 rate ratio：

```text
Russia / Ukraine = 2.060247
95% CI = [2.014172, 2.107377]
```

在 Oryx 影像验证口径下，俄方装备损失率显著高于乌方。

## 数据口径与限制

1. Oryx 和 WarSpotting 均为开源影像验证数据，不等于真实全部损失。
2. Oryx 双方数据适合做俄乌比较，但缺少稳定日期字段。
3. WarSpotting 数据有日期和坐标，适合做时间分析，但当前文件只包含俄方损失。
4. 不同数据源装备分类口径不同，分类型比较需要先做类别映射。
5. 当前 Poisson 模型假设观察期内损失过程可由平均损失率概括，未完全建模战役阶段、地域控制和影像可得性差异。

## 后续可扩展方向

1. 将 Oryx 和 WarSpotting 的装备类型进一步标准化，比较俄方记录一致性。
2. 若能获得乌方带日期数据，可扩展为真正的双方时间分层和 Block Bootstrap 检验。
3. 使用更精确的 GIS 行政区边界替代当前经纬度阈值区域划分。
4. 引入外部审计数据或多源匹配方法，直接估计不同地区和装备类型的观测概率。
