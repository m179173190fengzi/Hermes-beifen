---
name: hermes-cross-platform-deployment
description: Deploy and migrate Hermes Agent across Ubuntu/Linux, Windows, and WSL. Fresh install, config transfer, env differences, platform pitfalls.
category: software-development
---

# Hermes Cross-Platform Deployment

## When to Use
- Setting up Hermes on a fresh Ubuntu/Win11/Win7 machine
- Migrating Hermes config from one machine to another
- User reports "No messaging platforms enabled" or "No env user allowlists"
- User copies `.env` or `config.yaml` across OS boundaries and it breaks

## Key Principle
**Do NOT copy raw config.yaml between machines with different Hermes versions or OS.** Always let `hermes setup` generate a fresh config on the target machine, then migrate only the `.env` secrets.

---

## WSL Deployment (Ubuntu on Windows)

WSL (Windows Subsystem for Linux) runs Ubuntu inside Windows. Hermes setup here is similar to native Ubuntu but with WSL-specific pitfalls.

### Install Hermes on WSL
```bash
# 1. Update packages
sudo apt update && sudo apt upgrade -y

# 2. Install pipx (NOT pip3 — Ubuntu 24.04 has PEP 668 external-managed-environment guard)
sudo apt install pipx -y
pipx ensurepath
source ~/.bashrc

# 3. Install Hermes via pipx
pipx install hermes-agent

# 4. Verify
hermes --version
```

⚠️ **CRITICAL: Do NOT use `pip3 install hermes-agent` on Ubuntu 24.04+.** The system Python is externally managed (PEP 668). Only `pipx` works.

### Configure Telegram Bot Token on WSL

**Do NOT use `hermes config set telegram.bot_token`** — it fails with `ValueError: Invalid environment variable name: 'TELEGRAM.BOT_TOKEN'` because the config command tries to write `.env` as `TELEGRAM.BOT_TOKEN` (dots not allowed in env var names).

**Correct approach — two-step:**
```bash
# Step 1: Write token to .env
echo 'TELEGRAM_BOT_TOKEN=887530...' >> ~/.hermes/.env

# Step 2: Add bot_token to config.yaml (manual edit or sed)
echo '  bot_token: "887530..."' >> ~/.hermes/config.yaml
```

Or better, run `hermes setup` and let it handle Telegram config through the wizard.

### Proxy for Telegram Gateway on WSL
WSL cannot reach Telegram API without proxy. If gateway shows `TimedOut`:

**🔥 CRITICAL PITFALL: Use Windows host IP, NOT `127.0.0.1`**

From WSL, `127.0.0.1` refers to the WSL VM, NOT the Windows host. The Windows host is at the WSL gateway IP:
```bash
# Find Windows host IP from within WSL:
ip route | grep default | awk '{print $3}'
# Typical: 172.28.0.1 (varies per WSL version)
```

Correct proxy setup:
```bash
# Replace 172.28.0.1 with IP from `ip route` above
export HTTP_PROXY=http://172.28.0.1:7890
export HTTPS_PROXY=http://172.28.0.1:7890
hermes gateway run --replace
```
The proxy port (7890) matches the Windows host's proxy (FLClash/Clash). If the user's Win proxy is on a different port, adjust accordingly. **The old instruction using `127.0.0.1` will always fail on WSL** — do not use it.

To make proxy persistent across WSL sessions:
```bash
echo 'export HTTP_PROXY=http://172.28.0.1:7890' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://172.28.0.1:7890' >> ~/.bashrc
```

### Provider config on WSL (DashScope/Qwen)

If using DashScope API key with Chinese region account, set base_url to the domestic endpoint:
```bash
hermes config set model.base_url https://dashscope.aliyuncs.com/compatible-mode/v1
```
The default `dashscope` provider auto-selects `dashscope-intl.aliyuncs.com` which rejects Chinese-region keys with HTTP 401.

### When user is on a different machine (WSL/Remote)
**Never describe commands for the user to type.** Always construct the EXACT copy-paste-ready command and tell them to paste it. This is the most common source of user frustration in remote/WSL deployment.

---

## Windows Deployment (Win10/Win11)

### Prerequisites
```powershell
# Install Python (must check "Add Python to PATH")
python --version
pip --version
```

### Install Hermes
```powershell
pip install hermes-agent
```

### Run Setup (Recommended — NOT config copy)
```powershell
hermes setup
```
Select **2 (Full setup)** — not Quick Setup which requires Nous Portal.

### Setup Walkthrough
| Prompt | Answer |
|--------|--------|
| Provider | `17` (DeepSeek) |
| API Key | Paste your key |
| Base URL | Enter (default `https://api.deepseek.com/v1`) |
| Model | Enter (default `deepseek-chat`) |
| Execution mode | Enter (Keep current/local) |
| **Telegram** | Toggle `22` on, then paste Bot Token + Allowed Users |
| Image gen | `9` (Skip) or Enter to accept defaults |
| Vision/Aux | Enter (Auto) |
| Nous Portal login | **n** (No — unless user has subscription) |

### Environment File (`.env`) — Windows Format
Windows Hermes does NOT support `export` prefix. Valid lines:
```
DEEPSEEK_API_KEY=sk-xxx...
TELEGRAM_BOT_TOKEN=xxx...
TELEGRAM_ALLOWED_USERS=12345
TELEGRAM_HOME_CHANNEL=12345
```

Lines that will BREAK parsing:
- `export DEEPSEEK_API_KEY=sk-...` (export prefix)
- `FLClash proxy` (garbage text)
- Empty lines with trailing spaces

