---
name: community-skills
description: Discover, evaluate, and install community skills packs for Hermes Agent from GitHub and ecosystem registries.
category: hermes-agent
triggers:
  - "find skill"
  - "install skill"
  - "github skill"
  - "awesome hermes"
  - "superpowers"
  - "community skill"
  - "skill pack"
  - "装skill"
  - "skills包"
---

# Community Skills — Discovery & Installation

Find and install community-built skills packs for Hermes Agent.

## Discovery Sources

| Source | URL | Type |
|--------|-----|------|
| awesome-hermes-agent | https://github.com/0xNyk/awesome-hermes-agent | Curated list (4.6k⭐) |
| GitHub search | https://github.com/search?q=hermes+agent+skill&type=repositories&s=stars&o=desc | Raw search |
| hermeshub | https://github.com/amanning3390/hermeshub | Community hub |
| skilldock.io | https://skilldock.io | Cross-platform registry |
| agentskills.io | https://agentskills.io | Open standard ecosystem |
| GMGN official skills | https://github.com/GMGNAI/gmgn-skills | Official API skill pack (387⭐, crypto on-chain) |

## Install superpowers-zh (中文增强版)

The most popular Chinese-localized skills pack (20 skills, Hermes-compatible).

```bash
# RECOMMENDED — full install with hooks + bootstrap
cd /your/project
npx superpowers-zh --tool hermes
```

This creates `.hermes/skills/` with 20 skills + `HERMES.md` bootstrap.

### Pitfalls

- **DO NOT run in `~`** — it writes bootstrap files to your home directory, polluting all projects. Always run inside a project directory.
- **Manual `cp -r skills` is low-fidelity** — doesn't configure hooks or bootstrap. The AI won't auto-trigger skills. Use `npx superpowers-zh` when possible.
- **If already mistakenly run in `~`**: delete `~/skills/` and `~/HERMES.md` / `~/CLAUDE.md`.
- **`cp` truncates large SKILL.md files with embedded Python/heredoc** — when copying skills that embed inline Python scripts (e.g. `python3 << 'PYEOF'`), shell `cp` can truncate the file silently. Always use Python to copy: `python3 -c "open('dst','wb').write(open('src','rb').read())"` and verify sizes match. This affects repos like `GMGNAI/gmgn-skills` where SKILL.md files can be 40-68KB.

### Merge into Production Hermes

```bash
cp -r /path/to/project/.hermes/skills/* ~/.hermes/skills/
```

## Install Skills from awesome-hermes-agent

Each entry in awesome-hermes-agent has a maturity tag:

- `production` — stable, safe to build on
- `beta` — works but evolving
- `experimental` — proof of concept

Installation varies by skill. Common patterns:

```bash
# GitHub-based skills
git clone https://github.com/<user>/<repo>.git /tmp/<repo>
cp -r /tmp/<repo>/skills/* ~/.hermes/skills/

# npm-based (like superpowers-zh)
npx <package-name> --tool hermes

# hermes skills tap (rare)
hermes skills tap add <user>/<repo>
```

## Evaluating Community Skills

Checklist before installing:

1. **README quality** — clear description, install instructions, examples
2. **Maturity** — production > beta > experimental
3. **Last commit** — active in last 3 months
4. **Stars** — signal but not requirement
5. **License** — MIT preferred for compatibility
6. **Test coverage** — tests = maintained
7. **Skill format** — follows SKILL.md standard with proper frontmatter

### ⚠️ CRITICAL: Claude Code Plugin vs Hermes Skill Detection

Many repos labeled as "skills" are actually **Claude Code plugins** (or Codex/Grok plugins), NOT Hermes-native skills. They have a different format and can't be installed via `hermes skills add`.

**How to detect Claude Code plugins:**

| Signal | Look For |
|--------|----------|
| `.claude-plugin/` directory | Present in repo root — definitely Claude Code, not Hermes |
| `.codex-plugin/` directory | Present in repo root — Codex format, not Hermes |
| `.grok-plugin/` directory | Present in repo root — Grok format, not Hermes |
| `AGENTS.md` / `CLAUDE.md` | Project-level instruction files for Claude Code, not Hermes SKILL.md |
| `plugin.json` | Claude Code plugin manifest — no equivalent in Hermes |
| No `SKILL.md` | If the repo has no SKILL.md with YAML frontmatter, it's not a Hermes skill |
| `skills/` subdirectory with folders but no `SKILL.md` inside each | Might be Claude Code skills subdirectory pattern |

**Hermes-native skill format (what you want):**
```
repo/
  SKILL.md          ← YAML frontmatter + markdown body (REQUIRED)
  skill.py          ← optional Python module
  references/       ← optional support docs
  templates/        ← optional boilerplate
  scripts/          ← optional re-runnable scripts
```

