v4.py 策略代码路径: ~/ft_userdata/user_data/strategies/v4.py
类名: V4Strategy

核心变化历程:
1. 最初: 多级均线密集+多空都做 → 亏
2. 加日线趋势过滤 → 略好
3. 做空改空头排列+流畅下跌 → 开始盈利
4. 熊市只做空 → 大幅改善
5. 4h级别 → Sharpe 3.43, +9.79% (最佳)
6. 看大做小(从大到小逐级搜索) → 逻辑正确但1m不赚钱
7. 最终版: 6条均线固定 + 看大做小跨周期

关键修复:
- merge_informative_pair后缀bug (columns get _{tf} suffix)
- populate_indicators bool类型冲突 (can't set enter_short to bool then assign tuple)
- 看大做小理解修正: 从大到小逐级搜索, 不是固定组合
