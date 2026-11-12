# Subprocess Tool Outage Diagnosis（进程级工具全挂诊断）

**Symptom**: ALL child-process-spawning tools fail simultaneously — `terminal`, `execute_code`, `browser_*`, `delegate_task` subagents — while pure file tools (`read_file` / `write_file` / `search_files` / `patch`) keep working. Anything needing a subprocess (gmgn-cli, TVL scripts, Binance curl, node) is unreachable.

This is a **process-level environment failure of the Hermes gateway itself**, NOT a command/parameter problem. Retrying commands is useless. Do not blame gmgn-cli, the proxy, or the network.

## Error signatures (08-21 早场实测)

1. **terminal** — FileNotFoundError inside `_get_env_config`, no shell output at all:
```
FileNotFoundError: [Errno 2] No such file or directory
  File ".../site-packages/tools/terminal_tool.py", line 1638, in terminal_tool
  File ".../site-packages/tools/terminal_tool.py", line 957, in _get_env_config
```
2. **browser_navigate** — Node crashes at startup:
```
Error: ENOENT: no such file or directory, uv_cwd
    at process.wrappedCwd (node:internal/bootstrap/switches/does_own_process_state:142:28)
```
`uv_cwd` ENOENT = the process's current working directory was **deleted**. Decisive evidence.
3. **execute_code** — bare `FileNotFoundError`, no traceback.
4. **delegate_task** — subagent session exposes only the `process` tool (no terminal), cannot start commands.

## Root cause (this incident)

- pipx venv had been rebuilt `python3.14 → python3.11` (`~/.local/share/pipx/venvs/hermes-agent/lib/` contained only `python3.11`), but the running gateway was still the OLD python3.14 process: its in-memory module paths pointed at the deleted python3.14 directory, and its cwd pointed at a deleted directory.
- Cron ticker still worked (jobs.json `updated_at` advanced), file tools worked (absolute paths), everything spawning children failed.

## Diagnostic steps

1. **Read traceback paths vs filesystem**: take the paths in the tool error traceback and check them with `search_files` — a traceback referencing a non-existent path = venv moved/rebuilt under the running process.
2. **`uv_cwd` ENOENT** from any Node-based tool confirms deleted cwd.
3. **Check cron state**: `~/.hermes/cron/jobs.json` — `updated_at` advancing while `last_run_at` stale confirms the ticker works but execution is broken; `next_run_at` tells you when the next (recovered) run happens.
4. **Verify leftover data freshness** before any fallback: decode /tmp file timestamps (e.g. `alpha_*_6h_<ts>.json` epoch → UTC+8) and compare against current run time. 1787204480 ≈ 2026-08-20 11:41 BJT — 18h stale at the 08-21 05:40 run.

## Fix

```bash
systemctl --user restart hermes-gateway
```
After restart the process runs from the new venv with a valid cwd; the next cron run recovers automatically. If still broken after restart, check `pipx reinstall hermes-agent` / venv integrity.

### Self-heal when you cannot run `systemctl` (terminal is the thing that is dead)

You cannot execute the fix yourself — the tool that would run it is broken. But **file tools and the cron scheduler still work**, and that is enough to get the fix executed (verified 08-21):

1. `write_file` the restart script to a persistent path — `~/.hermes/scripts/restart_gateway.sh`:
   ```bash
   #!/bin/bash
   systemctl --user restart hermes-gateway
   ```
2. Create a **one-shot `no_agent` cron** and let the still-healthy scheduler do what you cannot:
   `cronjob(action='create', name='网关自愈重启(一次性)', schedule='1m', repeat=1, no_agent=True, script='restart_gateway.sh')`
   — `schedule='1m'` + `repeat=1` fires once, ~60s out; `no_agent` script mode bypasses the LLM path entirely.
3. Tell the user the restart lands in ~1 min and give the manual fallback: send `/restart` in Telegram, or run `systemctl --user restart hermes-gateway` from a shell. Confirm recovery with `hermes --version` — the install directory must report the **new** runtime (e.g. `.../lib/python3.11/site-packages`, not the dead `python3.14`).
4. `repeat=1` retires the job on first fire; no cleanup strictly needed.

**⚠️ `write_file` can report failure while succeeding.** In this state `write_file` returned `[Errno 2] No such file or directory` for a writable absolute path — yet the file **was** created (proven via `search_files` / `read_file` immediately after). The error comes from the tool's own broken subprocess/cwd plumbing, not from the write. **Never conclude a write failed from the error alone** — verify with `read_file` / `search_files(target='files')` before retrying or inventing a workaround. Treat any file tool that shells out internally as suspect in the same way.

**Do not thrash on impossible commands.** With terminal down, `python3 -c`, `curl`, `gmgn-cli` and similar either fail outright or sit in approval-pending until they time out ("Command timed out without user response" / "denied by user") — approval prompts cannot be meaningfully answered in this state, and repeated attempts just burn turns. Diagnose with `read_file` / `search_files`, then reach for the file-tools + cron path above.

## Cron failure-reporting protocol (when data sources are unreachable)

- **Do NOT fabricate the report from stale /tmp leftovers** — meme 6h trending data expires within hours (18h-old data was correctly rejected).
- **Do NOT reply [SILENT]** — [SILENT] means "no market signal / nothing new", not "system down". The user must learn the cron broke, or it stays broken silently.
- **Correct output**: a diagnosis report — root cause + evidence + fix command + expected recovery time (next scheduled run). Conclusions first, in Chinese, Telegram-friendly (no pipe tables).
