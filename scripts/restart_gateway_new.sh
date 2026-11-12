#!/bin/bash
# 一次性：把网关切到新安装（v0.23.0 源码安装）
systemctl --user restart hermes-gateway
sleep 3
systemctl --user is-active hermes-gateway
