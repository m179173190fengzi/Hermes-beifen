#!/usr/bin/env python3
"""
V4 密集→发散框架 回测脚本模板
用 ccxt + pandas 做本地回测，免依赖Vibe-Trading

使用方法:
  1. 修改回测参数（方向、时间范围、入场条件）
  2. python v4-backtest-xxx.py
  3. 分析输出结果

数据源: Binance CCXT (公开数据，免Key)
代理: 如在国内需设置 proxy
"""
import ccxt, pandas as pd, numpy as np

# ============================================================
# 配置
# ============================================================
TIMEFRAME = '4h'          # 周期
START = '2022-01-01'      # 回测起始
END = '2024-12-31'        # 回测结束
DATA_START = '2021-01-01' # 数据拉取起始（需预热均线）
DIRECTION = 'long'        # 'long' | 'short' | 'both'

CAPITAL = 100000.0        # 初始本金
RISK_PCT = 0.015          # 单笔风险

# 代理（国内需要）
PROXY = 'http://127.0.0.1:7890'

ex = ccxt.binance({
    'enableRateLimit': True,
    'proxies': {'http': PROXY, 'https': PROXY}
})

# ============================================================
# 数据下载
# ============================================================
def fetch_ohlcv(symbol, tf, since_str, until_str):
    all_c = []
    cur = ex.parse8601(since_str + 'T00:00:00Z')
    end = ex.parse8601(until_str + 'T23:59:59Z')
    while cur < end:
        c = ex.fetch_ohlcv(symbol, tf, since=cur, limit=1000)
        if not c: break
        all_c.extend(c)
        cur = c[-1][0] + 1
    df = pd.DataFrame(all_c, columns=['ts','o','h','l','c','v'])
    df['date'] = pd.to_datetime(df['ts'], unit='ms')
    df = df.set_index('date').sort_index()
    return df[~df.index.duplicated(keep='first')]

print(f"下载 {TIMEFRAME} 数据...")
df = fetch_ohlcv('BTC/USDT', TIMEFRAME, DATA_START, END)

# ============================================================
# 日线数据（用于大周期方向过滤）
# ============================================================
print("下载 1d 数据（方向过滤用）...")
df_d = fetch_ohlcv('BTC/USDT', '1d', DATA_START, END)
df_d['MA120'] = df_d['c'].rolling(120).mean()

# 价格 vs MA120 位置 (True=牛市区, False=熊市区)
df_d['bull_zone'] = df_d['c'] > df_d['MA120']

# 前向连接到4H
df['daily_bull_zone'] = np.nan
for i in range(len(df)):
    daily = df_d[df_d.index <= df.index[i]]
    if len(daily) > 0:
        df.iloc[i, df.columns.get_loc('daily_bull_zone')] = daily.iloc[-1]['bull_zone']

# ============================================================
# 指标计算
# ============================================================
def sma(s, p): return s.rolling(p).mean()
def ema(s, p): return s.ewm(span=p, adjust=False).mean()

df['SMA20'] = sma(df['c'], 20)
df['SMA60'] = sma(df['c'], 60)
df['SMA120'] = sma(df['c'], 120)
df['EMA20'] = ema(df['c'], 20)
df['EMA60'] = ema(df['c'], 60)
df['EMA120'] = ema(df['c'], 120)

def is_converged(row):
    """6条均线价差<3% = 均线密集"""
    vals = [row[k] for k in ['SMA20','SMA60','SMA120','EMA20','EMA60','EMA120']]
    vals = [v for v in vals if not np.isnan(v)]
    if len(vals) < 4: return False
    return (max(vals)-min(vals))/min(vals)*100 < 3.0

def min_ma(row):
    vals = [row[k] for k in ['SMA20','SMA60','SMA120','EMA20','EMA60','EMA120']]
    return min([v for v in vals if not np.isnan(v)])

def max_ma(row):
    vals = [row[k] for k in ['SMA20','SMA60','SMA120','EMA20','EMA60','EMA120']]
    return max([v for v in vals if not np.isnan(v)])

def ma20_val(row):
    vals = [row['SMA20'], row['EMA20']]
    vals = [v for v in vals if not np.isnan(v)]
    return sum(vals)/len(vals) if vals else None

# ============================================================
# 回测引擎
# ============================================================
start_bt = pd.Timestamp(START)
end_bt = pd.Timestamp(END)

