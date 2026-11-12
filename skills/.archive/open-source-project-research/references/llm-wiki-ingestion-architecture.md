# LLM Wiki (nashsu/llm_wiki) — Ingestion/Import Architecture

## Repository Location

GitHub: https://github.com/nashsu/llm_wiki
- **Language**: TypeScript (Svelte UI + logic) + Rust (Tauri backend)
- **Pattern**: Karpathy's LLM Wiki (three-layer: raw sources → wiki → schema)
- **Notable**: SHA256 incremental cache, two-step LLM ingest chain, source traceability in YAML frontmatter

## Key Architectural Directories

| Directory | Language | Purpose |
|-----------|----------|---------|
| `src/lib/` | TypeScript | Core business logic (ingest pipeline, search, graph, embedding) |
| `src-tauri/src/` | Rust | Tauri commands (file I/O, PDF/Office extraction, HTTP API server) |
| `mcp-server/src/` | TypeScript | MCP server (proxies to Rust HTTP API) |
| `src/stores/` | TypeScript | Svelte/Zustand stores (activity, review, wiki, chat, lint) |
| `src/types/` | TypeScript | Type definitions (wiki.ts: WikiProject, FileNode, WikiPage) |
| `src/components/` | TypeScript/TSX | Svelte UI components |

## File Ingestion Pipeline

### Ingestable Source Extensions (from `src/lib/source-lifecycle.ts`)
```
md, mdx, txt, pdf, doc, docx, pptx, xlsx, odt, odp, ods,
xls, csv, json, html, htm, rtf, xml, yaml, yml, epub, mobi
```
**JSON is fully supported** — read as UTF-8 text, fed into two-step LLM pipeline.

### Two-Step Chain-of-Thought Ingest (`src/lib/ingest.ts`)

```
Step 1 (Analysis): LLM reads source → structured analysis
  - Key entities, concepts, arguments
  - Connections to existing wiki content
  - Contradictions & tensions with existing knowledge
  - Recommendations for wiki structure

Step 2 (Generation): LLM takes analysis → generates wiki files
  - Source summary with frontmatter (type, title, sources[])
  - Entity pages, concept pages with cross-references
  - Updated index.md, log.md, overview.md
  - Review items for human judgment
```

### Key Files in the Pipeline

| File | Role |
|------|------|
| `ingest.ts` | Main analysis+generation prompts, FILE block parser (`parseFileBlocks`) |
| `ingest-queue.ts` | Persistent task queue (saved to `.llm-wiki/ingest-queue.json`) |
| `ingest-cache.ts` | SHA256-based content dedup cache |
| `ingest-sanitize.ts` | Content sanitization before LLM analysis |
| `ingest-parse.ts` | (Not exists? check ingest.ts for FILE_BLOCK parsing) |
| `source-lifecycle.ts` | Enqueue/dequeue sources, `isIngestableSourcePath()`, `importSourceFiles()`, `importSourceFolder()` |
| `scheduled-import.ts` | Directory watcher for auto-import |
| `url-source-import.ts` | HTTP(S) URL fetcher + import |
| `mineru.ts` | MinerU cloud/local PDF processing |
| `file-types.ts` | Extension → category mapping (markdown, text, code, data, etc.) |
| `frontmatter.ts` | YAML frontmatter parsing with wikilink-list repair |
| `source-watch-config.ts` | Source Watch config (extensions, excludes, globs) |
| `source-identity.ts` | Source file → identity mapping for traceability |
| `page-merge.ts` | Merge new LLM content into existing wiki pages |

### SHA256 Cache Mechanism (`ingest-cache.ts`)

- Source file content is SHA256-hashed before ingest
- Cache stored in `.llm-wiki/ingest-cache.json` as `{entries: {filename: {hash, timestamp, filesWritten[]}}}`
- Cache hit only returned if **every previously-written file still exists on disk**
- Otherwise treated as stale → full re-ingest

### Persistent Ingest Queue (`ingest-queue.ts`)

- Serial processing (one LLM call at a time)
- Queue persisted to `.llm-wiki/ingest-queue.json`
- Survives app restart
- Failed tasks auto-retry up to 3 times
- Tasks can be cancelled mid-flight (with file cleanup via `cascadeDeleteWikiPage`)

### Source Watch Auto-Import (`scheduled-import.ts`)

