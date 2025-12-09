"""
File Upload API for Log Ingestion
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import tempfile
import os
from pathlib import Path
from datetime import datetime

from src.db.repository.log_repo import insert_raw_log
from src.db.repository.server_repo import get_or_create_server
from src.db.repository.alert_repo import create_alert
from src.workers.sigma_rule_engine import SigmaRuleEngine

router = APIRouter(prefix="/api/upload", tags=["upload"])

# Initialize Sigma Engine (singleton)
sigma_engine = SigmaRuleEngine(r"./Sigma_Rules")
sigma_engine.load_rules()

@router.post("/log-file")
async def upload_log_file(
    file: UploadFile = File(...),
    log_source: str = Form(..., description="Log type: linux, windows, or nginx"),
    hostname: Optional[str] = Form(None),
    ip_address: Optional[str] = Form("file_upload")
):
    """
    Upload and ingest log file.
    Supports: .log/.csv (linux/nginx), .json (windows)
    """
    
    # Validate log source
    if log_source not in ["linux", "windows", "nginx"]:
        raise HTTPException(400, "Invalid log_source. Use: linux, windows, or nginx")
    
    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if log_source == "windows" and ext != ".json":
        raise HTTPException(400, "Windows logs must be .json format")
    if log_source in ["linux", "nginx"] and ext not in [".log", ".csv"]:
        raise HTTPException(400, "Linux/Nginx logs must be .log or .csv format")
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process file
        processed = await process_log_file(tmp_path, log_source, hostname, ip_address)
        
        return {
            "status": "success",
            "message": "File processed successfully",
            "file_info": {
                "filename": file.filename,
                "size_bytes": len(content),
                "log_source": log_source,
                "hostname": hostname or f"{log_source}_upload",
                "ip_address": ip_address
            },
            "processing_stats": {
                "total_lines": processed["total_lines"],
                "logs_processed": processed["logs_count"],
                "logs_failed": processed["logs_failed"],
                "alerts_generated": processed["alerts_count"]
            },
            "alert_breakdown": processed["alert_breakdown"],
            "timestamp": datetime.now().isoformat()
        }
    
    finally:
        # Cleanup temp file
        os.unlink(tmp_path)


async def process_log_file(file_path: str, log_source: str, hostname: Optional[str], ip_address: str):
    """Process uploaded log file and generate alerts."""
    import json
    
    total_lines = 0
    logs_count = 0
    logs_failed = 0
    alerts_count = 0
    alert_breakdown = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }
    
    # Get or create server
    server_id = get_or_create_server(
        hostname=hostname or f"{log_source}_upload",
        ip=ip_address,
        server_type=log_source
    )
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            total_lines += 1
            line = line.strip()
            if not line:
                continue
            
            try:
                # Create log entry
                log_entry_id = insert_raw_log(
                    server_id=server_id,
                    log_source=log_source,
                    content=line,
                    recv_time=datetime.now()
                )
                logs_count += 1
                
                # Run Sigma detection
                log_dict = {
                    'id': log_entry_id,
                    'timestamp': datetime.now().isoformat(),
                    'log_type': log_source,
                    'raw_line': line,
                    'hostname': hostname,
                    'ip_address': ip_address
                }
                
                alerts = sigma_engine.match_log(log_dict)
                
                if alerts:
                    # Store alerts and categorize by severity
                    for alert in alerts:
                        severity = alert['severity'].lower()
                        
                        create_alert(
                            log_entry_id=log_entry_id,
                            server_id=server_id,
                            rule_id=alert['rule_id'],
                            title=alert['rule_title'],
                            description=alert.get('rule_description', ''),
                            severity=severity,
                            metadata=alert
                        )
                        alerts_count += 1
                        
                        # Count by severity
                        if severity in alert_breakdown:
                            alert_breakdown[severity] += 1
            
            except Exception as e:
                print(f"[Upload] Error processing line: {e}")
                logs_failed += 1
                continue
    
    return {
        "total_lines": total_lines,
        "logs_count": logs_count,
        "logs_failed": logs_failed,
        "alerts_count": alerts_count,
        "alert_breakdown": alert_breakdown
    }
