#!/bin/bash
# 批量 token security 抓取模板 — 11项评分 ②③④ 项数据源（LP锁定销毁/owner renounced/tax/honeypot）
# 用法：改 ADDR 映射（label→chain|address），bash 运行；输出 /tmp/ts_<JOB>_<label>.json
# 解析字段：is_honeypot / is_renounced / renounced_mint / renounced_freeze_account /
#          buy_tax / sell_tax / burn_status / lock_summary.is_locked / lock_detail[].is_blackhole
# ⚠️ 一律带代理前缀；失败条目 sleep 2 重试一次（瞬时抖动单独重跑即恢复，整链全挂先查链名 flag）
# ⚠️ security --raw 输出 ~750B/条（compact JSON，顶层直接是字段，无 code/data 包裹——与 token info 同构）
# ⚠️ EVM 无铸币/冻结概念：renounced_mint/freeze 恒 false，11项评分用 is_renounced 替代
JOB=$$
echo "JOB=$JOB"
declare -A ADDR=(
  [pons_rh]="robinhood|0x39dbed3a2bd333467115de45665cc57f813c4571"
  [clan_rh]="robinhood|0xcebc0cfbc5dd0893a9e3b9d0f75b211ddf5934a0"
  [bnbcat_bsc]="bsc|0x3efbfff95576e1d23cf6ead0acd2e73f4d6a7777"
)
for label in "${!ADDR[@]}"; do
  IFS='|' read -r ch addr <<< "${ADDR[$label]}"
  out="/tmp/ts_${JOB}_${label}.json"
  HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 gmgn-cli token security --chain "$ch" --address "$addr" --raw > "$out" 2>/dev/null
  if [ ! -s "$out" ]; then
    sleep 2
    HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890 gmgn-cli token security --chain "$ch" --address "$addr" --raw > "$out" 2>/dev/null
  fi
  sz=$(wc -c < "$out" 2>/dev/null || echo 0)
  echo "$label: $sz bytes"
done
