# Hermes Windows Setup — Quick Reference

## One-time Install
```powershell
pip install hermes-agent
```

## Setup (skip Quick Setup, pick Full Setup)
```powershell
hermes setup
```
Answer prompts:
- **2** (Full setup)
- **17** (DeepSeek)
- Paste API key
- Enter (default base URL)
- Enter (default model)
- Enter (Keep current/local)
- **22** (toggle Telegram on) → paste Bot Token + user IDs
- **9** (Skip image gen)
- Enter for vision (Auto)
- **n** (don't login Nous Portal)

## Start
```powershell
hermes gateway run
```

## Common Fixes

### "No messaging platforms enabled"
→ Run `hermes setup` again, toggle Telegram on

### ".env contains export"
→ Remove `export ` prefix from all lines, remove garbage like `FLClash proxy`

### "C:\Users\Administrator\.hermes not found"
→ File explorer: `C:\Users\Administrator\.hermes\` (case sensitive)
→ Or let `hermes setup` create it automatically

### PowerShell paths
Use `$env:USERPROFILE` (not `%USERPROFILE%`)
Example: `cd $env:USERPROFILE\.hermes`
