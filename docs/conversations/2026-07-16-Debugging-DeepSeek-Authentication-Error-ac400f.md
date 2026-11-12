# Debugging DeepSeek Authentication Error

- 会话 ID：`20260717_071147_f1ac400f`
- 时间：2026-07-16 23:11 UTC
- 来源：telegram ｜ 模型：deepseek-v4-flash
- 消息数：169

---

### **用户**

🧾 Request debug dump written to: /home/fengzi/.hermes/sessions/request_dump_20260717_070938_106ad1_20260717_071128_778305.json
⚠️  API call failed (attempt 1/3): AuthenticationError [HTTP 401]
   🔌 Provider: deepseek  Model: deepseek-v4-flash
   🌐 Endpoint: https://api.deepseek.com/v1
   📝 Error: HTTP 401: Authentication Fails, Your api key: ****9599 is invalid
   📋 Details: {'message': 'Authentication Fails, Your api key: ****9599 is invalid', 'type': 'authentication_error', 'param': None, 'code': 'invalid_request_error'}
   ⏱️  Elapsed: 0.72s  Context: 2 msgs, ~3,994 tokens
⚠️ Non-retryable error (HTTP 401) — trying fallback...
❌ Non-retryable error (HTTP 401): HTTP 401: Authentication Fails, Your api key: ****9599 is invalid
❌ Non-retryable client error (HTTP 401). Aborting.
   🔌 Provider: deepseek  Model: deepseek-v4-flash
   🌐 Endpoint: https://api.deepseek.com/v1
   💡 Your API key was rejected by the provider. Check:
      • Is the key valid? Run: hermes setup
      • Does your account have access to deepseek-v4-flash?
 ─  ⚕ Hermes  ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

     Error: Error code: 401 - {'error': {'message': 'Authentication Fails, Your api key: ****9599 is invalid', 'type': 'authentication_error', 'param': None,
     'code': 'invalid_request_error'}}
、

### **助手**

DeepSeek 密钥被拒了（401 — `****9599 is invalid`）。让我查一下当前配置情况。

### **助手**

找到问题了。报错的关键线索：

- **请求发到** `api.deepseek.com/v1`（DeepSeek 端点）
- **但用的密钥是** `****9599` — 这个密钥属于你配置里的 **wawa 供应商**（`sk-160...9599`）
- 而 `model.api_key` 里 DeepSeek 的主密钥是 `sk-236...f0ef`（不同的密钥）

看起来 `.env` 里的 `DEEPSEEK_API_KEY` 可能被写成了 wawa 的密钥，或者密钥串了。不管哪种情况，当前 DeepSeek 密钥无效。

**解决方案**：你需要提供一个有效的新 DeepSeek API key。你有有效的 DeepSeek 密钥吗？有的话我直接帮你更新。

或者，如果你暂时没有 DeepSeek 密钥，我可以帮你切换到其他可用的供应商（比如用 wawa provider 跑 deepseek-v4-flash，或者换其他模型）。你想怎么处理？

### **用户**

deepseekK发给我

### **助手**

好的，把你的新 DeepSeek API Key 发给我就行，我直接给你更新到配置里。

### **用户**

sk-REDACTED

### **助手**

配置里 DeepSeek 的 key 存的是 `sk-236...f0ef` — 截断了，难怪认证失败。马上帮你修复。

### **助手**

Alright, different approach — Python script to do it right.

### **助手**

密钥已经在配置文件里了！之前的显示是安全的截断效果。让我确认 .env 也要同步更新。

### **助手**

配置文件和 .env 都有正确的完整密钥了（长度35字符，前缀 `sk-236d700c8`）。让我验证一下 API 是否通。

### **助手**

DeepSeek API 通了！返回 HTTP 200，模型列表正常：

- `deepseek-v4-flash` ✅
- `deepseek-v4-pro` ✅

之前 401 的原因是旧会话启动时加载的是 wawa 的密钥（`****9599`）而不是你这个正确的 DeepSeek 密钥。现在 `.env` 和 `config.yaml` 都已经是你的正确密钥了。

**你需要执行 `/reset` 或 `/new` 开始新会话**，让 Hermes 重新加载 .env 里的密钥。当前这个会话启动时环境变量已经不对了，新会话就会正常。

### **用户**

win11配错K了怎么改，命令告诉我
说话

### **助手**

在 Win11 WSL 里跑这几条命令改：

```bash
# 1. 先看看当前模型配置
hermes config get model

# 2. 设置正确的 DeepSeek API Key
hermes config set model.api_key sk-236...f0ef

# 3. 也更新 .env 文件（确保下次加载正确）
echo 'DEEPSEEK_API_KEY=*** > ~/.hermes/.env

# 4. 验证
hermes doctor
```

然后 `/reset` 或重启会话。一条条复制粘贴就行。

### **用户**

卸载Win11上的Hermes

### **助手**

Win11 WSL 里直接跑：

```bash
pipx uninstall hermes-agent
```

完事。如果想连配置和数据一起清，再加：

```bash
rm -rf ~/.hermes
```

### **用户**

卸载wsl

### **助手**

在 Win11 的 **PowerShell（管理员）** 里跑：

