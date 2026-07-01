# Kanban 工作节点

## 描述
Kanban 工作流中的执行节点（Worker），负责接收编排器分配的子任务并独立完成。每个 Worker 专注于单一任务，完成后汇报结果。

## 用途
- 执行编排器分解出的具体子任务
- 独立完成编码、测试、文档等专项工作
- 向编排器汇报进度和结果

## 工作方式
- 每个 Worker 拥有独立的上下文环境
- 接收来自编排器的任务描述和约束
- 完成任务后返回结果或错误信息
- 支持并行执行多个 Worker

## 配置示例
```yaml
# kanban-worker.yaml
worker:
  model: deepseek-v4-flash
  max_iterations: 10
  timeout: 300
  output_dir: ./output
```

## 使用示例
```
编排器 → Worker: "创建 User 模型，包含 id, name, email 字段"
Worker → 编排器: "已完成，文件位于 src/models/user.py"
```
