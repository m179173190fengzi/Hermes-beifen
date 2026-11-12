---
name: open-source-project-research
description: "Research open-source GitHub projects — compare multiple in parallel OR deep-dive into a single repo's architecture/ingestion/API. Covers README analysis, codebase exploration via GitHub API, cross-layer data-flow tracing, and structured reporting."
version: 2.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [research, github, open-source, comparison, evaluation, architecture-deep-dive]
    category: research
    related_skills: [github-repo-management, arxiv, blogwatcher, codebase-inspection]
---

# Open-Source Project Research

Research open-source GitHub projects. Two entry points:

1. **Multi-Repo Comparison** — evaluate 2+ projects in parallel with structured comparison
2. **Single-Repo Architecture Deep-Dive** — systematically explore one repo's codebase to understand its architecture, data flow, ingestion pipeline, and API surface

## Reference Files

This skill ships with reference notes for common architectures studied:
- `references/llm-wiki-ingestion-architecture.md` — LLM Wiki's ingest/import pipeline (Tauri + TypeScript, two-step LLM chain, SHA256 cache, source traceability)

## When This Skill Activates

Use this skill when the user:
- Shares links to multiple GitHub repos and asks "学一下", "对比一下", "recommend one", "compare these"
- Asks "哪个好" (which is better) between multiple open-source tools
- Says "研究一下这些项目" or "分析这几个"
- Wants to evaluate open-source options for a specific use case
- Asks "分析一下这个项目的架构" or "研究这个 repo 的导入机制/摄入机制/API" — triggers Single-Repo Deep-Dive mode
- Shares a single repo link and asks "这个怎么用的" / "这个什么原理" / "how does this work"

## Workflow — Multi-Repo Comparison

### Step 1: Identify the Evaluation Criteria

Before diving in, clarify what the user cares about. Common dimensions:
- **Use case alignment** — who is this for? (kids, developers, researchers, teams)
- **Deployment complexity** — desktop app vs self-hosted vs SaaS vs CLI
- **Tech stack** — what languages/frameworks does the user work with?
- **License** — open-source requirement, commercial use
- **Features** — PDF support? Knowledge graphs? MCP? Vector search?
- **Maturity** — stars, releases, maintenance, community

### Step 2: Parallel Research via delegate_task

Use `delegate_task(tasks=[...])` to research projects in parallel. Each task gets a dedicated subagent. **Limit: max_concurrent_children (default 3)** — if more than 3 projects, run in batches.

For each project, the subagent should:
1. **Read the README** — what it does, who it's for, key features
2. **Check repo metadata** — stars, license, recent commits, language
3. **Read ARCHITECTURE.md / docs** if available
4. **Identify the core architecture** — components, data flow, storage
5. **Extract the tech stack** — languages, frameworks, databases
6. **Find deployment options** — Docker, pip install, binary download
7. **Note strengths and limitations** — what it does well, what it doesn't

Each task context should include:
- The full GitHub URL
- What evaluation dimensions to focus on
- Any user-specific context (e.g., "this is for building a kids' knowledge base with PDF support")

### Step 3: Synthesize the Comparison

After all tasks complete, produce a **structured comparison**:

**For 2-4 projects** — a comparison table covering:
| Project | Tech | License | Deploy | Strengths | Best For |

**For 5+ projects** — group by category first, then compare within categories.

Always include:
- **Star count + latest version** for credibility signal
- **License note** — Apache 2.0 is most permissive, AGPL/GPL have implications
- **"Best For" verdict** — which project wins for the user's stated use case

### Step 4: Make a Recommendation

End with a clear recommendation based on the user's context:
- **🏆 最推荐** — the best match
- **备选** — other good options with their trade-offs
- **不适合** — projects that don't fit, and why

Format: concise, structured. User prefers direct Chinese responses with clear "scorecards" (project name + verdict in one line).

## Workflow — Single-Repo Architecture Deep-Dive

Use this when the user asks about a SINGLE repo's internals: architecture, ingestion mechanism, API surface, data flow, or specific feature ("怎么导入", "API 有哪些", "摄入原理").

### Phase 1: Surface Exploration

```bash
# 1. List top-level structure
curl -sL https://api.github.com/repos/{owner}/{repo}/contents/ | jq -r '.[].name'

# 2. Read README (always start here)
curl -sL https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/README.md | head -200

# 3. Check for ARCHITECTURE.md, CONTRIBUTING.md, docs/
curl -sL https://api.github.com/repos/{owner}/{repo}/contents/ | jq -r '.[] | select(.name | test("(?i)doc|arch|contrib|design|plan")) | .name'
```

### Phase 2: Directory-Level Drill Down

Identify the project's language/multi-layer structure. For each key directory:

```bash
# List contents of a subdirectory
curl -sL https://api.github.com/repos/{owner}/{repo}/contents/{path} | jq -r '.[].name'

# Read a specific source file
curl -sL https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/main/{path} | head -300
```

**Key directories to drill into for any project:**
- `src/` or `lib/` — main business logic
- Backend (e.g. `src-tauri/`, `server/`, `api/`) — file I/O, HTTP endpoints
- `types/` or type def files — data model contracts
- `config/` or config files at root — setup, defaults
- `scripts/` — batch tools, diagnostics
- `examples/` — usage patterns (if exists)
- Test files (`*.test.ts`, `*_test.rs`) — API contracts, edge cases

