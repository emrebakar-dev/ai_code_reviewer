import os
import tempfile
import zipfile
import shutil
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from analyzer import StaticAnalyzer
from llm_reviewer import LLMReviewer, AIReviewResult
from scanner import ProjectScanner
from reporter import Reporter, ProjectReporter

app = FastAPI(title="AI Code Reviewer API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CodeAnalyzeRequest(BaseModel):
    code: str
    filename: str = "snippet.py"
    enable_ai: bool = True
    model: Optional[str] = None
    confidence_threshold: float = 0.0

class DirectoryAnalyzeRequest(BaseModel):
    directory_path: str
    enable_ai: bool = True
    model: Optional[str] = None
    confidence_threshold: float = 0.0

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Code Reviewer API is running"}

@app.get("/api/models")
def get_models():
    default_model = os.getenv("OPENAI_MODEL", "qwen/qwen3.6-27b")
    available_models = [
        "qwen/qwen3.6-27b",
        "groq/compound-mini",
        "groq/compound",
        "openai/gpt-oss-20b",
    ]
    return {
        "default": default_model,
        "models": available_models
    }

@app.post("/api/analyze/code")
def analyze_code(req: CodeAnalyzeRequest):
    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Kod içeriği boş olamaz.")

    tmp_dir = tempfile.mkdtemp(prefix="aicr_single_")
    filepath = os.path.join(tmp_dir, req.filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(req.code)

        static_result = StaticAnalyzer().analyze(filepath)

        static_result.filepath = req.filename

        ai_result_dict = {"skipped": True, "error": "AI incelemesi kapalı", "findings": [], "parse_failed": False}

        if req.enable_ai:
            reviewer = LLMReviewer()
            if req.model:
                reviewer.model = req.model
            res = reviewer.review(source_code=req.code, filepath=req.filename)
            ai_result_dict = {
                "skipped": res.skipped,
                "error": res.error,
                "findings": [f.to_dict() if hasattr(f, "to_dict") else f.__dict__ for f in res.findings],
                "raw_response": res.raw_response,
                "model_used": res.model_used,
                "parse_failed": res.parse_failed
            }

        ai_obj = AIReviewResult(
            skipped=ai_result_dict["skipped"],
            error=ai_result_dict.get("error"),
            findings=res.findings if req.enable_ai and 'res' in locals() else [],
            raw_response=ai_result_dict.get("raw_response"),
            model_used=ai_result_dict.get("model_used"),
            parse_failed=ai_result_dict.get("parse_failed", False),
        )

        reporter = Reporter(static_result, ai_obj)
        report_path = reporter.save_report()


        report_content = ""
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as rf:
                report_content = rf.read()

        return {
            "filename": req.filename,
            "static": {
                "language": static_result.language,
                "syntax_error": static_result.syntax_error,
                "findings": [f.to_dict() for f in static_result.findings if getattr(f, "confidence", 1.0) >= req.confidence_threshold]
            },
            "ai": ai_result_dict,
            "report": report_content,
            "report_path": report_path
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

@app.post("/api/analyze/directory")
def analyze_directory(req: DirectoryAnalyzeRequest):
    dir_path = req.directory_path.strip()
    if not os.path.isdir(dir_path):
        raise HTTPException(status_code=400, detail=f"Klasör bulunamadı: {dir_path}")

    scanner = ProjectScanner(no_ai=not req.enable_ai, model=req.model)
    scan_res = scanner.scan(dir_path)

    reporter = ProjectReporter(scan_res)
    report_path = reporter.save_report()

    report_content = ""
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as rf:
            report_content = rf.read()

    formatted_results = []
    for fr in scan_res.sorted_by_risk():
        rel_path = os.path.relpath(fr.filepath, dir_path)
        formatted_results.append({
            "filepath": rel_path,
            "abs_path": fr.filepath,
            "language": fr.static.language,
            "total_findings": fr.total_findings,
            "high_count": fr.high_count,
            "medium_count": fr.medium_count,
            "low_count": fr.low_count,
            "static": {
                "syntax_error": fr.static.syntax_error,
                "findings": [f.to_dict() for f in fr.static.findings if getattr(f, "confidence", 1.0) >= req.confidence_threshold]
            },
            "ai": {
                "skipped": fr.ai.skipped,
                "error": fr.ai.error,
                "findings": [f.to_dict() if hasattr(f, "to_dict") else f.__dict__ for f in fr.ai.findings],
                "parse_failed": getattr(fr.ai, "parse_failed", False)
            }
        })

    return {
        "directory": os.path.basename(dir_path) or dir_path,
        "total_files": len(scan_res.results),
        "results": formatted_results,
        "report": report_content,
        "report_path": report_path
    }

@app.post("/api/analyze/zip")
async def analyze_zip(
    file: UploadFile = File(...),
    enable_ai: bool = Form(True),
    model: Optional[str] = Form(None),
    confidence_threshold: float = Form(0.0)
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Yalnızca .zip dosyaları desteklenir.")

    tmp_dir = tempfile.mkdtemp(prefix="aicr_zip_")
    zip_path = os.path.join(tmp_dir, file.filename)

    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        scanner = ProjectScanner(no_ai=not enable_ai, model=model)
        scan_res = scanner.scan(extract_dir)
        scan_res.directory = file.filename

        reporter = ProjectReporter(scan_res)
        report_path = reporter.save_report()

        report_content = ""
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as rf:
                report_content = rf.read()

        formatted_results = []
        for fr in scan_res.sorted_by_risk():
            rel_path = os.path.relpath(fr.filepath, extract_dir)
            formatted_results.append({
                "filepath": rel_path,
                "language": fr.static.language,
                "total_findings": fr.total_findings,
                "high_count": fr.high_count,
                "medium_count": fr.medium_count,
                "low_count": fr.low_count,
                "static": {
                    "syntax_error": fr.static.syntax_error,
                    "findings": [f.to_dict() for f in fr.static.findings if getattr(f, "confidence", 1.0) >= confidence_threshold]
                },
                "ai": {
                    "skipped": fr.ai.skipped,
                    "error": fr.ai.error,
                    "findings": [f.to_dict() if hasattr(f, "to_dict") else f.__dict__ for f in fr.ai.findings],
                    "parse_failed": getattr(fr.ai, "parse_failed", False)
                }
            })

        return {
            "directory": file.filename,
            "total_files": len(scan_res.results),
            "results": formatted_results,
            "report": report_content,
            "report_path": report_path
        }
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
