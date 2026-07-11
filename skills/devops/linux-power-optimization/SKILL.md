---
name: linux-power-optimization
description: 在 Linux 上运行 Hermes 时把系统降到最低功耗 — CPU powersave、内核省电参数、禁用不必要服务、持久化配置
category: devops
---

# Linux 最低功耗优化

用于在低功耗设备（Intel NUC/迷你机/工控机/旧笔记本）上运行 Hermes Agent 时，把系统功耗压到最低，同时保证 Hermes 正常工作。

## 触发条件

用户说：`设置系统最低功耗`、`省电模式`、`powersave`、`系统功耗`、`低功耗`、`省电`

## 步骤

### 1. 检查当前状态

```bash
# CPU Governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# 内核参数
cat /proc/sys/kernel/nmi_watchdog
cat /proc/sys/vm/swappiness
cat /proc/sys/vm/laptop_mode

# 运行中的服务
systemctl list-units --type=service --state=running --no-pager

# 是否有 NOPASSWD sudo
sudo -n echo "nocache" 2>/dev/null && echo "HAS_NOPASSWD" || echo "NEEDS_PW"
```

### 2. 内核参数（即时生效）

```bash
# CPU 锁定 powersave
echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 内核省电
echo 0 | sudo tee /proc/sys/kernel/nmi_watchdog
echo 10 | sudo tee /proc/sys/vm/swappiness
echo 5 | sudo tee /proc/sys/vm/laptop_mode
```

### 3. 禁用不必要的系统服务

以下服务在 Hermes 主机上几乎用不到：

```bash
# 安全列表（蓝牙/打印/定位/调制解调器/颜色管理）
SERVICES=(
    bluetooth.service
    avahi-daemon.service
    cups.service
    cups-browsed.service
    ModemManager.service
    colord.service
    fwupd.service
    geoclue.service
    iio-sensor-proxy.service
    accounts-daemon.service
)
for svc in "${SERVICES[@]}"; do
    sudo systemctl stop "$svc" 2>/dev/null || true
    sudo systemctl disable "$svc" 2>/dev/null || true
done
```

### 4. 持久化（重启后生效）

**sysctl 配置** → `/etc/sysctl.d/99-powersave.conf`:

```
kernel.nmi_watchdog = 0
vm.swappiness = 10
vm.laptop_mode = 5
kernel.printk = 3 3 3 3
```

**CPU Governor 持久化** → systemd oneshot 服务 + 脚本 `/usr/local/bin/set-powersave.sh`:

```ini
[Unit]
Description=Set CPU governor to powersave (lowest power)
After=sysinit.target
Before=multi-user.target
DefaultDependencies=no

[Service]
Type=oneshot
ExecStart=/usr/local/bin/set-powersave.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

脚本内容：
```bash
#!/bin/bash
echo powersave | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
exit 0
```

### 5. 显示器省电（桌面/GNOME Wayland）

> **⚠️ Wayland 下 `sleep-inactive-ac-timeout` 只会让屏幕变暗，不会真正息屏！**

正确做法是启用 screensaver 息屏激活：

```bash
# 关键：启用到点灭屏（屏幕全黑，不只是变暗）
gsettings set org.gnome.desktop.screensaver idle-activation-enabled true
gsettings set org.gnome.desktop.session idle-delay 60          # 60秒无操作后灭屏

# 可选：设置系统不休眠（Hermes 需要一直跑）
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'

# 可选：不锁屏（无人手动解锁）
gsettings set org.gnome.desktop.screensaver lock-enabled false
```

**验证灭生效：**
```bash
gsettings get org.gnome.desktop.screensaver idle-activation-enabled  # → true
gsettings get org.gnome.desktop.session idle-delay                   # → uint32 60
```

**不要用 `xset q` 查 DPMS** — Wayland 下 DPMS 扩展不存在，`xset q` 显示 `Server does not have the DPMS Extension`，这是正常行为。息屏由 GNOME 的 Mutter 合成器管理。

### 6. WiFi 省电

```bash
iw dev wlp1s0 set power_save on
```

### 一键脚本

技能附带了一个完整的安装脚本 `scripts/setup-powersave.sh`，把以上所有步骤打包成一条命令：

```bash
bash ~/.hermes/skills/devops/linux-power-optimization/scripts/setup-powersave.sh
```

包含：sysctl持久化 → CPU governor脚本+systemd服务 → 关10个多余服务 → Wayland灭屏 → WiFi省电。

### 验证

```bash
# CPU 与内核
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor  # 应显示 powersave
cat /proc/sys/vm/swappiness                                 # 应显示 10
cat /proc/sys/kernel/nmi_watchdog                           # 应显示 0
cat /proc/sys/vm/laptop_mode                                # 应显示 5

# Wayland 灭屏
gsettings get org.gnome.desktop.screensaver idle-activation-enabled  # 应显示 true
gsettings get org.gnome.desktop.session idle-delay                   # 应显示 uint32 60

# 开机自启服务
systemctl is-enabled powersave.service  # 应显示 enabled
systemctl status powersave.service      # 应显示 active/exited
```

## Related References

- `references/display-verification.md` — Wayland 显示省电验证和故障排查快速参考
- `scripts/ubuntu-setup-powersave.sh` — Ubuntu 专用版一键安装脚本（与默认脚本功能等价，保留以备参考）

## Merged Skills

This skill absorbed `ubuntu-power-optimization` which was a near-identical variant. All Ubuntu-specific content is integrated above; the variant's setup script is preserved as `scripts/ubuntu-setup-powersave.sh`.

## Pitfalls

- **sudo 密码被工具拦截**：Hermes 工具链会阻止交互式 sudo 和 `sudo -S` 密码管道。先检查 `sudo -n echo ok` 能否直接用。如果 `/etc/sudoers.d/hermes-nopasswd` 已存在（内容 `wei ALL=(ALL) NOPASSWD: ALL`），则全程用 `sudo -n` 即可。如果不存在，让用户手动运行一次生成的一键脚本。
- **Wayland 息屏 ≠ DPMS 息屏**：Wayland 下没有 DPMS 扩展，`xset` 不可用。屏幕只变暗不灭屏的根因是 `idle-activation-enabled` 为 false。必须设 `gsettings set org.gnome.desktop.screensaver idle-activation-enabled true` 才能让屏幕真正全黑。
- **VM/云服务器**：以上部分参数在云 VM 上可能不可用（CPU governor、C-states 由宿主机控制）。
- **eMMC/SSD**：`laptop_mode=5` 对 eMMC 没有旋转磁盘效果，但有助于减少非必要 IO。
- **不要禁用 Hermes 依赖的服务**：NetworkManager、systemd-journald、containerd/docker、cron、dbus、chrony（NTP）是必需的。
- **禁用服务安全列表**：bluetooth/avahi-daemon/cups/cups-browsed/ModemManager/colord/fwupd/geoclue/iio-sensor-proxy/accounts-daemon 这 10 个在 Hermes 主机上完全用不到，可安全禁用。