**Real-world findings (2026-07):**
- Trending repos like `mvanhorn/last30days-skill` (52k⭐), `coreyhaines31/marketingskills` (39k⭐), `antvis/chart-visualization-skills` (413⭐), `davepoon/buildwithclaude` (3.2k⭐), `gitroomhq/postiz-agent` (354⭐) all use `.claude-plugin/` format
- Most are NOT directly installable as Hermes skills — the SKILL.md structure differs
- Exception: `coreyhaines31/marketingskills` skills have a structure closest to Hermes format and could potentially be adapted
- Always check before recommending installation. If it has a `.claude-plugin/` dir, tell the user it's Claude Code format and not Hermes-compatible

**Multi-platform skill repos (Hermes + Claude Code + Codex + Cursor + OpenCode):**
Some repos ship skills for ALL agent platforms simultaneously via separate directories. These ARE Hermes-compatible — check the `skills/` dir specifically:

```text
repo/
  skills/           ← Hermes SKILL.md format (valid)
  .claude-plugin/   ← Claude Code (ignore for Hermes)
  .codex/           ← Codex (ignore)
  .cursor-plugin/   ← Cursor (ignore)
  .opencode/        ← OpenCode (ignore)
```

Example: `GMGNAI/gmgn-skills` (387⭐, official GMGN API skill pack) — `skills/` has valid SKILL.md files with frontmatter. Do NOT reject multi-platform repos just because `.claude-plugin/` exists alongside; verify the `skills/` dir independently.

## Installing Plugins (not just skills) — GitTrend 5-pack 2026-07-31

Installed 5 ecosystem repos from a GitTrend recommendation into `~/hermes-ecosystem/`. Key patterns + pitfalls:

