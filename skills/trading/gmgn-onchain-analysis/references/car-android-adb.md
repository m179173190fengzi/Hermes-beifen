# Car Android Head Unit ADB Installation (车机装App)

Covers installing third-party apps (高德地图车机版, 酷狗音乐, etc.) on Android car head units.

## The Core Problem: Host-to-Host USB

Car USB ports are **Host** (A-type, reads flash drives), same as computer USB ports. A regular USB cable won't connect them — both sides try to be the host.

## Solutions (in order of simplicity)

### 1. U盘安装 (USB Drive — Easiest)

1. Computer → download `.apk` files for car-use apps:
   - **高德地图车机版**: https://auto.amap.com/download
   - **酷狗音乐车机版**: search web
   - **QQ音乐车机版**: search web
2. Copy apks to USB flash drive (FAT32 formatted)
3. Plug into car USB port
4. Car → file manager app → open USB → tap apk → install

If no file manager is visible:
- Settings → Apps → Show system apps → find "File Manager" → open
- Or install ES File Explorer first via another method

### 2. 悟空遥控器 (Wukong Remote — Wireless)

1. Phone installs "悟空遥控器" app
2. Phone and car connect to same WiFi
3. Phone app finds car device → push APK to car
4. Car auto-installs

### 3. USB Dual-A Cable (ADB via Computer)

Buy a **USB-A to USB-A male cable** (双公头USB线, ~¥10 on Taobao). Also need a Type-C to USB-A female adapter if computer only has USB-C:

```
Computer USB-A ← dual-A cable → Car USB-A
```

**Steps:**
1. Car → Settings → About → tap Build Number 7x → Developer mode
2. Settings → Developer Options → USB Debugging → ON
3. Computer → connect cable to both ends
4. Computer → `adb devices` (verify connection)
5. Computer → `adb install 高德地图车机版.apk`

### 4. 甲壳虫ADB助手 (Beetle ADB Assistant — Phone-based)

An Android app that lets one phone control another Android over ADB.
**Limitation**: Car USB is HOST port, so direct USB connection won't work.
**Requires**: First connect via computer ADB to enable wireless ADB, then use phone.

**Workflow:**
1. First time: use Method 3 (dual-A cable + computer) to run `adb tcpip 5555`
2. Disconnect cable — car now has wireless ADB enabled
3. Phone (with 甲壳虫ADB installed) → connect to car's WiFi IP: `192.168.x.x:5555`
4. Phone can now install APKs to car wirelessly

Note: 甲壳虫ADB助手 was removed from Coolapk and its GitHub went 404. An alternative is "ADB 去广告" or "Scene" app from Coolapk.

### 5. Wireless ADB (No cable at all)

Some newer car head units have **Wireless Debugging** in Developer Options directly:
```
Settings → Developer Options → Wireless Debugging → ON
```

Then from computer/phone:
```bash
adb connect 192.168.x.x:5555
adb install app.apk
```

If the option isn't there, use Method 3 once to enable it.

## Recommended Apps for Chinese Car Users

| Purpose | App | Version |
|:--------|:----|:--------|
| 🗺️ Navigation | **高德地图车机版** | Latest (has traffic light countdown) |
| 🎵 Music | **酷狗音乐车机版** | Free songs, car-UI friendly |
| 🎵 Music | **QQ音乐车机版** | If user has QQ VIP |
| 📂 File mgr | **ES文件浏览器** / **FX File Manager** | For installing future APKs |

## Oushang X5 (欧尚X5) Specific Notes

- Model: 欧尚X5 (Changan OEM)
- Android base: ~Android 9-10 (custom ROM)
- USB port: Type-A (host), no HDMI input
- Developer mode: Settings → About → Tap build number 7x
- Debugging: Settings → Developer Options → USB Debugging
- **WiFi ADB:** Not available on stock ROM (requires one-time computer ADB to enable)
- **CarPlay/Android Auto:** NOT supported natively. For wireless projection, recommend **CarLinkit (车连易)** TBox/5.0 (~¥200-300) plugged into USB port
