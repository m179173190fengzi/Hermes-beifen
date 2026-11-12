# Hermes Ecosystem Catalog — 2026-07-13

Nine community projects evaluated in one session. Ordered by star count.

---

## 1. outsourc-e/hermes-workspace ⭐6,050

https://github.com/outsourc-e/hermes-workspace

**Type:** Standalone Web App (not a Hermes skill)
**Tech:** TypeScript, React 19, Vite, Node.js
**License:** MIT | **Version:** 2.3.0

Full-featured Hermes workspace: chat, terminal, memory, skills, jobs, MCP, dashboard, conductor, swarm mode. Zero-fork — runs on vanilla hermes-agent.

**Install:**
```bash
git clone https://github.com/outsourc-e/hermes-workspace.git
cd hermes-workspace
pnpm install && pnpm build
node server-entry.js    # http://127.0.0.1:3000
```

**Prerequisites:** Node.js 22+, Hermes Gateway with `API_SERVER_ENABLED=true` + `API_SERVER_KEY`. Optional: `hermes dashboard --port 9119` for enhanced APIs.

---

## 2. Cranot/super-hermes ⭐307

https://github.com/Cranot/super-hermes

**Type:** Skills pack (5 skills) + prism library (7 prisms)
**Tech:** Shell, Markdown
**License:** MIT

Meta-reasoning skills. Teaches Hermes to write its own analysis prompts, report blind spots, grow smarter per analysis.

**Install:** `git clone && bash install.sh`

**Skills:** prism-scan, prism-full, prism-3way, prism-discover, prism-reflect
**Prisms:** `~/.hermes/prisms/` (7 .md files usable as system prompts)

**Limitation:** Single-file analysis only. Model-dependent quality.

---

## 3. Yonkoo11/hermes-dojo ⭐117

https://github.com/Yonkoo11/hermes-dojo

**Type:** Skills + Python scripts
**Tech:** Python
**License:** MIT

Self-improvement system: measure → identify weakness → evolve → measure again → report.

**Install:** `git clone && bash install.sh`
**Installed to:** `~/.hermes/skills/hermes-dojo/`
**Quick test:** `python3 seed_demo_data.py --days 7 && python3 demo.py --reset`
**In Hermes:** `/dojo analyze`

---

## 4. witt3rd/oh-my-hermes ⭐105

https://github.com/witt3rd/oh-my-hermes

**Type:** Skills pack (4 skills) + optional plugin
**Tech:** Python, Markdown
**License:** MIT

Multi-agent orchestration. omh-deep-research (research pipeline), omh-ralplan (consensus planning), omh-deep-interview (Socratic requirements). Requires Hermes v0.7.0+.

---

## 5. Kori-x/hermes-dashboard ⭐62

https://github.com/Kori-x/hermes-dashboard

**Type:** Hermes plugin + Web UI
**Tech:** React 19, TypeScript, Python plugin
**License:** MIT

Real-time dashboard + auto-generated Wiki. Sessions/tool calls/subagents visualization.

**Known issue:** Requires `dashboard_auth` module that may be missing in some Hermes builds.

---

## 6. PCinkusz/hermes-achievements ⭐42

https://github.com/PCinkusz/hermes-achievements

**Type:** Dashboard plugin
**Tech:** Python + Node.js
**License:** MIT

Steam-style achievements from session history. Depends on hermes-dashboard.

---

## 7. Lethe044/hermes-skill-marketplace ⭐42

https://github.com/Lethe044/hermes-skill-marketplace

**Type:** Skills + Python scripts
**Tech:** Python
**License:** MIT

Self-evolving skill factory: watches tasks → extracts patterns → writes skill → tests in sandbox → publishes to agentskills.io. Architecture: Observe → Abstract → Write → Test → Publish + Atropos RL.

---

## 8. Alexeyisme/hermes-spotify-skill ⭐10

https://github.com/Alexeyisme/hermes-spotify-skill

**Type:** Hermes skill
**Tech:** Python (spotipy)
**License:** MIT

Spotify playback control. Linux & RPi 4/5. Works with raspotify.

---

## 9. nmrtn/blacktea ⭐5

https://github.com/nmrtn/blacktea

**Type:** TypeScript library + MCP server
**Tech:** TypeScript, x402 protocol
**License:** MIT

Agent spending controls. Policy-gated payments + audit log. Base USDC. Not relevant for most Chinese users.

---

## Install Patterns Summary

| Pattern | Example | Use When |
|---------|---------|----------|
| `git clone → install.sh` | super-hermes, dojo | Has install.sh |
| `git clone → pnpm i → pnpm build → node entry` | workspace | Standalone web app |
| `git clone → cp skills/ ~/.hermes/skills/` | Generic skill | Bare skills only |
| `hermes dashboard --port 9119` | Built-in | May fail if module missing |
