#!/usr/bin/env python3
"""Generate a sample documentation deliverable for a popular Python repository."""
import os
import sys

from codebase_genius import load_env
load_env()

from codebase_genius.orchestrator import CodeGeniusOrchestrator


def generate_sample_docs(repo_url: str, output_name: str = "sample_output"):
    """Generate documentation for a repository and save it as a sample deliverable."""
    
    print("=" * 70)
    print("CODEBASE GENIUS - SAMPLE DOCUMENTATION")
    print("=" * 70)
    
    orchestrator = CodeGeniusOrchestrator(
        repo_url=repo_url,
        analyze_deep=True,
        max_iterations=3,
    )
    
    result = orchestrator.run_pipeline()
    
    if result["status"] != "ok":
        print(f"\n❌ Couldn't generate the docs: {result.get('message', 'Unknown error')}")
        sys.exit(1)
    
    print("\n✅ Sample documentation ready!")
    print("=" * 70)
    print(f"\nOutput directory: {os.path.dirname(result['output_markdown'])}/")
    print(f"Main document:    {result['output_markdown']}")
    print("\n" + "=" * 70)
    
    return result["output_markdown"]


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate sample documentation for a GitHub repository"
    )
    parser.add_argument(
        "repo_url",
        nargs="?",
        default="https://github.com/requests/requests",
        help="GitHub repository URL (default: requests/requests)"
    )
    parser.add_argument(
        "--output",
        default="sample_output",
        help="Output directory name (default: sample_output)"
    )
    
    args = parser.parse_args()
    generate_sample_docs(args.repo_url, args.output)
