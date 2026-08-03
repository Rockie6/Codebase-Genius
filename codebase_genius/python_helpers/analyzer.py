"""The analyzer: reads source code and builds a Code Context Graph (CCG).

Uses Tree-sitter when it's available, and falls back to a simple line-based
parser otherwise. The CCG is our internal map of the codebase — who defines
what, and how the pieces reference each other.
"""
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Optional Tree-sitter support (graceful fallback if unavailable)
try:
    # Prebuilt grammars; successor of the discontinued tree_sitter_languages.
    from tree_sitter_language_pack import get_parser  # type: ignore

    HAS_TREESITTER = True
except Exception:  # pragma: no cover - optional path
    try:
        # Fallback for environments that still have the old package.
        from tree_sitter_languages import get_parser  # type: ignore

        HAS_TREESITTER = True
    except Exception:  # pragma: no cover - optional path
        HAS_TREESITTER = False

SUPPORTED_EXT = {".py"}

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".mypy_cache",
}


class CodeContextGraph:
    """An in-memory map of the symbols we've found and how they connect."""

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # Edge list items: {"source": key, "target": key, "type": str}
        self.edges: List[Dict[str, str]] = []

    def add_symbol(
        self, file_path: str, symbol_name: str, kind: str, **kwargs: Any
    ) -> None:
        key = f"{file_path}:{symbol_name}"
        if key not in self.nodes:
            self.nodes[key] = {
                "file": file_path,
                "name": symbol_name,
                "kind": kind,
                "complexity": kwargs.get("complexity", 1),
            }
        else:
            # Update complexity if provided
            if "complexity" in kwargs:
                self.nodes[key]["complexity"] = kwargs["complexity"]

    def add_edge(self, source: str, target: str, edge_type: str) -> None:
        """Record a relationship. Types: calls, inherits, imports, contains."""
        self.edges.append({
            "source": source,
            "target": target,
            "type": edge_type,
        })

    def query_calls_to(self, target_symbol: str) -> List[str]:
        """Find all symbols that call target_symbol."""
        return [
            e["source"]
            for e in self.edges
            if e["type"] == "calls" and target_symbol in e["target"]
        ]

    def query_inherits_from(self, base_class: str) -> List[str]:
        """Find all classes that inherit from base_class."""
        return [
            e["source"]
            for e in self.edges
            if e["type"] == "inherits" and base_class in e["target"]
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
        }


def naive_parse(file_content: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]]]:
    """Simple symbol finder: catches defs/classes/imports line by line.

    Returns:
        symbols: list of symbol dicts
        edges: list of (source, target, edge_type) tuples
    """
    symbols: List[Dict[str, Any]] = []
    edges: List[Tuple[str, str, str]] = []
    current_func: Optional[str] = None
    func_lines: List[str] = []
    
    for line in file_content.splitlines():
        line_strip = line.strip()
        
        # Detect inheritance: class Foo(Bar):
        if line_strip.startswith("class "):
            # finalize function if open
            if current_func and func_lines:
                complexity = _estimate_complexity(func_lines)
                symbols.append({
                    "name": current_func,
                    "kind": "function",
                    "complexity": complexity,
                })
                current_func = None
                func_lines = []
            
            parts = line_strip.split("class ")[1]
            if "(" in parts:
                name = parts.split("(")[0]
                bases_str = parts.split("(")[1].split(")")[0]
                bases = [b.strip() for b in bases_str.split(",") if b.strip()]
                symbols.append({"name": name, "kind": "class"})
                # Add inheritance edges
                for base in bases:
                    if base and base != "object":
                        edges.append((name, base, "inherits"))
            else:
                name = parts.split(":")[0]
                symbols.append({"name": name, "kind": "class"})
        
        elif line_strip.startswith("def "):
            # finalize previous function
            if current_func and func_lines:
                complexity = _estimate_complexity(func_lines)
                symbols.append({
                    "name": current_func,
                    "kind": "function",
                    "complexity": complexity,
                })
            current_func = line_strip.split("def ")[1].split("(")[0]
            func_lines = []
            # Handle single-line body: "def foo(): pass"
            if "):" in line_strip:
                rest = line_strip.split("):", 1)[-1].strip()
                if rest:
                    func_lines.append(rest)
        
        # Detect imports
        elif line_strip.startswith("import ") or line_strip.startswith("from "):
            # Simple heuristic: capture imported module names and import edges.
            # Edges use the full dotted module path so dependency discovery can
            # resolve internal modules (e.g. "flask.app" or ".utils").
            if line_strip.startswith("import "):
                mod_name = line_strip.split("import ")[1].split()[0]
                root = mod_name.split(".")[0]
                symbols.append({"name": root, "kind": "module"})
                edges.append((None, mod_name, "imports"))
            elif line_strip.startswith("from "):
                mod_name = line_strip.split("from ")[1].split(" import")[0].strip()
                root = mod_name.split(".")[0]
                symbols.append({"name": root, "kind": "module"})
                edges.append((None, mod_name, "imports"))
        else:
            if current_func:
                func_lines.append(line_strip)
    
    # finalize tail function
    if current_func and func_lines:
        complexity = _estimate_complexity(func_lines)
        symbols.append({
            "name": current_func,
            "kind": "function",
            "complexity": complexity,
        })
    
    return symbols, edges


