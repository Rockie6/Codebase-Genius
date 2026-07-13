# 🧠 Codebase Genius

AI-powered documentation generator for GitHub repositories using pure Python architecture.

## ✨ Features

- 🤖 **Orchestrated pipeline** with intelligent code analysis
- 🔍 **Iterative dependency discovery** with intelligent module analysis
- 📊 **Code Context Graph (CCG)** analysis with statistics
- 🎨 **Modern web UI** with download and preview functionality
- ✅ **URL validation** for GitHub, GitLab, and Bitbucket
- 🧪 **Comprehensive test suite** (20 tests, all passing)

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/codebase-genius
cd codebase-genius
python3 -m venv .venv
source .venv/bin/activate
pip install -r codebase_genius/requirements.txt

# Configure (optional - for LLM features)
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Start server
python start_server.py

# Open browser
# http://localhost:8000/gui
```

## 📖 Usage

### Web Interface
1. Open http://localhost:8000/gui
2. Enter a GitHub repository URL
3. Click "Generate Documentation"
4. Download or preview the generated documentation

### API
```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"repo_url": "https://github.com/pallets/flask"}'
```

### Command Line
```bash
python generate_sample.py https://github.com/owner/repo
```

## 🏗️ Architecture

**Orchestrator** (Python):
- `orchestrator.py` - Main pipeline with iterative discovery and coordination

**Python Helpers** (Implementation):
- `repo_tools.py` - URL validation, Git operations, file discovery
- `analyzer.py` - CCG construction, statistics, dependency discovery
- `docgen.py` - Markdown generation with LLM integration
- `llm.py` - Gemini API integration

**API & UI**:
- `api_server.py` - FastAPI server for REST endpoints
- `gui/index.html` - Modern web interface

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=codebase_genius/python_helpers --cov-report=term
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

## 📁 Project Structure

```
codebase_genius/
├── orchestrator.py       # Main orchestration pipeline
├── api_server.py         # FastAPI server
├── python_helpers/       # Core implementation modules
│   ├── repo_tools.py     # Repository operations
│   ├── analyzer.py       # Code analysis
│   ├── docgen.py         # Documentation generation
│   └── llm.py            # LLM integration
└── gui/                  # Web interface
tests/                    # Test suite

## 🔧 Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `USE_LLM` | Enable LLM features | No |
| `GEMINI_API_KEY` | Google Gemini API key | If USE_LLM=true |

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ using Python