capital = CAPITAL
position = 0.0
trades = []
in_pos = False
entry_px = 0.0
peak = capital
max_dd = 0.0
entry_method = ""

for i in range(150, len(df)):
    row = df.iloc[i]
    d = row.name
    if d < start_bt or d > end_bt: continue
    
    px = float(row['c'])
    eq = capital + position * px if DIRECTION == 'long' else capital - position * (px - entry_px if in_pos else 0)
    if in_pos:
        if DIRECTION == 'long':
            eq = capital + position * px
        else:
            eq = capital + position * (entry_px - px)
    
    peak = max(peak, eq)
    dd = (peak - eq) / peak * 100
    max_dd = max(max_dd, dd)
    
    converged = is_converged(row)
    mamin = min_ma(row)
    mamax = max_ma(row)
    ma20 = ma20_val(row)
    bull_zone = row.get('daily_bull_zone', None)
    
    # === 市场方向过滤 ===
    if DIRECTION == 'long' and bull_zone is not None and not bull_zone:
        continue  # 熊市区域不做多
    if DIRECTION == 'short' and bull_zone is not None and bull_zone:
        continue  # 牛市区域不做空
    
    if not in_pos:
        # ① 密集突破入场
        if converged:
            if DIRECTION == 'long' and px > mamax:  # 向上突破做多
                recent = df.iloc[max(0,i-3):i+1]
                above = sum(1 for j in range(len(recent)) if recent.iloc[j]['c'] > max_ma(recent.iloc[j]))
                if above >= 2:
                    entry_px = px
                    risk = capital * RISK_PCT
                    stop_px = mamin
                    stop_dist = (entry_px - stop_px) / entry_px
                    if stop_dist > 0 and stop_dist < 0.05:
                        position = risk / (entry_px - stop_px)
                        in_pos = True
                        entry_method = 'breakout'
                        tp_px = entry_px * (1.06 if DIRECTION == 'long' else 0.94)
            
            elif DIRECTION == 'short' and px < mamin:  # 向下突破做空
                recent = df.iloc[max(0,i-3):i+1]
                below = sum(1 for j in range(len(recent)) if recent.iloc[j]['c'] < min_ma(recent.iloc[j]))
                if below >= 2:
                    entry_px = px
                    risk = capital * RISK_PCT
                    stop_px = mamax
                    stop_dist = (stop_px - entry_px) / entry_px
                    if stop_dist > 0 and stop_dist < 0.05:
                        position = risk / (entry_px - stop_px)
                        in_pos = True
                        entry_method = 'breakout'
                        tp_px = entry_px * 0.94
        
        # ② 回踩MA20入场
        if not in_pos and ma20:
            if DIRECTION == 'long' and px > ma20:  # 回踩做多
                recent = df.iloc[max(0,i-20):i+1]
                prev_higher = recent.iloc[:-1]['c'].max() > px * 1.01
                near_ma20 = (px - ma20) / ma20 < 0.015
                if prev_higher and near_ma20:
                    entry_px = px
                    risk = capital * RISK_PCT
                    stop_px = ma20 * 0.99
                    stop_dist = (entry_px - stop_px) / entry_px
                    if stop_dist > 0 and stop_dist < 0.03:
                        position = risk / (entry_px - stop_px)
                        in_pos = True
                        entry_method = 'pullback'
                        tp_px = entry_px * 1.05
            
            elif DIRECTION == 'short' and px < ma20:  # 反弹做空
                recent = df.iloc[max(0,i-20):i+1]
                prev_lower = recent.iloc[:-1]['c'].min() < px * 0.99
                near_ma20 = (ma20 - px) / ma20 < 0.015
                if prev_lower and near_ma20:
                    entry_px = px
                    risk = capital * RISK_PCT
                    stop_px = ma20 * 1.01
                    stop_dist = (stop_px - entry_px) / entry_px
                    if stop_dist > 0 and stop_dist < 0.03:
                        position = risk / (entry_px - stop_px)
                        in_pos = True
                        entry_method = 'pullback'
                        tp_px = entry_px * 0.95
    
    if in_pos:
        exit_px = px
        reason = None
        
        if entry_method == 'breakout':
            if DIRECTION == 'long' and px <= mamin:
                reason = 'back_to_converge'
            elif DIRECTION == 'short' and px >= mamax:
                reason = 'back_to_converge'
            elif (DIRECTION == 'long' and px >= tp_px) or (DIRECTION == 'short' and px <= tp_px):
                reason, exit_px = 'tp', tp_px
        
        elif entry_method == 'pullback':
            if DIRECTION == 'long' and ma20 and px <= ma20 * 0.99:
                reason = 'below_ma20'
            elif DIRECTION == 'short' and ma20 and px >= ma20 * 1.01:
                reason = 'above_ma20'
            elif (DIRECTION == 'long' and px >= tp_px) or (DIRECTION == 'short' and px <= tp_px):
                reason, exit_px = 'tp', tp_px
        
        # 硬止损
        if not reason:
            if DIRECTION == 'long' and px <= entry_px * 0.95:
                reason, exit_px = 'hard_stop', entry_px * 0.95
            elif DIRECTION == 'short' and px >= entry_px * 1.05:
                reason, exit_px = 'hard_stop', entry_px * 1.05
        
        if reason:
            if DIRECTION == 'long':
                pnl = position * (exit_px - entry_px)
                pct = (exit_px - entry_px) / entry_px * 100
            else:
                pnl = position * (entry_px - exit_px)
                pct = (entry_px - exit_px) / entry_px * 100
            capital += pnl
            trades.append({
                'date':d, 'method':entry_method,
                'entry':entry_px, 'exit':exit_px,
                'pnl%':pct, 'reason':reason,
                'bull_zone': bull_zone
            })
            position = 0.0
            in_pos = False

