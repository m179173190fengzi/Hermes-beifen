# Upgrade blocked by Python version pin — full field transcript (2026-08)

Scenario: Ubuntu 26.04 (system Python 3.14.4), Hermes installed via pipx. User asked
"更新一下Hermes". Installed 0.15.2 (2026.5.29); PyPI actually had 0.19.0.

## What happened, in order

1. `hermes --version` → `Hermes Agent v0.15.2 ... Up to date` — the "Up to date"
   claim comes from the local version check, NOT PyPI. Don't trust it as proof of
   latest release.
2. `hermes update` → **BLOCKED: timed out without user response** (gateway context).
   The command is interactive / waits for confirmation; in a non-TTY gateway
   session it just hangs. Use pipx directly instead.
3. `pipx upgrade hermes-agent` → `hermes-agent is already at latest version 0.15.2`.
   Misleading — see root cause below.
4. Queried PyPI directly (via FLClash proxy 127.0.0.1:7890):
   `latest: 0.19.0` — so pipx was wrong.
5. `pipx install --force 'hermes-agent[telegram]'` → still 0.15.2 (pipx reuses the
   existing venv + its interpreter; force doesn't rebuild with a new Python).
6. `pipx runpip hermes-agent install --upgrade 'hermes-agent[telegram]'` → "Requirement
   already satisfied" (cached index + version resolution).
7. `pipx runpip hermes-agent install --upgrade --force-reinstall --no-cache-dir
   'hermes-agent[telegram]==0.19.0'` → **THE SMOKING GUN**:
   ```
   ERROR: Ignored the following versions that require a different python version:
   0.16.0 Requires-Python >=3.11,<3.14; ... 0.19.0 Requires-Python >=3.11,<3.14
   ERROR: Could not find a version that satisfies the requirement hermes-agent==0.19.0
   (from versions: 0.13.0, 0.14.0, 0.15.0, 0.15.1, 0.15.2)
   ```
   pip silently drops incompatible releases from its candidate list; that's why
   pipx reported "latest" without any error. 0.15.2 is the newest release
   installable on Python 3.14.
8. Available interpreters: `/usr/bin/python3.14` (system), `~/.local/bin/python3.11`.
   Chose 3.11 (3.11.15).
9. Fix:
   ```bash
   pipx uninstall hermes-agent
   HTTPS_PROXY=http://127.0.0.1:7890 pipx install --python /home/wei/.local/bin/python3.11 'hermes-agent[telegram]'
   # → installed package hermes-agent 0.19.0, installed using Python 3.11.15
   ```

## The gateway-breaks-mid-upgrade pitfall

After the pipx uninstall+reinstall, the RUNNING gateway process (still executing
0.15.2 code from the deleted python3.14 site-packages) could no longer run ANY
tool:

- `terminal` → `FileNotFoundError: [Errno 2] No such file or directory` at
  `tools/terminal_tool.py` `_get_env_config` — the session cwd
  (`/home/wei/.local/share/pipx/venvs/hermes-agent/lib/python3.14/site-packages`)
  no longer exists.
- Passing `workdir=/home/wei` did NOT help — the failure is in the tool's own
  env-config bootstrap, before any command runs.
- `execute_code` → same FileNotFoundError (subprocess bootstrap also broken).

Recovery: user sends `/restart` in Telegram (or `systemctl --user restart
hermes-gateway` on the server). New process loads 0.19.0 from the fresh venv.
Config/sessions/memory untouched (they live in ~/.hermes, not the venv).

## Lessons

- Always verify actual latest on PyPI (`pypi.org/pypi/hermes-agent/json`) before
  believing pipx's "already at latest".
- When pipx says "latest" but PyPI has newer: suspect Requires-Python pin.
  Force-install the target version to surface the real error.
- hermes-agent 0.16.0+ needs Python >=3.11,<3.14. Rebuild pipx venv with 3.11/3.12/3.13
  (`pipx install --python <path>`), keeping the `[telegram]` extra.
- Don't `pipx uninstall` while the gateway is running from that venv — the live
  session loses its module files. Upgrade, then restart gateway.
- `hermes update` hangs in gateway context; drive upgrades via pipx + proxy env.
