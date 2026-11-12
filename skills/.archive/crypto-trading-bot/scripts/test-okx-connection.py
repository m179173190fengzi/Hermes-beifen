#!/usr/bin/env python3
"""
test-okx-connection.py — Verify OKX API credentials from FreqTrade config.

Usage:
    python3 scripts/test-okx-connection.py [--config path/to/config.json]

Reads the exchange config (OKX key/secret/passphrase), signs v5 requests,
and tests multiple endpoints. Detects common failure modes:
  - 50111: Invalid OK-ACCESS-KEY (key deleted or never confirmed)
  - 50113: Bad signature (wrong secret)
  - 50114: Wrong passphrase
  - ccxt timeout: try direct requests (ccxt proxy handling may be flaky)

Requires: requests (pip install requests)
"""
import json
import hmac
import hashlib
import base64
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ 需要 requests 库: pip install requests")
    sys.exit(1)


def find_config():
    """Try common config paths."""
    if len(sys.argv) > 2 and sys.argv[1] == '--config':
        return Path(sys.argv[2])
    candidates = [
        'user_data/config-okx.json',
        'user_data/config.json',
        '../user_data/config-okx.json',
        '../user_data/config.json',
        os.path.expanduser('~/ft_userdata/user_data/config-okx.json'),
        os.path.expanduser('~/ft_userdata/user_data/config.json'),
    ]
    here = Path.cwd()
    for c in candidates:
        p = here / c if not c.startswith('/') and not c.startswith('~') else Path(c)
        p = p.resolve()
        if p.exists():
            return p
    return None


def sign(method, path, body, secret):
    """OKX v5 signature: HMAC-SHA256 → base64."""
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    sig_str = f'{ts}{method}{path}{body}'
    mac = hmac.new(secret.encode('utf-8'), sig_str.encode('utf-8'), hashlib.sha256)
    return ts, base64.b64encode(mac.digest()).decode('utf-8')


def test_endpoint(name, path, api_key, secret, password, proxy, session):
    """Test a single OKX v5 REST endpoint."""
    ts, sig = sign('GET', path, '', secret)
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': sig,
        'OK-ACCESS-TIMESTAMP': ts,
        'OK-ACCESS-PASSPHRASE': password,
    }
    try:
        r = session.get(f'https://www.okx.com{path}', headers=headers, timeout=10)
        data = r.json()
        code = data.get('code')
        msg = data.get('msg', '(no msg)')
        if code == '0':
            payload = data.get('data', [])
            if payload:
                print(f'  ✅ {name}: OK — {json.dumps(payload, indent=4)[:600]}')
            else:
                print(f'  ✅ {name}: OK (空数据 — 正常, 无持仓/无余额)')
            return True
        else:
            print(f'  ❌ {name}: [{code}] {msg}')
            return False
    except requests.exceptions.Timeout:
        print(f'  ⏱️  {name}: 超时')
        return False
    except Exception as e:
        print(f'  ⚠️  {name}: {type(e).__name__}: {e}')
        return False


def main():
    config_path = find_config()
    if not config_path:
        print("❌ 未找到配置文件。请指定: python3 test-okx-connection.py --config /path/to/config.json")
        print("   或者在 FreqTrade user_data/ 目录下运行")
        sys.exit(1)

    print(f"📄 使用配置文件: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    ex_cfg = config.get('exchange', {})
    api_key = ex_cfg.get('key', '')
    secret = ex_cfg.get('secret', '')
    password = ex_cfg.get('password', '')
    proxy_url = ex_cfg.get('ccxt_config', {}).get('httpProxy', '')

    if not api_key or not secret or not password:
        print("❌ 配置缺少 key/secret/password (exchange 字段)")
        sys.exit(1)

    print(f'🔑 Key: {api_key[:8]}...{api_key[-4:]}')
    print(f'🔒 Secret: {"*" * max(0, len(secret) - 4)}{secret[-4:]}')
    print(f'🔐 Passphrase set: {"✓" if password else "✗"}')
    print(f'🌐 Proxy: {proxy_url or "无"}\n')

    # --- Step 1: Test raw proxy (if configured) ---
    if proxy_url:
        print('--- Step 1: 代理连通性 ---')
        try:
            r = requests.get('https://www.okx.com/api/v5/public/time',
                           proxies={'http': proxy_url, 'https': proxy_url}, timeout=10)
            print(f'  ✅ 代理 -> OKX 公共API: {r.json()["data"][0]["ts"][:13]}')
        except Exception as e:
            print(f'  ❌ 代理不通: {e}')
            print('  请检查: 1) 代理地址是否正确  2) Clash/V2Ray 是否运行')
            return

    # --- Step 2: Test public endpoint (no auth) ---
    print('\n--- Step 2: 公共API (免认证) ---')
    session = requests.Session()
    if proxy_url:
        session.proxies = {'http': proxy_url, 'https': proxy_url}
    try:
        r = session.get('https://www.okx.com/api/v5/public/time', timeout=10)
        print(f'  ✅ OKX 服务器时间: {r.json()["data"][0]["ts"]}')
    except Exception as e:
        print(f'  ❌ 公共API不通: {e}')
        print('  提示: 从中国大陆访问 OKX 可能需要代理')
        return

    # --- Step 3: Test authenticated endpoints ---
    print('\n--- Step 3: 认证API (签名请求) ---')
    endpoints = [
        ('账户余额',   '/api/v5/account/balance'),
        ('持仓信息',   '/api/v5/account/positions'),
        ('交易账户余额', '/api/v5/asset/balances'),
        ('钱包余额',   '/api/v5/asset/currencies'),
    ]

    success_count = 0
    for name, path in endpoints:
        if test_endpoint(name, path, api_key, secret, password, proxy_url, session):
            success_count += 1

    # --- Summary ---
    print(f'\n{"=" * 40}')
    if success_count > 0:
        print(f'✅ {success_count}/{len(endpoints)} 个端点测试通过 — API 连接正常')
    else:
        print('❌ 所有端点都失败 — 请检查 API Key')
        print('  错误码说明:')
        print('    50111 — Key 无效 (已删除/未确认) → 去 OKX 重新创建 API')
        print('    50113 — 签名错误 (Secret 不匹配)')
        print('    50114 — 密码短语错误')

    # --- Step 4: Check ccxt (optional) ---
    print('\n--- Step 4: ccxt 库兼容性检查 ---')
    try:
        import ccxt
        ex = ccxt.okx({
            'apiKey': api_key,
            'secret': secret,
            'password': password,
            'httpProxy': proxy_url,
            'options': {'defaultType': 'swap'},
        })
        try:
            ex.fetch_time()
            print('  ✅ ccxt.fetch_time() 成功')
            print('  ℹ️  如果 ccxt 后续调用超时但本脚本正常，说明是 ccxt 的')
            print('     proxy 处理问题 (优先用 FreqTrade 而非直接 ccxt)')
        except Exception as e:
            print(f'  ⚠️  ccxt.fetch_time() 失败: {e}')
            print('  提示: 这是 ccxt 库的 proxy 处理问题, 不影响 FreqTrade')
    except ImportError:
        print('  ⏭️  ccxt 未安装 (非必须)')

    print('\n✅ 测试完成')


if __name__ == '__main__':
    main()
