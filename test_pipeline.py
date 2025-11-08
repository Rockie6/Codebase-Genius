#!/usr/bin/env python3
"""Test the complete documentation generation pipeline."""
import os
os.environ["USE_LLM"] = "true"
os.environ["GEMINI_API_KEY"] = "AIzaSyDYGtyz_5AfplZi0Og185BOX_8JO767i2w"

from codebase_genius.python_helpers.repo_tools import repo_map_workflow
from codebase_genius.python_helpers.analyzer import analyze_repo
from codebase_genius.python_helpers.docgen import generate_markdown

def test_flask_docs():
    print("=" * 60)
    print("Testing Complete Documentation Pipeline")
    print("=" * 60)
    
    repo_url = "https://github.com/pallets/flask"
    print(f"\n1. Mapping repository: {repo_url}")
    
    info = repo_map_workflow(repo_url)
    print(f"   ✓ Mapped: {info['repo_path']}")
    print(f"   ✓ README summary: {info['readme_summary'][:80]}...")
    print(f"   ✓ Priority files: {len(info.get('priority_files', []))}")
    
    print(f"\n2. Analyzing code...")
    ccg = analyze_repo(info["repo_path"])
    print(f"   ✓ Nodes: {len(ccg['nodes'])}")
    print(f"   ✓ Edges: {len(ccg['edges'])}")
    
    call_edges = [e for e in ccg['edges'] if e['type'] == 'calls']
    inherit_edges = [e for e in ccg['edges'] if e['type'] == 'inherits']
    print(f"   ✓ Call edges: {len(call_edges)}")
    print(f"   ✓ Inheritance edges: {len(inherit_edges)}")
    
    print(f"\n3. Generating documentation...")
    repo_name = info["repo_path"].split("/")[-1]
    out_dir = f"./outputs/{repo_name}_test"
    
    md_path = generate_markdown(
        repo_url,
        info["file_tree"],
        info["readme_summary"],
        ccg,
        out_dir
    )
    
    print(f"   ✓ Documentation: {md_path}")
    
    # Check for diagrams
    import glob
    diagrams = glob.glob(f"{out_dir}/*.png")
    print(f"   ✓ Diagrams generated: {len(diagrams)}")
    for d in diagrams:
        size = os.path.getsize(d)
        print(f"      - {os.path.basename(d)} ({size:,} bytes)")
    
    # Check documentation sections
    with open(md_path, 'r') as f:
        content = f.read()
    
    sections = ["Overview", "Installation", "Usage", "Architecture", "API Reference", "Project Structure"]
    print(f"\n4. Verifying documentation structure:")
    for section in sections:
        if f"## {section}" in content:
            print(f"   ✓ {section}")
        else:
            print(f"   ✗ {section} (missing)")
    
    # Check for diagram embeds
    diagram_embeds = content.count("![")
    print(f"\n5. Diagram embeds in markdown: {diagram_embeds}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ Pipeline test complete!")
    print(f"{'=' * 60}\n")
    
    return md_path

if __name__ == "__main__":
    test_flask_docs()