# ============================================================
# 结果输出
# ============================================================
ret = (capital / CAPITAL - 1) * 100
print(f"\n{'='*55}")
print(f"  V4 密集散发 · {TIMEFRAME} · BTC {START[:4]}-{END[:4]}")
print(f"  方向: {DIRECTION.upper()}  |  过滤: 价格vs日线MA120")
print(f"{'='*55}")
print(f"  总收益率:   {ret:>+8.2f}%")
print(f"  最大回撤:   {max_dd:>8.2f}%")
print(f"  交易次数:   {len(trades):>8}")

if trades:
    wins = [t for t in trades if t['pnl%'] > 0]
    losses = [t for t in trades if t['pnl%'] <= 0]
    wr = len(wins)/len(trades)*100
    avg_w = np.mean([t['pnl%'] for t in wins]) if wins else 0
    avg_l = abs(np.mean([t['pnl%'] for t in losses])) if losses else 1
    pf = sum(t['pnl%'] for t in wins) / max(abs(sum(t['pnl%'] for t in losses)) if losses else 0.001, 0.001)
    
    print(f"  胜率:       {wr:>8.1f}%")
    print(f"  平均盈利:   {avg_w:>8.2f}%")
    print(f"  平均亏损:   {avg_l:>8.2f}%")
    print(f"  利润因子:   {pf:>8.2f}")
    print(f"  突破入场:   {sum(1 for t in trades if t['method']=='breakout'):>4}")
    print(f"  回踩入场:   {sum(1 for t in trades if t['method']=='pullback'):>4}")
    
    print(f"\n年度拆分:")
    for yr in range(int(START[:4]), int(END[:4])+1):
        yr_t = [t for t in trades if t['date'].year == yr]
        if yr_t:
            yr_w = [t for t in yr_t if t['pnl%'] > 0]
            yr_ret = sum(t['pnl%'] for t in yr_t)
            print(f"  {yr}: {len(yr_t)}笔 胜率{len(yr_w)/len(yr_t)*100:.0f}% 总盈亏{yr_ret:+.1f}%")
    
    print(f"\n盈利TOP5:")
    for t in sorted([t for t in trades if t['pnl%'] > 0], key=lambda t: t['pnl%'], reverse=True)[:5]:
        print(f"  {str(t['date'])[:10]} {t['method']:<10} ${t['entry']:>6,.0f}->${t['exit']:>6,.0f} {t['pnl%']:>+6.2f}% {t['reason']}")
    
    print(f"\n亏损TOP5:")
    for t in sorted([t for t in trades if t['pnl%'] <= 0], key=lambda t: t['pnl%'])[:5]:
        print(f"  {str(t['date'])[:10]} {t['method']:<10} ${t['entry']:>6,.0f}->${t['exit']:>6,.0f} {t['pnl%']:>+6.2f}% {t['reason']}")
