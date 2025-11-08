# Code Context Graph (CCG) Node Types
node Module { 
    has path: str;
    has name: str;
}

node Class {
    has name: str;
    has file: str;
    has complexity: int;
}

node Function {
    has name: str;
    has file: str;
    has complexity: int;
}

# CCG Edge Types
edge Calls {}
edge InheritsFrom {}
edge Imports {}

walker code_analyzer {
    has repo_path: str;
    has ccg_data: dict = {};

    can build_graph with entry {
        # Build CCG using Python helper
        self.ccg_data = py_module(
            "codebase_genius.python_helpers.analyzer",
            "analyze_repo",
            self.repo_path
        );
        print("CCG built:", len(self.ccg_data["nodes"]), "nodes,", len(self.ccg_data["edges"]), "edges");
    }
}
