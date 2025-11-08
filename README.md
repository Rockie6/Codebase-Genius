# 🧠 Codebase Genius

**AI-Powered Documentation Generator** | Hybrid JacLang + Python Multi-Agent System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![JacLang](https://img.shields.io/badge/jaclang-0.8.x-purple.svg)](https://github.com/Jaseci-Labs/jaclang)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Generate professional, structured documentation for any public GitHub repository with embedded diagrams, LLM-enhanced summaries, and intelligent code analysis.

---

## ✨ Features

- **🤖 Multi-Agent Architecture**: Jac walkers orchestrating Python helpers
- **📊 Code Context Graph (CCG)**: Analyzes classes, functions, and inheritance relationships
- **🎨 Embedded Diagrams**: Auto-generated class hierarchies and call graphs (Graphviz)
- **🧠 LLM Integration**: Gemini-powered README summarization
- **📈 Complexity Analysis**: Identifies high-complexity functions and hotspots
- **🌐 Modern Web UI**: Beautiful, responsive frontend
- **🔄 Robust Error Handling**: URL validation, retry logic, graceful fallbacks
- **📦 Structured Output**: Installation, Usage, Architecture, API Reference sections

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git
- (Optional) Gemini API key for LLM summaries
- (Optional) Graphviz for diagram generation

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/codebase-genius
cd codebase-genius

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Graphviz (for diagrams)
sudo apt-get install graphviz  # Ubuntu/Debian
# brew install graphviz         # macOS
# choco install graphviz        # Windows
```

### Configuration

Create a `.env` file in the project root:

```bash
# Enable LLM-enhanced summaries (optional)
USE_LLM=true
GEMINI_API_KEY=your_api_key_here
```

### Start the Server

```bash
# Using the convenience script
python start_server.py

# Or directly with uvicorn
export $(cat .env | xargs)
uvicorn codebase_genius.api_server:app --host 0.0.0.0 --port 8000
```

**Server will be available at:**
- 🎨 **Web UI**: http://localhost:8000/gui
- 📚 **API Docs**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/health

---

## 📖 Usage

### Web Interface

1. Open http://localhost:8000/gui in your browser
2. Enter a GitHub repository URL (e.g., `https://github.com/requests/requests`)
3. Click "Generate Documentation"
4. View the generated documentation in `outputs/<repo_name>/docs.md`

### API Usage

#### Generate Documentation

```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{
    "repo_url": "https://github.com/pallets/flask",
    "analyze": true
  }'
```

**Response:**

```json
{
  "status": "ok",
  "markdown_path": "./outputs/flask/docs.md",
  "repo_url": "https://github.com/pallets/flask",
  "file_count": 245,
  "summary_length": 100
}
```

#### Health Check

```bash
curl http://localhost:8000/health
```

### Command Line

Generate documentation directly:

```bash
python generate_sample.py https://github.com/owner/repo
```

Or use the Jac orchestrator:

```bash
jac run codebase_genius/main.jac
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Codebase Genius                          │
│                   (Supervisor Walker)                         │
└──────────────┬────────────────────────────────┬──────────────┘
               │                                │
      ┌────────▼────────┐              ┌───────▼────────┐
      │  Repo Mapper    │              │ Code Analyzer  │
      │   (Jac Agent)   │              │  (Jac Agent)   │
      └────────┬────────┘              └───────┬────────┘
               │                                │
      ┌────────▼────────┐              ┌───────▼────────┐
      │  repo_tools.py  │              │ analyzer.py    │
      │  - Clone repo   │              │ - Build CCG    │
      │  - File tree    │              │ - Detect       │
      │  - README       │              │   inheritance  │
      └─────────────────┘              └────────────────┘
                     │                          │
                     └──────────┬───────────────┘
                                │
                       ┌────────▼────────┐
                       │   DocGenie      │
                       │  (Jac Agent)    │
                       └────────┬────────┘
                                │
                       ┌────────▼────────┐
                       │   docgen.py     │
                       │ - Generate MD   │
                       │ - Create        │
                       │   diagrams      │
                       │ - Query CCG     │
                       └─────────────────┘
```

### Components

#### **Jac Walkers** (Orchestration Layer)
- `orchestrate` - Main pipeline coordinator
- `repo_mapper` - Repository mapping agent
- `code_analyzer` - Code analysis agent
- `generate_docs` - Documentation generation agent

#### **Python Helpers** (Implementation Layer)
- `repo_tools.py` - Git operations, file trees, README extraction
- `analyzer.py` - Code parsing, CCG construction, complexity analysis
- `docgen.py` - Markdown generation, diagram rendering
- `llm.py` - Gemini LLM integration

#### **FastAPI Server** (`api_server.py`)
- `/generate` - Main documentation generation endpoint
- `/health` - Health check endpoint
- `/gui` - Static web interface
- `/docs` - Auto-generated API documentation

---

## 📊 Generated Documentation Structure

The system generates comprehensive documentation with the following sections:

### 1. **Overview**
- LLM-enhanced README summary
- Repository metadata

### 2. **Installation**
- Auto-detected installation instructions
- Supports `requirements.txt`, `setup.py`, `pyproject.toml`

### 3. **Usage**
- Detected entry points (main.py, app.py, etc.)
- Quick start examples

### 4. **Architecture**
- Symbol statistics (classes, functions, modules)
- Relationship counts (calls, inheritance)
- Base class identification

### 5. **Code Diagrams**
- **Class Hierarchy**: Visual inheritance tree
- **Call Graph**: Function call relationships (colored by complexity)
- **Full CCG**: Complete code context graph

### 6. **API Reference**
- Classes grouped by file
- High-complexity functions (>10 complexity)
- Most-called functions (hotspots)

### 7. **Project Structure**
- Complete file tree

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `USE_LLM` | Enable LLM-enhanced summaries | `false` | No |
| `GEMINI_API_KEY` | Google Gemini API key | - | If `USE_LLM=true` |

### Supported Repository Hosts

- ✅ GitHub
- ✅ GitLab (basic support)
- ✅ BitBucket (basic support)

---

## 📁 Project Structure

```
codebase-genius/
├── codebase_genius/
│   ├── __init__.py
│   ├── main.jac                 # Main orchestration walker
│   ├── api.jac                  # Jac serve API (experimental)
│   ├── api_server.py            # FastAPI server
│   ├── agents/
│   │   ├── analyzer.jac         # Code analysis agent
│   │   ├── docgen.jac           # Documentation generation agent
│   │   └── repo_mapper.jac      # Repository mapping agent
│   ├── python_helpers/
│   │   ├── analyzer.py          # CCG construction & parsing
│   │   ├── docgen.py            # Markdown & diagram generation
│   │   ├── llm.py               # LLM integration
│   │   └── repo_tools.py        # Git operations & file handling
│   └── gui/
│       └── index.html           # Web interface
├── outputs/                     # Generated documentation
├── .env                         # Environment configuration
├── requirements.txt             # Python dependencies
├── start_server.py              # Server startup script
├── generate_sample.py           # CLI sample generator
├── test_pipeline.py             # Pipeline test suite
└── README.md                    # This file
```

---

## 🧪 Testing

### Run Pipeline Test

```bash
python test_pipeline.py
```

### Generate Sample Documentation

```bash
python generate_sample.py https://github.com/requests/requests
```

### Test Specific Components

```bash
# Validate Jac syntax
jac check codebase_genius/agents/analyzer.jac

# Test URL validation
python -c "
from codebase_genius.python_helpers.repo_tools import validate_repo_url
print(validate_repo_url('https://github.com/psf/requests'))
"
```

---

## 🎯 Example Output

See `outputs/sample_output/` for a complete example generated from the **requests** library:

- **Documentation**: `docs.md` (318 lines, 8KB)
- **Class Hierarchy Diagram**: `class_hierarchy.png` (6KB)
- **Code Context Graph**: `ccg.png` (37KB)

### Statistics
- 861 symbols analyzed (103 classes, 595 functions)
- 57 inheritance relationships detected
- 6/6 documentation sections completed
- 2 embedded diagrams

---

## 🛠️ Development

### Prerequisites for Development

```bash
pip install -r requirements.txt
```

### Run in Development Mode

```bash
# Start with auto-reload
uvicorn codebase_genius.api_server:app --reload --port 8000
```

### Jac Development

```bash
# Check syntax
jac check codebase_genius/main.jac

# Run walker
jac run codebase_genius/main.jac
```

---

## 🐛 Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Kill process on port 8000
fuser -k 8000/tcp
```

**2. Graphviz not found**
```bash
# Install Graphviz
sudo apt-get install graphviz
```

**3. LLM not working**
```bash
# Verify environment variables
echo $USE_LLM
echo $GEMINI_API_KEY
```

**4. Jac syntax errors**
```bash
# Ensure JacLang is installed
pip install --upgrade jaclang
```

**5. Private repository access**

The system currently only supports public repositories. Private repos will return an authentication error.

---

## 📈 Roadmap

- [ ] **Enhanced Supervisor**: Intelligent file prioritization and planning
- [ ] **Iterative Discovery**: Dependency-driven module analysis
- [ ] **Multi-language Support**: JavaScript, TypeScript, Java, etc.
- [ ] **Call Graph Analysis**: Full function call tracking
- [ ] **Import Graph**: Module dependency visualization
- [ ] **Jac Serve API**: Native Jac HTTP endpoints
- [ ] **Streaming Progress**: Real-time generation updates
- [ ] **Caching**: Incremental analysis for large repos
- [ ] **Custom Templates**: Configurable documentation formats
- [ ] **CLI Tool**: Standalone command-line interface

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **JacLang Team** for the innovative programming language
- **Gemini AI** for LLM capabilities
- **FastAPI** for the excellent web framework
- **Graphviz** for diagram generation
- Open source community for inspiration and tools

---

## 📞 Support

For issues, questions, or suggestions:
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/codebase-genius/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/codebase-genius/discussions)

---

<div align="center">
  <strong>Made with ❤️ using JacLang</strong>
  <br>
  <sub>Multi-agent architecture • LLM-enhanced • Professional documentation</sub>
</div>
