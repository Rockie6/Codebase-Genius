# Codebase Genius

An agentic Jac + Python system that ingests a public GitHub repository and produces high-quality Markdown documentation (file tree, README summary, API relationships, diagrams) using a multi-agent pipeline.

## Architecture Overview
Agents (implemented as Jac walkers + Python helper modules):
- Supervisor (CodeGenius): orchestrates end-to-end flow.
- Repo Mapper: clones repo, builds file tree, summarizes README.
- Code Analyzer: builds a Code Context Graph (functions/classes relationships) via parsing (Tree-sitter planned).
- DocGenie: synthesizes Markdown docs including diagrams (Graphviz) and saves to `outputs/<repo_name>/docs.md`.

## Directory Structure
```
codebase_genius/
  README.md
  requirements.txt
  main.jac               # Jac walkers + graph types
  agents/                # (Optional) future split-out Jac modules
  python_helpers/
    repo_tools.py        # cloning, file tree, README summary
    analyzer.py          # code parsing & context graph stubs
    docgen.py            # markdown + diagram generation
  outputs/               # generated documentation artifacts
  .env.example           # environment variable template
```

## Quick Start
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your OPENAI_API_KEY or other provider keys if needed
uvicorn api_server:app --host 0.0.0.0 --port 8000  # start FastAPI deployment
## (Optional) Jac walker (placeholder walker prints a hint)
jac enter main.jac -e orchestrate
## Jac HTTP API (serve walkers)
jac serve api.jac
```

### Example API Usage
POST to `http://localhost:8000/generate` with JSON body:
```bash
curl -s -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/psf/requests"}'
```
Response includes markdown path and symbol count.

### Jac Serve Example
Start server:
```bash
jac serve codebase_genius/api.jac
```
Invoke walker (assuming server binds http://127.0.0.1:8000):
```bash
curl -s -X POST http://127.0.0.1:8000/generate_docs_api \
  -H 'Content-Type: application/json' \
  -d '{"repo_url":"https://github.com/Rockie6/Generative-AI"}'
```
Expected JSON:
```json
# Codebase Genius

Hybrid Jac + Python multi-agent system that ingests a Git repository, analyzes structure & complexity, and produces rich Markdown documentation (with optional LLM summaries & GUI).

## Overview

Pipeline (Jac orchestration + Python helpers):
1. Clone + map repo (retry & error capture)
2. Analyze functions (approx complexity)
3. Generate Markdown docs (complexity + summaries)
4. Return JSON + write `docs.md`

Optional: Gemini LLM README summarization, diagram test scaffold, minimal static GUI.

## Features

- Jac walkers: `repo_mapper`, `code_analyzer`, `doc_genie`, `orchestrate`
- FastAPI endpoints: `/generate`, `/health`, static GUI `/gui`
- Complexity estimation (naive) included in output
- LLM fallback strategy (heuristics when disabled/unavailable)
- Clone retry (exponential backoff)
- Structured error propagation

## Getting Started

### Prerequisites
- Python 3.11+
- Git installed
- (Optional) Gemini API key for LLM summaries

### Install Dependencies

```bash
make install
```

### Run the Service

```bash
make run
```

Open GUI: http://localhost:8000/gui

### Generate Docs via API

```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"repo_url": "https://github.com/pallets/flask", "analyze": true}'
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `USE_LLM` | Set to `true` to enable LLM summarization |
| `GEMINI_API_KEY` | Gemini API key (required if `USE_LLM=true`) |

### Output Location

Default docs path: `outputs/Generative-AI/docs.md` (subject to change). API response returns path + summary snippet.

## Jac Orchestration

Located in `main.jac` `walker orchestrate`:
1. Calls repo mapping walker
2. Performs analysis walker
3. Invokes doc generation walker
4. Aggregates results for API

## Error Handling

- Clone retry: transient network issues handled automatically
- Mapping error field returned if cloning fails
- LLM errors swallow + fallback summary applied

## Makefile Targets

```bash
make install       # Install dependencies
make run           # Start FastAPI (uvicorn)
make test          # Smoke test pipeline
make test-diagram  # Diagram presence test
make docker-build  # Build Docker image
make docker-run    # Run container locally
```

## Docker Usage

```bash
make docker-build
make docker-run
```

Service then available on `http://localhost:8000` (GUI at `/gui`).

## Continuous Integration

GitHub Action (not shown) runs install, smoke test, and docker build for regression safety.

## Roadmap

- Jac-native HTTP endpoint (parsing issues pending in `api.jac`)
- Enhanced GUI (markdown render, streaming progress)
- Advanced analysis: imports graph, call graph, inheritance hierarchy
- Multi-language parsing refinement (tree-sitter deeper integration)
- Config system (.env + feature flags)
- CLI interface wrapper
- Security & licensing audit
- Packaging (`pyproject.toml`, versioning, distribution)
- Incremental/cached analysis

## Troubleshooting

1. Jac parse errors: verify JacLang version in `requirements.txt` installed.
2. LLM inactive: ensure `USE_LLM=true` and `GEMINI_API_KEY` exported.
3. Graphviz missing: install system package providing `dot`.
4. IDE import warnings: create venv & run `make install`.

## License

Add appropriate license (e.g., Apache-2.0 or MIT) — pending.
