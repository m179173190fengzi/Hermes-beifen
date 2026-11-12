# 公众号排版组件库 —— 康奈尔笔记（Cornell Notes）

> **使用说明**：本组件库为「康奈尔笔记」主题（康奈尔笔记法视觉化），所有组件使用**内联样式**，可直接复制粘贴到微信公众号编辑器。
>
> **设计风格**：马卡龙配色（蓝 `#5B9BD5` / 绿 `#70AD47` / 橙 `#ED7D31`）+ 白底 + 圆角模块 + 浅色分区。模仿纸质康奈尔笔记布局：顶部标题区（科目/日期/课题）、左侧线索栏（提问）、右侧笔记栏（记录）、底部总结栏（回顾）、右下角一句话记忆。适合数据复盘、学习总结、知识整理类文章。
>
> **公众号平台限制须知**：
> - ❌ 不支持 `<style>`/`<script>`、CSS class/id/`<div>`、`position:fixed/absolute/sticky`、`float`、`@media`/`@keyframes`、`display:grid`、CSS 变量
> - ✅ 支持内联 `style`、`display:flex`（有限）、`border-radius`、`box-shadow`、`<section>/<p>/<span>/<strong>/<img>` 等基础标签
> - 所有文字节点用 `<span leaf="">文字</span>` 包裹（否则粘贴后样式丢失）

## 设计变量速查表

```
主色蓝：    #5B9BD5（标题区/线索栏/模块01）
主色绿：    #70AD47（总结栏/模块02）
主色橙：    #ED7D31（一句话记忆/风险/模块03）
浅蓝底：    #EAF2FA（线索栏背景/蓝色数据卡）
浅绿底：    #EAF4EC（总结栏背景/绿色数据卡）
浅橙底：    #FDF0E6（记忆卡/橙色数据卡/风险块）
正文色：    #444444
深字色：    #333333
辅助灰：    #888888 / #666666
白底：      #FFFFFF
正文字号：  13px
小字号：    11-12px
行高：      1.7
最大宽度：  677px
圆角：      8-10px
```

字体栈：`-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif`

## 组件 C1 全局容器

```html
<section style="max-width:677px;margin:0 auto;background:#FFFFFF;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#444444;line-height:1.7;letter-spacing:0.3px;overflow-x:hidden;">
```

## 组件 C2 顶部标题区（蓝底 + 科目日期 + 课题白卡）

> 布局：左「CORNELL NOTES + 康奈尔笔记」大标题，右「日期/科目」，下方白色课题卡。圆角上10px。

```html
<section style="background:#5B9BD5;border-radius:10px 10px 0 0;padding:18px 20px 14px;margin:8px 8px 0;">
  <section style="display:flex;justify-content:space-between;align-items:flex-end;">
    <section>
      <p style="font-size:11px;color:#FFFFFF;opacity:0.85;margin:0 0 4px;letter-spacing:2px;font-weight:500;"><span leaf="">CORNELL NOTES</span></p>
      <p style="font-size:22px;font-weight:800;color:#FFFFFF;margin:0;letter-spacing:1px;"><span leaf="">康奈尔笔记</span></p>
    </section>
    <section style="text-align:right;">
      <p style="font-size:11px;color:#FFFFFF;margin:0 0 2px;"><span leaf="">日期 {YYYY-MM-DD}</span></p>
      <p style="font-size:11px;color:#FFFFFF;margin:0;"><span leaf="">科目 {科目名}</span></p>
    </section>
  </section>
  <section style="background:#FFFFFF;border-radius:6px;padding:8px 14px;margin-top:10px;">
    <p style="font-size:14px;font-weight:700;color:#5B9BD5;margin:0;"><span leaf="">课题：{课题内容}</span></p>
  </section>
</section>
```

## 组件 C3 主体两栏容器（线索栏 + 笔记栏）

```html
<section style="display:flex;margin:0 8px;">
  <!-- 左侧线索栏 C4 -->
  <!-- 右侧笔记栏 C5 -->
</section>
```

## 组件 C4 左侧线索栏·提问（28% 宽，浅蓝底）

> 放置 6~10 个与主题相关的问题，编号圆点排列。圆角左下10px。

