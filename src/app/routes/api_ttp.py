from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel
from pathlib import Path
import os
import json

router = APIRouter(prefix="/api/ttp", tags=["ttp"])

TTP_INTELLIGENCE_DIR = Path("./TTP_Intelligence")

class TTPContent(BaseModel):
    path: str
    content: str

@router.get("/tree")
async def get_ttp_tree():
    """Get the full file tree of TTP files."""
    def build_tree(path: Path):
        tree = []
        try:
            # Sort: Directories first, then files
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                    
                node = {
                    "name": item.name,
                    "path": item.relative_to(TTP_INTELLIGENCE_DIR).as_posix(),
                    "type": "directory" if item.is_dir() else "file"
                }
                
                if item.is_dir():
                    node["children"] = build_tree(item)
                
                tree.append(node)
        except Exception:
            pass
        return tree

    if not TTP_INTELLIGENCE_DIR.exists():
        return []
        
    return build_tree(TTP_INTELLIGENCE_DIR)

@router.get("/file")
async def get_ttp_file(path: str):
    """Get content of a specific TTP file."""
    # Security check: prevent directory traversal
    if ".." in path or path.startswith("/") or path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    file_path = TTP_INTELLIGENCE_DIR / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/file")
async def save_ttp_file(file_data: TTPContent, x_user_role: str = Header(default="admin")):
    """Save content of a specific TTP file. Creates file if it doesn't exist."""
    # Check permissions
    if x_user_role == "node_admin":
        raise HTTPException(status_code=403, detail="Node Admin cannot save files")

    # Security check
    if ".." in file_data.path or file_data.path.startswith("/") or file_data.path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    file_path = TTP_INTELLIGENCE_DIR / file_data.path
    
    try:
        # Validate JSON before saving
        try:
            json.loads(file_data.content)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")
            
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(file_data.content, encoding="utf-8")
        return {"status": "success", "message": "File saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
