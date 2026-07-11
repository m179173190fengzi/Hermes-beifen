# Blockscout 链上验证操作记录

> 2026-07-10 实测有效的 Robinhood Chain 币的 Blockscout 访问方法。

## 查看代币总览

用 blockscout 的 **Token 页面**（不是 Address 页面）：

```
GET /token/<ADDRESS>
Example: /token/0x6365fd27ddefc42f50895994b67b04fab5f08d5e
```

此页面显示：
- 总供应量（Total supply）
- 持仓人数（Holders）
- 转账次数（Transfers）
- Decimals

## 查看持有人分布

```
GET /token/<ADDRESS>?tab=holders
```

**注意：** 持有人列表可能 JS 渲染后才显示，尽量直接从页面文本提取。

## 查看创造者地址

创造者在 **Address 页面** 显示：

```
GET /address/<ADDRESS>
```

页面显示：
- Creator: 创建者地址 + 创建交易哈希
- 余额
- Token 数量

## 已验证案例：$1 (0x6365fd27ddefc42f50895994b67b04fab5f08d5e)

| 检查项 | 结果 | 方式 |
|:-------|:-----|:-----|
| 总供应量 | 1,000,000,000 (10亿) | Token页面 |
| 持仓人数 | 2,364 | Token页面 |
| 转账次数 | 62,344 | Token页面 |
| 创造者 | 0xD9...FCcB | Address页面 |
| 部署交易 | 0x29...33b9 ✅ | Address页面 |

## 注意事项

- Blockscout 有时会返回空数据或加载失败 — 重试一次即可
- Robinhood Chain 的 block explorer 速度一般，等待 2-3 秒让页面完全渲染
- 用`browser_evaluate`获取`document.body.innerText`即可提取数据，不需要DOM解析
- 合约验证状态在 Robinhood 链上通常为"未验证"（链太新），这不一定是rug信号
