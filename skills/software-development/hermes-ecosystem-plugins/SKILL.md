---
name: hermes-ecosystem-plugins
description: 安装和管理第三方 Hermes 生态插件/技能（GitHub 仓库 → ~/.hermes/plugins 或 ~/.hermes/skills）。触发：用户发 Hermes 生态 GitHub 链接让安装（如 GitTrend 推荐帖）、hermes plugins/skills 装东西、装 evey 套件/skill-factory/hermeskill/oh-my-hermes/youtube-skills/gzh-design 这类社区项目。含三种安装路径（目录插件/entry-point插件/skill）、代理环境下的坑、验证步骤。
---

# Hermes 生态插件/技能安装

## 触发场景
- 用户转发 Hermes 生态 GitHub 链接（42-evey/hermes-plugins、Romanescu11/hermes-skill-factory、theopitori/hermeskill、ZeroPointRepo/youtube-skills、witt3rd/oh-my-hermes、isjiamu/gzh-design-skill、limin112/min-skill 等）
- 用户说"装这个/学习这个技能/先装这五个"
- 任何 hermes plugins / hermes skills 安装操作

## 工作流

### 1. Clone 到统一目录（走代理）
```bash
mkdir -p ~/hermes-ecosystem && cd ~/hermes-ecosystem
export https_proxy=http://127.0.0.1:7890 http_proxy=http://127.0.0.1:7890
git clone --depth 1 https://github.com/<owner>/<repo>.git <name>
```

### 2. 读 README + SKILL.md 判断安装方式
- `skills/` 子目录含 SKILL.md → 技能（skill）
- 插件目录含 `__init__.py` + `plugin.yaml` → 目录插件（git plugin）
- pyproject 声明 `hermes_agent.plugins` entry-point → entry-point 插件（pip 装，靠 config 启用）

### 3. 三种安装路径

**A. Skill（最可靠=手动复制，CLI 网络常卡）**
```bash
mkdir -p ~/.hermes/skills/<name>
cp -r <repo>/<skill-dir>/* ~/.hermes/skills/<name>/   # 必须带 references/ scripts/ assets/ 完整目录，只拷 SKILL.md 会断链
```
> ⚠️ `hermes skills install` 一次只接受**一个** identifier，多参数直接报 `unrecognized arguments`；且代理下经常超时卡死。本地已有 clone 时手动 cp 最快。

**B. 目录插件**
```bash
cp -r <repo>/<plugin-dir> ~/.hermes/plugins/
hermes plugins enable <name>   # 对 git/目录插件生效
```

**C. Entry-point 插件（pip 装进 hermes venv）**
```bash
pipx runpip hermes-agent install <pkg>          # 装进 hermes 的 venv（如 hermeskill-hermes）
hermes config set plugins.enabled '[omh, hermeskill]'   # entry-point 插件靠 config 启用
```

### 4. 验证
```bash
hermes skills list | grep <name>    # 应显示 enabled
hermes plugins list                 # 目录插件显示 source=user
grep -A3 "plugins:" ~/.hermes/config.yaml
```

## 坑清单（全部实测踩过）

1. **`hermes plugins enable X` 会覆盖 `plugins.enabled` 列表**——启用 omh 时把已启用的 hermeskill 顶掉了。启用任何插件后必须重设完整列表：
   `hermes config set plugins.enabled '[omh, hermeskill]'`
2. **config.yaml 是受保护文件**——write_file/patch 直接拒写（"protected system/credential file"），必须用 `hermes config set`。
3. **entry-point 插件不在 `hermes plugins list` 里**——`hermes plugins enable` 只管 git/目录安装的插件；pip 装的（hermeskill-hermes）自动被发现，靠 `plugins.enabled` config key 启用，且 config 里带引号 `'[omh, hermeskill]'` 是正常的。
4. **hermeskill 的 CLI 是独立 pipx 环境**——`hermeskill enable-hermes` 报 "Hermes Agent isn't importable" 是因为 CLI 看不到 hermes venv；正确做法：`pipx runpip hermes-agent install hermeskill-hermes` + config 启用，CLI 工具留作 doctor/logs/kill 查看。
5. **evey-* 套件**：23 个插件需连 `evey_utils.py` 一起复制（35 个文件），依赖 paho-mqtt（`pipx runpip hermes-agent install paho-mqtt`）。默认全 not enabled，按需开——这套是给自主运行 Agent 设计的，全开会和现有 cron/监控互相抢。
6. **技能复制必须带 references/scripts/assets**——gzh-design 的校验/预览脚本在 scripts/，组件库在 references/，只拷 SKILL.md 会全断。
7. **插件生效时机**：`hermes plugins enable` 提示 "Takes effect on next session"；技能则立即可见。

