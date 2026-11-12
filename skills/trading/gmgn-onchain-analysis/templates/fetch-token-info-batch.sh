#!/bin/bash
# Batch token info fetch — 批量抓取 token info 供叙事核验/新币 creation_timestamp 核验。
# 用法：编辑下方 ADDR 映射（label -> "chain|address"），然后 `bash fetch-token-info-batch.sh`。
# ⚠️⚠️ chain 列必须用 CLI 全称：robinhood（写 `rh` 会整批 RH 条目 FAIL/空文件——08-17 实测踩坑）。
#    整链条目全挂先查链名，零星单条失败才是瞬时抖动（单独重跑即恢复）。
# 特性：顺序循环（勿用 & 并行，会被安全拦截）+ retry-once + `-s` 空文件检查；
#       JOB=PID 前缀唯一化输出文件名（ti_<JOB>_<label>.json），防 /tmp 跨运行残留混入。
# 配套解析：python3 parse-token-info-batch.py <JOB>（JOB 取脚本末尾打印值）。
set -u
export HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890
JOB="alpha_$$"
declare -A ADDR
# 示例（每行一个候选：label 用 token_链 命名）：
# ADDR[cashcat_rh]="robinhood|0x020bfc650a365f8bb26819deaabf3e21291018b4"
# ADDR[gpu_bsc]="bsc|0x9dbef6496134c151b9f9855cc5a1ee77f0324444"
# ADDR[doom_sol]="sol|Gymbmn9wwMKe4NnmVceyyfpncp9arbwPfSdBsyY9pump"
for k in "${!ADDR[@]}"; do
  IFS='|' read -r ch addr <<< "${ADDR[$k]}"
  gmgn-cli token info --chain "$ch" --address "$addr" --raw > "/tmp/ti_${JOB}_${k}.json" 2>/dev/null
  if [ ! -s "/tmp/ti_${JOB}_${k}.json" ]; then
    sleep 2
    gmgn-cli token info --chain "$ch" --address "$addr" --raw > "/tmp/ti_${JOB}_${k}.json" 2>/dev/null
  fi
  if [ -s "/tmp/ti_${JOB}_${k}.json" ]; then
    echo "$k OK $(wc -c < "/tmp/ti_${JOB}_${k}.json") bytes"
  else
    echo "$k FAIL"
  fi
done
echo "JOB=$JOB"
