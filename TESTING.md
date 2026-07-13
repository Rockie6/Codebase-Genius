# Testing Documentation

## Test Suite Overview

This project includes a comprehensive test suite with **20 tests** covering core functionality.

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=codebase_genius/python_helpers --cov-report=term

# Run specific test file
python -m pytest tests/test_analyzer.py -v
python -m pytest tests/test_repo_tools.py -v
```

### Test Coverage

Current test coverage (as of latest run):
- **Overall**: 19% of Python helpers
- **repo_tools.py**: 42% coverage
- **analyzer.py**: 28% coverage
- **All 20 tests passing** ✅

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

### `tests/test_analyzer.py` (9 tests)

**CCG Statistics Tests** (3 tests):
- `test_basic_statistics`: Validates counts for classes, functions, modules, edges
- `test_empty_ccg`: Handles empty code context graphs
- `test_missing_kind_field`: Graceful handling of malformed data

**Dependency Discovery Tests** (5 tests):
- `test_discover_external_dependencies`: Identifies third-party imports
- `test_discover_stdlib_imports`: Recognizes Python standard library
- `test_discovery_complete_flag`: Detects when discovery is finished
- `test_empty_ccg_discovery`: Handles empty graphs
- `test_module_name_extraction`: Parses module names from paths

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

## Development Workflow

1. **Before commits**: Run full test suite
   ```bash
   python -m pytest tests/ -v
   ```

2. **After changes**: Verify coverage didn't drop
   ```bash
   python -m pytest tests/ --cov=codebase_genius/python_helpers --cov-report=term
   ```

3. **Add new tests**: When adding features, create corresponding tests in `tests/`

## Known Limitations

- Coverage focuses on new features (validation, discovery, statistics)
- Full codebase coverage not yet implemented
- Integration tests limited to core workflow
- No tests for `docgen.py` (LLM generation) - requires mocking

## Future Testing Goals

- [ ] Increase coverage to 50%+
- [ ] Add integration tests for full pipeline
- [ ] Mock LLM calls for docgen testing
- [ ] Add performance benchmarks
- [ ] Test error handling paths
