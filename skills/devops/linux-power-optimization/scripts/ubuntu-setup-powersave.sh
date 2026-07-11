# Ubuntu Power Optimization — One-Shot Script

Created: 2026-07-01
Tested on: Ubuntu 26.04 LTS (Resolute Raccoon), GeminiLake CPU

## Script: setup-powersave.sh

```bash
#!/bin/bash
set -e

echo "========================================"
echo "  系统最低功耗优化 - 安装脚本"
echo "========================================"

# 1. 写入sysctl持久化配置
echo "[1/5] 写入内核省电参数..."
sudo tee /etc/sysctl.d/99-powersave.conf > /dev/null <<'EOF'
kernel.nmi_watchdog = 0
vm.swappiness = 10
vm.laptop_mode = 5
kernel.printk = 3 3 3 3
EOF
sudo sysctl -p /etc/sysctl.d/99-powersave.conf

# 2. CPU Governor powersave脚本
echo "[2/5] 创建CPU省电脚本..."
sudo tee /usr/local/bin/set-powersave.sh > /dev/null <<'EOF'
#!/bin/bash
echo powersave | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
exit 0
EOF
sudo chmod +x /usr/local/bin/set-powersave.sh

# 3. 创建开机自启服务
echo "[3/5] 创建systemd自启服务..."
sudo tee /etc/systemd/system/powersave.service > /dev/null <<'EOF'
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
EOF
sudo systemctl daemon-reload
sudo systemctl enable powersave.service
sudo systemctl start powersave.service

# 4. 关闭不必要服务
echo "[4/5] 关闭不必要的后台服务..."
for svc in bluetooth.service avahi-daemon.service cups.service \
           cups-browsed.service ModemManager.service colord.service \
           fwupd.service geoclue.service iio-sensor-proxy.service \
           accounts-daemon.service; do
    sudo systemctl stop "$svc" 2>/dev/null || true
    sudo systemctl disable "$svc" 2>/dev/null || true
    echo "  ✓ $svc"
done

# 5. 显示设置 (Wayland)
echo "[5/5] 设置显示器省电..."
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 1800 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 600 2>/dev/null || true
iw dev wlp1s0 set power_save on 2>/dev/null && echo "  ✓ WiFi省电已开启" || echo "  - WiFi省电跳过"

echo ""
echo "========================================"
echo "  ✅ 优化完成！"
echo "  - CPU: powersave (最低频率)"
echo "  - NMI watchdog: 关闭"
echo "  - Swappiness: 10 (减少磁盘IO)"
echo "  - Laptop mode: 5 (激进省电)"
echo "  - 多余服务: 已禁用"
echo "  - 显示器: 自动关闭"
echo "========================================"
```

## On-Screen Blanking (Wayland)

After running the main script, also run:

```bash
gsettings set org.gnome.desktop.screensaver idle-activation-enabled true
gsettings set org.gnome.desktop.session idle-delay 60
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.desktop.screensaver lock-enabled false
```

This makes the screen go black (not just dim) after 60s of inactivity, without suspending the system.
