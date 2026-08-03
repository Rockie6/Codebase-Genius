# Testing

## Overview

Codebase Genius ships with a test suite of **26 tests** covering the core machinery: URL handling, file discovery, the code analyzer, and dependency discovery.

### Running the tests

```bash
# Everything
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=codebase_genius/python_helpers --cov-report=term

# Just one file
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_repo_tools.py -v
```

### Test coverage

Latest run:
- **Overall**: 19% of Python helpers
- **repo_tools.py**: 42%
- **analyzer.py**: 28%
- **All 26 tests passing** ✅

## Test Organization

### `tests/test_repo_tools.py` (11 tests)

**URL Validation Tests** (7 tests):
- `test_valid_github_url`: Validates standard GitHub URLs
- `test_valid_github_url_with_git_extension`: Handles `.git` suffix
- `test_valid_gitlab_url`: GitLab URL support
- `test_valid_bitbucket_url`: Bitbucket URL support
- `test_invalid_url_format`: Rejects malformed URLs
- `test_unsupported_host`: Rejects unsupported Git hosts
- `test_missing_owner_or_repo`: Validates owner/repo structure

**File Discovery Tests** (4 tests):
- `test_find_python_entry_points`: Finds main.py, app.py, etc.
- `test_find_init_files`: Locates __init__.py files
- `test_find_priority_files_only`: Verifies only Python entry points are prioritized
- `test_empty_tree`: Handles empty file trees

### `tests/test_analyzer.py` (15 tests)

**CCG Statistics Tests** (3 tests):
- `test_basic_statistics`: Counts classes, functions, modules, and edges
- `test_empty_ccg`: Handles empty code context graphs
- `test_missing_kind_field`: Tolerates malformed data

**Dependency Discovery Tests** (5 tests):
- `test_discover_external_dependencies`: Identifies third-party imports
- `test_discover_stdlib_imports`: Recognizes Python standard library
- `test_discovery_complete_flag`: Detects when discovery is finished
- `test_empty_ccg_discovery`: Handles empty graphs
- `test_module_name_extraction`: Parses module names from paths

**Import Edge Tests** (3 tests):
- `test_naive_parse_emits_import_edges`: Imports surface as graph edges
- `test_build_ccg_creates_import_edges`: Real files produce import edges
- `test_statistics_count_lowercase_edges`: Stats match the edge types we emit

**Iterative Discovery Tests** (3 tests):
- `test_absolute_import_discovery`: Finds and analyzes unanalyzed internal modules
- `test_relative_import_resolution`: Relative imports resolve after analysis
- `test_external_deps_not_treated_as_internal`: Third-party imports stay external

**Integration Tests** (1 test):
- `test_full_analysis_workflow`: End-to-end workflow validation

## Features Tested

### ✅ URL Validation
- GitHub, GitLab, Bitbucket support
- URL format validation
- Owner/repo structure validation
- Normalized URL output

### ✅ File Prioritization
- Entry point detection (main.py, app.py, cli.py, etc.)
- __init__.py discovery
- Exclusion of non-code files (requirements.txt, config files)

### ✅ CCG Statistics
- Class/function/module counting
- Edge type analysis
- Empty graph handling

### ✅ Iterative Dependency Discovery
- External dependency identification
- Standard library filtering
- Completion detection
- Multi-iteration support
- Real import-edge generation (Tree-sitter and naive parser)

## Workflow

1. **Before committing**: run the whole suite.
   ```bash
   python -m pytest tests/ -v
   ```

2. **After changes**: make sure coverage hasn't dropped.
   ```bash
   python -m pytest tests/ --cov=codebase_genius/python_helpers --cov-report=term
   ```

3. **Adding tests**: when you add a feature, add tests alongside it in `tests/`.

## Known limitations

- Coverage is focused on the newer parts (validation, discovery, statistics)
- `docgen.py` isn't covered yet — it needs LLM mocking
- Integration tests only cover the core workflow

## Where to go next

- [ ] Push coverage to 50%+
- [ ] Mock LLM calls and test `docgen.py`
- [ ] Add performance benchmarks
- [ ] Exercise the error-handling paths more
