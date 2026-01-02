from fastapi import APIRouter, HTTPException, Query, Header, UploadFile, File

from pydantic import BaseModel
from pathlib import Path
import json
from typing import Any, Dict

from src.app.routes.api_tasks import task_state
from src.workers.ttp_engine import TTPEngine

router = APIRouter(prefix="/api/ttp", tags=["ttp"])

TTP_DIR = Path("./TTP_Intelligence")
UPLOAD_DIR = TTP_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _load_engine_stats() -> Dict[str, Any]:
    engine = TTPEngine(str(TTP_DIR))
    engine.load_ttps()
    return engine.get_stats()


class TTPContent(BaseModel):
    path: str
    content: str


@router.get("/tree")
async def get_ttp_tree():
    """Get the full file tree of TTP Intelligence."""

    def build_tree(path: Path):
        tree = []
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                if item.name.startswith('.'):
                    continue
                node = {
                    "name": item.name,
                    "path": item.relative_to(TTP_DIR).as_posix(),
                    "type": "directory" if item.is_dir() else "file"
                }
                if item.is_dir():
                    node["children"] = build_tree(item)
                tree.append(node)
        except Exception:
            pass
        return tree

    if not TTP_DIR.exists():
        return []

    return build_tree(TTP_DIR)


@router.get("/file")
async def get_ttp_file(path: str):
    """Get content of a specific TTP file."""
    if ".." in path or path.startswith("/") or path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = TTP_DIR / path
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        content = file_path.read_text(encoding="utf-8")
        return {"content": content, "path": path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/file")
async def save_ttp_file(file_data: TTPContent, x_user_role: str = Header(default="admin")):
    """Save content of a specific TTP file."""
    if x_user_role == "node_admin":
        raise HTTPException(status_code=403, detail="Node Admin cannot save TTP files")

    if ".." in file_data.path or file_data.path.startswith("/") or file_data.path.startswith("\\"):
        raise HTTPException(status_code=400, detail="Invalid path")

    file_path = TTP_DIR / file_data.path

    try:
        try:
            json.loads(file_data.content)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_data.content, encoding="utf-8")
        return {"status": "success", "message": "File saved successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/stats")
async def get_ttp_stats():
    """Return current status of the TTP engine/worker."""
    worker = getattr(task_state, "ttp_worker", None)
    if worker and worker.is_running():
        return {"source": "worker", "stats": worker.get_stats()}

    return {"source": "engine", "stats": _load_engine_stats()}


@router.post("/reload")
async def reload_ttp_engine():
    """Force a reload of TTP intelligence data."""
    worker = getattr(task_state, "ttp_worker", None)
    if worker:
        result = worker.reload_intelligence()
        return {
            "status": "reloaded",
            "patterns_loaded": result.get("patterns_loaded"),
            "stats": result.get("stats"),
            "source": "worker"
        }

    stats = _load_engine_stats()
    return {"status": "reloaded", "patterns_loaded": stats.get("total_patterns"), "stats": stats, "source": "engine"}


@router.post("/upload")
async def upload_ttp_file(file: UploadFile = File(...)):
    """Upload a custom TTP JSON file and reload intelligence."""
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only JSON files are supported")

    content = await file.read()
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {exc}") from exc

    if not isinstance(payload, dict) or "ttps" not in payload:
        raise HTTPException(status_code=400, detail="JSON must contain a 'ttps' array")

    ttp_count = len(payload.get("ttps", []))

    target = UPLOAD_DIR / file.filename
    counter = 1
    while target.exists():
        target = UPLOAD_DIR / f"{target.stem}_{counter}{target.suffix}"
        counter += 1

    with open(target, "wb") as handle:
        handle.write(content)

    worker = getattr(task_state, "ttp_worker", None)
    if worker:
        reload_info = worker.reload_intelligence()
        stats = reload_info.get("stats", {})
        patterns_loaded = reload_info.get("patterns_loaded")
        source = "worker"
    else:
        engine = TTPEngine(str(TTP_DIR))
        patterns_loaded = engine.load_ttps()
        stats = engine.get_stats()
        source = "engine"

    return {
        "status": "uploaded",
        "filename": target.name,
        "saved_path": str(target),
        "ttps_in_file": ttp_count,
        "patterns_loaded": patterns_loaded,
        "stats": stats,
        "source": source
    }


@router.get("/files")
async def list_ttp_files():
    """List available TTP intelligence JSON files."""
    files = []
    for path in sorted(TTP_DIR.rglob("*.json")):
        try:
            files.append({
                "name": path.name,
                "relative_path": str(path.relative_to(TTP_DIR)),
                "size": path.stat().st_size
            })
        except FileNotFoundError:
            continue

    return {"files": files, "count": len(files)}