def _estimate_complexity(lines: List[str]) -> int:
    """Rough complexity estimate based on branching keywords (if/for/and/or...)."""
    score = 1
    for line in lines:
        if any(
            k in line
            for k in [
                "if ",
                "elif ",
                "for ",
                "while ",
                " and ",
                " or ",
                " except ",
            ]
        ):
            score += 1
    return score


def _add_file_to_ccg(ccg: CodeContextGraph, fpath: str, content: str) -> None:
    """Parse a single Python source file and add symbols/edges to the graph."""
    ext = Path(fpath).suffix
    symbols: List[Dict[str, Any]] = []
    call_edges: List[Tuple[str, str]] = []  # (caller, callee)
    inherit_edges: List[Tuple[str, str]] = []  # (child, parent)
    import_edges: List[str] = []  # imported module targets

    if ext == ".py" and HAS_TREESITTER:
        try:
            ts_symbols, ts_calls, ts_imports, ts_inherits = (
                _py_symbols_and_calls_treesitter(content)
            )
            symbols = ts_symbols
            call_edges = ts_calls
            import_edges = ts_imports
            inherit_edges = ts_inherits
        except Exception:
            symbols, edges = naive_parse(content)
            inherit_edges = [
                (src, tgt) for src, tgt, etype in edges if etype == "inherits"
            ]
            import_edges = [tgt for src, tgt, etype in edges if etype == "imports"]
    else:
        symbols, edges = naive_parse(content)
        inherit_edges = [
            (src, tgt) for src, tgt, etype in edges if etype == "inherits"
        ]
        import_edges = [tgt for src, tgt, etype in edges if etype == "imports"]

    for s in symbols:
        ccg.add_symbol(
            fpath,
            s["name"],
            s["kind"],
            complexity=s.get("complexity", 1),
        )

    # Add call edges
    for caller, callee in call_edges:
        src = f"{fpath}:{caller}"
        tgt = f"{fpath}:{callee}"
        # Ensure target exists (best-effort)
        if tgt not in ccg.nodes:
            ccg.add_symbol(fpath, callee, "function")
        if src not in ccg.nodes:
            ccg.add_symbol(fpath, caller, "function")
        ccg.add_edge(src, tgt, "calls")

    # Add inheritance edges
    for child, parent in inherit_edges:
        src = f"{fpath}:{child}"
        tgt = f"{fpath}:{parent}"
        # Ensure both exist
        if src not in ccg.nodes:
            ccg.add_symbol(fpath, child, "class")
        if tgt not in ccg.nodes:
            ccg.add_symbol(fpath, parent, "class")
        ccg.add_edge(src, tgt, "inherits")

    # Add import edges (file-level: source is the importing file path)
    for module in import_edges:
        ccg.add_edge(fpath, module, "imports")


