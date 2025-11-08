"""Enhanced Code Genius Supervisor - Intelligent pipeline with iterative discovery"""

glob py_module = __jac_import__("jaclang.plugin.feature").py_module;

walker orchestrate {
    has repo_url: str = "https://github.com/pallets/flask";
    has analyze_deep: bool = True;
    has max_iterations: int = 3;

    can run_pipeline with entry {
        # Read environment variables if set
        env_url = py_module("os", "getenv", "JAC_REPO_URL");
        env_analyze = py_module("os", "getenv", "JAC_ANALYZE_DEEP");
        
        if env_url {
            self.repo_url = env_url;
        }
        if env_analyze {
            self.analyze_deep = env_analyze == "true";
        }
        
        print("🚀 Starting Code Genius Supervisor");
        print("=" * 60);
        
        print("🔍 Step 1: Validating repository URL...");
        validation = py_module(
            "codebase_genius.python_helpers.repo_tools",
            "validate_repo_url",
            self.repo_url
        );
        
        if not validation["valid"] {
            print("❌ Invalid repository URL:", validation["error"]);
            std.out({
                "status": "error",
                "error_code": "invalid_url",
                "message": validation["error"]
            });
            disengage;
        }
        
        print("✓ Repository URL validated");
        normalized_url = validation["normalized_url"];
        
        print("\n🗺️  Step 2: Mapping repository structure...");
        info = py_module(
            "codebase_genius.python_helpers.repo_tools",
            "repo_map_workflow",
            normalized_url
        );
        
        priority_files = py_module(
            "codebase_genius.python_helpers.repo_tools",
            "find_important_files",
            info["file_tree"]
        );
        
        print("✓ Repository mapped");
        print("  Found", len(priority_files), "priority files:", ", ".join(priority_files[:5]));
        
        print("\n🔬 Step 3: Analyzing code structure (iterative discovery)...");
        ccg = py_module(
            "codebase_genius.python_helpers.analyzer",
            "analyze_repo",
            info["repo_path"]
        );
        
        iteration = 1;
        total_discovered = 0;
        
        while iteration <= self.max_iterations {
            print("  🔄 Discovery iteration", iteration, "of", self.max_iterations);
            
            dependencies = py_module(
                "codebase_genius.python_helpers.analyzer",
                "discover_dependencies",
                ccg,
                info["repo_path"]
            );
            
            unanalyzed = len(dependencies["unanalyzed_internal"]);
            
            if unanalyzed > 0 {
                print("    Found", unanalyzed, "unanalyzed internal modules");
                total_discovered = total_discovered + unanalyzed;
            }
            
            if dependencies["discovery_complete"] {
                print("    ✓ Discovery complete - all dependencies analyzed");
                break;
            }
            
            iteration = iteration + 1;
        }
        
        stats = py_module(
            "codebase_genius.python_helpers.analyzer",
            "aggregate_ccg_statistics",
            ccg
        );
        
        final_dependencies = py_module(
            "codebase_genius.python_helpers.analyzer",
            "discover_dependencies",
            ccg,
            info["repo_path"]
        );
        
        print("✓ Code analyzed:");
        print("  - Total symbols:", stats["total_symbols"]);
        print("  - Classes:", stats["classes"]);
        print("  - Functions:", stats["functions"]);
        print("  - Total imports:", final_dependencies["total_imports"]);
        print("  - External dependencies:", len(final_dependencies["external_dependencies"]));
        print("  - Discovery iterations:", iteration);
        
        print("\n📝 Step 4: Generating documentation...");
        repo_name = info["repo_path"].split("/")[-1];
        out_dir = "./outputs/" + repo_name;
        
        md_path = py_module(
            "codebase_genius.python_helpers.docgen",
            "generate_markdown",
            normalized_url,
            info["file_tree"],
            info["readme_summary"],
            ccg,
            out_dir
        );

        print("✓ Documentation generated at:", md_path);
        
        print("\n✅ Pipeline complete!");
        print("=" * 60);
        
        # Output JSON for API consumption
        std.out({
            "status": "ok",
            "repo_path": info["repo_path"],
            "output_markdown": md_path,
            "readme_summary": info["readme_summary"],
            "symbol_count": stats["total_symbols"],
            "file_tree_root": info["file_tree"]["path"] if "path" in info["file_tree"] else ".",
            "statistics": stats,
            "dependencies": {
                "total_imports": final_dependencies["total_imports"],
                "external_dependencies": final_dependencies["external_dependencies"][:20],
                "stdlib_imports": final_dependencies["stdlib_imports"][:20],
                "unanalyzed_internal": final_dependencies["unanalyzed_internal"],
                "discovery_complete": final_dependencies["discovery_complete"]
            },
            "discovery_iterations": iteration,
            "priority_files_count": len(priority_files)
        });
    }
}

# Entry point to spawn the walker
with entry {
    orchestrate() spawn root;
}

