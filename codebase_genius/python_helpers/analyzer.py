"""Analyzer stub: builds a Code Context Graph (CCG) from source.
Future: integrate Tree-sitter for Python/Jac parsing.
"""
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Optional Tree-sitter support (graceful fallback if unavailable)
try:
    # Provides prebuilt grammars; not required at runtime.
    from tree_sitter_languages import get_parser  # type: ignore

    HAS_TREESITTER = True
except Exception:  # pragma: no cover - optional path
    HAS_TREESITTER = False

SUPPORTED_EXT = {".py", ".jac"}


class CodeContextGraph:
    """In-memory representation of symbols and relationships."""

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
        """Add relationship edge. Types: calls, inherits, imports, contains."""
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
    """Naive symbol finder: captures defs/classes; estimates complexity.
    
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
        
        # Detect imports
        elif line_strip.startswith("import ") or line_strip.startswith("from "):
            # Simple heuristic: capture imported module names
            if line_strip.startswith("import "):
                mod_name = line_strip.split("import ")[1].split()[0].split(".")[0]
                symbols.append({"name": mod_name, "kind": "module"})
            elif line_strip.startswith("from "):
                mod_name = line_strip.split("from ")[1].split()[0].split(".")[0]
                symbols.append({"name": mod_name, "kind": "module"})
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
    """Very rough cyclomatic complexity estimate using decision keywords."""
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
            symbols = []
            call_edges: List[Tuple[str, str]] = []  # (caller, callee)
            inherit_edges: List[Tuple[str, str]] = []  # (child, parent)

            if ext == ".py" and HAS_TREESITTER:
                try:
                    ts_symbols, ts_calls = _py_symbols_and_calls_treesitter(
                        content
                    )
                    symbols = ts_symbols
                    call_edges = ts_calls
                except Exception:
                    symbols, edges = naive_parse(content)
                    inherit_edges = [
                        (src, tgt) for src, tgt, etype in edges if etype == "inherits"
                    ]
            else:
                symbols, edges = naive_parse(content)
                inherit_edges = [
                    (src, tgt) for src, tgt, etype in edges if etype == "inherits"
                ]

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
) -> Tuple[List[Dict[str, str]], List[Tuple[str, str]]]:
    """Extract Python function/class symbols and intra-function call edges.
    Requires tree_sitter_languages to be installed; caller wraps in try/except.
    """
    parser = get_parser("python")  # type: ignore[name-defined]
    tree = parser.parse(bytes(content, "utf-8"))

    symbols: List[Dict[str, str]] = []
    calls: List[Tuple[str, str]] = []

    # Minimal recursive walk to capture function/class definitions and calls
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
    return symbols, calls


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
    
    # Count edge types
    inheritance_edges = sum(1 for e in edges if e.get("type") == "INHERITS_FROM")
    call_edges = sum(1 for e in edges if e.get("type") == "CALLS")
    import_edges = sum(1 for e in edges if e.get("type") == "IMPORTS")
    
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
    
    Analyzes IMPORTS edges to find:
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
    
    # Get all analyzed modules
    analyzed_modules = {n.get("name") for n in nodes if n.get("kind") == "module"}
    
    # Extract all imported modules from IMPORTS edges
    imported_modules = set()
    for edge in edges:
        if edge.get("type") == "IMPORTS":
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
    
    for module in imported_modules:
        # Skip already analyzed modules
        if module in analyzed_modules:
            continue
            
        # Check if it's a standard library module
        module_root = module.split(".")[0]
        if module_root in STDLIB_MODULES:
            stdlib_imports.add(module)
        # Check if it's an internal module (starts with repo name)
        elif module.startswith(repo_name) or module.startswith("."):
            unanalyzed_internal.add(module)
        else:
            # Likely external dependency
            external_deps.add(module)
    
    # Find potential files to analyze
    potential_files = []
    for module in unanalyzed_internal:
        # Convert module name to potential file path
        # e.g., "myapp.utils" -> "myapp/utils.py"
        module_path = module.replace(".", "/")
        potential_py = os.path.join(repo_path, f"{module_path}.py")
        potential_init = os.path.join(repo_path, module_path, "__init__.py")
        
        if os.path.exists(potential_py):
            potential_files.append(potential_py)
        elif os.path.exists(potential_init):
            potential_files.append(potential_init)
    
    return {
        "total_imports": len(imported_modules),
        "analyzed_modules": len(analyzed_modules),
        "unanalyzed_internal": list(unanalyzed_internal),
        "external_dependencies": list(external_deps),
        "stdlib_imports": list(stdlib_imports),
        "potential_files_to_analyze": potential_files,
        "discovery_complete": len(unanalyzed_internal) == 0
    }