| Repo | Type | Install |
|------|------|---------|
| 42-evey/hermes-plugins | 23 plugins | `cp -r evey-* ~/.hermes/plugins/` + `cp evey_utils.py ~/.hermes/plugins/`; needs `pipx runpip hermes-agent install paho-mqtt`; all land **not enabled** — enable individually |
| Romanescu11/hermes-skill-factory | skill + plugin | `bash install.sh` (copies SKILL.md → `~/.hermes/skills/meta/skill-factory/`, plugin → `~/.hermes/plugins/skill_factory.py`) |
| theopitori/hermeskill | entry-point plugin + CLI | `pipx install hermeskill` + `pipx runpip hermes-agent install hermeskill-hermes`, then enable via config key (below) |
| ZeroPointRepo/youtube-skills | skill | `hermes skills install skills-sh/ZeroPointRepo/youtube-skills/skills/youtube-full --yes`; needs TranscriptAPI key (free 100 credits) to actually work |
| witt3rd/oh-my-hermes | 10 skills + plugin | `hermes skills tap add witt3rd/oh-my-hermes` then install, OR manual: `cp -r plugins/omh/skills/omh-* ~/.hermes/skills/` + `cp -r plugins/omh ~/.hermes/plugins/omh` |
| limin112/min-skill | 2 skills | `cp -r skills/{wechat-publish-template,explain-video} ~/.hermes/skills/`. wechat-publish-template = 橙黑赛博朋克公众号排版(主橙#FF5722+深黑#0A0A0A, 12种block, 附wechatsync CLI同步草稿箱方案, CLI未装); explain-video = 讲解视频流水线(HTML幻灯→TTS→字幕→BGM→ffmpeg合成, 需Playwright补装) |

### Pitfalls (all hit this session)

- **`hermes plugins enable X` OVERWRITES the whole `plugins.enabled` list.** Enabling omh silently dropped hermeskill from config. Always re-set the full list afterwards: `hermes config set plugins.enabled '[omh, hermeskill]'`.
- **`config.yaml` is a protected file** — write_file/patch on it is denied. Use `hermes config set <key> '<value>'` instead.
- **Entry-point plugins (pip-installed, e.g. hermeskill-hermes) don't appear in `hermes plugins list` git-plugin section** and can't be enabled via `hermes plugins enable`. They're enabled by adding the name to `plugins.enabled` in config. The plugin's own `enable-hermes` CLI may fail if run from a separate pipx venv that can't import Hermes — manual config set is the reliable path.
- **`hermes skills install` accepts ONE identifier at a time** — multiple positional args error with "unrecognized arguments". Use `--yes` to skip confirmation (needed in TUI mode).
- **`hermes skills search`/install over network can hang/timeout behind proxy** (even with config `http_proxy` set, CLI calls timed out at 90-300s). Reliable fallback: clone the repo locally and `cp -r` the `skills/*` dirs and plugin dirs into `~/.hermes/` directly — same result, no network dependency. Verify with `hermes skills list` / `hermes plugins list`.
- **evey plugin pack is designed for autonomous always-on agents** — enabling all 23 at once creates interference with existing cron/monitoring. Default all-off is correct; enable selectively (`hermes plugins enable evey-cost-guard` etc.).
- Plugins enabled via config take effect **next session**, not immediately.

## Chinese-Focused Community Skills

Especially useful for Chinese-speaking users:

| Pack | Skills | Install |
|------|--------|---------|
| superpowers-zh | 20 skills (14 translated + 6 original) | `npx superpowers-zh --tool hermes` |
| hermes-skills (winterliu6) | content-studio, security-newsletter, tech-ops-bot | GitHub clone |
| hermes-feishu-zh (plugin) | Feishu display fixes + lark-cli-toolbox | `hermes plugins install` |

## This Session's Discoveries (2026-07-18)

GMGN official skills pack updated from upstream (v1.5.2):

| Skill | Action | Notes |
|-------|--------|-------|
| gmgn-market | ✅ Updated | Added hot-searches ranking + Robinhood chain support |
| gmgn-holder-analysis | ✅ **New** | Deep holder chip analysis, installed from official repo |
| gmgn-token/track/portfolio/swap | ✅ Updated | Added Robinhood chain support |
| gmgn-cooking | ≈ unchanged | No Robinhood support upstream either |

**Pitfall hit:** `cp -r` truncated the 47KB SKILL.md with embedded Python heredoc. Fixed by copying with Python (`open('dst','wb').write(open('src','rb').read())`).

## Historical: Session 2026-07-13

Nine community projects evaluated and partially installed:

| Project | Stars | Type | Installed |
|---------|:-----:|:----:|:---------:|
| hermes-workspace | 6,050 | Web UI | ✅ `~/hermes-workspace/` |
| super-hermes | 307 | Skills (prism) | ✅ 5 skills + 7 prisms |
| hermes-dojo | 117 | Skills + scripts | ✅ `~/.hermes/skills/hermes-dojo/` |
| oh-my-hermes | 105 | Skills pack (4 skills) | ❌ optional |
| hermes-dashboard | 62 | Plugin + Web UI | ❌ skipped (dashboard_auth missing) |
| hermes-achievements | 42 | Plugin (dashboard addon) | ❌ skipped (depends on dashboard) |
| hermes-skill-marketplace | 42 | Skills + scripts | ❌ optional |
| hermes-spotify-skill | 10 | Skill | ❌ optional |
| blacktea | 5 | MCP + lib | ❌ not relevant |
| **hermes-browser-extension** | **1,046** | **Chrome/Edge side panel** | **✅ Recommended** — connects active web context to Hermes Agent via Local/Cloud/Remote gateway. Requires `npm install && npm run build` then load unpacked. See `abundantbeing/hermes-browser-extension` |

See `references/hermes-ecosystem-catalog-20260713.md` for full descriptions and install notes.

### Install Patterns Used This Session

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `git clone → install.sh` | super-hermes, hermes-dojo | Has `install.sh` in repo root |
| `git clone → pnpm install → pnpm build → node server-entry.js` | hermes-workspace | Standalone web app, not a Hermes skill |
| `git clone → cp skills/ ~/.hermes/skills/` | Generic | Bare skills without install script |
| `hermes dashboard --port 9119` | Built-in dashboard | Fails if `dashboard_auth` module missing |

### Workspace Notes

- Runs on `node server-entry.js` from project root
- Starts on `http://127.0.0.1:3000`
- Needs Hermes Gateway HTTP API running (`API_SERVER_ENABLED=true` + `API_SERVER_KEY` in `~/.hermes/.env`)
- Dashboard-backed APIs (`/api/sessions`, enhanced chat, memory, jobs) require `hermes dashboard` on :9119
- If `dashboard_auth` module is missing, the core features (chat, terminal, memory, skills) still work fine
- The workspace also pairs with `hermes gateway run` for live session streaming

### Super Hermes Notes

- Installs 5 prism skills + 7 proven prisms under `~/.hermes/prisms/`
- Commands: `/prism-scan`, `/prism-full`, `/prism-3way`, `/prism-discover`, `/prism-reflect`
- Prisms can also be used as standalone system prompts with any tool
- Tested on Gemini 2.5 Flash, Claude Sonnet, Hermes 3/Llama 405B

### Hermes Dojo Notes

- Installs to `~/.hermes/skills/hermes-dojo/` with scripts/ and references/
- Quick test: `cd ~/.hermes/skills/hermes-dojo/scripts && python3 seed_demo_data.py --days 7 && python3 demo.py --reset`
- In Hermes: `/dojo analyze`

## Related

- `~/demo-superpowers/` — reference installation from this session
- `awesome-hermes-agent` — full ecosystem catalog, includes 100+ entries across skills, plugins, memory providers, deployment, integrations
- `~/hermes-workspace/` — installed web workspace
- `~/super-hermes/` — installed prism skills source
- `~/hermes-dojo/` — installed dojo source