```html
<section style="width:27%;background:#EAF2FA;border-radius:0 0 0 10px;padding:16px 12px;margin-right:0;">
  <p style="font-size:12px;font-weight:800;color:#5B9BD5;margin:0 0 12px;letter-spacing:1px;border-bottom:2px solid #5B9BD5;padding-bottom:6px;"><span leaf="">线索栏 · 提问</span></p>
  <p style="margin:0 0 12px;font-size:13px;line-height:1.6;color:#3B6DA0;">
    <span style="display:inline-block;background:#5B9BD5;color:#FFFFFF;font-size:10px;font-weight:700;width:16px;height:16px;line-height:16px;text-align:center;border-radius:50%;margin-right:6px;"><span leaf="">1</span></span>
    <span leaf="">{问题一}</span>
  </p>
  <!-- 重复 N 个问题 -->
</section>
```

## 组件 C5 右侧笔记栏·记录（72% 宽，白底）

> 知识点模块化排版，每个知识点一个圆角模块（左4px色条 + 标题 + 内容），模块间12px间距。圆角右下10px。

```html
<section style="width:73%;background:#FFFFFF;padding:16px 14px;">
  <p style="font-size:12px;font-weight:800;color:#333333;margin:0 0 12px;letter-spacing:1px;border-bottom:2px solid #70AD47;padding-bottom:6px;"><span leaf="">笔记栏 · 记录</span></p>

  <!-- 模块（组件 C6，重复多个） -->
</section>
```

## 组件 C6 知识模块卡

> 左4px色条（可换蓝/绿/橙）+ 圆角8px + 图标标题。内容可含数据卡、列表、风险块。

```html
<section style="border:1px solid #EAF2FA;border-left:4px solid #5B9BD5;border-radius:8px;padding:12px 14px;margin:0 0 12px;background:#FFFFFF;">
  <p style="font-size:13px;font-weight:800;color:#5B9BD5;margin:0 0 8px;"><span leaf="">📊 01 模块标题</span></p>
  <!-- 模块内容 -->
</section>
```

## 组件 C7 三色数据卡（横排）

> 蓝/绿/橙三色浅底数据卡并排，大号数字 + 小标签。用于TVL、关键指标对比。

```html
<section style="display:flex;margin:0 0 6px;">
  <section style="flex:1;background:#EAF2FA;border-radius:6px;padding:10px 8px;text-align:center;margin-right:6px;">
    <p style="font-size:17px;font-weight:800;color:#5B9BD5;margin:0 0 2px;line-height:1.2;"><span leaf="">{数值}</span></p>
    <p style="font-size:10px;color:#888888;margin:0;"><span leaf="">{标签}</span></p>
  </section>
  <section style="flex:1;background:#EAF4EC;border-radius:6px;padding:10px 8px;text-align:center;margin-right:6px;">
    <p style="font-size:17px;font-weight:800;color:#70AD47;margin:0 0 2px;line-height:1.2;"><span leaf="">{数值}</span></p>
    <p style="font-size:10px;color:#888888;margin:0;"><span leaf="">{标签}</span></p>
  </section>
  <section style="flex:1;background:#FDF0E6;border-radius:6px;padding:10px 8px;text-align:center;">
    <p style="font-size:17px;font-weight:800;color:#ED7D31;margin:0 0 2px;line-height:1.2;"><span leaf="">{数值}</span></p>
    <p style="font-size:10px;color:#888888;margin:0;"><span leaf="">{标签}</span></p>
  </section>
</section>
```

## 组件 C8 标的信息行（优质标的分条）

> 每条标的：色字标题行 + 说明行。标题色可循环蓝/绿/橙。

```html
<section style="margin:0 0 6px;">
  <p style="font-size:12px;font-weight:700;color:#5B9BD5;margin:0 0 3px;"><span leaf="">#1 {SYMBOL}（{CHAIN}）{评分}/75</span></p>
  <p style="font-size:12px;color:#666666;margin:0 0 6px;line-height:1.6;"><span leaf="">{叙事一句话} · 6h {±X%} · 持币{X} · 聪明钱{X} · </span><strong style="color:#70AD47;"><span leaf="">{亮点}</span></strong></p>
</section>
```

## 组件 C9 橙色风险/达标块

