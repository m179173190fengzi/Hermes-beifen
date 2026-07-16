# Hermes Config Auto-Backup to GitHub Private Repo

Automatically push `.hermes/` (config, skills, memories, cron) to a private GitHub repo on a schedule.

## Setup

```bash
cd ~/.hermes
git init
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git

# Credential helper (avoids re-prompt every push)
git config credential.helper 'store --file ~/.hermes/.git-credentials'
echo 'https://YOUR_USER:YOUR_TOKEN@github.com' > ~/.hermes/.git-credentials
chmod 600 ~/.hermes/.git-credentials
```

## .gitignore for ~/.hermes/

Most of `~/.hermes/` is ephemeral or huge — only config/skills/memories/cron matter:

```
*.log
__pycache__/
.env
node/
node_modules/
bin/
backups/
hermes-agent/
hermes_agent.egg-info/
state.db
state.db-wal
state.db-shm
cache/
audio_cache/
.skills_prompt_snapshot.json
models_dev_cache.json
kanban.db
sessions/
```

## Initial Push

```bash
cd ~/.hermes
git add -A
git commit -m "初始备份 $(date '+%Y-%m-%d %H:%M')"
git branch -M main
git push -u origin main --force
```

## Cron Job for Periodic Auto-Push

```bash
# Edit crontab
crontab -e

# Add: push every 6 hours at minute 0
0 */6 * * * cd ~/.hermes && git add -A . && git diff --cached --quiet || (git commit -m "自动备份 $(date '+%Y-%m-%d %H:%M')" && git push)
```

Or use Hermes' own cron system:

```bash
hermes cron create \
  --schedule "0 */6 * * *" \
  --name "config-backup" \
  --prompt "Run: cd ~/.hermes && git add -A . && git diff --cached --quiet || (git commit -m \"auto backup $(date)\" && git push). Skip if token expired — do NOT retry silently."
```

## Known Pitfalls

### Token Expired → Silent Timeout
The most common failure: GitHub token expires, `git push` hangs until timeout (no clear "401" error — just silence). Always verify the token first:

```bash
curl -s -H "Authorization: token $TOKEN" https://api.github.com/user
# → {"message": "Bad credentials"} means expired
```

Fix: generate new token at https://github.com/settings/tokens (scopes: `repo`), update `~/.hermes/.git-credentials`.
### Large Files Bloat the Repo

The `.gitignore` above drops huge dirs (node/, bin/, backups/, state.db), keeping the repo < 20MB. If you accidentally committed them, purge with `git filter-branch` or start fresh with `--force`.

### Multi-Machine Backup — `git pull --rebase` Required

When `.hermes/` is a shared backup repo pushed from **multiple machines** (e.g., Bot A WSL + Bot B Linux), you MUST pull before push or get `! [rejected]`:

```bash
cd ~/.hermes
git pull origin main --rebase   # apply remote changes first
git push origin main
```

Key points:
- **`--rebase` not `--merge`**: Keeps history linear for single-user backup. Merge commits are unnecessary noise.
- **Submodule warnings**: If `skills/` contains `.git` submodules (e.g. `huashu-nuwa`), rebase emits `unable to rmdir` — harmless, ignore it.
- **No double auto-push crons**: If both machines auto-push, they'll fight. Only one machine should auto-push; the other pulls manually or uses pull-before-push.

### git push --force on Remote with Existing History
If the remote already has a different history, `--force` is needed but destroys remote history. Acceptable for single-user backup repos.