- Monitors a directory for new/changed files
- Copies files into `raw/sources/scheduled-import/` preserving relative path
- Tracks via `.llm-wiki/scheduled-import-db.json`
- Configurable via Source Watch config (file type groups, size limits, exclusion patterns)

## HTTP API Server (Rust, port 19828)

`src-tauri/src/api_server.rs` — built-in tiny_http server.

```
GET    /health                              → status, version, auth info
GET    /api/v1/projects                     → list projects
GET    /api/v1/projects/{id}/files          → file tree (root=wiki|sources|all)
GET    /api/v1/projects/{id}/files/content  → read file content
GET    /api/v1/projects/{id}/reviews        → list review items
PATCH  /api/v1/projects/{id}/reviews/{id}   → update review
POST   /api/v1/projects/{id}/reviews/resolve→ bulk resolve reviews
POST   /api/v1/projects/{id}/search         → hybrid search
GET    /api/v1/projects/{id}/graph          → knowledge graph
POST   /api/v1/projects/{id}/sources/rescan → trigger source watch rescan
POST   /api/v1/projects/{id}/chat           → agent chat (40MB body limit)
POST   /api/v1/projects/{id}/chat/{id}/cancel
```

**No dedicated ingest/import endpoints.** Ingestion is triggered by UI actions, file drops, Clip Server, or Source Watch.

## Clip Server (Rust, port 19827)

`src-tauri/src/clip_server.rs` — companion server for browser extensions:

```
GET  /status          → health
GET  /project         → current project path
POST /project         → set project
GET  /projects        → list projects
POST /projects        → sync project list
GET  /clips/pending   → pop pending clips (browser extension polls this)
POST /clip            → receive new HTML clip for ingest
```

## MCP Server (`mcp-server/src/index.ts`)

9 tools, all proxy to Rust API (port 19828):
- `llm_wiki_status`, `llm_wiki_projects`, `llm_wiki_set_project`
- `llm_wiki_files`, `llm_wiki_read_file`, `llm_wiki_reviews`
- `llm_wiki_search`, `llm_wiki_chat`, `llm_wiki_graph`
- `llm_wiki_rescan_sources`

No direct ingest/write tools except `rescan_sources`.

## Project Directory Structure

```
<project-root>/
├── raw/sources/            # Immutable source files (PDF, MD, JSON, etc.)
│   ├── .cache/             # Pre-processed text cache (auto-managed)
│   ├── scheduled-import/   # Auto-imported files
│   └── <topic>/            # User-organized folders
├── wiki/                   # LLM-generated wiki
│   ├── index.md            # Content catalog
│   ├── overview.md         # Global summary
│   ├── log.md              # Operation log
│   ├── purpose.md          # Wiki intent (user-created)
│   ├── media/<slug>/       # Extracted images
│   ├── sources/            # Source summary pages
│   ├── entities/           # Entity pages
│   └── concepts/           # Concept pages
└── .llm-wiki/              # Internal state
    ├── project.json        # UUID, name
    ├── ingest-queue.json   # Queue persistence
    ├── ingest-cache.json   # SHA256 cache
    └── scheduled-import-db.json
```

## How to Import External JSON (e.g., OS Taxonomy topics.json)

1. Place JSON file into `raw/sources/`
2. File is read as UTF-8 text (data category)
3. SHA256 hash check → if unchanged, skip
4. Two-step LLM pipeline runs automatically
5. Result: Wiki pages generated with `sources: ["filename.json"]` in frontmatter
6. Pages are searchable, graph-connected, vector-embedded

Alternative automated workflows:
- Write a script that copies JSON files into a Source Watch directory
- Use `llm_wiki_rescan_sources` MCP tool to trigger batch re-scan
- Use Clip Server's POST /clip for programmatic injection

## Key Test Files (Good for Understanding API Contracts)

- `src/lib/ingest.prompt.test.ts` — shows exact prompt structure for analysis/generation
- `src/lib/ingest-queue.test.ts` — queue lifecycle
- `src/lib/source-lifecycle.test.ts` — source management edge cases
- `src/lib/ingest-cache.test.ts` — cache hit/miss behavior
- `src/lib/scheduled-import.test.ts` — directory watching
- `src/lib/url-source-import.test.ts` — URL fetching
- `mcp-server/test/api-client.test.ts` — MCP client API surface
