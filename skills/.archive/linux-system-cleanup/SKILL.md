---
name: linux-system-cleanup
description: 安全清理 Linux 桌面系统 — 卸载不常用软件、清旧内核/日志/孤儿snap。先调查再动手，用使用证据判断"不常用"，避免误删工作流依赖。用户说"优化系统/清理磁盘/卸载不常用的软件"时使用。
---

# Linux 系统清理 / 卸载不常用软件

## 核心原则
1. 先调查，再动手。删除前必须有"不使用"的证据（进程不在跑 + 日志/数据目录 mtime 旧）。
2. 用户要求卸载软件 ≠ 可以随意批量 rm -rf 缓存目录。~/.cache 整批删除要单独提出、单独确认。
3. 每个删除项都要能说清理由 + 恢复方式（如 `apt install wechat` 一键装回）。

## 调查清单（第一步全部并行）
- `df -h /`、`free -h`、`uptime`
- `dpkg-query -W -f='${Installed-Size}\t${Package}\n' | sort -rn | head -40` — 大包排名
- `ps aux --sort=-%mem | head -20` — 正在运行的进程 = 在用
- `snap list`、`flatpak list`、`apt-get autoremove --dry-run`
- `du -sh ~/.cache /var/log /var/cache/apt/archives`、`journalctl --disk-usage`

## 使用证据判断"不常用"
- 进程不在跑 + 数据/日志目录 mtime 很旧（如 `~/.xwechat/log` 最后日志 >4 周）= 可卸载候选
- 陷阱：snap 应用的数据目录 mtime 在每次登录/挂载时被刷新（`~/snap/telegram-desktop` 会显示当天时间）——这不是使用证据，别据此误判
- 删 docker 前必查：`docker ps -a`/`docker images` 为空 ≠ 没用。搜 `~` 及项目目录的 `docker-compose*.yml`/`compose.yaml`。实例：用户 freqtrade、cognee、hermes-workspace 都有 compose 文件 → docker 必须保留（即使当前零容器）
- 删 snap SDK 前查引用：`snap connections <snap> | grep -c <sdk名>`，为 0 才是孤儿
- 旧内核：`uname -r` 确认当前，`dpkg -l | grep -E 'linux-(image|modules|headers)'` 看状态（rc = 只剩配置，可 purge）

## 安全清理项
1. 旧内核：`sudo apt-get purge linux-image-<旧> linux-headers-<旧>...`（保留当前 + 1 个兜底）
2. rc 残留包：`RC_PKGS=$(dpkg -l | awk '/^rc/{print $2}'); sudo apt-get purge -y $RC_PKGS`
3. 孤儿 snap：`sudo snap remove <sdk>`（snap 会拒绝仍被引用的，安全）
4. journal：`sudo journalctl --vacuum-size=100M`（常可释放数百 MB）
5. apt 缓存：`sudo apt-get clean`
6. 孤儿依赖：`sudo apt-get autoremove --purge -y`

## 陷阱
- ⚠️ apt purge 大软件包（如 wechat 734MB）时，purge+autoremove+clean 链式跑会超过 300s 前台超时 → 用 background=true 或拆成多条命令
- 超时中断会留下 dpkg 半途状态：报错 `E: dpkg 被中断，您必须手工运行 'sudo dpkg --configure -a'`。修复：`sudo dpkg --configure -a`（安全，只补完配置步骤）
- 卸载后验证：`dpkg -l <pkg>` 应为 un（彻底移除）、无 rc 残留、`df` 对比释放量
- 删 GUI 应用前先想好恢复命令并告知用户（微信 Linux：`apt install wechat`）

## 本用户偏好（实测）
- 拒绝整批 `rm -rf ~/.cache/<chrome/pip/pnpm/uv/huggingface/electron>` 式清理。缓存清理必须单独提出经确认，或只清特定小项，绝不与其他操作打包成一条命令
- 汇报格式：结论先行，分"已删 / 保留及具体原因 / 遗留问题"三块；保留理由必须具体（如 docker 服务于 freqtrade compose），不能只说"可能有用"