## 社区帖只给了裸插件名 → 先解析成 owner/repo，再判断能不能装

社区帖常直接写「`hermes plugins install <name>`」（实测：手机控制插件 **phone-harness**）。裸名必失败：

```
Error: Invalid plugin identifier: 'phone-harness'. Use a Git URL or 'owner/repo'
shorthand (optionally with a subdirectory: 'owner/repo/path/to/plugin').
```

**别猜仓库名**（实测 5 个猜测全 404，白烧一轮），直接搜：

```bash
curl -s --max-time 25 "https://api.github.com/search/repositories?q=<name>" \
  | jq -r '.items[]? | "\(.full_name) | ★\(.stargazers_count) | \(.description // "")"' | head -8
```

拿到仓库后**从 README 里抄官方给的集成子目录**——很多项目 Hermes 侧是 `owner/repo/integrations/hermes`，
直接 `hermes plugins install owner/repo/integrations/hermes`。

⚠️ 搜索 API 与仓库详情 API 的限流是分开的：共享出口 IP 下 `api.github.com/search/repositories` 能用，
而 `api.github.com/repos/<o>/<r>` 往往先返回 `403 API rate limit exceeded`。仓库/文件存在性用**普通 HTTP 状态码**验
（`curl -sL -o /dev/null -w "%{http_code}" https://github.com/<o>/<r>`，404=不存在），并拿一个不存在的名字做对照。

### ⚠️ manifest_version 门槛：插件可能要求比 PyPI 更新的 Hermes

实测：

```
Cloning https://github.com/<owner>/<repo>.git (subdir: integrations/hermes)...
Error: Plugin '<name>' requires manifest_version 2, but this installer only supports up to 1.
       Run pip install --upgrade hermes-agent to update Hermes.
```

**先核版本再动手**：`pipx list | grep hermes` 对比
`curl -s https://pypi.org/pypi/hermes-agent/json | jq -r .info.version`。
两者相同 = **没有可升的版本**，该插件面向尚未发布的 Hermes —— 这不是本机配置问题：
**不要 `--break-system-packages`、不要装 git main 分支硬上**，走下面的替代路径并如实告诉用户「插件要等 Hermes 更新」。

### 替代路径：插件往往只是包装，底层是独立 CLI → 直接装 CLI

```bash
# 1) 先确认底层真的是个 PyPI 包（插件 README 通常写了它自己的安装方式）
curl -s --max-time 20 "https://pypi.org/pypi/<name>/json" | jq -r '.info.version, .info.summary'
# 2) 独立 pipx 环境 + 指定 Python（避开系统 3.14 的兼容问题；本机 py3.11 在 ~/.local/bin/）
pipx install --python /home/wei/.local/bin/python3.11 <name>
# 3) 自检：doctor 会列出还缺什么（依赖 / 设备 / 账号）
<name> --version && <name> doctor
```

好处：**能力立刻可用**（agent 直接在终端驱动它，这类 CLI 设计上就同时支持 Claude Code/Codex 等 agent），
等 Hermes 支持新 manifest 再装插件拿原生工具（如 `phone_exec`）。
`doctor` 的 `[FAIL]` 要分清**必需 vs 可选**（实测 phone-harness：缺 `adb` 是必需 → `sudo apt install adb`；
缺 `scrcpy` 只是可选的实时镜像，不影响控制；最后的 `no-device` 是「还没有手机」而不是装错了）。

⚠️ `no-device` 之后的排查（USB 认不认、`error -71` 到底是线还是驱动、MIUI 的两个隐藏开关）见
`references/android-adb-triage.md`：四层证据链 + adb 服务端 USB trace 的读法。**别在"USB 插好了"上想当然。**

