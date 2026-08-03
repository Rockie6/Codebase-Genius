"""Code Genius Orchestrator - Pure Python pipeline with iterative discovery."""
from __future__ import annotations
import os
import json
from typing import Dict, Any

from . import load_env
load_env()

from .python_helpers.repo_tools import (
    validate_repo_url,
    repo_map_workflow,
    find_important_files,
)
from .python_helpers.analyzer import (
    analyze_files,
    discover_dependencies,
    aggregate_ccg_statistics,
    list_python_files,
)
from .python_helpers.docgen import generate_markdown


class CodeGeniusOrchestrator:
    """Runs the whole pipeline: fetch the repo, dig through the code, and
    turn what we learn into a readable Markdown document."""

    def __init__(
        self,
        repo_url: str = "https://github.com/pallets/flask",
        analyze_deep: bool = True,
        max_iterations: int = 3,
    ):
        """Set up the run.
        
        Args:
            repo_url: Repository URL to analyze
            analyze_deep: Whether to do the full code analysis (or just map the repo)
            max_iterations: How many rounds of dependency discovery to allow
        """
        # Read environment variables if set
        self.repo_url = os.getenv("CODEBASE_GENIUS_REPO_URL", repo_url)
        self.analyze_deep = os.getenv("CODEBASE_GENIUS_ANALYZE_DEEP", str(analyze_deep)).lower() == "true"
        self.max_iterations = max_iterations

    def run_pipeline(self) -> Dict[str, Any]:
        """Run the complete documentation generation pipeline.
        
        Returns:
            Dictionary with pipeline results including status, paths, statistics, etc.
        """
        print("🚀 Codebase Genius")
        print("=" * 60)

        # Step 1: Validate URL
        print("\n🔍 Checking the repository URL...")
        validation = validate_repo_url(self.repo_url)

        if not validation["valid"]:
            print("❌ That URL doesn't look right:", validation["error"])
            return {
                "status": "error",
                "error_code": "invalid_url",
                "message": validation["error"],
            }

        print("✓ URL looks good")
        normalized_url = validation["normalized_url"]

        # Step 2: Map repository
        print("\n🗺️  Cloning the repo and mapping its structure...")
        info = repo_map_workflow(normalized_url)
        
        if info.get("error"):
            print(f"❌ Couldn't map the repository: {info['error']}")
            return {
                "status": "error",
                "error_code": "repo_map_failed",
                "message": info["error"],
            }

        priority_files = find_important_files(info["file_tree"])
        print("✓ Repository ready")
        print(
            f"  Spotted {len(priority_files)} likely entry points:",
            ", ".join(priority_files[:5]),
        )

        # Step 3: Analyze code with iterative discovery
        print("\n🔬 Analyzing the code — tracking imports, classes, and calls...")
        
        if self.analyze_deep:
            repo_path = info["repo_path"]

            # Seed analysis with the priority files, or all files if none
            # were identified as entry points.
            priority_paths = [os.path.join(repo_path, f) for f in priority_files]
            if priority_paths:
                ccg = analyze_files(priority_paths)
                analyzed: set = set(priority_paths)
            else:
                all_files = list_python_files(repo_path)
                ccg = analyze_files(all_files)
                analyzed = set(all_files)

            iteration = 0
            total_discovered = 0

            while iteration < self.max_iterations:
                iteration += 1
                print(f"  🔄 Discovery pass {iteration} of {self.max_iterations}")

                dependencies = discover_dependencies(ccg, repo_path)
                unanalyzed = len(dependencies["unanalyzed_internal"])

                if unanalyzed > 0:
                    print(f"    Found {unanalyzed} modules we haven't looked at yet")

                new_files = [
                    f
                    for f in dependencies["potential_files_to_analyze"]
                    if f not in analyzed
                ]
                if not new_files:
                    print("    ✓ Nothing left to chase — analysis is complete")
                    break

                total_discovered += len(new_files)
                ccg = analyze_files(new_files, base_ccg=ccg)
                analyzed.update(new_files)
        else:
            ccg = {"nodes": [], "edges": []}
            iteration = 0
            dependencies = {}

        # Get statistics
        stats = aggregate_ccg_statistics(ccg)
        final_dependencies = discover_dependencies(ccg, info["repo_path"])

        print("✓ Code analysis finished:")
        print(f"  - Symbols found: {stats['total_symbols']}")
        print(f"  - Classes: {stats['classes']}")
        print(f"  - Functions: {stats['functions']}")
        print(f"  - Imports: {final_dependencies['total_imports']}")
        print(f"  - External dependencies: {len(final_dependencies['external_dependencies'])}")
        print(f"  - Discovery passes: {iteration}")

        # Step 4: Generate documentation
        print("\n📝 Writing the documentation...")
        repo_name = info["repo_path"].split("/")[-1]
        out_dir = f"./outputs/{repo_name}"

        md_path = generate_markdown(
            normalized_url,
            info["file_tree"],
            info["readme_summary"],
            ccg,
            out_dir,
        )

        print(f"✓ Docs saved to: {md_path}")

        print("\n✅ All done!")
        print("=" * 60)

        # Return results
        return {
            "status": "ok",
            "repo_path": info["repo_path"],
            "output_markdown": md_path,
            "readme_summary": info["readme_summary"],
            "symbol_count": stats["total_symbols"],
            "file_tree_root": info["file_tree"].get("path", "."),
            "statistics": stats,
            "dependencies": {
                "total_imports": final_dependencies["total_imports"],
                "external_dependencies": final_dependencies["external_dependencies"][:20],
                "stdlib_imports": final_dependencies["stdlib_imports"][:20],
                "unanalyzed_internal": final_dependencies["unanalyzed_internal"],
                "discovery_complete": final_dependencies["discovery_complete"],
            },
            "discovery_iterations": iteration,
            "priority_files_count": len(priority_files),
        }
