---
name: openwrt-bypass-router
description: Set up a soft router / bypass router (旁路由) with OpenWrt for proxy/gateway purposes — hardware selection, flashing, topology design, and proxy integration
category: devops
---

# OpenWrt Bypass Router (旁路由)

Set up a dedicated router running OpenWrt/ImmortalWrt as a **旁路由 (bypass router)** — sits alongside the main router, intercepts traffic at the gateway level, and provides system-wide proxy access without installing clients on any device.

Perfect for: Win7 machines that can't run FLClash, old laptops too slow for modern apps, or making all devices in a home network go through proxy automatically.

## Trigger

Use this skill when the user asks about:
- "软路由" / "旁路由" / "OpenWrt" / "刷机"
- "小米路由器刷" / "小米可以刷OpenWrt吗"
- "不想每台设备装代理" / "全局科学上网"
- Router-level proxy setup

## Hardware Selection

### Xiaomi / Redmi Routers (best documented, biggest Chinese community)

**Classic models (MT7621A, ¥30-80 second-hand):**

| Model | CPU | RAM | Firmware | 二手价 | Verdict |
|-------|-----|:---:|:--------:|:------:|:--------|
| **Mi Router 3G (R3G)** ⭐ | MT7621A | 256MB | OpenWrt / Padavan | ¥30-50 | Best classic pick, 256MB RAM runs proxy fine |
| **Mi Router 4A Gigabit (R4A)** ⭐ | MT7621A | 128MB | OpenWrt | ¥40-60 | Best budget pick, huge community |
| **Redmi AC2100 (RM2100)** | MT7621A | 128MB | OpenWrt / Padavan | ¥50-80 | Best signal, most firmware options |
| **Mi Router 3 Pro (R3P)** | IPQ8064 | 512MB | OpenWrt / QSDK | ¥50-80 | Beastly RAM, runs proxy + adblock + NAS |
| **Mi Router 3G v2** | MT7621A | 256MB | OpenWrt | ¥30-50 | Variant of R3G |
| **Mi Router Mini** | MT7620A | 128MB | OpenWrt / Padavan | ¥20-30 | Old, weak CPU |

**WiFi6 models (IPQ8071A or newer, ¥80-200):**

| Model | CPU | RAM | 二手价 | Notes |
|-------|-----|:---:|:------:|:-------|
| **Redmi AX6 (RA76)** ⭐ | IPQ8071A | 512MB | ¥100-150 | Best WiFi6 value, gigabit VPN |
| **Mi AX3600** | IPQ8071A | 512MB | ¥150-200 | Premium, similar to AX6 |
| **Mi AX3000T (RA81)** | MT7981B | 256MB | ¥80-100 | Newer, easy to flash |
| **Redmi AX5** | IPQ6000 | 256MB | ¥60-80 | Older WiFi6, still capable |

### Non-Xiaomi alternatives

| Brand | Model | Notes |
|-------|-------|-------|
| GL.iNet | GL-MT1300 / GL-AX1800 | Ships with OpenWrt, no flashing needed |
| Asus | RT-AC68U / RT-AC86U | Merlin firmware (OpenWrt-like) |
| Linksys | WRT32X / WRT1900ACS | OpenWrt native |
| TP-Link | Archer C7 v2+ | OpenWrt support but tedious flash process |

### Hardware Rule of Thumb

| Use case | Min RAM | Min CPU | Recommended |
|----------|:-------:|:-------:|-------------|
| Proxy only (pass-through) | 128MB | MT7621A | R4A Gigabit ¥40 |
| Proxy + adblock (+ clash) | 256MB | MT7621A | R3G ¥40 |
| Heavy VPN (+ wireguard) | 512MB | IPQ8071A | Redmi AX6 ¥120 |
| All-in-one (+ NAS) | 512MB+ | IPQ8074 | Mini PC N100 ¥300 |

## Topology: 旁路由 Mode

The bypass router is the recommended pattern — it doesn't replace the main router, just sits alongside:

```
Internet → 光猫 (ONT)
               ↓
         主路由 (existing router, any brand)
               ↓
  旁路由 (OpenWrt box, LAN cable to main router's LAN port)
               ↓
      All devices (Win7/Win11/phone/tablet)
        Gateway → 旁路由 IP
        DNS → 旁路由 IP
```

**Setup on each device:**
- Set default gateway to the 旁路由's IP (e.g. 192.168.1.2)
- Set DNS to the same IP
- The 旁路由 runs Clash/SSR/V2Ray, routes traffic through proxy

**Easier alternative (DHCP approach):**
- On the main router, set DHCP option "Gateway" to the 旁路由's IP
- Now ALL devices automatically use the 旁路由 as gateway — zero config per device

## Proxy Integration on OpenWrt

After flashing OpenWrt on the router, install the proxy client:

```bash
# Install luci-app-passwall (best Chinese community option)
opkg update
opkg install luci-app-passwall

# Or install luci-app-openclash (more features)
opkg install luci-app-openclash
```

Then configure:
1. Go to `192.168.1.x/cgi-bin/luci` → Services → PassWall/OpenClash
2. Import your proxy subscription URL (same one used in FLClash)
3. Set "Main Switch" to ON
4. Set mode to "GFW List" or "Global" depending on need

## Verification

```bash
# From any device on the network, check external IP
curl -s ifconfig.me

# Check proxy status via OpenWrt
curl -s --proxy http://192.168.1.x:7890 https://www.google.com -o /dev/null -w "%{http_code}"
```

## Pitfalls

- **Don't set the 旁路由 IP to the same as the main router** — use a different IP (e.g. main 192.168.1.1, bypass 192.168.1.2). Set the bypass router's gateway to point to the main router.
- **DHCP conflict**: Only ONE router on the network should run DHCP. Disable DHCP on the 旁路由 (leave it to the main router) unless you're replacing the main router entirely.
- **WiFi disabled on 旁路由**: In 旁路由 mode, it doesn't need to serve WiFi. Just connect via LAN cable. Disable its WiFi to avoid interference.
- **防火墙设置**：旁路由需要关闭防火墙或添加转发规则，否则客户端无法联网：`echo 0 | sudo tee /proc/sys/net/ipv4/ip_forward` (OpenWrt already has this on by default).
- **FLClash subscription**: The proxy subscription URL used in FLClash can be directly imported into OpenWrt (PassWall/OpenClash). No need for separate subscription services.
- **Mi BE3600 (RA69)**: This is a newer WiFi7 router with Qualcomm IPQ5312. As of mid-2026, **ImmortalWrt firmware selector returns "未找到型号"** (no official support). However, Chinese developers on 恩山论坛 (right.com.cn) have released experimental QSDK builds — the user confirmed this. Check availability before dismissing as unsupported; always verify with `firmware-selector.immortalwrt.org` AND Chinese forums before giving a definitive "no".
- **Mi Router 4A non-gigabit version**: The 4C/4A百兆版 use MT7628 CPU (100Mbps ports only) — too slow for any real use. Always get the **千兆版** (gigabit version).
- **WWAN limitation**: Chinese Xiaomi routers may have modified bootloaders (Bdata partition) that limit which OpenWrt builds can be flashed. Check the specific model's flashing guide on right.com.cn (恩山论坛) before buying.