> 浅橙底圆角块，用于风险预警、筛选达标、记忆卡等强调内容。

```html
<section style="background:#FDF0E6;border-radius:6px;padding:10px 12px;margin:0 0 6px;">
  <p style="font-size:12px;font-weight:700;color:#ED7D31;margin:0 0 2px;"><span leaf="">{标题}</span></p>
  <p style="font-size:12px;color:#666666;margin:0;line-height:1.6;"><span leaf="">{内容}</span></p>
</section>
```

## 组件 C10 底部总结栏·回顾（浅绿底）

> 2~5句总结 + 右下角「💡 一句话记忆」橙色记忆卡。圆角下10px。

```html
<section style="background:#EAF4EC;border-radius:0 0 10px 10px;padding:16px 20px;margin:0 8px 8px;">
  <p style="font-size:12px;font-weight:800;color:#70AD47;margin:0 0 8px;letter-spacing:1px;"><span leaf="">总结栏 · 回顾</span></p>
  <p style="font-size:13px;color:#444444;margin:0 0 6px;line-height:1.7;"><span leaf="">{总结句1}</span></p>
  <p style="font-size:13px;color:#444444;margin:0 0 6px;line-height:1.7;"><span leaf="">{总结句2}</span></p>
  <p style="font-size:13px;color:#444444;margin:0;line-height:1.7;"><span leaf="">{总结句3}</span></p>
  <section style="background:#FDF0E6;border-radius:6px;padding:10px 12px;margin-top:10px;">
    <p style="font-size:11px;font-weight:700;color:#ED7D31;margin:0 0 2px;letter-spacing:1px;"><span leaf="">💡 一句话记忆</span></p>
    <p style="font-size:13px;font-weight:700;color:#C05A1B;margin:0;line-height:1.6;"><span leaf="">{最易记忆的一句话}</span></p>
  </section>
</section>
```

## 完整文章模板骨架

```html
<section style="max-width:677px;margin:0 auto;background:#FFFFFF;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#444444;line-height:1.7;letter-spacing:0.3px;overflow-x:hidden;">

  <!-- 1. 顶部标题区（C2） -->

  <!-- 2. 主体两栏（C3）：左线索栏 C4（6-10个问题）+ 右笔记栏 C5（4-6个知识模块 C6） -->

  <!-- 3. 底部总结栏（C10）：2-5句总结 + 一句话记忆 -->

</section>
```

**骨架铁律**：顶部标题区在最前；两栏并列（线索栏左27% / 笔记栏右73%）；总结栏在最后，右下角必有「一句话记忆」橙色卡。一篇只有一个总结栏。

## 文章类型 → 组件组合配方

| 文章类型 | 核心组件组合 | 点缀组件 |
|---|---|---|
| 数据复盘/报告 | C6 模块 + C7 三色数据卡 + C8 标的信息行 | C9 风险块、C4 线索问题 |
| 学习总结/知识整理 | C6 模块 + C7 数据卡 + C4 线索问题 | C8 信息行、C9 达标块 |
| 教程/方法论 | C6 模块（步骤化）+ C4 线索问题 | C8 信息行、C9 提示块 |
| 观点/分析 | C6 模块 + C8 信息行 | C9 风险块、C7 数据卡 |

## Markdown → 康奈尔笔记 映射规则

| Markdown 元素 | 对应组件 | 说明 |
|---|---|---|
| `# 标题` | 不使用 | 公众号标题在平台设置 |
| 文章开头 `> 引言` | C2 顶部标题区 | 课题卡承载主题 |
| `## 章节标题` | C6 模块标题 | 编号 01/02… 图标+色条 |
| `### 子标题` | C6 内小标题 | 色字加粗 |
| 普通段落 | 13px 正文 | 放在 C6 模块内 |
| `**加粗**` | `strong` 深色 | 亮点用绿 `#70AD47` |
| 数据/指标 | C7 三色数据卡 | 大号数字+小标签 |
| 标的分条 | C8 信息行 | 色字标题+说明行 |
| 风险/注意 | C9 橙色块 | 浅橙底 |
| 并列要点 | 12px 行 + 圆点 | 模块内列表 |
| 文末总结 | C10 总结栏 | 2-5句 + 一句话记忆 |
