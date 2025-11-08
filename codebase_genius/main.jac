"""Enhanced Code Genius Supervisor - Intelligent pipeline with iterative discovery"""

walker orchestrate {
    has repo_url: str = "https://github.com/pallets/flask";
    has analyze_deep: bool = True;
    has max_iterations: int = 3;

    can run_pipeline with entry {
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
        
        std.out({
            "status": "complete",
            "repo_url": normalized_url,
            "markdown_path": md_path,
            "repo_path": info["repo_path"],
            "priority_files_found": len(priority_files),
            "statistics": stats,
            "dependencies": {
                "total_imports": final_dependencies["total_imports"],
                "external_dependencies": final_dependencies["external_dependencies"][:20],
                "stdlib_imports": final_dependencies["stdlib_imports"][:20],
                "unanalyzed_internal": final_dependencies["unanalyzed_internal"],
                "discovery_complete": final_dependencies["discovery_complete"]
            },
            "analysis_plan": {
                "deep_analysis": self.analyze_deep,
                "priority_files_count": len(priority_files),
                "discovery_iterations": iteration,
                "modules_discovered": total_discovered
            }
        });
    }
}

