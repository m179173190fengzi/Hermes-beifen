#!/bin/bash
# 延迟 15 秒后重启网关：让当前回复先送达，再切换进程
sleep 15
systemctl --user restart hermes-gateway
