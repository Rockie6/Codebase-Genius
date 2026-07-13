#!/usr/bin/env python3
"""Generate sample documentation deliverable for a popular Python repository."""
import os
import sys
import shutil

os.environ["USE_LLM"] = "true"
os.environ["GEMINI_API_KEY"] = "AIzaSyDYGtyz_5AfplZi0Og185BOX_8JO767i2w"

from codebase_genius.python_helpers.repo_tools import repo_map_workflow, validate_repo_url
from codebase_genius.python_helpers.analyzer import analyze_repo
from codebase_genius.python_helpers.docgen import generate_markdown


def generate_sample_docs(repo_url: str, output_name: str = "sample_output"):
    """Generate documentation for a repository as a deliverable sample."""
    
    print("=" * 70)
    print("CODEBASE GENIUS - SAMPLE DOCUMENTATION GENERATION")
    print("=" * 70)
    
    # Validate URL
    print(f"\n[1/5] Validating repository URL...")
    validation = validate_repo_url(repo_url)
    if not validation["valid"]:
        print(f"   ✗ Invalid URL: {validation['error']}")
        sys.exit(1)
    
    print(f"   ✓ Valid URL: {validation['normalized_url']}")
    repo_url = validation["normalized_url"]
    
    # Map repository
    print(f"\n[2/5] Cloning and mapping repository...")
    try:
        info = repo_map_workflow(repo_url)
        if info.get("error"):
            print(f"   ✗ Error: {info['error']}")
            sys.exit(1)
        print(f"   ✓ Cloned to: {info['repo_path']}")
        print(f"   ✓ README summary: {info['readme_summary'][:100]}...")
        print(f"   ✓ Priority files found: {len(info.get('priority_files', []))}")
    except Exception as e:
        print(f"   ✗ Failed to map repository: {e}")
        sys.exit(1)
    
    # Analyze code
    print(f"\n[3/5] Analyzing code and building CCG...")
    try:
        ccg = analyze_repo(info["repo_path"])
        call_edges = [e for e in ccg['edges'] if e['type'] == 'calls']
        inherit_edges = [e for e in ccg['edges'] if e['type'] == 'inherits']
        
        print(f"   ✓ Nodes: {len(ccg['nodes'])} ({len([n for n in ccg['nodes'] if n['kind']=='class'])} classes, "
              f"{len([n for n in ccg['nodes'] if n['kind']=='function'])} functions)")
        print(f"   ✓ Edges: {len(ccg['edges'])} ({len(call_edges)} calls, {len(inherit_edges)} inheritance)")
    except Exception as e:
        print(f"   ✗ Failed to analyze code: {e}")
        sys.exit(1)
    
    # Generate documentation
    print(f"\n[4/5] Generating structured documentation...")
    try:
        out_dir = f"./outputs/{output_name}"
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        
        md_path = generate_markdown(
            repo_url,
            info["file_tree"],
            info["readme_summary"],
            ccg,
            out_dir
        )
        print(f"   ✓ Documentation: {md_path}")
    except Exception as e:
        print(f"   ✗ Failed to generate documentation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Verify output
    print(f"\n[5/5] Verifying deliverable...")
    
    # Check file exists
    if not os.path.exists(md_path):
        print(f"   ✗ Documentation file not found")
        sys.exit(1)
    
    # Check diagrams
    import glob
    diagrams = glob.glob(f"{out_dir}/*.png")
    print(f"   ✓ Diagrams: {len(diagrams)}")
    for d in diagrams:
        size = os.path.getsize(d) / 1024  # KB
        print(f"      - {os.path.basename(d)} ({size:.1f} KB)")
    
    # Check documentation structure
    with open(md_path, 'r') as f:
        content = f.read()
    
    doc_size = len(content)
    lines = len(content.splitlines())
    
    sections = ["Overview", "Installation", "Usage", "Architecture", "API Reference", "Project Structure"]
    found_sections = sum(1 for s in sections if f"## {s}" in content)
    
    print(f"   ✓ Documentation: {doc_size:,} bytes, {lines} lines")
    print(f"   ✓ Sections: {found_sections}/{len(sections)}")
    print(f"   ✓ Diagram embeds: {content.count('![')}")
    
    print("\n" + "=" * 70)
    print("✅ SAMPLE DOCUMENTATION GENERATED SUCCESSFULLY!")
    print("=" * 70)
    print(f"\nOutput directory: {out_dir}/")
    print(f"Main document:    {md_path}")
    print(f"Diagrams:         {', '.join([os.path.basename(d) for d in diagrams])}")
    print("\nThis sample demonstrates:")
    print("  • Automatic repository cloning and analysis")
    print("  • LLM-enhanced README summarization")
    print("  • Code Context Graph (CCG) with inheritance detection")
    print("  • Structured documentation sections")
    print("  • Embedded class hierarchy and CCG diagrams")
    print("  • Complexity analysis and hotspot identification")
    print("\n" + "=" * 70)
    
    return md_path


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