def _seed_ccg_from_dict(ccg: CodeContextGraph, ccg_dict: Dict[str, Any]) -> None:
    """Seed a CodeContextGraph from an existing CCG dict (for iterative merging)."""
    for n in ccg_dict.get("nodes", []):
        key = f"{n.get('file', '')}:{n.get('name', '')}"
        if key not in ccg.nodes:
            ccg.nodes[key] = {
                "file": n.get("file", ""),
                "name": n.get("name", ""),
                "kind": n.get("kind", ""),
                "complexity": n.get("complexity", 1),
            }
    ccg.edges = list(ccg_dict.get("edges", []))


def list_python_files(root_path: str) -> List[str]:
    """Return all supported source file paths under root_path."""
    files: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [
            d for d in dirnames if d not in IGNORE_DIRS
        ]
        for fname in filenames:
            if Path(fname).suffix in SUPPORTED_EXT:
                files.append(os.path.join(dirpath, fname))
    return files


def analyze_files(
    file_paths: List[str],
    base_ccg: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse a specific list of files into a CCG dict.

    Args:
        file_paths: Source files to analyze
        base_ccg: Optional existing CCG to merge into (iterative discovery)

    Returns:
        Merged CCG as a dict
    """
    ccg = CodeContextGraph()
    if base_ccg:
        _seed_ccg_from_dict(ccg, base_ccg)

    for fpath in file_paths:
        if Path(fpath).suffix not in SUPPORTED_EXT:
            continue
        try:
            content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        _add_file_to_ccg(ccg, fpath, content)

    return ccg.to_dict()


def build_ccg(root_path: str) -> Dict[str, Any]:
    ccg = CodeContextGraph()
    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            ext = Path(fname).suffix
            if ext not in SUPPORTED_EXT:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                content = Path(fpath).read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except Exception:
                continue
            _add_file_to_ccg(ccg, fpath, content)
    return ccg.to_dict()


def analyze_repo(repo_path: str) -> Dict[str, Any]:
    return build_ccg(repo_path)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_path")
    args = ap.parse_args()
    result = analyze_repo(args.repo_path)
    print(json.dumps(result, indent=2))


# ---- Internal helpers (Tree-sitter best-effort) ----
def _py_symbols_and_calls_treesitter(
    content: str,
) -> Tuple[List[Dict[str, str]], List[Tuple[str, str]], List[str], List[Tuple[str, str]]]:
    """Extract Python symbols, intra-function calls, imports, and inheritance.
    Requires a tree-sitter python grammar; caller wraps in try/except.

    Returns:
        symbols: list of symbol dicts
        calls: list of (caller, callee) tuples
        imports: list of imported module targets (dotted paths, may start with '.')
        inherits: list of (child_class, base_class) tuples
    """
    parser = get_parser("python")  # type: ignore[name-defined]
    tree = parser.parse(bytes(content, "utf-8"))

    symbols: List[Dict[str, str]] = []
    calls: List[Tuple[str, str]] = []
    imports: List[str] = []
    inherits: List[Tuple[str, str]] = []

    # Minimal recursive walk to capture definitions, calls, and imports
    def node_text(node) -> str:
        return content[node.start_byte:node.end_byte]

    current_func: Optional[str] = None

    def walk(node):
        nonlocal current_func
        t = node.type

        # function_definition: first child with type 'identifier' is the name
        if t == "function_definition":
            # Children: 'def', name(identifier), parameters, ':' , block
            name = None
            for ch in node.children:
                if ch.type == "identifier":
                    name = node_text(ch)
                    break
            if name:
                symbols.append({"name": name, "kind": "function"})
                prev = current_func
                current_func = name
                for ch in node.children:
                    walk(ch)
                current_func = prev
                return

        # class_definition: first child identifier is name
        if t == "class_definition":
            name = None
            for ch in node.children:
                if ch.type == "identifier":
                    name = node_text(ch)
                    break
            if name:
                symbols.append({"name": name, "kind": "class"})
                # Extract base classes (e.g. Foo(Base, Mixin)); grammar uses
                # "superclass" (older grammars) or "argument_list" (newer).
                for ch in node.children:
                    if ch.type in ("superclass", "argument_list"):
                        bases: List[str] = []
                        _collect_base_names(ch, node_text, bases)
                        for base in bases:
                            if base != name and base != "object":
                                inherits.append((name, base))

        # import a.b.c, d  -> capture full dotted module paths
        if t == "import_statement":
            for ch in node.children:
                if ch.type == "dotted_name":
                    imports.append(node_text(ch))
                elif ch.type == "aliased_import":
                    for c in ch.children:
                        if c.type == "dotted_name":
                            imports.append(node_text(c))
                            break

        # from <module> import <names>  (module may be relative: "..utils")
        if t == "import_from_statement":
            module_parts: List[str] = []
            for ch in node.children:
                if ch.type == "import":  # only the module part precedes it
                    break
                if ch.type == "relative_import":
                    module_parts.append(node_text(ch))
                elif ch.type == "dotted_name":
                    module_parts.append(node_text(ch))
            if module_parts:
                imports.append("".join(module_parts))

        # call: extract simple identifier callee
        if t == "call":
            # Heuristic: first child may be the function name
            if node.children:
                fn = node.children[0]
                # For attribute access (obj.method), child may be attribute
                callee = None
                if fn.type == "identifier":
                    callee = node_text(fn)
                elif fn.type == "attribute":
                    # attribute -> child identifier is the attribute name
                    for ch in fn.children:
                        if ch.type == "property_identifier":
                            callee = node_text(ch)
                            break
                        if ch.type == "identifier":  # fallback
                            callee = node_text(ch)
                            break
                if callee and current_func:
                    calls.append((current_func, callee))

        for ch in node.children:
            walk(ch)

    walk(tree.root_node)
    return symbols, calls, imports, inherits


def _collect_base_names(
    node,
    node_text,
    out: List[str],
) -> None:
    """Collect base-class names from a superclass node, skipping call args."""
    if node.type == "call":
        return
    if node.type in ("identifier", "attribute"):
        out.append(node_text(node))
        return
    for ch in node.children:
        _collect_base_names(ch, node_text, out)


def aggregate_ccg_statistics(ccg: Dict[str, Any]) -> Dict[str, Any]:
    """Aggregate comprehensive statistics from CCG for reporting.
    
    Args:
        ccg: Code Context Graph with nodes and edges
        
    Returns:
        Dictionary with detailed statistics breakdown
    """
    nodes = ccg.get("nodes", [])
    edges = ccg.get("edges", [])
    
    # Count node types
    classes = sum(1 for n in nodes if n.get("kind") == "class")
    functions = sum(1 for n in nodes if n.get("kind") == "function")
    modules = sum(1 for n in nodes if n.get("kind") == "module")
    
    # Count edge types (lowercase, matching what build_ccg produces)
    inheritance_edges = sum(1 for e in edges if e.get("type") == "inherits")
    call_edges = sum(1 for e in edges if e.get("type") == "calls")
    import_edges = sum(1 for e in edges if e.get("type") == "imports")
    
    return {
        "total_symbols": len(nodes),
        "classes": classes,
        "functions": functions,
        "modules": modules,
        "total_edges": len(edges),
        "inheritance_edges": inheritance_edges,
        "call_edges": call_edges,
        "import_edges": import_edges,
    }


def discover_dependencies(ccg: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
    """Discover unanalyzed dependencies from CCG imports.
    
    Analyzes "imports" edges to find:
    - External dependencies (stdlib, third-party)
    - Internal modules not yet analyzed
    - Potential files to parse next
    
    Args:
        ccg: Code Context Graph with nodes and edges
        repo_path: Path to repository root
        
    Returns:
        Dictionary with discovered dependencies and recommendations
    """
    edges = ccg.get("edges", [])
    nodes = ccg.get("nodes", [])
    
    # Get all analyzed modules, derived from the files that were actually
    # parsed into the CCG (e.g. ".../flask/flask/app.py" -> "flask.app").
    # Using file paths instead of module-kind node names prevents imported
    # modules from being misclassified as "already analyzed".
    analyzed_modules: Set[str] = set()
    for n in nodes:
        fpath = n.get("file")
        if not fpath:
            continue
        rel = os.path.relpath(fpath, repo_path)
        if rel.startswith(os.pardir):
            rel = os.path.basename(fpath)
        if rel.endswith(".py"):
            rel = rel[:-3]
        analyzed_modules.add(rel.replace(os.sep, "."))

    # Extract all imported modules from "imports" edges
    imported_modules = set()
    for edge in edges:
        if edge.get("type") == "imports":
            target = edge.get("target", "")
            # Extract module name (could be like "module:symbol" or just "module")
            module_name = target.split(":")[0] if ":" in target else target
            if module_name:
                imported_modules.add(module_name)
    
    # Find unanalyzed internal modules
    repo_name = os.path.basename(repo_path)
    unanalyzed_internal = set()
    external_deps = set()
    stdlib_imports = set()
    
    # Common stdlib modules
    STDLIB_MODULES = {
        "os", "sys", "re", "json", "time", "datetime", "collections",
        "itertools", "functools", "pathlib", "typing", "abc", "enum",
        "logging", "argparse", "configparser", "io", "shutil", "subprocess",
        "threading", "multiprocessing", "asyncio", "contextlib", "traceback",
        "unittest", "pytest", "math", "random", "string", "copy", "pickle"
    }
    
    potential_files = []
    for module in imported_modules:
        # Normalize relative imports for comparison: ".utils" -> "utils"
        base = module.lstrip(".")
        if not base:
            # Bare relative import ("from . import x") doesn't name a module
            continue

        # Skip already analyzed modules (exact match or relative suffix match,
        # e.g. ".utils" resolves once "myapp.utils" has been analyzed)
        if module in analyzed_modules or base in analyzed_modules:
            continue
        if any(a == base or a.endswith("." + base) for a in analyzed_modules):
            continue

        # Check if it's a standard library module
        module_root = module.split(".")[0].lstrip(".")
        if module_root in STDLIB_MODULES:
            stdlib_imports.add(module)
            continue

        # Convert module name to potential file path
        # e.g., "myapp.utils" -> "myapp/utils.py"; ".utils" -> "utils.py"
        module_path = base.replace(".", "/")
        potential_py = os.path.join(repo_path, f"{module_path}.py")
        potential_init = os.path.join(repo_path, module_path, "__init__.py")

        # Treat as internal if it's relative, matches the repo name, or maps
        # to an existing file under the repo (covers repos where the package
        # name differs from the repo directory name).
        is_internal = (
            module.startswith(".")
            or module.startswith(repo_name)
            or os.path.exists(potential_py)
            or os.path.exists(potential_init)
        )

        if is_internal:
            unanalyzed_internal.add(module)
            if os.path.exists(potential_py):
                potential_files.append(potential_py)
            elif os.path.exists(potential_init):
                potential_files.append(potential_init)
        else:
            # Likely external dependency
            external_deps.add(module)
    
    return {
        "total_imports": len(imported_modules),
        "analyzed_modules": len(analyzed_modules),
        "unanalyzed_internal": list(unanalyzed_internal),
        "external_dependencies": list(external_deps),
        "stdlib_imports": list(stdlib_imports),
        "potential_files_to_analyze": potential_files,
        "discovery_complete": len(unanalyzed_internal) == 0
    }
