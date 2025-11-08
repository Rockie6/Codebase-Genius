# Repository structure nodes
node Repo {
    has url: str;
    has path: str;
    has readme_summary: str;
}

node FileNode {
    has rel_path: str;
    has is_dir: bool;
}

edge ChildOf {}

walker repo_mapper {
    has repo_url: str;
    has repo_info: dict = {};

    can map_repository with entry {
        # Clone and analyze repository using Python helper
        self.repo_info = py_module(
            "codebase_genius.python_helpers.repo_tools",
            "repo_map_workflow",
            self.repo_url
        );
        
        if self.repo_info["error"] {
            print("Mapping error:", self.repo_info["error"]);
        } else {
            print("Repository mapped:", self.repo_info["repo_path"]);
            print("README summary:", self.repo_info["readme_summary"][:100] + "...");
        }
    }
}
