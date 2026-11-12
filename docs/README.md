# Hermes 会话提炼与技能库

本目录保存**可复用的结论**，不含原始对话、持仓明细、钱包地址或任何密钥。

## 目录

| 文件 | 内容 |
|---|---|
| [session-digests/2026-11-12-digest-part1.md](session-digests/2026-11-12-digest-part1.md) | Hermes 升级 v0.19→v0.23、配置迁移坑、Telegram 自愈脚本 bug、叙事扩散计数器设计 |
| [session-digests/2026-11-12-digest-part2.md](session-digests/2026-11-12-digest-part2.md) | CA 体检四段法、钱包行为审计、打提前量的拆解与书单、市场状态判断框架 |

## 相关脚本

都在 `~/.hermes/scripts/`，全部**零 token 消耗**（纯本地执行）：

| 脚本 | 用途 |
|---|---|
| `narrative_radar.py` | 叙事扩散计数，`--brief` 输出 3 行 |
| `wallet_audit.py` | 钱包行为审计（胜率/持仓时长/补仓/金额分布） |
| `ma_watch.py` | 六均线五级信号（含「第一次回踩 SMA20 不破」） |
| `ma_state.py` | 任意 OKX 标的的多周期均线状态 |
| `tg_heal.sh` | Telegram 通道自愈（水位线 + 冷却 + 静默） |
| `secret_scan.py` | 提交前密钥扫描 |
| `redact_keys.py` | 提交前密钥脱敏 |

## 提交前必做

```bash
python3 ~/.hermes/scripts/secret_scan.py
```

命中即停，先脱敏再提交。本仓库的 `.gitignore` 已排除：

```
.env  state.db  state.db-wal  state.db-shm  kanban.db
```

**注意**：本仓库为公开仓库，任何内容推送前请确认可公开。
