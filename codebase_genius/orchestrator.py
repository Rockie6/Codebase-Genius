"""Code Genius Orchestrator - Pure Python pipeline with iterative discovery."""
from __future__ import annotations
import os
import json
from typing import Dict, Any
from .python_helpers.repo_tools import (
    validate_repo_url,
    repo_map_workflow,
    find_important_files,
)
from .python_helpers.analyzer import (
    analyze_repo,
    discover_dependencies,
    aggregate_ccg_statistics,
)
from .python_helpers.docgen import generate_markdown


class CodeGeniusOrchestrator:
    """Orchestrates the code analysis and documentation generation pipeline."""

    def __init__(
        self,
        repo_url: str = "https://github.com/pallets/flask",
        analyze_deep: bool = True,
        max_iterations: int = 3,
    ):
        """Initialize orchestrator with configuration.
        
        Args:
            repo_url: Repository URL to analyze
            analyze_deep: Whether to perform deep code analysis
            max_iterations: Maximum iterations for dependency discovery
        """
        # Read environment variables if set
        self.repo_url = os.getenv("JAC_REPO_URL", repo_url)
        self.analyze_deep = os.getenv("JAC_ANALYZE_DEEP", str(analyze_deep)).lower() == "true"
        self.max_iterations = max_iterations

    def run_pipeline(self) -> Dict[str, Any]:
        """Run the complete documentation generation pipeline.
        
        Returns:
            Dictionary with pipeline results including status, paths, statistics, etc.
        """
        print("🚀 Starting Code Genius Supervisor")
        print("=" * 60)

        # Step 1: Validate URL
        print("🔍 Step 1: Validating repository URL...")
        validation = validate_repo_url(self.repo_url)

        if not validation["valid"]:
            print("❌ Invalid repository URL:", validation["error"])
            return {
                "status": "error",
                "error_code": "invalid_url",
                "message": validation["error"],
            }

        print("✓ Repository URL validated")
        normalized_url = validation["normalized_url"]

        # Step 2: Map repository
        print("\n🗺️  Step 2: Mapping repository structure...")
        info = repo_map_workflow(normalized_url)
        
        if info.get("error"):
            print(f"❌ Repository mapping failed: {info['error']}")
            return {
                "status": "error",
                "error_code": "repo_map_failed",
                "message": info["error"],
            }

        priority_files = find_important_files(info["file_tree"])
        print("✓ Repository mapped")
        print(
            f"  Found {len(priority_files)} priority files:",
            ", ".join(priority_files[:5]),
        )

        # Step 3: Analyze code with iterative discovery
        print("\n🔬 Step 3: Analyzing code structure (iterative discovery)...")
        
        if self.analyze_deep:
            ccg = analyze_repo(info["repo_path"])
            iteration = 1
            total_discovered = 0

            while iteration <= self.max_iterations:
                print(f"  🔄 Discovery iteration {iteration} of {self.max_iterations}")

                dependencies = discover_dependencies(ccg, info["repo_path"])
                unanalyzed = len(dependencies["unanalyzed_internal"])

                if unanalyzed > 0:
                    print(f"    Found {unanalyzed} unanalyzed internal modules")
                    total_discovered += unanalyzed

                if dependencies["discovery_complete"]:
                    print("    ✓ Discovery complete - all dependencies analyzed")
                    break

                iteration += 1
        else:
            ccg = {"nodes": [], "edges": []}
            iteration = 0
            dependencies = {}

        # Get statistics
        stats = aggregate_ccg_statistics(ccg)
        final_dependencies = discover_dependencies(ccg, info["repo_path"])

        print("✓ Code analyzed:")
        print(f"  - Total symbols: {stats['total_symbols']}")
        print(f"  - Classes: {stats['classes']}")
        print(f"  - Functions: {stats['functions']}")
        print(f"  - Total imports: {final_dependencies['total_imports']}")
        print(f"  - External dependencies: {len(final_dependencies['external_dependencies'])}")
        print(f"  - Discovery iterations: {iteration}")

        # Step 4: Generate documentation
        print("\n📝 Step 4: Generating documentation...")
        repo_name = info["repo_path"].split("/")[-1]
        out_dir = f"./outputs/{repo_name}"

        md_path = generate_markdown(
            normalized_url,
            info["file_tree"],
            info["readme_summary"],
            ccg,
            out_dir,
        )

        print(f"✓ Documentation generated at: {md_path}")

        print("\n✅ Pipeline complete!")
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
