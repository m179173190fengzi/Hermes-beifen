# 安卓机接 Linux 的 adb 连通性排查（四层）

phone-harness 之类插件装好后，`doctor` 报 `[FAIL] a phone is reachable (state: no-device)`
时按这四层往下走。**每一层用不同的证据判断，不要凭"USB 插好了"下结论。**

## 第 1 层：adb 看不到设备 → 系统到底认没认这个 USB 设备

```bash
adb devices -l                       # 空 → 继续
lsusb | grep -viE "root hub|intel|realtek|hub"   # 有没有手机
```

- 有（如 `2717:ff48 Xiaomi Inc. Mi/Redmi series (MTP + ADB)`）→ 跳到第 3 层
- 没有 → 第 2 层

## 第 2 层：USB 层没认到 → 看内核在枚举哪一步失败

```bash
sudo dmesg | grep -iE "usb [0-9]-|new .* device|unable to enumerate|error -71" | tail -12
```

| 内核输出 | 含义 | 结论 |
|---|---|---|
| `new high-speed USB device number N` 之后有 `New USB device found` | 枚举成功 | 问题在更上层（第 3/4 层） |
| `device not accepting address N, error -71` / `Device not responding to setup address` / `unable to enumerate USB device` | **握手失败（EPROTO）** | **物理层**：线 / 口 / 手机接口 |
| 完全没有 `new ... device` 那行 | 口没感知到插入 | 线只通充电 / 口坏 / 没插到底 |

**`error -71` 的判据组合（足够下结论，不用再查驱动）**：
- 同一个 USB 控制器上其他设备（鼠标/读卡器/摄像头/蓝牙）全部正常 → 控制器与驱动没问题
- 换口后**同样报 -71** → 错误跟着线/手机走，不跟电脑走
- 修法优先级：**换一根确定能传数据的线**（90%）→ 清理手机 USB-C 口（2019 年前的机器积灰很常见）→ 换口并插到底 → 换台电脑交叉验证（同一根线插别的机器，能认=本机口的问题）

## 第 3 层：lsusb 认到了，但 adb 仍为空 → 看暴露了哪些接口

```bash
sudo lsusb -v -d <vid>:<pid> 2>/dev/null \
  | grep -E "bInterfaceNumber|bInterfaceClass|bInterfaceSubClass|bInterfaceProtocol"
```

- **ADB 接口特征：class `255`(0xFF) + subclass `66`(0x42) + protocol `1`** → 手机侧调试接口已暴露，
  问题在权限或链路质量
- 只有 `255/255/0`（MTP/vendor）而没有 `255/66/1` → **手机没真正开 USB 调试**
  （或 MIUI 的 USB 模式停在"仅充电"，此时不激活 ADB 功能）

权限（Linux 常见坑，但本例不是它）：
```bash
groups | grep plugdev                 # 用户要在 plugdev 组
ls -l /dev/bus/usb/<bus>/<dev>        # 应为 crw-rw---- root plugdev
ls /lib/udev/rules.d/ | grep android   # 51-android.rules 存在
```
`sudo adb devices` 也看不到设备 = **不是权限问题**，别再折腾 udev。

## 第 4 层：接口在、权限对，但 adb 仍不握手 → 抓 adb 服务端 USB 日志

这是最决定性的一步。`ADB_TRACE=usb adb devices` 只打客户端日志，必须让 server 前台跑：

```bash
adb kill-server
(ADB_TRACE=usb timeout 20 adb -a nodaemon server > /tmp/srv.txt 2>&1 &)
sleep 7; adb devices; sleep 2
grep -iE "usb|claim|error|interface|found" /tmp/srv.txt | head -20
```

对照日志定位：

```
usb located new device /dev/bus/usb/001/048     ← adb 找到了设备
usb opened /dev/bus/usb/001/048, fd=13          ← 打开成功（权限没问题）
usb_bulk_write ...                              ← 握手包写进去了
urb status = -71, actual = 0                    ← 读回来的响应：协议错误
ERROR: n = -1, errno = 71 (Protocol error)      ← 物理层信号问题
```

→ 出现 `errno = 71` 就**回到第 2 层的修法**（换线/清口）。
`unable to claim interface` → 接口被别的驱动占用；`permission denied` → 第 3 层的权限。

## 小米 / Redmi（MIUI）专属坑

1. **USB 用途必须是「传输文件(MTP)」**：下拉通知栏 → 点"正在通过 USB 充电" → 传输文件。
   MIUI 默认"仅充电"，这个模式下 ADB 功能不激活（表现为 USB 认到、adb 空白）。
   永久改：`开发者选项 → 默认 USB 配置 → 传输文件(MTP)`
2. **「USB 调试（安全设置）」单独一个开关**：只有它打开，`adb shell input tap` 这类**模拟点击**才生效；
   不开的话能看屏幕但点不动。开启条件通常是**插 SIM 卡 + 登录小米账号**（有的版本要等几分钟）。
3. 开关"已开"但无效时：**关掉等 3 秒再打开**（MIUI 有开关失效的已知问题）。
4. **无线调试要 Android 11+**。Redmi Note 7 官方最高 Android 10（MIUI 12）→ 没有无线调试，
   本地只能走 USB；想绕开线只能上云手机（`phone-harness cloud`，通常有免费试用分钟数）。

## 连接到之后的验收

```bash
adb devices -l          # 应显示 <serial>  device
phone-harness doctor    # 应全 PASS（scrcpy 的 FAIL 是可选的实时镜像，可忽略）
adb shell dumpsys window | grep mCurrentFocus    # 能读到前台 Activity = 真的能读屏
```