### Paths (Windows — Hermes v33+)
```powershell
# Hermes config lives at (NEW — AppData based):
%AppData%\\hermes\\                    # cmd
$env:APPDATA\\hermes\\                 # PowerShell
C:\\Users\\<username>\\AppData\\Local\\hermes\\  # absolute (Win11)

# OLD path (pre-v33 — may still exist from copies):
%USERPROFILE%\\.hermes\\                # cmd
$env:USERPROFILE\\.hermes\\             # PowerShell
```
**Key difference:** Newer Hermes versions (v33+) on Windows store config at `AppData\Local\hermes\`, NOT at `%USERPROFILE%\.hermes\`. If `hermes setup` runs and creates a new config but your old one is in `.hermes`, the old one is ignored.

### Start Gateway
```powershell
hermes gateway run
```
For persistent background: `hermes gateway install` (creates systemd-like service).

---

## Ubuntu → Windows Migration

### DO
1. Note the `.env` values from the source machine
2. On Windows, run `hermes setup` fresh
3. Enter the same API keys during setup
4. Install tools (GMGN, etc.) fresh via npm

### DON'T
1. ❌ Don't copy Ubuntu's `config.yaml` directly — version mismatch causes "No messaging platforms enabled"
2. ❌ Don't copy `.env` directly — Ubuntu file likely has `export` prefix lines Windows can't parse
3. ❌ Don't skip `hermes setup` and hand-write config — wizard handles platform config correctly

### Troubleshooting "No messaging platforms enabled"
1. Did you run `hermes setup` or copy config? → Rerun `hermes setup`
2. Did you toggle Telegram (option 22) during setup? → Must explicitly select it
3. Does `.env` have `export` or garbage lines? → Clean to just key=value pairs
4. Test with: `set GATEWAY_ALLOW_ALL_USERS=true` before `hermes gateway run`

---

## Across-Machine Sync (GitHub Backup Repo)

When running Hermes on multiple machines, skills and memory are **not shared** by default. The recommended sync method:

### Backup Repo Workflow

1. On the **source machine** (e.g. Ubuntu server), the `~/.hermes` directory is a git repo pushed to GitHub:
   ```bash
   # Source machine already set up:
   cd ~/.hermes
   git remote -v
   # → origin  https://github.com/<user>/Hermes-beifen.git
   ```

2. On the **target machine** (e.g. Win11), clone the repo to get all skills:
   ```bash
   cd ~
   git clone https://github.com/<user>/Hermes-beifen.git .hermes
   ```

3. **Do NOT copy config.yaml or .env** between machines — run `hermes setup` fresh on the target. Only copy:
   - `skills/` directory — all custom skills
   - `memories/` directory — persistent user/memory notes

### 🔴 对话不是记忆：要让新机器「学会」的是另外三样

用户说「把对话上传，让 Win 上的 Hermes 也学会你的记忆」时，先纠正这个前提：
**对话不会被注入。** 每轮上下文里常驻的是 `memories/`（MEMORY.md / USER.md）+ 已启用的 skill，
`state.db` 里的历史对话只有被主动检索时才出现。所以：

| 目标 | 真正要搬的 | 搬对话有用吗 |
|---|---|---|
| 让它知道你的规则/偏好 | `memories/*.md` | ❌ 不注入 |
| 让它会干你的活 | `skills/` + `scripts/` | ❌ 不加载 |
| 让它能查旧案例 | `docs/conversations/` 当档案（可选） | ⚠️ 只能当检索源 |

**更有效的替代**：把几十个会话蒸馏成 ~500 字的「用户画像/决策模式」写进 `memories/USER.md`，
比推原文有用得多——它是每轮注入的。

### 导出对话（真的需要时）——state.db → Markdown

`state.db` 会很大（实测 521MB），但**文本总量只有 61MB**，去掉工具输出后能压到个位数 MB：

```python
# 关键过滤：只要 user/assistant 正文，跳过 role=tool 与 system prompt
con.execute("SELECT role, content, timestamp FROM messages "
            "WHERE session_id = ? AND role IN ('user','assistant') ORDER BY timestamp, id")
```

- **`role='tool'` 占体积 80% 且对「学习」无价值**，不过滤就会导出几百 MB 垃圾。
- 单条消息截断（~6000 字符），长代码块/日志折叠。
- 导出时必须走一遍 `redact_keys.py`（同一目录下的 `repo-secret-hygiene` 有现成脚本）——
  会话里用户的 `sk-…` / bot token 是真值，不是占位符。
- 落盘路径建议 `docs/conversations/<date>-<slug>-<id末6位>.md`，一天一个文件名便于定位。

**GitHub 硬限：单文件 100MB，超了点不上去。** 先看体积再 add：

```bash
git diff --cached --name-only -z | xargs -0 -r du -ch | tail -1   # 目标 < 20MB
```

实测：309 个会话 → 6.7MB；连同 skills/scripts/memories 一次提交共 13MB / 840 个文件。

### Sync Considerations

| Item | Sync? | Method |
|:-----|:------|:-------|
| `skills/` | ✅ Copy | Git clone or manual copy |
| `memories/` | ✅ Copy | File copy (JSON files) |
| `config.yaml` | ❌ Don't copy | Run `hermes setup` fresh |
| `.env` | ❌ Don't copy | Re-enter secrets per machine |
| `plugins/` | ⚠️ Selective | Platform-specific plugins should match the target's messaging setup |
| `cron/` | ⚠️ Review | Cron jobs reference machine-specific paths — adjust per machine |
| `scripts/` | ✅ Copy | Self-contained scripts are machine-agnostic |

### 🔴 备份仓库的密钥卫生（真实泄露事故，务必先读）

**绝不把 `~/.hermes/.env` 复制进备份仓库。** 备份脚本里一行
`cp "$HERMES_HOME/.env" "$REPO/config/hermes-env.txt"` 就把 `TELEGRAM_BOT_TOKEN` /
`OPENROUTER_API_KEY` / `DEEPSEEK_API_KEY` / `API_SERVER_KEY` 明文写进 git 历史 ——
而仓库是**公开**的，最早那次提交在 7 月，暴露了两个多月。

1. **备份密钥名，不备份值**：
   ```bash
   grep -oE '^[A-Z_0-9]+=' "$HERMES_HOME/.env" | sed 's/=$/=<REDACTED>/' > "$REPO/config/env-keys-only.txt"
   ```
2. **发现后先止血**（改脚本 + 从仓库移除该文件），再清历史：
   ```bash
   cd <repo>
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch config/hermes-env.txt' --prune-empty -- --all
   git push origin main --force
   ```
   （force-push 会改写远端历史，属破坏性操作 —— 需用户确认；这是备份仓库，工作区数据不会丢。）
3. **公开过 = 已泄露，必须全部轮换** —— 清历史救不回已被爬走的副本：
   Telegram → @BotFather `/revoke`（换完写回 `~/.hermes/.env` 并重启网关）；
   OpenRouter / DeepSeek 后台重新生成 key；`API_SERVER_KEY` 直接改。**顺带把仓库改成 Private。**

**查仓库可见性（30 秒，别猜）**：
```bash
curl -sI --max-time 20 "https://github.com/<user>/<repo>" | head -1
# HTTP/2 200 → 未登录也能打开 = 公开 ⚠️        HTTP/2 404 → 私有
```
（`api.github.com/repos/...` 在共享出口 IP 下常直接 `403 rate limit exceeded`，不如看网页状态码。）

**定期核对仓库里到底有什么**：`find <repo> -type f -not -path '*/.git/*'`
再检查是否存在 `env` / `token` / `secret` 类文件；把「绝不备份 .env」写进脚本注释，
防止下次"顺手加回来"。

⚠️ **备份源路径要核对（单复数陷阱）**：真实记忆在 `~/.hermes/memories/`（复数），
而 `~/.hermes/memory/`（单数）是个 7 月的死目录。备份脚本指向错的目录 → 两个月都在复制同一个
不再变化的旧文件，git 因此一直没有新提交，任务却天天报 ok。排查法见 `cron-job-diagnostics`（"假成功"一节），
备份任务的投递可靠性（脚本自己发消息 + 重试）也在那份技能里。

### Cron Backup Auto-Sync

The source machine should push regularly via cron:
```bash
cd ~/.hermes && git add -A && git commit -m "auto backup $(date +%F_%H%M)" && git push
```
The target machine pulls when needed. This keeps skills/memory in sync without manual file transfer.

## Post-Deployment: Infrastructure Health Monitoring

After deploying Hermes, critical infrastructure can fail silently (TG token revoked, gateway crash, API key expiry). Set up no_agent watchdog scripts for proactive alerts.

### Telegram Bot Token Watchdog

The most common silent failure: the TG bot token is revoked/reset via @BotFather. The gateway hangs on `Connecting to Telegram (attempt 1/8)…` and all messages are lost.

**Solution — periodic no_agent cron check:**

Script at `~/.hermes/scripts/tg_token_check.sh`:
```bash
#!/bin/bash
# Checks TG token validity via getMe API
TOKEN=$(grep '^TELEGRAM_BOT_TOKEN='*** "$HOME/.hermes/.env" | cut -d= -f2-)
RESULT=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "https://api.telegram.org/bot${TOKEN}/getMe")
if [ "$RESULT" = "200" ]; then
  exit 0  # SILENT
elif [ "$RESULT" = "401" ]; then
  echo "🚨 TG Bot Token 已失效！HTTP 401 Unauthorized"
  exit 1  # alert
fi
exit 0  # network error → silent (avoid false alarms)
```

Cron setup (no_agent mode — no LLM tokens consumed):
```bash
cronjob action=create \
  name='TG Token 有效性检查' \
  schedule='0 10,16,22 * * *' \
  script='tg_token_check.sh' \
  no_agent=true
```

**Behavior:**
- ✅ Token valid → exits 0 → no output → no delivery → silent
- 🚨 Token invalid (401) → non-zero exit + message → delivered alert
- 🌐 Network flaky → exits 0 → silent (don't bother user with transient issues)

### Extending the Watchdog Pattern

The same no_agent pattern can monitor:
- **Gateway health**: Check `systemctl --user is-active hermes-gateway`
- **API key validity**: Ping the provider API endpoint
- **Disk space**: Alert on high usage
- **Cron job health**: Verify last run was successful via `cronjob action=list`

### Watchdog Requirements

| Element | Detail |
|:--------|:-------|
| Script location | `~/.hermes/scripts/<name>.sh` (use just the filename in cron) |
| Success behavior | Exit 0, produce no stdout → [SILENT] |
| Failure behavior | Non-zero exit + stdout message → delivered as alert |
| Transient tolerance | Network errors should exit 0 — only alert on definitive failures |
| Cron mode | `no_agent=true` — pure script, zero LLM cost |

## Dual-Bot Instance (Same Account, Two Machines)

You can run two Hermes instances on different machines, each with a different Telegram bot, sharing the same DeepSeek API key:

| Machine | Bot | Telegram Token | Purpose |
|:--------|:----|:---------------|:--------|
| Win11 | Bot A | Token A (original) | Primary — full skills/memory |
| Ubuntu/Linux | Bot B | Token B (from BotFather) | Secondary — independent instance |

### Setup Pattern
1. On **Machine 1** (primary): `hermes setup` with existing bot token
2. On **Machine 2** (secondary): `hermes setup` with new bot token
3. Both share the same `.env` values for `DEEPSEEK_API_KEY` and `TELEGRAM_ALLOWED_USERS`
4. Each has its own config.yaml (run `hermes setup` fresh per machine)

### Notes
- Memory/skills are NOT shared between instances
- Same DeepSeek API key works fine on both simultaneously
- Each bot has independent Telegram reactions

### gmgn-cli update checks (npm, NOT PyPI)
`gmgn-cli` is a **node** package (`#!/usr/bin/env node`, installed to `~/.local/lib/node_modules/gmgn-cli`). It does NOT exist on PyPI — `pip index versions gmgn-cli` / `pipx list | grep gmgn` / `pip show gmgn-cli` all come up empty. That's expected, not a broken install. Verify/update with npm:
```bash
which gmgn-cli                    # → ~/.local/bin/gmgn-cli (symlink into node_modules)
gmgn-cli --version                # local version, e.g. 1.5.6
npm view gmgn-cli version         # latest on registry
npm update -g gmgn-cli            # update
```
Quick identification trick: `head -1 $(which gmgn-cli)` → `#!/usr/bin/env node` means it's npm-managed; use npm for updates, not pipx/pip.

### Ubuntu
```bash
npm install -g gmgn-cli
```

### Windows
```powershell
# First install Node.js from nodejs.org (LTS)
npm install -g gmgn-cli
```
If `EACCES` error, configure prefix:
```powershell
mkdir ~\.npm-global
npm config set prefix "$HOME\.npm-global"
```

---

## Pitfalls
- **PowerShell vs CMD**: `%USERPROFILE%` works in CMD but NOT PowerShell. Use `$env:USERPROFILE` in PowerShell.
- **`.env` parsing**: Windows Hermes silently skips invalid lines. Ubuntu Hermes is more tolerant.
- **Nous Portal login**: Setup defaults to Quick Setup which requires Nous Portal. Always pick Full Setup (2).
- **Old config files**: Config format changes between versions. Delete old config.yaml and regenerate.
- **xurl**: Requires X Developer Portal app registration — user must create the app.

### 🔴 PowerShell `echo >>` corrupts YAML
**Never** use `echo text >> config.yaml` in PowerShell to append lines to YAML files. PowerShell's `echo` / `Write-Output` introduces **UTF-8 BOM and null bytes** (`#x0000` control characters) that YAML parsers reject with:
```
unacceptable character #x0000: control characters are not allowed
```
**Fix:** Always use `notepad config.yaml` for editing, or delete the file and regenerate with `hermes setup`.

To recover from a corrupted config.yaml:

**Option A (preferred — preserves most settings):** Use Python to fix specific sections. The config file is mostly intact — only the `echo`-appended lines are corrupted. Write a fix script to `/tmp/fix_config.py` and run:
```bash
python3 /tmp/fix_config.py
```
See the exact script at `references/telegram-setup-troubleshooting.md`.

**Option B (nuclear):** Delete and regenerate:
```powershell
del C:\\...\\config.yaml
hermes setup
```

### 🔴 WSL proxy IP: NOT `127.0.0.1`

From WSL, `127.0.0.1` refers to the WSL VM, NOT the Windows host. Always use the WSL gateway IP:
```bash
ip route | grep default | awk '{print $3}'   # e.g. 172.28.0.1
```
Proxy setup with wrong IP causes persistent `TimedOut` on Telegram connect.

### 🔴 `hermes config get` vs `hermes config show` — version-dependent
Newer Hermes versions (v33+) support `hermes config get <key>` to read a single value. **Older versions (pre-v33) reject `get`** with `invalid choice: 'get'` — only `hermes config show` works. When on Windows, never assume `hermes config get` exists:
```powershell
# Works everywhere:
hermes config show     # full dump

# New only — old will fail:
hermes config get model.provider    # → error on Win
```
Workaround: parse `hermes config show` output or read config.yaml directly.

### 🔴 Config path: `%APPDATA%` vs `%USERPROFILE%`
Hermes v33+ on Windows stores config at `%APPDATA%\\hermes\\` (usually `C:\\Users\\<user>\\AppData\\Local\\hermes\\`). The old path at `%USERPROFILE%\\.hermes\\` is IGNORED. When troubleshooting "No messaging platforms enabled":
1. Run `hermes config` to see which config file is ACTIVE
2. Check `%APPDATA%\\hermes\\` for the real config
3. If the user copied files to `.hermes\\`, those aren't being read

### 🔴 Gateway setup: toggle FIRST, token SECOND
When running `hermes setup gateway`, the **wizard order is invisible** to users:
1. **First screen**: `Toggle # (or Enter to confirm):` — you must enter the **option number** (e.g. `22` for Telegram) to toggle it on
2. **Second screen**: THEN it asks for bot token
3. **Third screen**: THEN it asks for allowed users
4. **Final**: Enter to confirm

Common mistake: User types the bot token at the first prompt (option toggle screen), which fails with "No platforms selected". The fix: re-run `hermes setup gateway` and enter the toggle number first.

### 🔴 Config path mismatch after fresh install
On Win11 with Hermes v33+, `hermes setup` creates config at `AppData\Local\hermes\config.yaml`. If the user earlier created `%USERPROFILE%\.hermes\config.yaml` (manual copy from Ubuntu), Hermes will use the **AppData one** and the `.hermes\` copy is **ignored**. Always check which config is actually loaded when debugging:
```
hermes config  # shows which config file is active
```

### 🔴 Auto QR-Code Telegram bot creation
`hermes setup gateway` option **1 (Automatic)** generates a QR code / link. The user scans with their phone → Telegram opens → taps "Create Bot". This works without any BotFather interaction. If the user already has a bot token, pick **2 (Manual)** instead.

### 🔴 Config repair when `patch`/`write_file` are blocked
If the Hermes config file is protected and `patch`/`write_file` tools are denied, use Python:
1. Write a fix script to `/tmp/fix_config.py`
2. Run `python3 /tmp/fix_config.py`
See `references/telegram-setup-troubleshooting.md` for the exact script and verification.

## Updating Hermes & the update-check git mirror

### 🔴 v0.22+：pipx/PyPI 路径已废，只能官方安装器（2026-11 实测装到 v0.23.0）

`pipx install --force "hermes-agent[telegram] @ git+https://github.com/NousResearch/hermes-agent@v0.23.0"` 会直接失败：

```
RuntimeError: Building wheels or sdists for hermes-agent is not supported.
Hermes is distributed via the shell installer, Docker image, or Nix.
```

PyPI 也停在 0.19.0（2026-07-20），之后的版本只发 GitHub release。**别再折腾 pipx / 别再 rebuild venv 追新版**，走安装器：

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh -o /tmp/install.sh
bash /tmp/install.sh --non-interactive --channel stable   # --channel 只有 stable|main，写 release 会报错退出
```

流程与耗时：git fetch tag（代理下 10+ 分钟）→ 装 uv + python3.11 到 `~/.hermes/tools/`（约 1.4G，含 chromium/ffmpeg）→
建 `~/.hermes/hermes-agent/venv` → 自动迁移 config（实测 v33 → v52）。

**跑之前必须先修 config 里的「字符串型列表」**，否则会崩在 pm install 阶段：

```
ValueError: plugins.enabled must be a list of names: ~/.hermes/config.yaml
```

`hermes config set` 会把 `'[a, b]'` 存成**一个 YAML 字符串**。装前自检：

```bash
grep -nE ": '\[" ~/.hermes/config.yaml     # 命中即是地雷（plugins.enabled / skills.disabled 都中过）
```

**装完三件必做**，否则网关还在跑旧代码：

| 项 | 旧值 → 新值 |
|---|---|
| `~/.local/bin/hermes` | pipx 软链 → `~/.hermes/hermes-agent/hermes`（不改则 `hermes --version` 永远显示旧版）|
| systemd unit `ExecStart` | `.../pipx/venvs/hermes-agent/bin/python -m hermes_cli.main gateway run` → `~/.hermes/hermes-agent/venv/bin/python ~/.hermes/hermes-agent/hermes gateway run` |
| 同 unit 的 `ExecStopPost` / `PATH` / `VIRTUAL_ENV` | 全部改指新 venv，然后 `systemctl --user daemon-reload` |

**版本号显示陷阱**：新版 `hermes --version` 可能印成 `vgit.<sha> (2026.9.24)`，看着像旧版。以
`git -C ~/.hermes/hermes-agent describe --tags`（应为 `v0.23.0`）+ `git rev-list --count HEAD..v0.23.0`（应为 0）为准。

**`skills.disabled` 是同一个坑，且后果更隐蔽**：`hermes config set skills.disabled '["a","b"]'` 存成**字符串**后
command 不报错、`hermes skills list` 也照常输出 —— 那几项仍然 enabled，你会以为「已经关了」。值必须是真列表：

```bash
grep -nE ": '\[" ~/.hermes/config.yaml     # 命中 = 字符串型列表（plugins.enabled / skills.disabled 都中过）
python3 -c "import yaml,os;d=yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml')));print(d['plugins']['enabled'], d['skills']['disabled'])"
```
改成 `disabled: [a, b]`（或 `enabled: [omh, hermeskill]`，不帶引號）后才会生效。
**通用结论：`hermes config set` 写列表时存成字符串，所以凡是 list 型 key 都要回读验证。**

**升级后确认网关真的换了运行时**：新版可能自己用 `~/.hermes/tools/python-3.14.9/.../python3` 拉起 gateway
（即使 unit 里写的是 venv 的 3.11）—— 两者都能跑，但要知道在跑哪个：

```bash
ps -o pid,etime,cmd -p $(systemctl --user show hermes-gateway -p MainPID --value) | tail -2
```

`~/.local/bin/hermes` 若软链到 `~/.hermes/hermes-agent/hermes`（`#!/usr/bin/env python3`），CLI 用的是 PATH 里的
python，可能与网关不同；要一致就换成显式 wrapper：
`exec ~/.hermes/hermes-agent/venv/bin/python ~/.hermes/hermes-agent/hermes "$@"`。

**两个别误判的收尾项：** `hermes doctor` 可能跑过 2 分钟（exit 124 只是超时，不是失败，放后台跑）；
技能总数会变（内置技能随版本增删，实测 227 → 242），不是丢失。

完整实录（回滚脚本、验证清单、时间成本）见 `references/upgrade-to-v0.23-installer.md`。

### 🔴 Python version pin silently blocks upgrades (pipx says "already latest" — but PyPI has newer)

`pipx upgrade hermes-agent` can report **"already at latest version X.Y.Z" while PyPI actually has a much newer release**. Root cause: hermes-agent **0.16.0+ requires Python `>=3.11,<3.14`**. If the pipx venv was built on Python 3.14 (e.g. system default on Ubuntu 26.04), pip **silently skips** every newer release and resolves to the newest installable version — so pipx reports that as "latest" with no error. Same with `pipx install --force` (reuses the existing venv and its interpreter).

**Diagnose** (query PyPI directly, and force pip to reveal the Requires-Python rejection):
```bash
# 1. What's actually on PyPI? (use proxy if needed)
HTTPS_PROXY=http://127.0.0.1:7890 curl -s https://pypi.org/pypi/hermes-agent/json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['info']['version'])"

# 2. Force-install the target version → shows the real blocker
HTTPS_PROXY=http://127.0.0.1:7890 pipx runpip hermes-agent install --upgrade --force-reinstall --no-cache-dir 'hermes-agent[telegram]==<latest>' 
# → "ERROR: Ignored the following versions that require a different python version: 0.16.0 Requires-Python >=3.11,<3.14 ..."
```

**Fix = rebuild the venv on a compatible interpreter** (3.11/3.12/3.13; check `ls /usr/bin/python3* ~/.local/bin/python3*` for available ones):
```bash
pipx uninstall hermes-agent
HTTPS_PROXY=http://127.0.0.1:7890 pipx install --python /home/wei/.local/bin/python3.11 'hermes-agent[telegram]'
```
⚠️ Keep the `[telegram]` extra — plain `pipx install hermes-agent` drops the messaging platform deps.

**🔴 CRITICAL: upgrading while the gateway is running breaks the live session.** `pipx uninstall` deletes the venv the *running* gateway process is executing from. The old process keeps running but its module files are gone → tools that resolve paths relative to the session cwd start failing. The session cwd points into the deleted site-packages.

**Diagnose (don't assume generic tool outage):** compare the traceback path vs the venv on disk. Traceback shows the OLD python version (e.g. `.../venvs/hermes-agent/lib/python3.14/site-packages/tools/terminal_tool.py`) while `search_files` on the pipx venv shows the NEW one (`lib/python3.11/site-packages/hermes_agent-0.19.0.dist-info`). Version mismatch = stale process.

**Tool survival matrix in this state:**
- ✅ `read_file` / `search_files` work (absolute paths, no cwd dependency)
- ✅ `cronjob` tool works — the cron scheduler runs separately and loads the new venv
- ⚠️ `write_file` may return `FileNotFoundError` yet ACTUALLY write the file — always verify with `read_file` before assuming failure
- ❌ `terminal` / `execute_code` fail (`FileNotFoundError: [Errno 2] ... _get_env_config`)
- ❌ `browser_navigate` fails (`ENOENT: no such file or directory, uv_cwd` — npm subprocess can't getcwd)

**⚠️ Self-heal via cron is now BLOCKED（2026-11 实测）:** 早期做法是排一个 one-shot `no_agent` cron 跑
`systemctl --user restart hermes-gateway`，**这条路径已被护栏 #30719 封死**：

```
cronjob → "Blocked: cron job contains a gateway lifecycle command (restart/stop/kill) ...
           Run `hermes gateway restart` from a shell outside the running gateway instead."
systemd-run --user --on-active=150 systemctl --user restart hermes-gateway
        → "Blocked: cannot restart or stop the gateway from inside the gateway process"
```

**结论：agent 无法自行重启网关。** 唯一可靠路径是让用户操作 —— Telegram 发 `/restart`，或外部终端跑
`hermes gateway restart`。交付话术：先完成安装/配置并验证 `hermes --version`，再明确说
「已装好、差最后一步，请发 `/restart`」，**同一条消息里给出回滚命令**，这样他按之前就有退路。
（历史记录：曾有一次 one-shot job 到点没落地，最后是用户 `/restart` 救的 —— 别把恢复归功于自愈。）
```bash
systemctl --user show hermes-gateway -p ExecMainStartTimestamp   # actual (re)start time
cronjob action=list                                              # did the one-shot job run? is it gone from the list?
```
If `ExecMainStartTimestamp` does not line up with the scheduled fire time, say the cron restart didn't land and name what actually recovered it — do not attribute the recovery to the self-heal. Also note the session that dies on restart may not deliver a final message, so announce the plan *before* the job fires.

**Fallback: restart the gateway manually** — user sends `/restart` in Telegram, or `systemctl --user restart hermes-gateway`. The new process loads the new venv; config/sessions/memory are untouched. Verify with `hermes --version` after restart. Offer the cron self-heal and the `/restart` fallback **in the same message**, so a self-heal that doesn't fire still leaves the user unblocked.

**While tools are broken, `python3 -c` inline commands may also be blocked by command approval.** To read the full prompt of a cron job (e.g. before updating it with `cronjob action=update` — the `prompt_preview` from `list` is truncated), extract from jobs.json with `jq` instead of python:
```bash
jq -r '.jobs[] | select(.id=="<job_id>") | .prompt' ~/.hermes/cron/jobs.json > /tmp/prompt.txt
# then read_file /tmp/prompt.txt for the full text
```

**Also:** `hermes update` is interactive (prompts/confirmation) and will hang in a gateway/non-TTY context — use pipx directly. Full transcript: `references/upgrade-python-version-pin.md`.

### `hermes --version` says "N commits behind" but pipx says already latest — the check is the git mirror, not PyPI

On a pipx install, `hermes --version` prints `Update available: N commits behind — run 'pip install --upgrade hermes-agent'` while `pipx upgrade hermes-agent` / `pipx runpip hermes-agent install --upgrade hermes-agent` report "already at latest version". **This is not a lie and not a PyPI issue** — the update check (`hermes_cli/banner.py::check_for_updates`) resolves in this order:

1. `HERMES_REVISION` env set → compare to upstream via git (nix builds)
2. `.git` next to the running code (pipx site-packages has none)
3. fallback: `~/.hermes/hermes-agent/.git` → **count commits behind `origin/main` via git rev-list**
4. no git checkout anywhere → `check_via_pypi()`

So on a pipx install, the message reflects the **mirror checkout** at `~/.hermes/hermes-agent/`, not the installed package. **Fix = sync the mirror, not the package.** `git main` is also a dev version ahead of the PyPI release (e.g. main 0.20.1 vs PyPI 0.15.2) — "commits behind" does NOT mean a new release exists.

### Mirror sync pitfalls (shallow clone)

The mirror is often a shallow clone. Syncing it has traps, all hit in the field:

- `git pull`/`git fetch` **hangs with no output** behind the FLClash proxy → prefix with `HTTPS_PROXY=http://127.0.0.1:7890` (curl direct also 200, but git stalls).
- git may hang waiting for credentials → always use `GIT_TERMINAL_PROMPT=0`.
- `git merge origin/main` fails with `fatal: 拒绝合并无关的历史` (refusing to merge unrelated histories) — shallow clone + no common ancestor.
- `git fetch --unshallow` can silently do nothing; **deleting `.git/shallow` corrupts the repo** (unresolved deltas, `Could not read <parent>`).
- `git reset --hard` / destructive recovery commands may be blocked by command-approval; prefer non-destructive steps below.

### Recovery recipe (corrupted mirror)

```bash
cd ~/.hermes/hermes-agent
mv .git .git.broken                      # non-destructive backup (don't rm)
git init -b main
git remote add origin https://github.com/NousResearch/hermes-agent.git
# proxy + no-prompt fetch; if full fetch times out, shallow-clone fresh and copy .git:
HTTPS_PROXY=http://127.0.0.1:7890 GIT_TERMINAL_PROMPT=0 git clone --depth 1 \
  https://github.com/NousResearch/hermes-agent.git /tmp/hermes-agent-fresh
cp -r /tmp/hermes-agent-fresh/.git .git.fresh && mv .git .git.empty && mv .git.fresh .git
git checkout -f main && git status -sb     # should show up-to-date with origin/main
```

The update check is cached 6h at `~/.hermes/.update_check` — `rm -f ~/.hermes/.update_check` then re-run `hermes --version` to verify ("Up to date"). Verified end state: `hermes --version` reports `Up to date`, running code untouched (still the pipx venv). Full transcript: `references/update-check-git-mirror.md`.

## Post-Upgrade Integrity Self-Check ("自查系统丢失部分")

After any pipx venv rebuild / version upgrade, verify nothing got lost. Run all of these in one batch — each covers a different "lost part" class:

```bash
hermes --version          # version + install method (pipx venv path reveals the python version)
hermes status --all       # env, API keys, auth providers, terminal backend, messaging platforms
hermes doctor             # missing deps, toolsets without keys, config issues, "Reinstall entry point" hint
hermes config check       # config version drift: "Config version N → M (update available)"
hermes skills list        # skill counts: "206 enabled, 0 disabled" — confirms skills survived
hermes plugins list       # bundled plugins show "not enabled" = normal; missing dir plugins = problem
cronjob action=list       # all scheduled jobs intact (6 jobs, 5 enabled = expected on this setup)
hermes gateway status     # plus: systemctl --user show hermes-gateway -p NRestarts --value
```

**Known post-rebuild loss pattern:** rebuilding the venv with only `[telegram]` extra drops other platform deps. Symptom in gateway log: `API Server: aiohttp not installed` / `No adapter available for api_server`. Fix: `pipx inject hermes-agent aiohttp` (or reinstall with `[all]`) then restart gateway. `hermes doctor` flags this as "Reinstall entry point ... pip install -e '.[all]'".

**Config version drift:** `hermes config check` reporting `Config version 24 → 33` is expected after a major upgrade — fix with `hermes config migrate`.

**Crash-loop check:** if gateway restarts continuously, check `NRestarts` counter (100+ = loop) and `journalctl --user -u hermes-gateway | grep "already running"` — an orphan manual `gateway run --replace` process holding the lock is the usual cause (see gateway-troubleshooting skill, "Gateway Crash Loop — Orphan Process Holds the Lock").

## System & Toolchain Update Sweep ("更新一下自己 + 系统应用")

When asked to update Hermes *and* the system, resist blind upgrading — establish what actually needs
updating, then work the layers in order. Verified order that avoids wasted work:

### 1. Hermes itself — check before touching pipx

```bash
hermes --version    # "already latest" if no 'Update available / N commits behind' line → the git mirror is in sync too
HTTPS_PROXY=http://127.0.0.1:7890 curl -s https://pypi.org/pypi/hermes-agent/json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['info']['version'], d['info'].requires_python)"
```
Installed == PyPI latest **and** no "commits behind" line ⇒ nothing to do. Report that as the result;
do not `pipx uninstall/install` for its own sake (that path is what breaks the running gateway, see
the upgrade section above).

### 2. Toolchain sweep (npm + pipx) — fast, safe while the gateway runs

```bash
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
npm list -g --depth=0                       # inventory, then update by name
npm update -g gmgn-cli @okx_ai/okx-trade-cli xhs-cli opencli mcporter
pipx upgrade yt-dlp                          # repeat per package
```
- **Name packages explicitly — never `pipx upgrade-all`.** A blanket upgrade pulls in `hermes-agent`,
  which is the venv-rebuild-while-running trap above.
- `pipx upgrade <pkg>` on an already-current package prints "already at latest version" — keep those
  lines in the summary, they're the evidence the sweep was complete.
- Behind the proxy npm/pipx are slow (measured: "changed 4 packages in 1m") — run the sweep in the
  background with `notify_on_complete=true` rather than blocking.

### 3. OS packages (apt) — env proxy vars do NOT work, apt needs its own flags

`sudo apt update` ignores `HTTPS_PROXY`/`HTTP_PROXY` entirely. Bare apt behind the FLClash proxy fails
with **`暂时不能解析域名 "archive.ubuntu.com"`** (DNS never reaches the proxy) and then
`full-upgrade` hangs for **6+ minutes** retrying downloads with no output. Pass the proxy via
`Acquire` options instead:

```bash
sudo -n true && echo "免密sudo可用"          # check first — otherwise it blocks on a password prompt
sudo apt -o Acquire::http::Proxy="http://127.0.0.1:7890" \
         -o Acquire::https::Proxy="http://127.0.0.1:7890" update
sudo apt -o Acquire::http::Proxy="http://127.0.0.1:7890" \
         -o Acquire::https::Proxy="http://127.0.0.1:7890" \
         full-upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--confold"
```
- Even then, **per-host results differ**: `archive.ubuntu.com` fetched fine through the proxy while
  `security.ubuntu.com` returned `502 Bad Gateway [IP: 127.0.0.1 7890]` — a proxy-side failure, not a
  local misconfiguration. Signatures for the missing index then fail ("仓库 … 的签名不再生效").
  Retrying a second time moved one more index from error to `命中` — retry once before concluding.
- If a source stays 502, the durable fix is switching to a domestic mirror (mirrors.aliyun.com /
  mirrors.tuna.tsinghua.edu.cn) in `/etc/apt/sources.list.d/` — **ask the user first**: it's a
  persistent system-config change, and mirror choice is region/preference-dependent.
- `full-upgrade` and `autoremove` are slow and interactive-prone: background + `notify_on_complete`,
  and always pair `DEBIAN_FRONTEND=noninteractive` with `--force-confdef --force-confold` so a config
  prompt can't wedge the run.
- Upgrades that need approval but time out are **not** consent — report the exact command for the user
  to run/approve instead of retrying.

## Plugin & Skill Installation (community plugins)

Installing third-party Hermes ecosystem plugins (e.g. 42-evey/hermes-plugins, theopitori/hermeskill, witt3rd/oh-my-hermes) has several traps:

### hermes CLI network operations stall behind proxy
`hermes skills install`, `hermes skills search`, `hermes skills tap add` hit the network. Behind a proxy, `hermes skills install <url>` may hang or time out with no output. Workarounds in order of reliability:
1. **git clone the repo directly** (with `HTTPS_PROXY` env set), then manually copy the skill dir: `cp -r repo/skills/<name> ~/.hermes/skills/`. This always works — the local skill appears in `hermes skills list` as `local` and is enabled.
2. `hermes skills install` does NOT accept local filesystem paths (error: "Could not fetch ... from any source") — don't try.
3. `hermes skills install` takes exactly ONE identifier; multiple args → `unrecognized arguments` error. Loop one-by-one if you must use it.
4. After `hermes skills tap add owner/repo`, `hermes skills install <skill>` can still hang — prefer the manual copy path.

### pip-installed (entry-point) plugins vs directory plugins
Two kinds of Hermes plugins:
- **Directory plugins** (`~/.hermes/plugins/<name>/` with `plugin.yaml`) — managed via `hermes plugins enable/disable/list`. Install by copying the repo's plugin folder there.
- **Entry-point plugins** (pip-installed, e.g. `pipx runpip hermes-agent install hermeskill-hermes`) — auto-discovered via `hermes_agent.plugins` entry-point group, but **NOT shown/managed by `hermes plugins list`**. Enable them ONLY via config key:
  ```
  hermes config set plugins.enabled '[omh, hermeskill]'
  ```
  ⚠️ **PITFALL: `hermes plugins enable <name>` OVERWRITES the whole `plugins.enabled` list** (it set `[omh]` and silently dropped `hermeskill`). After enabling any directory plugin, re-set the full list with `hermes config set plugins.enabled '[a, b, c]'` to restore entry-point plugins.

### Dependency installs for plugins
Community plugin suites often need extra packages in the hermes venv:
```bash
pipx runpip hermes-agent install paho-mqtt pyyaml
```
Check plugin `__init__.py` imports first (e.g. evey-mqtt needs `paho`, evey-sandbox needs `yaml`).

### hermeskill specifics
- Install: `pipx install hermeskill` (CLI) + `pipx runpip hermes-agent install hermeskill-hermes` (plugin into hermes venv).
- `hermeskill enable-hermes` fails with "Hermes Agent isn't importable from this environment" when run from a separate pipx venv — the CLI can't see hermes. Fix: just set `plugins.enabled` via `hermes config set` manually; the plugin is entry-point discovered.
- No API key → runs local-only (in-process runaway kill + death cert saved to `~/.hermeskill/kills/`), which is fine.
- `hermeskill doctor` doesn't exist (README is ahead of the CLI); use `hermeskill --help` to see actual commands.
