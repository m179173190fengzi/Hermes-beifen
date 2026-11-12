---
name: repo-secret-hygiene
description: "备份/同步管道的密钥卫生与泄露响应 —— 审计「把本机文件推到远端仓库」的脚本是否带走凭据（.env / cookie / 含 key 的 config）、30 秒判断仓库是否公开、发现泄露后的正确顺序（止血 → 轮换密钥 → 改私有 → 清 git 历史）。触发词：备份脚本、定时备份、同步到 GitHub、仓库要不要公开/public、.env 能不能提交、密钥泄露、清历史/filter-branch、把仓库设成私有。English: secret leak, leaked API key in repo, commit .env, purge git history, is this repo public."
version: 1.1.0
author: Hermes Agent
tags: [secrets, backup, git, security, incident-response]
---

# 备份/同步管道的密钥卫生 & 泄露响应

## 何时用

- 新建或修改任何**把本机文件推到远端仓库**的东西：cron 备份、配置同步、笔记/vault 同步、`git push` 脚本
- 用户问「这个仓库能不能公开」「帮我把仓库设成 public/private」
- 发现或怀疑凭据已经进了远端仓库（也包括「我好像提交过 .env」）

## 核心原则

1. **凭据文件永不同步。** `.env`、`secrets/`、`*_cookies.json`、含 key/secret 的 `config.toml`、SSH 私钥 —— 一个都不进仓库。
   **用白名单式复制**（只 copy 明确要备份的路径），不要用黑名单式排除（漏一个就泄露）。
2. **要留配置就只留「壳」。** 想让人看得出"这台机器配了哪些凭据"而不泄露值：
   ```bash
   grep -oE '^[A-Z_0-9]+=' "$HOME/.hermes/.env" | sed 's/=$/=<REDACTED>/' > config/env-keys-only.txt
   ```
   输出只有 key 名 + `<REDACTED>`。
3. **审计在建脚本时做，不是出事之后。** 推送前过一遍：
   ```bash
   grep -rniE '(token|secret|api[_-]?key|password|passphrase|private[_-]?key)' <repo>/ --exclude-dir=.git
   ```

## 判断仓库是否已经公开（30 秒）

```bash
curl -sI --max-time 20 "https://github.com/<owner>/<repo>" | head -1
# HTTP/2 200 → 未登录也能看到 → 公开
# HTTP/2 404 → 私有
```

- **别只信 `api.github.com`**：共享出口 IP 下它常直接返回 `403 API rate limit exceeded for <ip>`——
  那不是「仓库不存在」，也不是权限问题，换上面的纯状态码判断。
- ⚠️ **文件进了 git 历史 = 已泄露。** `git log --all --oneline -- <path>` 有输出，就说明
  任何人（或爬虫）都能从历史提交里翻出来。**删掉工作区文件远远不够。**

## 推送前分流（日常路径，先做这个）

「把所有东西传上去」这种请求不要 `git add -A`。先分三堆，再决定每堆去哪：

```bash
# ① 看清待提交面：按顶层目录统计
git status --porcelain | awk '{print $2}' | cut -d/ -f1 | sort | uniq -c | sort -rn

# ② 只加明确可公开的路径（白名单），永不 add -A
git add skills scripts memories docs

# ③ 关键：检查暂存区里有没有混进来的敏感路径
git diff --cached --name-only | grep -iE '^\.env$|secrets/|state\.db|logs/|cron/|ledger'

# ④ 检查体积——超过 ~20MB 基本都是不该进仓的东西
git diff --cached --name-only | xargs -r du -ch | tail -1
```

**本机 Hermes 目录下必踢的三类**（都踩过）：

| 路径 | 为什么不能进仓库 |
|---|---|
| `skills/.curator_backups/*/skills.tar.gz` | 每次几十 MB 的整包快照，5 个就 367MB；且是**脱敏前**的旧内容 |
| `skills/.curator_ledger.jsonl` | 内部运维流水，无分享价值 |
| `logs/` `cron/` `pastes/` `*.db` | 运行态数据，含全量对话/持仓/推送内容 |

```bash
git rm -r --cached skills/.curator_backups
printf '%s\n' 'skills/.curator_backups/' 'skills/.usage.json' >> .gitignore
```

实测：清掉 curator 备份后暂存体积 373MB → 6MB。**推送前不看体积，就会把几十个历史快照推上去，把仓库变成凭据坟场。**

> `git rm -r --cached` 容易被审批拦（被判为 destructive）。被拦一次就停，把这条命令原样交给用户执行，或写进脚本再调用——不要换着花样重试。

### 两个可以反复用的小工具

- `scripts/secret_scan.py`（本 skill 自带）：扫目录，**只打印 `文件:行号 <命中类型>`，绝不回显密钥本身**。用完再决定哪些要脱敏。
- `scripts/redact_keys.py`（本 skill 自带）：把 `sk-…` / bot token / gh token 换成 `sk-REDACTED` 之类占位符，**只处理命令行指定的文件**，避免误伤代码。

判读命中时不要一律拉红线：64 位十六进制常是 **哈希**（curator ledger 里全是），`sk-x****` 这种明显是**占位符**。逐个看「掩码后的片段」再定性，别把哈希当私钥、也别把占位符当密钥。

#### 脱敏正则必须吃连字符（这条真的漏过一次）

