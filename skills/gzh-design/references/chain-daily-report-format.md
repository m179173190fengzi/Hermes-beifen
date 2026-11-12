# 链上日报排版格式决策记录（用户偏好，勿重复试错）

## 最终定案（2026-07-31）
链上日报（cron fa0df7d27b24，6/11/19/22点）用 **wechat-publish-template 橙黑赛博朋克风** HTML 交付。

## 被否掉的方案（按时间顺序）
1. **纯文本 Alpha 简报**（📡💰🔥🧠 版式）— 曾短暂恢复，后被 HTML 排版取代
2. **gzh-design 石墨极简风** — 用户否（"不行"）
3. **gzh-design 康奈尔笔记主题**（本会话新建 theme-cornell-notes.md）— 用户否（"不行，改成以前的版本"）
4. 最终：**wechat-publish-template 橙黑赛博朋克**（主橙 #FF5722 + 深黑 #0A0A0A）— 用户接受（"试试看看"→OK）

## 教训
- 用户对链上日报排版偏好：**先给用户看效果（HTML预览页），确认后再改cron**。本会话走了 4 轮格式迭代，每轮都先手动生成预览再问，用户才最终满意。
- 用户说"换成昨天的版本"指**纯文本版式**；说"用这种排版"配图指**新模板**。语境里"昨天/以前"容易歧义，先确认或先出预览。
- 新币监控筛选标准：**1D内 MC稳定≥$1M**（非瞬时冲高，看 MC历史最高值 vs 当前值）。

## 康奈尔主题现状
`references/theme-cornell-notes.md` 已建并登记 theme-index，组件完整（C1-C10）、lint 0 ERROR，但**用户已否**。保留供其他文章类型用（学习总结/知识整理类仍适用），链上日报不用。

## cron 定时跑排版的环境坑（2026-07-31 实测）
- **cron 环境无代理变量**：手动终端跑 gmgn-cli 能通（继承 shell 环境或显式前缀），但 cron 会话里裸跑 gmgn-cli 会 `ECONNREFUSED 0.0.0.0:443` → 整个报告任务报 `RuntimeError: Connection error.` 失败。
- **修复**：cron prompt 里必须显式写死 `HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890` 作为所有 gmgn-cli / 网络命令的前缀；tvl_monitor.py 内部已带代理无需处理。
- **投递也会超时**：报告生成完但 Telegram 投递失败（`httpx.ConnectError`）也会算 error——代理前缀同样适用于投递路径。
- **验证方式**：手动触发 cron `run` 后，等输出文件出现在 `~/.hermes/cron/output/fa0df7d27b24/`，检查末尾是否 `## Error` 段；有则说明某步网络失败。

## 两个公众号排版技能的体系差异（勿混用校验）
- **gzh-design**：要求 `<span leaf="">` 包裹所有文字节点（粘贴保样式的关键），校验脚本 `validate_gzh_html.py` 强制检查它。
- **wechat-publish-template**：不要求 span leaf（模板本身没用），全 inline style + 无 class 即可。**用 gzh-design 的 validate_gzh_html.py 校验 wechat 模板会误报**（"全文无 span leaf → ERROR"）——那不是真错，是两套体系不同。
- 但 `wrap_preview.py`（生成带复制按钮预览页）**两套通用**，wechat 模板的 HTML 也可以用它包预览页。
