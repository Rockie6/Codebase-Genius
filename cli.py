#!/usr/bin/env python3
"""Command-line interface for Codebase Genius."""
import sys
import os
from pathlib import Path

from codebase_genius import load_env
load_env()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from codebase_genius.orchestrator import CodeGeniusOrchestrator


def main():
    """Run the orchestrator from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate documentation for a GitHub repository",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py https://github.com/pallets/flask
  python cli.py https://github.com/requests/requests --no-analysis
  CODEBASE_GENIUS_REPO_URL="https://github.com/django/django" python cli.py
        """,
    )

    parser.add_argument(
        "repo_url",
        nargs="?",
        help="Repository URL to analyze (can also use CODEBASE_GENIUS_REPO_URL env var)",
    )
    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip deep code analysis (faster)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="Maximum iterations for dependency discovery (default: 3)",
    )

    args = parser.parse_args()

    # Determine repo URL
    repo_url = args.repo_url or os.getenv("CODEBASE_GENIUS_REPO_URL")
    if not repo_url:
        parser.print_help()
        print("\n❌ Oops — we need a repository URL. Pass one as an argument, or set CODEBASE_GENIUS_REPO_URL.")
        sys.exit(1)

    # Create and run orchestrator
    orchestrator = CodeGeniusOrchestrator(
        repo_url=repo_url,
        analyze_deep=not args.no_analysis,
        max_iterations=args.max_iterations,
    )

    result = orchestrator.run_pipeline()

    # Exit with appropriate code
    if result["status"] != "ok":
        print(f"\n❌ Something went wrong: {result.get('message', 'Unknown error')}")
        sys.exit(1)

    print("\n✅ Done! Here's what we got:")
    print(f"  Repo:   {result['repo_path']}")
    print(f"  Docs:   {result['output_markdown']}")
    print(f"  Symbols: {result['symbol_count']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
