"""FastAPI wrapper for Codebase Genius pipeline.
Run: uvicorn codebase_genius.api_server:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations
import os
import traceback
import shutil
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pathlib import Path
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Union, Optional
from .python_helpers.repo_tools import repo_map_workflow
from .python_helpers.analyzer import analyze_repo
from .python_helpers.docgen import generate_markdown

app = FastAPI(title="Codebase Genius", version="0.1.0")

 
class GenerateRequest(BaseModel):
    repo_url: HttpUrl
    analyze: bool = True
    force: bool = False  # future: re-clone / cache bust

 
class GenerateResponse(BaseModel):
    status: str
    repo_path: str
    output_markdown: str
    readme_summary: str
    symbol_count: int
    file_tree_root: str


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None

 
@app.post("/generate", response_model=Union[GenerateResponse, ErrorResponse])
def generate(req: GenerateRequest) -> Union[GenerateResponse, ErrorResponse]:
    """Generate repository documentation.

    Returns GenerateResponse on success or ErrorResponse with structured
    error_code/message when mapping fails or unexpected errors occur.
    """
    info = repo_map_workflow(str(req.repo_url))
    if info.get("error"):
        raw_err = info["error"]  # e.g., 'repo_map_failed: Git clone failed...'
        # Parse code prefix pattern 'code: message'
        if ":" in raw_err:
            code, msg = raw_err.split(":", 1)
            code = code.strip()
            msg = msg.strip()
        else:
            code, msg = "unknown_error", raw_err
        return ErrorResponse(
            error_code=code,
            message=msg,
            details={"repo_url": str(req.repo_url)},
        )
    try:
        ccg: Dict[str, Any]
        if req.analyze:
            ccg = analyze_repo(info["repo_path"])
        else:
            ccg = {"nodes": [], "edges": []}
        repo_name = os.path.basename(info["repo_path"]) or "repo"
        out_dir = os.path.join("outputs", repo_name)
        md_path = generate_markdown(
            str(req.repo_url),
            info["file_tree"],
            info["readme_summary"],
            ccg,
            out_dir,
        )
        return GenerateResponse(
            status="ok",
            repo_path=info["repo_path"],
            output_markdown=md_path,
            readme_summary=info["readme_summary"],
            symbol_count=len(ccg.get("nodes", [])),
            file_tree_root=(info["file_tree"].get("path", ".") if info.get("file_tree") else "."),
        )
    except Exception as e:  # pragma: no cover
        traceback.print_exc()
        return ErrorResponse(
            error_code="unhandled_exception",
            message=str(e),
            details={"trace": traceback.format_exc().splitlines()[-3:]},
        )

 
@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/download/{repo_name}")
def download_documentation(repo_name: str):
    """Download generated documentation as markdown file.
    
    Args:
        repo_name: Name of the repository (used to locate output directory)
    
    Returns:
        FileResponse with the generated docs.md file
    """
    # Sanitize repo name to prevent directory traversal
    safe_repo_name = repo_name.replace("..", "").replace("/", "").replace("\\", "")
    
    docs_path = Path("outputs") / safe_repo_name / "docs.md"
    
    if not docs_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Documentation not found for repository '{safe_repo_name}'. "
                   f"Please generate documentation first."
        )
    
    return FileResponse(
        path=str(docs_path),
        filename=f"{safe_repo_name}_documentation.md",
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename={safe_repo_name}_documentation.md"
        }
    )


@app.get("/download-content/{repo_name}")
def download_documentation_content(repo_name: str):
    """Get documentation content as plain text (for frontend preview/copy).
    
    Args:
        repo_name: Name of the repository
    
    Returns:
        Plain text content of the documentation
    """
    safe_repo_name = repo_name.replace("..", "").replace("/", "").replace("\\", "")
    docs_path = Path("outputs") / safe_repo_name / "docs.md"
    
    if not docs_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Documentation not found for repository '{safe_repo_name}'"
        )
    
    with open(docs_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Content-Type": "text/plain; charset=utf-8"
        }
    )

 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)

# Mount GUI (static files)
gui_dir = Path(__file__).parent / "gui"
if gui_dir.exists():
    app.mount("/gui", StaticFiles(directory=str(gui_dir), html=True), name="gui")