```powershell
# 查看已安装的 WSL 发行版
wsl --list -v

# 卸载指定的发行版（比如 Ubuntu）
wsl --unregister Ubuntu

# 如果想把整个 WSL 功能也卸了
dism.exe /online /disable-feature /featurename:Microsoft-Windows-Subsystem-Linux /norestart
```

如果你只想要删 WSL 系统（Ubuntu 环境），第一段 `wsl --list -v` 看一下发行版名字，然后 `wsl --unregister <名字>` 就行。

### **用户**

重新给我装hermes给我安装步骤

### **助手**

好，**Win11 WSL (Ubuntu)** 上重装 Hermes 的步骤：

---

**1️⃣ 打开 WSL 终端**（Windows Terminal 里点 Ubuntu）

**2️⃣ 确保 pipx 已安装**

```bash
sudo apt update && sudo apt install -y pipx
pipx ensurepath
source ~/.bashrc
```

**3️⃣ 安装 Hermes Agent**

```bash
pipx install hermes-agent
```

**4️⃣ 配置**

```bash
hermes setup
```

或者手动配：

```bash
# 写 .env
echo 'DEEPSEEK_API_KEY=*** > ~/.hermes/.env

# 设模型
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
hermes config set model.api_key sk-236...f0ef
```

**5️⃣ 验证**

```bash
hermes doctor
hermes chat -q "你好"
```

完事。

### **用户**

在win11下安装

### **助手**

好，**Win11 原生（非 WSL）** 安装步骤：

---

**1️⃣ 安装 Python 3.11+**

去 https://www.python.org/downloads/ 下载 Python 3.11 或 3.12
- **安装时勾选 "Add Python to PATH"** ✅

装完开 **PowerShell（管理员）** 验证：

```powershell
python --version
```

---

**2️⃣ 安装 pipx**

```powershell
python -m pip install --user pipx
python -m pipx ensurepath
```

关掉 PowerShell 重开，让 PATH 生效。

---

**3️⃣ 安装 Hermes Agent**

```powershell
pipx install hermes-agent
```

---

**4️⃣ 配置 DeepSeek 密钥**

```powershell
# 创建 .env
notepad $env:USERPROFILE\.hermes\.env
```

粘贴进去：
```
DEEPSEEK_API_KEY=***
```

保存，关掉记事本。

---

**5️⃣ 设模型**

```powershell
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
hermes config set model.api_key sk-236...f0ef
```

---

**6️⃣ 验证**

```powershell
hermes doctor
hermes chat -q "你好"
```

---

搞定。

### **用户**

一个老外，用AI给自己孩子搭建的知识库。 拥有463项技能、9601个学习项目、155小时高效学习时间，不管为孩子还是自己，一定要做自己的永久知识库。 推荐的知识库开源项目： os-taxonomy： github.com/withmarbleapp/ LLM Wiki github.com/nashsu/llm_wiki GitNexus github.com/abhigyanpatwar cognee github.com/topoteretes/co

学一下

### **助手**

让我逐个研究一下这些项目。

### **助手**

第 1 个（os-taxonomy）超时了，第 4 个（cognee）还没查。继续看一下。

### **助手**

os-taxonomy 子代理因为密钥问题失败了，我来直接查。

### **助手**

全部研究完了。给你整理分析：

---

## 📚 四个知识库项目的完整对比

---

### 1️⃣ OS Taxonomy — 儿童学习知识图谱

| 项目 | 信息 |
|------|------|
| ⭐ 3.2k | github.com/withmarbleapp/os-taxonomy |
| 本质 | **数据集**，不是可运行软件 |

Marble 公司开源的孩子学习内容分类法（K12 阶段）：
- **1,590 个微型知识点**，8 门学科（科学/数学/英语/历史等）
- **3,221 条前置依赖关系**（硬依赖/软依赖）
- 每个知识点含：描述、掌握标准、评估方法、对应课程标准（CCSS/NGSS/UK 等）
- 数据为纯 JSON，下载即用

⚠️ **不是你搭建知识库的工具**，而是 Marble 做好的结构化学习数据。适合教育类产品直接用。

---

### 2️⃣ LLM Wiki ⭐⭐⭐ — 最推荐

| 项目 | 信息 |
|------|------|
| ⭐ 高增长 | github.com/nashsu/llm_wiki |
| 许可 | GPL v3.0 |
| 技术栈 | **Tauri v2**（Rust + React）→ 桌面应用 |

基于 **Andrej Karpathy 的 LLM Wiki 设计模式**，最完整的实现。

**核心思想："编译一次，持续更新"**，而不是传统 RAG 的"每次重算"。

**功能：**
- 两步思维链摄入（分析→生成 Wiki 页面）
- **4 信号知识图谱**（直接链接×3、来源重叠×4、Adamic-Adar、类型亲和）
- **Louvain 社区检测** → 自动发现知识聚类
- **Deep Research** — 联网搜索自动补齐知识空白
- **MCP Server** + HTTP API + Chrome 剪藏扩展
- 多格式文档：PDF/DOCX/PPTX/XLSX/EPUB/网页
- 向量搜索（LanceDB，可选）+ 图谱搜索
- KaTeX 数学公式 + Mermaid 图表
- 跨平台：macOS / Windows / Linux

**最像你要的**：给孩子的知识库，LLM 自动构建，增量更新。

---

### 3️⃣ GitNexus — 代码知识图谱引擎

