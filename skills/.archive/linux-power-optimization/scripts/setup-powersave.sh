#!/bin/bash
# ============================================
# Linux 最低功耗优化 - 一键安装脚本
# 关联技能: linux-power-optimization
# ============================================
# 运行: bash setup-powersave.sh
# 作用: 一键完成 CPU powersave + 内核参数 +
#       持久化 + 关多余服务 + 灭屏配置
# ============================================

set -e

echo "========================================"
echo "  系统最低功耗优化 - 安装脚本"
echo "========================================"

# 1. 写入sysctl持久化配置
echo "[1/5] 写入内核省电参数..."
sudo tee /etc/sysctl.d/99-powersave.conf > /dev/null <<'EOF'
# 最低功耗内核参数 - 由 Hermes 配置
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
# 开机自动设置CPU powersave
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

# 5. Wayland 真·灭屏（不只是变暗）
echo "[5/5] 设置显示器灭屏（Wayland）..."
gsettings set org.gnome.desktop.screensaver idle-activation-enabled true 2>/dev/null || true
gsettings set org.gnome.desktop.session idle-delay 60 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 2>/dev/null || true
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing' 2>/dev/null || true
gsettings set org.gnome.desktop.screensaver lock-enabled false 2>/dev/null || true

# WiFi省电
iw dev wlp1s0 set power_save on 2>/dev/null && echo "  ✓ WiFi省电已开启" || echo "  - WiFi省电跳过（无WiFi或接口名不同）"

echo ""
echo "========================================"
echo "  ✅ 优化完成！"
echo "  - CPU: powersave (最低频率)"
echo "  - NMI watchdog: 关闭"
echo "  - Swappiness: 10 (减少磁盘IO)"
echo "  - Laptop mode: 5 (激进省电)"
echo "  - 多余服务: 已禁用"
echo "  - 显示器: 60秒无操作全黑"
echo "  - 系统: 永不休眠"
echo "========================================"
echo ""
echo "当前CPU频率:"
cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq 2>/dev/null || echo "  (不可用)"
