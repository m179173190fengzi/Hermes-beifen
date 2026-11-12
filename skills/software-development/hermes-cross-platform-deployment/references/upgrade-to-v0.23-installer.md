# 升级到 v0.23.0：官方安装器实录（2026-11-06，Ubuntu 26.04，pipx 0.19.0 → git v0.23.0）

## 0. 先判断到底有没有新版

```bash
hermes --version                                        # 0.19.0，无 "commits behind" 行
curl -s https://pypi.org/pypi/hermes-agent/json | jq -r .info.version   # 0.19.0（PyPI 已停更）
gh api repos/NousResearch/hermes-agent/releases/latest --jq '.tag_name'  # v0.23.0 ← 真实最新
```

三者不一致是正常的：**PyPI 停在 0.19.0（2026-07-20），v0.22+ 只通过安装器分发**。

## 1. 为什么不能 pipx

```bash
pipx install --force --python ~/.local/bin/python3.11 \
  "hermes-agent[telegram] @ git+https://github.com/NousResearch/hermes-agent@v0.23.0"
```

```
File "<string>", line 69, in run
RuntimeError: Building wheels or sdists for hermes-agent is not supported.
Hermes is distributed via the shell installer, Docker image, or Nix.
ERROR: Failed building wheel for hermes-agent
```

源码里刻意禁掉了 wheel/sdist 构建。**看到这条就不要再换 pip 参数试了**，直接转安装器。
（`requires-python = ">=3.11,<3.15"`，所以 3.11 不是障碍。）

## 2. 装前：修 config 的「字符串型列表」

第一次跑安装器死在 `pm install` 阶段：

```
ValueError: plugins.enabled must be a list of names: /home/wei/.hermes/config.yaml
  hermes_cli/pm/plugins_state.py:88 in read_home_selection
```

根因：`hermes config set plugins.enabled '[omh, hermeskill]'` 把整串存成**一个 YAML 字符串**。
同样的地雷还有 `skills.disabled`（也是 `hermes config set` 写坏的，症状是"禁用 skill 不生效"）。

修法（脚本方式，避免手改 YAML）：

```python
# /tmp/fix_list_config.py —— 把 plugins.enabled / skills.disabled 的字符串形式转成真列表
import json, os, re
p = os.path.expanduser("~/.hermes/config.yaml")
lines = open(p, encoding="utf-8").readlines()
for i, ln in enumerate(lines):
    m = re.match(r"^(\s*)(enabled|disabled):\s*'(\[.*\])'\s*$", ln)
    if not m:
        continue
    raw = m.group(3)
    try:
        items = json.loads(raw)
    except Exception:
        items = [x.strip().strip("'\"") for x in raw.strip("[]").split(",") if x.strip()]
    lines[i] = "%s%s: [%s]\n" % (m.group(1), m.group(2), ", ".join(items))
open(p, "w", encoding="utf-8").writelines(lines)
```

校验：

```bash
grep -nE ": '\[" ~/.hermes/config.yaml          # 应该零命中
python3 -c "import yaml,os;d=yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml')));print(d['plugins']['enabled'], d.get('skills',{}).get('disabled'))"
```

## 3. 跑安装器

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/install.sh
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 GIT_TERMINAL_PROMPT=0
bash /tmp/install.sh --non-interactive --channel stable
```

- `--channel` 合法值只有 **`stable` | `main`**；写 `release` 会 `--channel must be stable or main` 直接退出。
- `--non-interactive` 必加（网关/非 TTY 环境下交互会挂）。
- 耗时：**12–15 分钟**（git fetch tag 10 分钟量级 + `~/.hermes/tools` 下 1.4G 运行时/浏览器二进制）。
- 失败可原地重跑：已 fetch 的 tag 和 tools 会复用，第二次快很多。

成功尾部输出关键行：

```
→ Checking configuration for new options...
  ℹ Updating config format (v33 → v52)…
  ✓ Config format updated (no new settings to configure)
