#!/usr/bin/env python3
"""本地演示服务：模拟检索、增量去重和 NEW 状态管理。"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SEED_PATH = DATA_DIR / "seed_jobs.json"
STATE_PATH = DATA_DIR / "state.json"
STATIC_DIR = ROOT / "docs"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_job(job: dict[str, Any], status: str = "existing") -> dict[str, Any]:
    result = dict(job)
    result.setdefault("status", status)
    result.setdefault("first_seen", now_iso())
    result.setdefault("last_seen", result["first_seen"])
    return result


def seed_state() -> dict[str, Any]:
    fixture = read_json(SEED_PATH)
    return {
        "jobs": [normalize_job(job) for job in fixture["seed_jobs"]],
        "refresh_index": 0,
        "last_refresh": None,
    }


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        state = seed_state()
        save_state(state)
        return state
    return read_json(STATE_PATH)


def save_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_candidates(refresh_index: int) -> list[dict[str, Any]]:
    """演示数据源。生产版可在这里接入 CLI、MCP、API 或公开职位源。"""
    fixture = read_json(SEED_PATH)
    batches = fixture.get("refresh_batches", [])
    if not batches:
        return []
    return batches[refresh_index % len(batches)]


def merge_refresh(state: dict[str, Any], candidates: list[dict[str, Any]]) -> int:
    """每次刷新先清掉全部 NEW，再把本次首次入库的职位标记为 NEW。"""
    for job in state["jobs"]:
        job["status"] = "existing"

    by_id = {job["id"]: job for job in state["jobs"]}
    new_count = 0
    refreshed_at = now_iso()
    for candidate in candidates:
        job_id = candidate["id"]
        if job_id in by_id:
            existing = by_id[job_id]
            existing.update(candidate)
            existing["status"] = "existing"
            existing["last_seen"] = refreshed_at
        else:
            new_job = normalize_job(candidate, status="new")
            new_job["first_seen"] = refreshed_at
            new_job["last_seen"] = refreshed_at
            state["jobs"].append(new_job)
            by_id[job_id] = new_job
            new_count += 1

    state["refresh_index"] += 1
    state["last_refresh"] = refreshed_at
    save_state(state)
    return new_count


def payload(state: dict[str, Any], message: str = "") -> dict[str, Any]:
    jobs = sorted(
        state["jobs"],
        key=lambda job: (job.get("status") == "new", job.get("score", 0)),
        reverse=True,
    )
    return {
        "ok": True,
        "jobs": jobs,
        "new_count": sum(job.get("status") == "new" for job in jobs),
        "total": len(jobs),
        "refresh_index": state.get("refresh_index", 0),
        "last_refresh": state.get("last_refresh"),
        "message": message,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "JobMatcherDemo/1.0"

    def send_json(self, body: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/public_jobs.json":
            raw = (STATIC_DIR / "public_jobs.json").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.path == "/api/jobs":
            self.send_json(payload(load_state()))
            return
        if self.path in ("/", "/index.html"):
            html = (STATIC_DIR / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        self.send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/refresh":
            state = load_state()
            candidates = fetch_candidates(state.get("refresh_index", 0))
            new_count = merge_refresh(state, candidates)
            self.send_json(payload(state, f"本次模拟获取 {len(candidates)} 条，新增 {new_count} 条"))
            return
        if self.path == "/api/reset":
            state = seed_state()
            save_state(state)
            self.send_json(payload(state, "已重置演示数据"))
            return
        self.send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def main() -> None:
    host, port = "127.0.0.1", 8765
    print(f"Job Matcher Demo: http://{host}:{port}")
    print("按 Ctrl+C 停止服务")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
