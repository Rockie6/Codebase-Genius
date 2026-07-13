"""DocGenie: synthesize Markdown docs and simple diagrams.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any, List, Set
try:
    from graphviz import Digraph
except Exception:  # pragma: no cover - optional at runtime
    Digraph = None  # type: ignore


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def render_ccg_diagram(
    ccg: Dict[str, Any],
    out_dir: str,
    name: str = "ccg",
    max_nodes: int = 50,
) -> str:
    """Render full CCG diagram with all nodes and edges."""
    if Digraph is None:
        return ""
    
    nodes = ccg.get("nodes", [])
    edges = ccg.get("edges", [])
    
    # Limit diagram size for readability
    if len(nodes) > max_nodes:
        nodes = nodes[:max_nodes]
    
    dot = Digraph(comment="Code Context Graph")
    dot.attr(rankdir='LR', size='12,8')
    
    for n in nodes:
        file_label = Path(n.get("file", "")).name
        sym = n.get("name", "")
        kind = n.get("kind", "")
        key = f"{n.get('file', '')}:{sym}".replace(":", "_COLON_")  # Escape colons for graphviz
        
        # Style by kind
        if kind == "class":
            dot.node(key, label=f"{sym}\n({file_label})", shape="box", style="filled", fillcolor="lightblue")
        elif kind == "function":
            dot.node(key, label=f"{sym}\n({file_label})", shape="ellipse", style="filled", fillcolor="lightgreen")
        else:
            dot.node(key, label=f"{sym}\n({file_label})", shape="note")
    
    # Render edges
    node_keys = {f"{n.get('file', '')}:{n.get('name', '')}".replace(":", "_COLON_") for n in nodes}
    for e in edges:
        src = e.get("source", "").replace(":", "_COLON_")
        tgt = e.get("target", "").replace(":", "_COLON_")
        et = e.get("type", "")
        
        # Only include edges where both nodes are in the diagram
        if src in node_keys and tgt in node_keys:
            if et == "inherits":
                dot.edge(src, tgt, label=et, color="blue", style="dashed")
            elif et == "calls":
                dot.edge(src, tgt, label=et, color="green")
            else:
                dot.edge(src, tgt, label=et)
    
    ensure_dir(out_dir)
    path = os.path.join(out_dir, name)
    dot.format = "png"
    try:
        dot.render(path, cleanup=True)
        return f"{path}.png"
    except Exception:
        return ""


def render_class_hierarchy_diagram(
    ccg: Dict[str, Any],
    out_dir: str,
    name: str = "class_hierarchy",
) -> str:
    """Render class inheritance hierarchy diagram."""
    if Digraph is None:
        return ""
    
    nodes = ccg.get("nodes", [])
    edges = ccg.get("edges", [])
    
    # Filter to classes only
    classes = {f"{n.get('file', '')}:{n.get('name', '')}": n 
               for n in nodes if n.get("kind") == "class"}
    
    if not classes:
        return ""
    
    inherit_edges = [e for e in edges if e.get("type") == "inherits"]
    
    if not inherit_edges:
        return ""
    
    dot = Digraph(comment="Class Hierarchy")
    dot.attr(rankdir='TB', size='10,10')
    
    for key, cls in classes.items():
        sym = cls.get("name", "")
        file_label = Path(cls.get("file", "")).name
        dot.node(key, label=f"{sym}\n[{file_label}]", shape="box", style="filled", fillcolor="lightblue")
    
    for e in inherit_edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if src in classes and tgt in classes:
            dot.edge(src, tgt, label="inherits", color="blue", style="bold")
    
    ensure_dir(out_dir)
    path = os.path.join(out_dir, name)
    dot.format = "png"
    try:
        dot.render(path, cleanup=True)
        return f"{path}.png"
    except Exception:
        return ""


def render_call_graph_diagram(
    ccg: Dict[str, Any],
    out_dir: str,
    name: str = "call_graph",
    max_nodes: int = 30,
) -> str:
    """Render function call graph diagram."""
    if Digraph is None:
        return ""
    
    edges = ccg.get("edges", [])
    call_edges = [e for e in edges if e.get("type") == "calls"]
    
    if not call_edges:
        return ""
    
    # Get all nodes involved in calls
    call_nodes: Set[str] = set()
    for e in call_edges:
        call_nodes.add(e.get("source", "").replace(":", "_COLON_"))
        call_nodes.add(e.get("target", "").replace(":", "_COLON_"))
    
    # Limit for readability
    if len(call_nodes) > max_nodes:
        call_nodes = set(list(call_nodes)[:max_nodes])
        call_edges = [e for e in call_edges 
                      if e.get("source", "").replace(":", "_COLON_") in call_nodes 
                      and e.get("target", "").replace(":", "_COLON_") in call_nodes]
    
    nodes = ccg.get("nodes", [])
    node_map = {f"{n.get('file', '')}:{n.get('name', '')}".replace(":", "_COLON_"): n for n in nodes}
    
    dot = Digraph(comment="Call Graph")
    dot.attr(rankdir='LR', size='12,8')
    
    for key in call_nodes:
        if key in node_map:
            n = node_map[key]
            sym = n.get("name", "")
            file_label = Path(n.get("file", "")).name
            complexity = n.get("complexity", 1)
            
            # Color by complexity
            if complexity > 10:
                color = "red"
            elif complexity > 5:
                color = "yellow"
            else:
                color = "lightgreen"
            
            dot.node(key, label=f"{sym}\n({file_label})\ncx={complexity}", 
                    shape="ellipse", style="filled", fillcolor=color)
    
    for e in call_edges:
        src = e.get("source", "").replace(":", "_COLON_")
        tgt = e.get("target", "").replace(":", "_COLON_")
        if src in call_nodes and tgt in call_nodes:
            dot.edge(src, tgt, color="green")
    
    ensure_dir(out_dir)
    path = os.path.join(out_dir, name)
    dot.format = "png"
    try:
        dot.render(path, cleanup=True)
        return f"{path}.png"
    except Exception:
        return ""


def _analyze_ccg_stats(ccg: Dict[str, Any]) -> Dict[str, Any]:
    """Extract statistics and insights from CCG."""
    nodes = ccg.get("nodes", [])
    edges = ccg.get("edges", [])
    
    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "classes": [n for n in nodes if n.get("kind") == "class"],
        "functions": [n for n in nodes if n.get("kind") == "function"],
        "modules": [n for n in nodes if n.get("kind") == "module"],
        "call_edges": [e for e in edges if e.get("type") == "calls"],
        "inherit_edges": [e for e in edges if e.get("type") == "inherits"],
        "import_edges": [e for e in edges if e.get("type") == "imports"],
    }
    
    # Find high-complexity functions
    stats["high_complexity"] = sorted(
        [f for f in stats["functions"] if f.get("complexity", 0) > 10],
        key=lambda x: x.get("complexity", 0),
        reverse=True
    )[:10]
    
    # Find most-called functions (hotspots)
    call_targets: Dict[str, int] = {}
    for e in stats["call_edges"]:
        tgt = e.get("target", "")
        call_targets[tgt] = call_targets.get(tgt, 0) + 1
    
    stats["hotspots"] = sorted(
        call_targets.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Find base classes (classes that are inherited from)
    base_classes: Set[str] = set()
    for e in stats["inherit_edges"]:
        base_classes.add(e.get("target", ""))
    
    stats["base_classes"] = list(base_classes)
    
    return stats


def _format_installation_section(repo_url: str, file_tree: Dict[str, Any]) -> str:
    """Generate Installation section by detecting package files."""
    lines = []
    lines.append("## Installation\n")
    
    # Check for common package files
    has_requirements = False
    has_setup_py = False
    has_pyproject = False
    
    def check_files(tree: Dict[str, Any]) -> None:
        nonlocal has_requirements, has_setup_py, has_pyproject
        path = tree.get("path", "")
        if path == "requirements.txt":
            has_requirements = True
        elif path == "setup.py":
            has_setup_py = True
        elif path == "pyproject.toml":
            has_pyproject = True
        
        for child in tree.get("children", []) or []:
            check_files(child)
    
    check_files(file_tree)
    
    # Clone instruction
    lines.append("Clone the repository:\n")
    lines.append("```bash")
    lines.append(f"git clone {repo_url}")
    lines.append("cd " + repo_url.split("/")[-1].replace(".git", ""))
    lines.append("```\n")
    
    # Install instructions
    if has_requirements:
        lines.append("Install dependencies:")
        lines.append("```bash")
        lines.append("pip install -r requirements.txt")
        lines.append("```\n")
    elif has_setup_py:
        lines.append("Install the package:")
        lines.append("```bash")
        lines.append("pip install -e .")
        lines.append("```\n")
    elif has_pyproject:
        lines.append("Install using poetry or pip:")
        lines.append("```bash")
        lines.append("poetry install")
        lines.append("# or")
        lines.append("pip install .")
        lines.append("```\n")
    
    return "\n".join(lines)


def _format_usage_section(ccg_stats: Dict[str, Any]) -> str:
    """Generate Usage section with entry points."""
    lines = []
    lines.append("## Usage\n")
    
    # Look for main.py, app.py, or __main__ patterns
    entry_points = []
    for mod in ccg_stats.get("modules", []):
        name = mod.get("name", "")
        if "main" in name.lower() or "app" in name.lower():
            entry_points.append(mod)
    
    if entry_points:
        lines.append("Entry points detected:\n")
        for ep in entry_points[:3]:
            file_path = Path(ep.get("file", ""))
            lines.append(f"- `{file_path.name}`: {ep.get('name', 'N/A')}")
        lines.append("")
    else:
        lines.append("Please refer to the repository documentation for usage instructions.\n")
    
    return "\n".join(lines)


def _format_api_reference_section(ccg_stats: Dict[str, Any]) -> str:
    """Generate API Reference section with classes and key functions."""
    lines = []
    lines.append("## API Reference\n")
    
    # Classes
    classes = ccg_stats.get("classes", [])
    if classes:
        lines.append("### Classes\n")
        
        # Group by file
        class_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for cls in classes:
            fpath = cls.get("file", "")
            if fpath not in class_by_file:
                class_by_file[fpath] = []
            class_by_file[fpath].append(cls)
        
        for fpath in sorted(class_by_file.keys())[:10]:  # Limit to 10 files
            file_label = Path(fpath).name
            lines.append(f"#### {file_label}\n")
            for cls in class_by_file[fpath][:5]:  # Limit to 5 classes per file
                name = cls.get("name", "")
                lines.append(f"- **`{name}`**")
            lines.append("")
    
    # Key Functions (high complexity or hotspots)
    high_complexity = ccg_stats.get("high_complexity", [])
    if high_complexity:
        lines.append("### High-Complexity Functions\n")
        lines.append("Functions with complexity > 10 (may need refactoring):\n")
        for func in high_complexity[:10]:
            name = func.get("name", "")
            file_path = Path(func.get("file", ""))
            complexity = func.get("complexity", 0)
            lines.append(f"- `{name}` in `{file_path.name}` (complexity: {complexity})")
        lines.append("")
    
    hotspots = ccg_stats.get("hotspots", [])
    if hotspots:
        lines.append("### Most-Called Functions (Hotspots)\n")
        lines.append("Functions frequently called by others:\n")
        for target, count in hotspots[:10]:
            # Extract function name from key (file:name)
            func_name = target.split(":")[-1] if ":" in target else target
            lines.append(f"- `{func_name}` ({count} calls)")
        lines.append("")
    
    return "\n".join(lines)


def _format_architecture_section(ccg_stats: Dict[str, Any]) -> str:
    """Generate Architecture section with inheritance hierarchy."""
    lines = []
    lines.append("## Architecture\n")
    
    stats_summary = [
        f"- **Total Symbols**: {ccg_stats['total_nodes']}",
        f"- **Classes**: {len(ccg_stats['classes'])}",
        f"- **Functions**: {len(ccg_stats['functions'])}",
        f"- **Modules**: {len(ccg_stats['modules'])}",
        f"- **Call Relationships**: {len(ccg_stats['call_edges'])}",
        f"- **Inheritance Relationships**: {len(ccg_stats['inherit_edges'])}",
    ]
    lines.extend(stats_summary)
    lines.append("")
    
    # Base classes
    base_classes = ccg_stats.get("base_classes", [])
    if base_classes:
        lines.append("### Base Classes\n")
        lines.append("Classes that serve as base classes for others:\n")
        for bc in base_classes[:10]:
            class_name = bc.split(":")[-1] if ":" in bc else bc
            lines.append(f"- `{class_name}`")
        lines.append("")
    
    return "\n".join(lines)


def generate_markdown(
    repo_url: str,
    file_tree: Dict[str, Any],
    readme_summary: str,
    ccg: Dict[str, Any],
    out_dir: str,
) -> str:
    ensure_dir(out_dir)
    md_path = os.path.join(out_dir, "docs.md")
    
    # Analyze CCG for insights
    ccg_stats = _analyze_ccg_stats(ccg)
    
    # Generate diagrams
    ccg_diagram = render_ccg_diagram(ccg, out_dir, max_nodes=40)
    class_diagram = render_class_hierarchy_diagram(ccg, out_dir)
    call_diagram = render_call_graph_diagram(ccg, out_dir, max_nodes=25)
    
    with open(md_path, "w", encoding="utf-8") as f:
        # Title
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        f.write(f"# {repo_name} - Documentation\n\n")
        f.write(f"*Auto-generated documentation for [{repo_url}]({repo_url})*\n\n")
        f.write("---\n\n")
        
        # Overview
        f.write("## Overview\n\n")
        f.write(readme_summary + "\n\n")
        
        # Installation
        f.write(_format_installation_section(repo_url, file_tree))
        f.write("\n")
        
        # Usage
        f.write(_format_usage_section(ccg_stats))
        f.write("\n")
        
        # Architecture
        f.write(_format_architecture_section(ccg_stats))
        
        # Diagrams section
        f.write("### Code Diagrams\n\n")
        
        if class_diagram:
            f.write("#### Class Hierarchy\n\n")
            f.write(f"![Class Hierarchy]({Path(class_diagram).name})\n\n")
        
        if call_diagram:
            f.write("#### Call Graph\n\n")
            f.write(f"![Call Graph]({Path(call_diagram).name})\n\n")
        
        if ccg_diagram:
            f.write("#### Full Code Context Graph\n\n")
            f.write(f"![CCG Diagram]({Path(ccg_diagram).name})\n\n")
        
        # API Reference
        f.write(_format_api_reference_section(ccg_stats))
        
        # File Tree
        f.write("## Project Structure\n\n")
        f.write("```\n")
        f.write(_format_tree(file_tree))
        f.write("\n```\n\n")
        
        # Footer
        f.write("---\n\n")
        f.write("*Generated by Codebase Genius - AI-powered documentation system*\n")
    
    return md_path


def _format_tree(tree: Dict[str, Any], indent: int = 0) -> str:
    if not tree:
        return "<empty>"
    lines = []
    prefix = "  " * indent
    path = tree.get("path", ".")
    t = tree.get("type", "dir")
    lines.append(f"{prefix}{path}/" if t == "dir" else f"{prefix}{path}")
    for ch in tree.get("children", []) or []:
        lines.append(_format_tree(ch, indent + 1))
    return "\n".join(lines)
