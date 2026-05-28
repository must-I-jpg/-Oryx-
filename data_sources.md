# 数据来源说明

## warspotting_losses.csv

- 来源：Automated WarSpotting scraper / Kaggle 同步源
- 下载地址：https://raw.githubusercontent.com/lazar-bit/automated-warspotting-scraper/main/warspotting_losses.csv
- 用途：逐件影像验证的俄罗斯装备损失记录。
- 主要字段：`id`, `date`, `type`, `model`, `status`, `lost_by`, `nearest_location`, `latitude`, `longitude`, `unit`, `tags`, `sources`, `photos`
- 注意：当前文件中 `lost_by` 字段全部为 `Russia`，不包含乌克兰装备损失。

## russia_losses_equipment.json

- 来源：2022 Ukraine Russia War Dataset
- 下载地址：https://raw.githubusercontent.com/PetroIvaniuk/2022-Ukraine-Russia-War-Dataset/main/data/russia_losses_equipment.json
- 用途：俄罗斯装备损失累计时序数据，可用于时间趋势对照。

## russia_losses_equipment_oryx.json

- 来源：2022 Ukraine Russia War Dataset
- 下载地址：https://raw.githubusercontent.com/PetroIvaniuk/2022-Ukraine-Russia-War-Dataset/main/data/russia_losses_equipment_oryx.json
- 用途：Oryx 装备类别对照数据，可辅助装备分类映射。

## oryx_losses_combined.csv

- 来源：Oryx 俄方页面与 Oryx 乌方页面。
- 俄方页面：https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-equipment.html
- 乌方页面：https://www.oryxspioenkop.com/2022/02/attack-on-europe-documenting-ukrainian.html
- 生成脚本：`scripts/scrape_oryx.py`
- 用途：俄乌双方装备损失的统一结构化 CSV，可用于双方损失率比较、分装备类型比较和 Poisson rate ratio 检验。
- 计数说明：每行对应一个 Oryx 证据链接；统计损失件数时应汇总 `item_count` 字段，而不是简单计算行数。

## 备注

Kaggle API 当前不可用：本机未安装 `kaggle` 命令，且没有检测到 `~/.kaggle/kaggle.json` 凭据。因此主数据采用 Kaggle 数据集作者公开的 GitHub 同步 CSV。

WarSpotting API 文档说明当前只统计俄罗斯损失，其他参战方参数会被忽略。因此 WarSpotting/Kaggle 数据不能直接完成俄乌双方逐件损失率对比；双方比较应优先使用 `oryx_losses_combined.csv`。
