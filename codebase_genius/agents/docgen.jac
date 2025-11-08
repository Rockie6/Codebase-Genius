walker generate_docs {
    has repo_url: str;
    has repo_path: str;
    has file_tree: dict;
    has readme_summary: str;
    
    can generate with entry {
        # Analyzer again for current repo state (could be passed in instead)
        ccg = py_module(
            "codebase_genius.python_helpers.analyzer",
            "analyze_repo",
            self.repo_path,
        );

        # Output directory derived from repo name
        repo_name = self.repo_path.split("/")[-1];
        out_dir = "./outputs/" + repo_name;

        # Generate markdown (Python helper handles diagrams)
        md_path = py_module(
            "codebase_genius.python_helpers.docgen",
            "generate_markdown",
            self.repo_url,
            self.file_tree,
            self.readme_summary,
            ccg,
            out_dir,
        );
        
        std.out({ 
            "output_markdown": md_path, 
            "ccg_stats": {
                "nodes": len(ccg["nodes"]),
                "edges": len(ccg["edges"])
            }
        });
    }
}