### Phase 3: Core Pipeline Tracing

For a **data-ingestion/import question** (like this session), trace the data flow:

1. **Entry points** — How does data enter the system? (UI drag-drop? CLI? API? URL import? watched directories? clipboard?)
2. **File format support** — Check the file-type/extension mapping (usually a `file-types.ts` or `EXT_MAP`)
3. **Processing pipeline** — What happens to each file? (caching? extraction? LLM analysis? chunking?)
4. **Persistence** — Where does the result go? (filesystem layout, database, cache)
5. **API surface** — What external APIs are exposed? (HTTP, MCP, IPC)
6. **Test files** — Read test files for the pipeline — they reveal interface contracts, edge cases, and expected behaviors often better than implementation code

### Phase 4: Cross-Layer Analysis

When the project has multiple layers (e.g., Rust backend + TypeScript frontend + MCP server):

| Layer | What to Check |
|-------|---------------|
| **Frontend/UI** | `src/stores/` for state management, `src/lib/` for business logic |
| **Backend** | `src-tauri/src/commands/` for file operations, `api_server.rs` for HTTP API, `clip_server.rs` for side-channel servers |
| **MCP/Plugin** | `mcp-server/src/index.ts` for tool definitions, `mcp-server/src/api-client.ts` for backend proxy calls |
| **Types** | `src/types/` for data model contracts (WikiProject, FileNode, etc.) |
| **Config** | `components.json`, `package.json`, `tauri.conf.json`, default JSON configs |

### Phase 5: Compile the Report

Structure the answer as:

```
## Project Overview
- Language stack, architecture pattern, key design decisions

## 1. Entry Points (how data gets in)
- [list all import/ingest mechanisms found]

## 2. File Format Support
- [supported extensions, how each is handled]

## 3. Processing Pipeline
- [step-by-step data flow through the system]

## 4. API Surface
- [HTTP endpoints, MCP tools, IPC commands]

## 5. Persistence & Caching
- [filesystem layout, cache mechanisms, state files]

## 6. Integration Guide (for the user's specific use case)
- [how to bridge external data into this system]
```

Format: Technical, precise, code-backed. Use labeled sections with bullet points — avoid pipe tables (Telegram breaks them). Cite specific file paths from the repo as evidence.

### Reference to Saved Notes

After completing a deep-dive, save the detailed findings as:
```
skill_manage(action='write_file', name='open-source-project-research',
  file_path='references/{repo-name}-{topic}.md',
  file_content='...')
```

This builds a library of known architectures for future sessions. Already saved:
- `references/llm-wiki-ingestion-architecture.md`

## Common Research Sources

| Source | How to Access |
|--------|--------------|
| GitHub README | `curl -sL https://raw.githubusercontent.com/{owner}/{repo}/main/README.md` |
| GitHub repo page | Browser navigation + snapshot |
| Official docs site | Web search or direct navigation |
| Architecture docs | `ARCHITECTURE.md`, `docs/` directory |
| Release notes | `CHANGELOG.md`, GitHub Releases |
| npm/pypi page | `npm.im/{package}`, `pypi.org/project/{package}` |

## Pitfalls

- **Rate limiting**: GitHub unauthenticated has low rate limits. For 4+ repos, stagger requests or use `gh` CLI if authenticated.
- **Obsolete links**: User's repo URLs may be wrong (typos, renamed repos). Verify the URL first with `curl -sI` to check HTTP 200.
- **Fake "stats"**: Star counts don't equal quality. Always check recency of commits and real issue activity.
- **License confusion**: Some repos have unusual licenses (PolyForm Noncommercial, ODbL). Double-check what they allow.
- **Parallel task limits**: max_concurrent_children is 3 by default. Batch larger sets.
- **Auth in subagents**: Subagents inherit the parent's API credentials. If the parent is using a provider with auth issues, subagents will fail too. Add `'web'` toolset to subagents so they can fetch GitHub data via curl/browser independently.
- **Multi-layer blind spots**: In projects with separate frontend + backend (e.g., Tauri apps: TypeScript UI + Rust backend), don't just check one layer. The business logic may be in TypeScript (`src/lib/`) while the file I/O and HTTP API are in Rust (`src-tauri/src/`). Always check BOTH layers.
- **GitHub API pagination**: The GitHub Contents API returns at most 1000 items per directory. For large directories, you'll get a truncated view. Check `'truncated'` field in the API response.
- **Raw content URL branches**: Use `refs/heads/main` not just `main` in raw.githubusercontent.com URLs — some repos use `master`, `develop`, or `main` as default branch. Check with a HEAD request first if `main` 404s.
- **Config vs real behavior**: Don't rely on docs/config comments alone. Read the actual source that parses the config — defaults in code often differ from documented defaults.
- **Test files are gold**: Test files reveal edge cases and expected behaviors that implementation code hides. When studying a complex pipeline, read the test file FIRST to understand the interface contract.

## User Preference Notes

- User (Chinese-speaking) prefers structured reports over prose
- Technical deep-dive reports should cite specific file paths as evidence (`source-lifecycle.ts:42`)
- Direct, no fluff — "说话" style
- For architecture reports: labeled sections with bullet lists (no pipe tables — Telegram rewrites them as row-group bullets anyway)
- Action-first: end with concrete next steps or a call to action in Chinese