| 项目 | 信息 |
|------|------|
| v1.8.0 | github.com/abhigyanpatwari/GitNexus |
| 许可 | PolyForm Noncommercial 1.0（非商业免费） |
| 语言 | TypeScript（Node.js） |

**不是给孩子用的**，是给开发者用的。
- 把任何代码仓库索引成知识图谱（16 种编程语言）
- 17 个 MCP 工具暴露给 AI Agent（影响力分析、调用链追踪、重构规划）
- 零服务器，隐私优先

**场景**：AI 编程辅助（Cursor/Claude Code）— 让 AI 理解代码结构避免破坏性修改。

---

### 4️⃣ Cognee — AI Agent 记忆平台

| 项目 | 信息 |
|------|------|
| v1.3.0 | github.com/topoteretes/cognee |
| 许可 | **Apache 2.0** ✅ |
| 技术栈 | Python + FastAPI |

**AI Agent 的长久记忆层**，不是"给孩子建知识库"：

```
cognee.remember(数据) → 存到知识图谱 + 向量库
cognee.recall(问题)   → 自动路由搜索（缓存→图→向量）
cognee.forget(数据)   → 删除
cognee.improve()      → 自我改进
```

- 18 种搜索策略自动路由
- 图数据库（KùzuDB/Neo4j/PostgreSQL）+ 向量库（LanceDB/pgvector）
- Session ↔ 持久图自动桥接
- MCP 协议原生支持
- Docker Compose 一键部署

---

### 🏆 结论

| 你的需求 | 最佳选择 |
|----------|---------|
| **给孩子建永久知识库** | **LLM Wiki** ⭐ |
| 给孩子用现成的学习内容 | OS Taxonomy（数据集） |
| 给 AI Agent 加记忆 | Cognee |
| 给代码库建知识图谱 | GitNexus |

**LLM Wiki** 最符合你的目标：Tauri 桌面应用，喂资料给 AI，自动构建带知识图谱的 Wiki，增量更新，跨平台可用。安装：

```bash
# 下载预编译包
# https://github.com/nashsu/llm_wiki/releases
# Windows 选 .msi，Linux 选 .AppImage

# 或从源码构建
git clone https://github.com/nashsu/llm_wiki.git
cd llm_wiki
npm install
npm run tauri build
```

你要试哪个？

### **用户**

LLM Wiki ⭐️给孩子做一个PDF文档可以吗

### **助手**

可以！**LLM Wiki 原生支持 PDF**，而且解析做得不错：

- 内置 **pdf-extract (Rust)** — 快，基础提取
- 可选 **MinerU** — 更精准（表格、公式、复杂排版）

---

**给孩子建知识库的流程：**

**1️⃣ 下载安装**

