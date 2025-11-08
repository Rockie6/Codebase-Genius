walker generate_docs_api {
    has repo_url: str;

    can process with entry {
        info = py_module(
            "codebase_genius.python_helpers.repo_tools",
            "repo_map_workflow",
            self.repo_url
        );
        
        if info["error"] {
            print("Error:", info["error"]);
            return;
        }
        
        ccg = py_module(
            "codebase_genius.python_helpers.analyzer",
            "analyze_repo",
            info["repo_path"]
        );
        
        repo_name = info["repo_path"].split("/")[-1];
        out_dir = "./outputs/" + repo_name;
        md_path = py_module(
            "codebase_genius.python_helpers.docgen",
            "generate_markdown",
            self.repo_url,
            info["file_tree"],
            info["readme_summary"],
            ccg,
            out_dir
        );
        
        print("Documentation path:", md_path);
    }
}