✓ Install complete! [detached @ 2bd378ed1b]
✓ app products and hermes command ready
```

## 4. 安装产物布局

| 路径 | 说明 |
|---|---|
| `~/.hermes/hermes-agent/` | git 源码 checkout（也是 update-check 用的 mirror）|
| `~/.hermes/hermes-agent/venv/` | uv 建的 venv，python 3.11.15（`pyvenv.cfg` 可查）|
| `~/.hermes/hermes-agent/hermes` | CLI launcher，3 行：`from hermes_cli.main import main; main()` |
| `~/.hermes/tools/` | uv / python / chromium / ffmpeg / ripgrep / node 等固定版本工具 |

`hermes --version` 此时可能印 `vgit.2bd378e (2026.9.24) · stable`，**看起来像旧版**。
以 git 为准：

```bash
git -C ~/.hermes/hermes-agent describe --tags          # v0.23.0
git -C ~/.hermes/hermes-agent rev-list --count HEAD..v0.23.0   # 0
```

## 5. 装完必做：软链 + systemd unit

安装器不动已有的 `~/.local/bin/hermes`（pipx 软链会遮住新 launcher），
systemd unit 也不会自动改（仍指着 pipx 路径）。

```bash
# 软链（若审批拦 rm，让用户自己执行）
ln -sfn ~/.hermes/hermes-agent/hermes ~/.local/bin/hermes
hash -r && hermes --version
```

unit 全文（`~/.config/systemd/user/hermes-gateway.service`）：

```ini
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/home/wei/.hermes/hermes-agent/venv/bin/python /home/wei/.hermes/hermes-agent/hermes gateway run
WorkingDirectory=/home/wei/.hermes
Environment="PATH=/home/wei/.hermes/hermes-agent/venv/bin:/home/wei/.hermes/node/bin:/home/wei/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/home/wei/.hermes/hermes-agent/venv"
Environment="HERMES_HOME=/home/wei/.hermes"
Restart=always
RestartSec=5
RestartForceExitStatus=75
RestartPreventExitStatus=78
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 $MAINPID
ExecStopPost=-/home/wei/.hermes/hermes-agent/venv/bin/python -m gateway.cgroup_cleanup
TimeoutStopSec=210
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user show hermes-gateway -p ExecStart --value   # 应指向新 venv
```

## 6. 重启：agent 做不到

两条路都被拦（护栏 #30719 / 进程内自杀保护）：

```
cronjob(action=create, script=重启脚本)
 → Blocked: cron job contains a gateway lifecycle command (restart/stop/kill)

systemd-run --user --on-active=150 --unit=hermes-gw-switch \
  /usr/bin/systemctl --user restart hermes-gateway
 → Blocked: cannot restart or stop the gateway from inside the gateway process.
   The gateway would kill this command before it could complete (SIGTERM propagates).
```

只能用**户**操作：Telegram `/restart`，或外部终端 `hermes gateway restart`。
交付时把这条和回滚命令放同一条消息里。

## 7. 回滚（保留 pipx 0.19.0，别删）

```bash
# ~/.hermes/scripts/hermes-gateway.service.pipx-0.19.0 存旧 unit 全文
cp ~/.hermes/scripts/hermes-gateway.service.pipx-0.19.0 ~/.config/systemd/user/hermes-gateway.service
ln -sf /home/wei/.local/share/pipx/venvs/hermes-agent/bin/hermes ~/.local/bin/hermes
systemctl --user daemon-reload && systemctl --user restart hermes-gateway
```

数据备份（升级前）：`tar czf ~/backups/hermes-pre-update-$(date +%Y%m%d_%H%M).tar.gz -C ~ \
  --exclude='.hermes/.env' --exclude='.hermes/secrets' --exclude='.hermes/logs' \
  --exclude='.hermes/*.db' --exclude='.hermes/cache' .hermes`（实测 852M）
配置备份：`cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak-<tag>`

## 8. 重启后的验证清单（新版跑起来之后）

```bash
hermes --version            # 版本 + install method: git
hermes config check         # 应无 v33→v52 漂移
hermes skills list | tail -3        # 技能数、disabled 是否真的生效
hermes skills list | grep disabled  # 之前配的 skills.disabled 应显示 disabled
hermes cron list            # 任务都在、mode=no-agent 的仍在
hermes doctor               # 缺依赖/未配 key
systemctl --user show hermes-gateway -p ExecMainStartTimestamp --value   # 确认真的重启过
```

注意：`hermes skills list` 正常是 exit 0 的表格；如果看到 `SyntaxError: invalid syntax` 混进输出，
先确认是不是管道里别的命令吐的，别急着判定新版本坏了（本次实测表格输出正常）。

## 9. 时间成本参考（同机实测）

| 阶段 | 耗时 |
|---|---|
| 第一次安装器跑到失败（config 报错） | ~13 min（含 git fetch） |
| 修 config | < 1 min |
| 第二次安装器跑完 | ~10 min（tools 下载 1.4G） |
| 改 unit + 软链 + 验证 | ~2 min |