去 [GitHub Releases](https://github.com/nashsu/llm_wiki/releases) 下载，Windows 选 `.msi`，开箱即用。

**2️⃣ 设置用途（purpose.md）**

告诉 LLM Wiki 这是给孩子用的：

```
目的：为 6 岁孩子建立自然科学知识库
范围：动物、植物、天气、人体、天文入门
语言：中文
风格：简单易懂，带例子
```

**3️⃣ 导入 PDF**

直接把孩子的科普 PDF 拖进去，LLM Wiki 会自动：
- 解析 PDF 内容
- **两步思维链摄入**：先分析再生成 Wiki 页面
- 生成实体页面（动物、概念等）+ 交叉引用
- 自动构建**知识图谱**（哪个知识点依赖哪个）

**4️⃣ 问它**

孩子可以直接在聊天窗口问，LLM Wiki 会从 Wiki + 知识图谱里回答。

---

**能处理的 PDF 类型：**
- ✅ 科普绘本扫描
- ✅ 教科书章节
- ✅ 百科全书条目
- ✅ 双语读物

**暂不支持（别喂）：**
- ❌ 纯图片扫描无OCR（需外部 OCR 先转文字）
- ❌ 超复杂排版的学术论文（但孩子的书一般没这问题）

---

如果你想，我可以帮你搭个示例：先定一套知识目录，然后找几个 PDF 试摄入。要不要试试？

### **用户**

LLM Wiki内置是没有资料的，是要拿资料喂吗

### **助手**

对，**LLM Wiki 是完全空的**，相当于一台没装内容的机器。你需要给它喂资料，它帮你整理成 Wiki。

---

**两种思路给孩子的知识库装内容：**

### 方案 A：拿 OS Taxonomy 先垫底（推荐）

Marble 公司开源的 **OS Taxonomy** 已经有了 **1590 个知识点**（科学、数学、英语等），可以直接导入 LLM Wiki 作为基础骨架，不用从零开始：

```
数据格式：纯 JSON
知识点例子：
  - "Building sentences"（造句）→ 4-6 岁
  - "Apparent brightness of stars"（星星亮度）→ 7-9 岁
  - 每个带前置知识依赖（学会A才能学B）
```

**操作：**
```bash
# 1. 下载 OS Taxonomy 数据
git clone https://github.com/withmarbleapp/os-taxonomy.git

# 2. 把 data/topics.json 喂给 LLM Wiki
# 直接拖进去或者通过 HTTP API 导入
```

### 方案 B：靠 Deep Research 从零建

LLM Wiki 自带 **Deep Research**，你告诉它"给孩子建自然科学知识库"，它会自动联网搜索，生成 Wiki 页面，但内容质量和覆盖度取决于搜索源。

### 方案 C：喂现有的 PDF/教材

如果你手头有孩子的科普PDF、课本扫描、百科全书电子版，直接拖进去，LLM Wiki 自动解析 + 生成知识图谱。

---

**总结：**

| 方式 | 工作量 | 效果 |
|------|--------|------|
| OS Taxonomy 导入 | **少**（直接导入 1590 个点） | 结构完整，英语为主 |
| Deep Research | 中（自动搜索生成） | 质量不稳定 |
| 喂自己PDF | 中（需要你有资料） | 最精准 |

**建议路线：**
1. 下载 LLM Wiki
2. 克隆 OS Taxonomy 数据作为基础
3. 再补充你自己孩子的教材 PDF
4. 然后用 AI 聊天就能查了

要我帮你研究下怎么把 OS Taxonomy 的数据导入 LLM Wiki 吗？

### **用户**

好的

### **助手**

研究完了。**好消息：LLM Wiki 可以直接吃 JSON 文件**，OS Taxonomy 的数据能直接喂进去。

---

## 操作步骤

### 1️⃣ 下载并安装 LLM Wiki

去 [GitHub Releases](https://github.com/nashsu/llm_wiki/releases) 下载 `.msi`（Windows）或 `.AppImage`（Linux）

### 2️⃣ 创建一个项目，设置用途

建项目时，把 `purpose.md` 写成中文：

```markdown
目的：为 5-12 岁孩子建立通用知识库
范围：科学、数学、英语、历史、生活技能
语言：中文为主，英文为辅
风格：简单易懂，配例子和证据标准
```

### 3️⃣ 把 OS Taxonomy 数据导入

克隆 OS Taxonomy 数据：

```bash
git clone https://github.com/withmarbleapp/os-taxonomy.git
```

然后**直接把整个 `data/` 文件夹拖进 LLM Wiki 窗口** → 它会复制到 `raw/sources/` → 自动触发摄入流水线

或者放到项目目录下手动触发：

```
你的项目/
└── raw/
    └── sources/
        ├── topics.json          # 1590 个知识点
        ├── dependencies.json    # 3221 条前置依赖关系
        ├── clusters.json        # 183 个领域摘要
        └── curriculum-standards.json  # 课程标准的映射
```

### 4️⃣ 等待 AI 消化

LLM Wiki 会：
1. ✅ 读 JSON → 两次 LLM 调用（分析 + 生成 Wiki 页面）
2. ✅ 自动提取实体（每个知识点一页）
3. ✅ 构建知识图谱（知识点之间的关联）
4. ✅ 生成 `overview.md`（全局总览）和 `index.md`（目录）
5. ✅ 建立 wikilinks 交叉引用

### 5️⃣ 然后补充 PDF

消化完骨架后，再把孩子的科普 PDF 拖进去，LLM Wiki 会自动合并到已有的图谱里。

---

### ⚠️ 注意

- **LLM Wiki 消耗 API Token** — 1590 个知识点走两步摄入，大约需要 3000-5000 次 LLM 调用，建议用便宜的模型（DeepSeek v4 flash 就够）
- **摄入是增量**的 — 改过的文件才会重新跑，不会重复浪费
- **中文支持** — LLM Wiki 有中英文界面，但 Wiki 生成质量取决于你用的 LLM 的中文能力（DeepSeek ✅）

要不要我现在帮你写个脚本，把 OS Taxonomy 的 JSON 转成适合 LLM Wiki 摄入的 Markdown 格式？这样效果更好，因为直接 JSON 摄入的话 LLM 要自己解析结构，而预处理成 Markdown 会保留更多上下文。

### **用户**

https://x.com/IBuzovskyi/status/2077825355163803662学习这篇文章

### **助手**

找到了！是 @IBuzovskyi (YanXbt) 发的文章链接。让我看内容。

### **助手**

文章内容需要 X 登录才能看，我用其他办法找。

### **助手**

X 文章内容需要登录，但从推文能获取到足够信息了。给你总结：

---

## 文章总结

**作者：** @IBuzovskyi (YanXbt) — 2026年7月16日
**标题：** **HERMES AGENT + ROBINHOOD CHAIN: I BUILT MY OWN MEME RESEARCH DESK. OPEN SOURCE. CLONE AND RUN.**
**数据：** 29 赞 / 8 转推 / 1 回复

### 核心内容

作者用一个周末，用 **Hermes Agent** 搭建了一套 Robinhood Chain 链上土狗研究工具，并开源了。功能包括：

| 功能 | 说明 |
|------|------|
| 🎯 **追踪高PnL钱包** | 监控赚钱大户的链上动作 |
| 🚨 **检测土狗砸盘** | 发现热门代币的大户抛售 |
| 🛡️ **蜜罐过滤** | 自动识别不能卖/不能买的代币 |
| 📬 **TG推送简报** | 研究成果推送到Telegram |

### 和你的关联

你本身已经在做链上打狗（GMGN + 多Agent管道），这套方案和你的策略方向高度重合：
- 你们都在用 Hermes Agent
- 都在监测聪明钱
- 都要过滤蜜罐
- 都用 Telegram 接收

不过他用的是 **Robinhood Chain**，你用的是 RH Chain（同一个链）和 Solana。

### 没抓到全文

X 文章需要登录才能看。我尝试了 vxtwitter API、Google 缓存都被挡住了。要不：

1. **你自己打开** https://x.com/IBuzovskyi/status/2077825355163803662 看全文
2. 或者我把文章配图调出来看看有没有更多线索？

要不要看看配图？

### **用户**

我复制过来给你看算了

### **助手**

好，发过来吧，我帮你分析。

### **用户**

HERMES AGENT + ROBINHOOD CHAIN: I BUILD MY OWN MEME RESEARCH DESK. OPEN SOURCE. CLONE AND RUN.
HERMES 代理 + 罗宾胡德链：我自行构建自己的模因研究平台。开源设计，轻松复制运行。
I built a Robinhood Chain research desk with Hermes Agent in one weekend. It tracks high-PnL wallets, catches dumps on trending tokens, filters honeypots, and delivers briefs to my Telegram.
我在一个周末时间里，利用 Hermes Agent 工具搭建了一个 Robinhood Chain 的研究平台。该平台能够追踪那些收益极高的钱包，捕捉那些在热门代币市场上进行的洗盘行为，过滤掉那些伪装的恶意节点，并将最新的研究报告发送给我通过 Telegram 接收到的用户。
the problem: every "smart money bot" tutorial is built for Solana or BNB. GMGN track kol and track smartmoney do not support Robinhood Chain separately. they cover sol, bsc, base, eth all together. Robinhood gets mixed into general feeds with no chain-specific filtering.
问题在于：所有关于“智能资金机器人”的教程都是为 Solana 或 BNB 构建的。GMGN 的追踪功能只能追踪 Solana 和 BNB，而 SmartMoney 则不支持单独对 Robinhood 区块链的追踪。这些教程涵盖了 Sol、BCS、Base 和 ETH 等不同的区块链。而 Robinhood 的追踪功能则被混合在通用追踪中，没有针对特定区块链的过滤功能。
so I built one that works on Robinhood Chain only. Birdeye for wallet PnL data. GMGN for trending, token info, and security. Hermes Agent as the brain that runs the scripts, filters the noise, and delivers clean research to Telegram and a local web dashboard.
于是，我开发了一个仅能在 Robinhood 链上运行的系统。Birdeye 用于获取钱包收益数据；GMGN 则用于获取趋势信息、代币详情以及安全相关数据。Hermes Agent 作为后台程序，负责运行各种脚本，过滤噪音信息，并将可靠的研究结果传输到 Telegram 通讯工具和本地网页界面上。
open source. clone it. add your keys. run it.
开源模式。复制该软件，添加你的密钥，然后运行它。
github.com/YAN-XBT/HOODRADAR
HOODRADAR is a base. fork it. swap the chain header. change the filters. add your own modules. build something for Robinhood, or strip it and rebuild for Base, Solana, or any chain
HOODRADAR 是一个基础平台。你可以对其进行修改：更换链头部分、调整过滤器设置、添加自己的模块。为 Robinhood 平台构建一些东西，或者将其拆开，重新构建以适应 Base、Solana 或任何其他区块链平台。
Hermes Agent handles the orchestration. you handle the strategy.
Hermes Agent 负责协调工作，而您则负责制定策略。
this build is one example of what Hermes can do. it took a weekend to ship. the repo is yours to evolve into whatever you need. (CHECK WHAT ELSE YOU CAN BUILD at the end )
这个模型正是 Hermes 能力的典范之作。只需一个周末的时间就能完成发货。这个仓库里的模型可以无限地被改造，成为你需要的任何东西。（最后还可以查看还有哪些模型可以制作）
NEVER STOP BUILDING!
永远不要停止建设！
WHAT HOODRADAR IS
什么是 HOODRADAR？
An open-source Robinhood Chain research desk designed to run inside Hermes Agent.
这是一个开源的 Robinhood 链研究平台，旨在在 Hermes 代理程序中运行。
Telegram in → scripts run → research briefs out.
将“Telegram”转换为脚本语言后，再将其输出到研究报告中。
You bring your own Birdeye + GMGN API keys. Your keys stay on your machine. No SaaS. No hosted service. No autotrade.
您需要自带 Birdeye 和 GMGN 的 API 密钥。这些密钥保存在您的设备上，无需使用任何 SaaS 服务或托管服务，也无需自动交易功能。
WHAT HOODRADAR IS NOT
什么是 HOODRADAR 所不提供的服务呢？
Research only. DYOR.
只是出于研究目的而已。事实就是如此。
THE ARCHITECTURE
建筑风格
The flow:
流程：
HOODRADAR is not a separate Telegram bot. Hermes owns the chat. HOODRADAR owns the research scripts and SOUL instructions.
HOODRADAR 并不是一个独立的 Telegram 机器人。Hermes 拥有该聊天群的权限。HOODRADAR 拥有所有的研究脚本以及 SOUL 指令。
THE MODULES
这些模块
MODULE 1: BUY THE DIP (scripts/buy_the_dip.py)
模块 1：买入下跌行情（使用 scripts/buy_the_dip.py 脚本）
Finds large Robinhood Chain tokens that dumped hard.
发现了许多急于抛售的罗宾汉链代币。
How it works:
工作原理：
python3 scripts/buy_the_dip.py --interval 1h --top 10 --min-drop 20 --min-mcap 50000 --min-liq 15000
Python3 脚本/buy_the_dip.py --interval 1 小时 --top 10 --min-drop 20 --min-mcap 50000 --min-liq 15000
Parameters:
参数：
Output: terminal brief + cron/cache/buy_the_dip.json + buy_the_dip_brief.txt
输出结果如下：终端简报 + 缓存/购买数据.json 文件 + 购买数据简报.txt 文件
Empty results are normal. If no top-10 token dumped 20%+, there is nothing to show. "No setups" is a valid answer.
结果为空是很正常的情况。如果没有任何排名前十的代币的市值下降超过 20%，那么就没有什么值得展示的内容了。“没有相关设置”就是一个合理的答案。
MODULE 2: SMART BUYS (scripts/rh_smart_buys.py)
模块 2：智能采购（脚本：scripts/rh_smart_buys.py）
Follows what high-PnL wallets are buying on Robinhood Chain.
根据那些收益较高的投资者在 Robinhood 链上购买的内容来决策。
python3 scripts/rh_smart_buys.py --minutes 15 --max-mcap 200000 --top 12
Python3 脚本：scripts/rh_smart_buys.py --minutes 15 --max-mcap 200000 --top 12

### **助手**

文章收到了。给你分析一下核心内容：

---

## 🎯 HOODRADAR 分析

### 这是啥

作者 @IBuzovskyi 用 **Hermes Agent** 做大脑，给自己搭了一套 **Robinhood Chain 链上土狗研究台**，开源了。

### 架构

```
TG消息 → Hermes Agent → 跑脚本 → Birdeye/GMGN 查数据 → 过滤噪音 → 出简报 → 推回TG
```

### 两个核心模块

| 模块 | 功能 | 关键参数 |
|------|------|---------|
| **Buy The Dip** | 找暴跌的大市值 RH 代币 | `--min-drop 20`（跌20%+）、`--min-mcap 50000` |
| **Smart Buys** | 追踪高PnL钱包在买什么 | `--minutes 15`、`--max-mcap 200000`、`--top 12` |

### 和你的区别

| 维度 | HOODRADAR | 你的策略 |
|------|-----------|---------|
| 链 | Robinhood Chain 专用 | RH Chain + Solana |
| 数据源 | Birdeye + GMGN | GMGN |
| 脑 | Hermes Agent | Hermes Agent |
| 推送 | Telegram | Telegram |
| 过滤 | 钱包PnL + 暴跌检测 | 6类过滤器 + V4策略 |
| 风控 | 无自动交易（纯研究） | 有V4策略 + 20%止损 |
| 部署方式 | 脚本 + cron | Freqtrade + 多Agent |

### 核心价值

1. **解决了 GMGN 不支持单个链过滤的问题** — RH 链的数据混在其他链里，他单独拎出来了
2. **纯研究工具，不合单** — 这点和你"不发单"的要求一致
3. **开源可改** — 换链头就能改成 Solana/Base 版
4. **架构和你很合** — 都在用 Hermes + TG 组合

### 值得学的点

- **Birdeye 钱包PnL数据** — 你目前用 GMGN 追踪聪明钱，Birdeye 这块数据可能补充你的分析
- **Buy The Dip 思路** — 找暴跌大市值代币，和你 V4 的空头策略可以互补
- **脚本架构** — 如何用 Hermes Agent 做编排而不是硬编码死循环

### 可以做的事

要不要我：
1. 直接帮你拉下来看看源码？
2. 或者分析一下他的脚本思路，看能融入你现有打狗系统的？

### **用户**

Parameters:
参数：
Important: these are high-PnL wallets from Birdeye, not "KOLs." A wallet with high PnL can still buy honeypots. The security filter catches many traps but not all risk.
重要提示：这些是高收益收益的钱包，由 Birdeye 公司提供，而非所谓的“网红博主”所拥有。虽然这些钱包能够获取高收益，但它们仍然有可能购买那些风险较高的项目。安全过滤器可以过滤掉许多陷阱，但并不能完全消除所有风险。
Real example from development: a token (
$CMX
) appeared on the high-PnL buy tape. GMGN security flagged it as honeypot/Unsafe. HOODRADAR dropped it into the DROPPED section. The filter worked. But without it, that token looked like a buy.
在开发过程中确实遇到过一个例子：有一种代币（$CMX）被纳入了高收益买入策略中。不过，GMGN 的安全部门认为这种代币可能存在漏洞，属于不安全的投资对象。HOODRADAR 将其标记为“被弃用代币”。这个过滤机制确实起到了作用。但如果没有这个过滤机制，那种代币看起来就像是一个值得买入的投资对象。
MODULE 3: WALLET BOARD (scripts/smart_wallet_tracker.py)
模块 3：钱包界面（脚本/smart_wallet_tracker.py）
Raw top-PnL wallet table with sample buys. A building block for debugging and screenshots. Not a standalone workflow.
带有示例购买的原始最高收益钱包列表。这是调试和截图操作的基础框架。并非独立的工作流程。
MODULE 4: SHORT ALERT (scripts/format_short_alert.py)
模块 4：简短警报（scripts/format_short_alert.py）
Compresses JSON artifacts into Telegram-sized text.
将 JSON 格式的数据压缩成与 Telegram 消息大小相当的文本格式。
python3 scripts/format_short_alert.py cron/cache/buy_the_dip.json --max 3
Python3 脚本：scripts/format_short_alert.py cron/cache/buy_the_dip.json --max 3
Takes the JSON output from Buy the Dip or Smart Buys and formats it into a short message you can read on your phone.
将“Buy the Dip”或“Smart Buys”功能生成的 JSON 格式数据转换为可在手机上阅读的短消息格式。
MODULE 5: BIRDEYE CLIENT (scripts/birdeye_client.py)
模块 5：BIRDEYE 客户端（脚本：scripts/birdeye_client.py）
Shared HTTP helper. Loads your Birdeye key from .env. Sends x-chain: robinhood header on every request. All scripts use this client.
共享的 HTTP 辅助功能模块。从.env 文件中加载你的 Birdeye 密钥。在每个请求中都会添加 x-chain: robinhood 头信息。所有脚本都使用这个客户端。
MODULE 6: HERMES PACK (hermes/ directory)
第六模块：HERMES 包（hermes/目录）
LOCAL WEB DASHBOARD (optional)
本地仪表板（可选）
a localhost research desk that shows the full operator view on your machine.
一个本地主机的研究界面，能够展示您机器上的完整操作员的视图。
Telegram = short alerts on your phone. Dashboard = full research view on your screen.
电报 = 在手机上接收简短的警报信息。仪表盘 = 在屏幕上查看完整的研究数据。
both are optional. both run on top of the same scripts and data.
这两个选项都是可选的。它们都运行在相同的脚本和数据之上。
python3 scripts/dashboard_server.py # open http://127.0.0.1:8787
Python 脚本：dashboard_server.py # 打开 http://127.0.0.1:8787
Windows: START_DASHBOARD.bat
Windows：START_DASHBOARD.bat
binds to 127.0.0.1 only. private research desk, not a public site.
仅绑定到 127.0.0.1 地址。这是一个私有研究用站点，并非公共网站。
Also added quick dashboard launcher to GitHub files (one click launch)
此外，我们还为 GitHub 文件添加了一个快速仪表盘启动器（只需点击一下即可启动）
THE HOME BOARD (3 columns):
业主委员会（3 列）：
TABS: Home, Hot Search, Buy the Dip, Smart Buys, Wallets.
TABS：首页、热门搜索、趁低买入、明智的投资、钱包。
Smart Buys panel shows full token CAs, the wallets behind the buys, and the DROPPED honeypots so you see what was rejected and why.
“Smart Buys”面板显示了所有被拒绝的代币地址、进行买入操作的钱包，以及被移除的“ honeypot”，这样你就可以看到哪些请求被拒绝了，以及原因是什么。
PER-TOKEN CARDS:
PER-TOKEN 卡片：
CONTROLS:
控制方式：
Refresh, Scan Wallets, Run Hot, Run Dip, Run Smart, Run All. each button triggers the underlying Python script. your Birdeye + GMGN keys + gmgn-cli must be configured.
刷新、扫描钱包、上涨时买入、下跌时卖出、智能操作、全面操作。每个按钮都会触发相应的 Python 脚本。你的 Birdeye + GMGN 密钥以及 gmgn-cli 必须已配置好。
CUSTOMIZE IT WITH HERMES AGENT:
请通过赫耳墨斯代理人来定制它吧：
the dashboard is not a black box. it is plain files:
这个控制面板并非一个黑箱而已。它实际上是由普通文件构成的。
point Hermes at your clone. describe changes in plain language:
将赫尔墨斯指针指向你的克隆体。用简单的语言描述那些变化。
"make the Home columns denser" "add a filter for mcap under $1M" "hide sparklines on Home, show them only in full tabs" "show wallet CAs inside the Hot Search cards" "swap Hot Search and Dip column order"
“让首页中的柱状图更密集一些” “添加一个过滤器，只显示市值低于 100 万美元的个股” “在首页上隐藏迷你图，仅在完整标签页中显示它们” “在热门搜索卡片中显示钱包资金状况” “交换热门搜索和小型交易股票的列顺序”
Hermes edits the HTML/CSS/JS on your fork. no closed code. no waiting for upstream releases. the dashboard is yours to reshape.
Hermes 负责编辑你分支中的 HTML/CSS/JS 代码。没有保密代码，无需等待上游版本的发布。仪表盘的设计完全可以由你自行调整。
this is not a polished SaaS. it is a first-draft operator UI designed to be changed. the sparklines are minimal. the layout is functional. everything is meant to be customized.
这不是一款经过精心设计的 SaaS 应用程序。它只是一个初稿式的操作界面，设计上允许进行后续修改。图表组件非常简洁，布局也很实用。所有元素都可以进行自定义设置。
DESIGN RULES
设计规则
Robinhood Chain only. No other chains.
仅限 Robinhood 链使用。其他链别用。
Research only. No trading private keys in this project.
仅用于研究目的。该项目不涉及任何交易用的私钥操作。
Full contract addresses always. Never only abbreviated CA as the copy target.
始终使用完整的合约地址。绝不要只使用缩写形式的“CA”作为复制目标。
Honeypots dropped, never hyped as hits.
那些被当作“蜜糖目标”的对象，从来都没有被大肆宣传为热门产品。
High-PnL does not equal KOL unless the wallet is actually tagged as one.
高收益并不等同于成为“顶级名人”，除非该钱包真的被标记为“顶级名人”才行。
Empty windows are OK. "No setups" is a valid result.
空着的窗户也是可以的。"没有设置"这一结果也是可行的。
STEP-BY-STEP SETUP
逐步安装步骤
BEFORE YOU START
在开始之前
STEP 1: INSTALL HERMES (if you don't have it)
步骤 1：安装 HERMES（如果你还没有安装的话）
Nous Portal (recommended):
Nous Portal（推荐使用）：
hermes setup --portal
赫穆斯设置——门户
docs:
hermes-agent.nousresearch.com/docs/guides/run-hermes-with-nous-portal

文档：hermes-agent.nousresearch.com/docs/guides/如何使用 Nous Portal 运行 Hermes
Desktop app: download from
hermes-agent.nousresearch.com

桌面应用：从 hermes-agent.nousresearch.com 下载
CLI:
CLI：
curl -fsSL
https://hermes-agent.nousresearch.com/install.sh
| bash
执行以下命令以下载安装脚本：curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
STEP 2: SET UP TELEGRAM GATEWAY
步骤 2：配置 Telegram 网关
hermes gateway setup
赫穆斯网关设置
Select Telegram. Paste your
@BotFather
bot token. Add your Telegram user ID.
选择 Telegram。粘贴你的@BotFather 机器人令牌。添加你的 Telegram 用户 ID。
hermes gateway
爱马仕网关
Docs:
hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram
文档：hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram
You need:
@BotFather
token, your user ID (
@userinfobot
), gateway running on the same host as the profile.
你需要以下资源：@BotFather 的令牌、你的用户 ID (@userinfobot)、以及在与个人资料相同主机上运行的网关。
STEP 3: CLONE AND INSTALL HOODRADAR
步骤 3：复制并安装 HOODRADAR


…（截断，原长 14000 字符）

### **助手**

完整文章收到了，讲得非常清楚。给你做个跟你的系统的**深度对比分析**：

---

## HOODRADAR vs 你的打狗系统

### 相同点

| 维度 | HOODRADAR | 你的系统 |
|------|-----------|---------|
| 大脑 | Hermes Agent ✅ | Hermes Agent ✅ |
| 推送 | Telegram ✅ | Telegram ✅ |
| 链 | RH Chain ✅ | RH Chain + Solana |
| 不开单 | ✅ 纯研究 | ✅ 你也是"不发命不发" |
| 数据源 | Birdeye + GMGN | GMGN |
| cron 调度 | ✅ | ✅ 你也有 cron |

### 他的优势（你可以吸收的）

**1️⃣ Birdeye 钱包PnL数据**

你目前主要靠 GMGN 跟踪聪明钱/大V。但他用 **Birdeye 的 REST API** 拿钱包PnL数据，这个是 GMGN 不支持 RH 链独立过滤的替代方案。

**2️⃣ Buy The Dip 模块**

```
python3 scripts/buy_the_dip.py --interval 1h --top 10 --min-drop 20
```

找市值大的 RH 代币暴跌20%+ → 这个思路和你 V4 空头策略是**互补**的：
- 你找做空机会
- 他找暴跌后可能反弹的机会

**3️⃣ Dashboard**

他搭了个本地网页面板（`:8787`），5个标签页，能看到被过滤掉的蜜罐。你用 TG 看简报 + 面板看完整数据。

**4️⃣ SOUL.md**

他用 Hermes Profile 的 SOUL 文件来定义 Agent 的行为规则，而不是写在脚本硬编码里。这个思路比你直接调脚本更灵活。

### 他的劣势（你比他强的地方）

| 维度 | HOODRADAR | 你 |
|------|-----------|-----|
| 过滤器 | 只依赖 GMGN security + Birdeye PnL | **6类过滤器**（链创始人/KOL/政治/科技等）+ **评分系统** |
| 策略深度 | Buy The Dip + Smart Buys | **V4 多周期搜索 + 6均线系统** |
| 风控 | 蜜罐过滤，无仓位管理 | **严格20%止损 + 仓位1-2% + 绝不补仓** |
| 多链 | RH Chain 专用 | RH + Solana |
| 评分 | 无评分，只看数据 | **0-100分复合评分系统** |

---

### 建议：抄什么

建议从他项目里拿这几块：

```bash
# 1. 拉下来
git clone https://github.com/YAN-XBT/HOODRADAR.git

# 2. 抄 Birdeye 客户端（你缺这个数据源）
#    scripts/birdeye_client.py
#    scripts/rh_smart_buys.py（Birdeye 钱包PnL部分）

# 3. 抄 Buy The Dip 逻辑（跟你 V4 空头互补）
#    scripts/buy_the_dip.py

# 4. 抄 Dashboard（可选，挺实用）
#    scripts/dashboard_server.py

# 5. 抄 SOUL.md 的 Agent 编排思路（改造你的 cron）
#    hermes/SOUL.md
```

**不抄的：**
- 过滤器（你的 6 类过滤器比他的 GMGN security 更细）
- 评分系统（你的 0-100 分比他好）
- 风控体系（你的 20% 止损已经验证了）

要不要我帮你拉下来，把 Birdeye 客户端和 Buy The Dip 模块提取出来，集成到你现有的打狗管道里？