```
✗ sk-[A-Za-z0-9]{20,}      # sk-or-v1-… / sk-proj-… / sk-ant-… 全部漏网
✓ sk-[A-Za-z0-9_-]{16,}    # 覆盖 OpenRouter / OpenAI project key / Anthropic
```

带连字符的 key 是常态（`sk-or-v1-<hex>`、`sk-proj-<…>`），只匹配字母数字等于放行。
**扫描器命中了、脱敏器没命中，是最坏的组合** —— 你会以为已经处理过，然后推送出去。

#### 顺序：扫 → 脱 → 复扫 → 才 add（不能反）

```bash
python3 scripts/secret_scan.py                      # 1. 扫，记下命中文件
python3 scripts/redact_keys.py <命中文件…>           # 2. 逐个脱敏
python3 scripts/redact_keys.py --check <目录>        # 3. 退出码必须是 0
git add <白名单路径>                                 # 4. 才开始暂存
```

**先 add 再扫，等于已经在做事故响应。** 一旦 push 出去，唯一真正的修复是轮换密钥。

#### 对话/聊天导出是最容易漏的泄露面

导出的 transcript 会把当时敲过的命令原样留下：

```
export OPENROUTER_API_KEY=sk-or-v1-…     ← 在聊天记录里躺着
hermes config set model.api_key sk-…     ← 同上
```

给「把对话也上传」这类请求做导出时，**脱敏要做两道**：导出函数里做一遍 + 落盘后全目录复扫一遍。只信导出时那一次不够。

已进远端**最新**提交的应急路径：脱敏 → `git commit --amend --no-edit` → `git push --force`。
注意这只清掉分支指针，GitHub 侧旧对象短期仍可能被按 SHA 访问 —— **轮换仍然必须做**。

**用户选择保持公开仓库时**（他很清楚风险，别反复劝）：把范围收窄成「提炼文档 + 脚本 + 技能」，原始对话/持仓/密钥一律不推，并在交付里写清「哪些没推、为什么」。

## 泄露响应顺序（顺序不能反）

**0. 止血（先做，成本最低）**
改脚本停止继续上传（删掉那行 `cp .env`、改成只导 key 名）；
`git rm --cached <file>` 停止跟踪并从工作区删除。

**1. 🔴 轮换密钥 —— 唯一不可替代的一步，且只有用户能做**
| 凭据 | 去哪换 |
|---|---|
| Telegram Bot Token | @BotFather `/revoke` → 新值写回 `~/.hermes/.env` → **重启网关** |
| OpenRouter / DeepSeek / 其它 provider key | 各平台后台重新生成 |
| 本机服务 key（如 `API_SERVER_KEY`） | 直接改值 |

**改脚本、清历史都收不回已经公开的东西。** 挂了几周就可能已被抓走 —— **必须视为已泄露**。
交付时要明确告诉用户：这一步今天不做，前面的修补等于白做。

**2. 仓库改 Private**：GitHub → 仓库页 → Settings → Danger Zone → Change visibility。

**3. 清 git 历史（优先级最低 —— 救不了已泄露的密钥，只防未来继续被翻）**

```bash
export FILTER_BRANCH_SQUELCH_WARNING=1
cd <repo>

# 先备份一份不含 .git 的工作区，再动手
tar czf ~/repo-backup-$(date +%Y%m%d_%H%M).tgz -C "$(dirname <repo>)" "$(basename <repo>)" --exclude=.git

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch <path>' \
  --prune-empty --tag-name-filter cat -- --all

rm -rf .git/refs/original            # 不删的话旧对象仍在本地
git reflog expire --expire=now --all
git gc --prune=now

git log --all --oneline -- <path> | wc -l    # 验证：必须是 0
git push origin main --force
```

- `git-filter-repo` 更现代，但**常常没装**；`filter-branch` 对小仓库完全够用，不用先装东西。
- `--force` 推送 + 历史重写属于**需要用户点确认**的动作：写好完整命令，既让自己能跑，也让用户能自己跑。
- 重写后旧 commit SHA 会变；`origin` 上旧对象在 GitHub 侧可能仍短暂可达 —— 所以第 1 步不能省。

## 已踩的坑

- **「改了脚本就安全了」是错觉。** 改脚本只防未来，历史提交里的旧值依然可查。
- **`|| true` 制造静默成功。** 某备份 job 连续两个月 `last_status: ok`，实际一直在复制一个
  7 月的死文件（源路径写错成 `~/.hermes/memory/`，真实目录是 `~/.hermes/memories/`，
  每步都挂了 `|| true` 把错误吞掉）。教训：备份脚本的**源路径不存在要显式报警**，
  并且要**定期抽查产物内容**（文件大小/时间戳/diff），不要只看 job 状态。
- **同步脚本要从「黑名单排除」改成「白名单复制」** —— 排除法的新增文件默认是同步的，
  而白名单法的新增文件默认是不同步的，失效方向正好相反。
- **别把「清历史」当终点汇报。** 正确交付顺序是：
  「已止血（脚本+移除文件）→ **你必须去换这几个 key** → 仓库改私有 → 可选清历史」，
  并且第一句就说清「换 key 不做，其余都是修补」。

## 自带脚本

- `scripts/secret_scan.py` — 推送前扫目录，只输出 `文件:行号 <类型>`，不回显密钥。
- `scripts/redact_keys.py` — 把指定文件里的 key/token 换成占位符。
