# `hermes dashboard --tui` Troubleshooting

## Error: `ModuleNotFoundError: No module named 'hermes_cli.dashboard_auth'`

Observed on Hermes v0.15.2 (2026.5.29.2), Python 3.14.4, pipx install.

### Root Cause

The `web_server.py` imports `from hermes_cli.dashboard_auth.routes import router`
at module level. The `dashboard_auth` plugin lives at:

```
plugins/dashboard_auth/nous/__init__.py
```

but the import expects it at:

```
hermes_cli/dashboard_auth/routes.py
```

The plugin directory `dashboard_auth/` exists under `hermes_cli/` in some
builds but is absent in others. The exact trigger is unknown — may be a
pipx install artifact or a version mismatch between the Hermes CLI package
and its bundled plugins.

### Full Traceback

```
Traceback (most recent call last):
  File "/home/wei/.local/bin/hermes", line 6, in <module>
    sys.exit(main())
  File ".../hermes_cli/main.py", line 14303, in main
    args.func(args)
  File ".../hermes_cli/main.py", line 10937, in cmd_dashboard
    from hermes_cli.web_server import start_server
  File ".../hermes_cli/web_server.py", line 4822, in <module>
    from hermes_cli.dashboard_auth.routes import router as _dashboard_auth_router
ModuleNotFoundError: No module named 'hermes_cli.dashboard_auth'
```

### Quick Check

```bash
ls -la /path/to/hermes_cli/dashboard_auth/  # returns error → missing
```

### Workarounds

1. **Use ttyd instead** (see SKILL.md — works 100% reliably)
2. **Update Hermes** (`hermes update`) — newer version may fix the import

### Verified Working

- `hermes dashboard` (without `--tui`) — works (no TUI chat mode, config/sessions UI only)
- `curl http://127.0.0.1:9119` returns HTTP 502 when dashboard starts but TUI fails
- ttyd on port 7681 returns HTTP 200 immediately
