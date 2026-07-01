# Codex 隔离通道

## 描述
Kanban 工作流中为 Codex CLI 设置的专用隔离通道。将 Codex 任务独立运行在沙箱环境中，避免与其他 Worker 相互干扰。

## 用途
- 隔离运行 Codex CLI 任务
- 防止 Codex 生成的代码污染主工作流
- 独立管理 Codex 的 token 消耗和运行超时
- 安全执行未经审查的 AI 生成代码

## 配置示例
```yaml
# codex-lane.yaml
codex_lane:
  enabled: true
  sandbox: docker
  image: codex-sandbox:latest
  timeout: 600
  max_tokens: 100000
  output_dir: ./codex-output
```

## 使用流程
1. 编排器识别适合 Codex 的子任务
2. 将任务路由到 Codex 隔离通道
3. Codex 在沙箱中独立执行
4. 结果经审核后合并回主工作流

## 适用场景
- 大规模代码生成
- 不熟悉的语言或框架原型
- 需要隔离测试的代码片段
