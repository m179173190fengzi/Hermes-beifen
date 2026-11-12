# Display Power Verification on Wayland

## Quick Checks

```bash
# Current screen blanking status
gsettings get org.gnome.desktop.screensaver idle-activation-enabled
gsettings get org.gnome.desktop.session idle-delay
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout
gsettings get org.gnome.desktop.screensaver lock-enabled
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Screen dims but never goes black | `idle-activation-enabled` is false | Set to `true` |
| System suspends after screen off | `sleep-inactive-ac-timeout` set to value > 0 | Set to `0` |
| Screen never turns off at all | DPMS is not applicable (Wayland) | Must use `gsettings` |
| Lock screen appears | `lock-enabled` is true | Set to `false` if headless |