## 另一条路径：Vercel skills CLI（`npx skills add owner/repo`）

agentskills.io 生态的包用 Vercel 的 `skills` CLI 装（npm 包 `skills`，repo `vercel-labs/skills`），
和 `hermes skills install` 是**两套完全不同的东西**。实测（2026-10，binance-skills-hub）：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
npx -y skills add <owner>/<repo> --agent '*' -y   # 项目级（推荐）
npx -y skills add <owner>/<repo> -g -y            # 全局（很多包不支持，见下）
npx -y skills list | remove <name>                # 查 / 删
```

**四条实测坑**：

1. **`-g` 全局安装经常整包失败**：`✗ <skill> → PromptScript: PromptScript does not support global skill installation`。
   PromptScript 格式的包只能装项目级 —— 去掉 `-g` 重来。
2. **无 TTY 时必须显式给 `--agent`**：否则卡在 `■ Select skills to install` 后报
   `Interactive prompt required but stdin is not a TTY. Nothing was installed`。
   即便报 cancelled，也可能已经写了一半——**装完用 `ls -ld` 实际核实，别信退出信息**。
3. **实际落点是 `~/.agents/skills/<name>`**，再软链进 `~/.hermes/skills/`（`ls -ld` 能看到
   `../../.agents/skills/xxx`）。删的时候两边都要清。
4. **仓库名别信帖子**：实测「`binance/agentic-wallet-skills`」直接 404，真实仓库是
   `binance/binance-skills-hub`（★1071，含 `skills/binance-web3/*` 8 个 + `skills/binance/*` 7 个）。
   先验存在性再搜真名：
   ```bash
   gh api repos/<o>/<r> --jq '.full_name'     # 404 = 不存在
   gh search repos "<关键词>" --limit 8 --json fullName,stargazersCount
   ```
   （`gh` 已登录时优先用它，可绕开共享出口 IP 的 GitHub API 403 限流。）

**装完必须补 CLI，否则 skill 是空壳**：这类包在 frontmatter 声明依赖

```yaml
metadata:
  requiredCliVersion: '1.11.0'
  openclaw:
    requires: { bins: [baw] }
    install: [{ kind: node, package: '@binance/agentic-wallet', bins: [baw] }]
```

读法：`grep -A12 '^metadata:' ~/.hermes/skills/<name>/SKILL.md` → `npm i -g <package>` →
`<bin> --version` 对齐 `requiredCliVersion`。

**装上 ≠ 能用**：钱包类 skill 还要 `baw auth signin`（邮箱验证码/二维码）。这类能力等于
「agent 可无确认地签名/转账」，交付时必须同时说清风险与限额手段（`baw wallet settings` 的 daily limit）。

### `baw` 的能力边界（实测，交付前先讲清，别让用户以为能一键跨链）

```
支持链：Base 8453 | BSC 56 | Ethereum 1 | Polygon 137 | Robinhood 4663 | Solana CT_501 | Arbitrum 42161
swap  ：market-order quote/swap 只接受**单个 --binanceChainId** → 只能同链换
桥    ：**没有 bridge 命令** → 跨链买币要外部桥，工具内做不到
```

实测连环坑：用户把 104 USDC 转到钱包（**BSC 链**），要买的是 **Robinhood 链（4663）** 上的币 →
`baw` 无法完成，必须先跨链；而该币 `quote` 出来的滑点是 15.88%（LP 太薄）。
**正确做法是先把这三个障碍（链不同 / 无桥 / 滑点）一次说清，再问要不要做**，不要先答应"我帮你买"。

另外两条：
- **`baw wallet settings` 只能查不能改**（无 set 子命令）→ 日限额必须让用户去币安 App 改；
  CLI 报的 `dailyLimit` 常是 50000 这种高位，等于"没有限额"，不能当安全措施。
- **钱包只有 USDC ≠ 能交易**：任何 swap 都要原生 gas 币（BSC 要 BNB）。余额里只看到稳定币时，
  先提醒用户转几刀 gas 进来。


**成本提醒（本用户很在意）**：每个装上的 skill 描述都常驻每轮上下文，9 个 ≈ 800-1200 tokens/轮。
装完立刻问要不要删掉用不上的（`npx skills remove <a> <b>`），别默认全留。

### 装了之后想「禁用而不删除」：`skills.disabled` 会静默失败

`hermes skills` **没有 disable 子命令**（`opt-out` 只针对 bundled skills）。正解是 config 的
`skills.disabled` 列表，由 `hermes_cli/skills_config.py` 的 `get_disabled_skills()` 读取。

⚠️ **实测坑**：`hermes config set skills.disabled '["a","b"]'` 会把整串存成**一个 YAML 字符串**：

```yaml
skills:
  disabled: '["a","b"]'
```

而 `_normalize_skill_names()` 遇到字符串是「当成单个名字」→ 列表里没有任何名字匹配 →
**设置成功但一个都没禁用**（`hermes skills list` 里仍全是 enabled）。CLI 当时只给一句
`'skills.disabled' is not a recognized config key — it was saved anyway`，不报错。

落地与验证顺序：

```bash
hermes config set skills.disabled '[...]'
grep -A8 '^skills:' ~/.hermes/config.yaml              # 必须是 YAML 列表（每行 - name），不是带引号的整串
hermes skills list --enabled-only | grep <prefix>      # 数量真的变了才算生效
```

改不动就老实删目录（先征得同意）：`rm -f ~/.hermes/skills/<n>` + `rm -rf ~/.agents/skills/<n>`。
**删除会被审批拦，超时=未同意**——这时把命令原文交给用户自己跑，不要换个写法重试同一个结果。

### npm CLI 走代理：`HTTPS_PROXY` 不够，还要 `NODE_USE_ENV_PROXY=1`

`baw auth signin` 只带 `HTTPS_PROXY` 时返回 `50001001 NETWORK_ERROR / fetch failed`
（Node 的 undici 默认不读环境代理变量）。加一个变量即可：

```bash
NODE_USE_ENV_PROXY=1 baw auth signin --json     # 或 NODE_OPTIONS=--use-env-proxy
```

顺带：`baw auth signin --json` 返回 `{qrCodeId, urlForWeb, pairingCode, expireAt}`，
手机端打开 `urlForWeb` 授权后，用 `baw auth verify --qrCodeId <id>` 轮询到 `{"status":"SUCCESS"}`；
二维码约 4 分钟过期。这类 CLI 的登录态 48h 无操作自动失效，不是装坏。

## 相关生态项目速查
- **gzh-design**（isjiamu）：公众号排版引擎，6+ 主题（摸鱼绿/红白/石墨极简/禅意/票据/橄榄手记/康奈尔），脚本：`scripts/validate_gzh_html.py`（校验 span leaf 包裹）、`scripts/wrap_preview.py`（生成带复制按钮预览页）、`scripts/component_lint.py`（主题库 lint）
- **wechat-publish-template**（limin112）：公众号排版，橙黑赛博朋克风（#FF5722/#0A0A0A），12 种 block，可选 wechatsync CLI 直推草稿箱。⚠️ 其 HTML 规范与 gzh-design 不同——**不用 span leaf 包裹**，所以 gzh-design 的 validate 脚本对它不适用（会误报）
- **explain-video**（limin112）：概念讲解视频流水线（HTML 幻灯→TTS→字幕→BGM→录屏→合成），需 ffmpeg（通常已有）
- **evey-plugins**（42-evey）：23 插件，autonomy/council/cost-guard/goals/telemetry 等
- **skill-factory**（Romanescu11）：元技能工厂，`bash install.sh` 或手动 cp SKILL.md + skill_factory.py
- **oh-my-hermes**（witt3rd）：多 Agent 编排，skills 在 `plugins/omh/skills/` 下
- **hermeskill**（theopitori）：apoptosis 监督协议，杀死 runaway/超预算 agent 并出死亡证书

## 用户偏好
- 装社区项目 = clone + 分析 + 装，不要只收藏（action-first）
- 代理：所有 git/npm/hermes 网络操作带 `https_proxy=http://127.0.0.1:7890`
- evey 套件默认全关，用户要哪个开哪个，不要一次全 enable
