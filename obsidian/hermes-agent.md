# Hermes Agent

## 描述
Nous Research 开发的智能 AI 代理框架。支持多平台部署（Telegram、Discord、CLI），可扩展技能、插件和记忆系统。

## 用途
- 配置和自定义 AI 代理行为
- 开发自定义技能（Skills）和插件（Plugins）
- 管理代理记忆和知识库
- 多代理协作编排

## 配置示例
```bash
# 查看当前配置
hermes config show

# 设置默认模型
hermes config set model deepseek-v4-flash

# 安装技能
hermes skill install git

# 查看可用技能
hermes skill list
```

## 目录结构
```
~/.hermes/
├── profiles/
│   └── default/
│       ├── skills/     # 自定义技能
│       ├── plugins/    # 插件
│       ├── cron/       # 定时任务
│       └── memories/   # 记忆文件
```
