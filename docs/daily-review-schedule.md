# 日报调度

`tasks/daily-review.yaml` 每天北京时间 18:05、23:50 执行 `scripts/daily_review_scheduled.py --push`，复用 `F:/personal-projects/daily-review/daily_review.py` 生成当天完整日报。

18:05 照常生成和推送。23:50（含当晚失败重试）先读取 Claude/Codex 会话：只有 18:05 之后、检查时刻之前出现用户指令、工具调用或助手正文，才生成并推送带「全日版」标识的全天日报到钉钉和 RSS。跨越 18:05 的已有会话也会检查。元数据、token 统计、后台进度、内部审查及子会话不会触发。无新增工作时正常退出，不调用 LLM、不写报告、不推送。

工作活动沿用日报的本机会话数据源，不包含脱离 Claude/Codex 的手动操作。报告文件仍由原脚本保存为 `reports/<日期>.md`，全日版覆盖白天版。

验证：`python -m unittest discover -s tests -v`。测试只使用临时样本和推送替身，不实际发送日报。

配置修改后重启 `PyTaskSched` 服务，使调度器重新加载入口。
