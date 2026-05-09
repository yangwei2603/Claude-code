# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Intelligent file classifier for a digital transformation office. Organizes scattered files into a standardized directory structure based on 4-level priority rules: keyword → LLM semantic → content analysis → extension fallback.

**Entry points**: `run.py` (primary, v5.0), `main.py` (legacy). Both are CLI interfaces.

## Common Commands

```bash
# Preview (no file movement)
python run.py --preview

# Execute actual organization
python run.py --execute

# Full scan (all files, not just recent)
python run.py --execute --full

# Incremental scan (last N days)
python run.py --execute --days 3

# Setup directory structure
python run.py --setup
python run.py --setup --execute

# Watch mode (continuous polling)
python run.py --watch

# Rollback last session
python run.py --rollback

# Duplicate detection
python run.py --duplicates
python run.py --duplicates --execute

# Web UI
python run.py --web --port 5001

# Run tests
pytest tests/ -v
pytest tests/test_classifier.py -v        # single test file
pytest tests/ -v -k "classify"           # by keyword
```

## Architecture

### Core Modules

| File/Package | Role |
|-------------|------|
| `organizer.py` | Monolithic engine (1475 lines, targeted for refactoring into `organizer/` package) |
| `organizer/` | Modular engine package (content_extractor, file_organizer, rollback, constants) |
| `run.py` | Primary CLI entry with argparse |
| `main.py` | Legacy CLI entry (imports from `organizer.py`) |
| `web.py` | Flask Web API (~610 lines) |
| `scheduler.py` | Watch mode polling loop |
| `task_manager.py` | Task CRUD and templates |

### 4-Level Classification Cascade

```
Priority 1: business_domain_rules  (filename keyword → project directory)
Priority 2: keyword_rules         (filename keyword → subdirectory)
Priority 3: content_analysis       (file content extraction → semantic match)
Priority 4: extension_rules        (file extension → extension-only directory)
```

**LLM fallback**: Files unmatched after Priority 2 are sent to LLM (MiniMax/DeepSeek/OpenAI) for semantic classification when `use_llm=True`.

### State & Logs

- `state/organizer_state.json` — processed file hashes (for deduplication)
- `logs/session_*.json` — operation records with rule hit stats

## Known Issues (from SPEC.md v5.0)

- `organizer.py` is 1475 lines, violates single responsibility — refactor into `organizer/` package
- `DEFAULT_RULES` hardcoded in `organizer.py`, duplicated in `config.json` and `templates/*.json`
- Hardcoded `\\` paths break on macOS — use `pathlib.Path` and `/` or `os.sep`
- 8 bare `except:` in `organizer.py` silently swallow exceptions
- `rglob` loads entire directory into memory — use pagination for large dirs
- `web.py` (610 lines) couples business logic with Flask handlers

## Code Conventions

- **Paths**: Always `pathlib.Path`, never `\\` or `/` in strings
- **Exceptions**: Never bare `except:` — catch specific types and log
- **Functions**: All public functions need docstrings and type annotations
- **Rules**: JSON templates in `templates/`, referenced by `--template` flag
- **Config**: `config.json` (forward slashes) with YAML backup in `config.yaml`

## Testing Strategy

Tests live in `tests/`: `test_classifier.py`, `test_file_organizer.py`, `test_llm_classifier.py`. Target is 100% coverage on classification logic. New features require accompanying tests.
