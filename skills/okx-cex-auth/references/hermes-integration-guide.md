# OKX Agent Trade Kit + Hermes 集成指南

## 技能生态概览

OKX ATK 提供 **11 个 Hermes 技能**，与现有的 `gmgn-*` 链上技能形成互补：

| 类别 | ATK 技能 | 用途 | 补充 |
|------|---------|------|------|
| **市场数据** | `okx-cex-market` | 行情/深度/K线/资金费率/OI/指数 | 补充GMGN链上数据 |
| **情绪** | `okx-sentiment-tracker` | 3万+KOL情绪聚合 | 替代手动推特监控 |
| **聪明钱** | `okx-cex-smartmoney` | OKX星球交易员信号 | 补充GMGN Smart Money |
| **交易** | `okx-cex-trade` | 现货/合约/期权/算法单 | GMGN只管链上swap |
| **资产** | `okx-cex-portfolio` | 余额/持仓/账单/费率 | 补充钱包维度 |
| **机器人** | `okx-cex-bot` | 网格/马丁格尔/定投 | 自动策略执行 |
| **赚币** | `okx-cex-earn` | 简单/链上/双币赢 | 零钱管理 |
| **猎手** | `earn-hunter` | 7×24利率监控提醒 | 自动赚币通知 |
| **事件** | `okx-outcomes` | 世界杯预测市场 | 新品类 |
| **认证** | `okx-cex-auth` | OAuth一键授权 | 连接入口 |
| **多角色** | `okx-cex-skill-mp` | 多persona路由 | 高级编排 |

## 安装方式

### 方式 A：npx skills add（交互式）

```bash
cd ~/.hermes/skills
npx skills add okx/agent-skills
```

### 方式 B：直接克隆（绕过交互选择，装全部）

```bash
cd /tmp
git clone --depth 1 https://github.com/okx/agent-skills.git
# 复制所有11个技能 + _shared
for d in /tmp/agent-skills/skills/*/; do cp -r "$d" ~/.hermes/skills/; done
cp -r /tmp/agent-skills/skills/_shared ~/.hermes/skills/
```

### CLI

```bash
npm i -g @okx_ai/okx-trade-cli
```

## 认证流程

使用 OAuth Device Flow（无需 API Key）：

1. `okx config show --json` 和 `okx auth status --json` 检查状态
2. 确认无 `api_key` 配置
3. 用户选择站点（global/eea/us/tr）
4. `okx auth login --manual --site <site>` → 获取验证URL + 验证码
5. 用户在浏览器打开URL并输入验证码授权
6. `okx auth status --json` 确认 `logged_in`

## 与已有系统的协作

```
用户现有体系（GMGN）           ATK 补充
──────────────────────────────────────────
GMGN扫链 → 筛选meme币    ⏪ okx-cex-market → CEX数据验证
推特+KOL监控              ⏪ okx-sentiment-tracker → 量化情绪
GMGN Smart Money          ⏪ okx-cex-smartmoney → CEX聪明钱
手动挂单                  ⏪ okx-cex-trade → 一句话交易
无                        ⏪ okx-cex-earn → 闲钱理财
```

## 权限说明

- **市场数据**（`okx-cex-market`）无需认证，公开API
- **交易/资产**（`trade/portfolio/earn/bot`）需OAuth授权
- 权限分级：`live:read`（只读）| `live:trade`（交易）| `live:earn`（赚币）
- 7天无活动自动过期
- 禁止提币（ATK无此能力）

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `okx auth login` 返回 `api_key_configured` | 已有API Key配置 | 删掉或切换到无API Key的profile |
| `okx config init` 卡住 | 这是API Key向导，不是OAuth | 用 `okx auth login --manual` 代替 |
| market数据可用但trade不行 | 市场数据无需认证 | 先走OAuth授权 |
