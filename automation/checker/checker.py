#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical GitHub -> Orca/OpenCode project checker.

Infrastructure only. It never designs research, edits research files, launches a new
OpenCode process, or pulls/merges the visible worktree. It fetches the configured
remote branch, reads the remote task contract, and sends exactly one `继续` to the
existing OpenCode terminal for this repository when the task is eligible.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import locale
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
CLAIMABLE = {"PENDING", "READY", "READY_FOR_OPENCODE"}
TERMINAL_REPORT_WORDS = ("DONE", "COMPLETE", "SUCCESS", "FAILED", "BLOCKED", "REVIEW", "RUNNING")
HEADER_RE = re.compile(r"(?m)^([A-Z][A-Z0-9_]*)\s*[:=]\s*`?([^`\r\n]+?)`?\s*$")


class CheckerError(RuntimeError):
    pass


class NotReady(CheckerError):
    pass


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def decode(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    candidates = ["utf-8-sig", locale.getpreferredencoding(False), "gb18030"]
    seen: set[str] = set()
    for enc in candidates:
        if not enc or enc.lower() in seen:
            continue
        seen.add(enc.lower())
        try:
            return data.decode(enc, errors="strict")
        except (UnicodeDecodeError, LookupError):
            pass
    return data.decode("utf-8", errors="replace")


def run(args: list[str], cwd: Path | None = None, timeout: float = 60) -> subprocess.CompletedProcess[bytes]:
    kwargs: dict[str, Any] = {}
    if os.name == "nt":
        kwargs["creationflags"] = CREATE_NO_WINDOW
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            **kwargs,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise NotReady(f"COMMAND_UNAVAILABLE_OR_TIMEOUT:{args[0]}") from exc


def git(repo: Path, *args: str, check: bool = True) -> str:
    cp = run(["git", "-C", str(repo), *args], cwd=repo, timeout=60)
    out, err = decode(cp.stdout).strip(), decode(cp.stderr).strip()
    if check and cp.returncode:
        raise NotReady(f"GIT_FAILED:{' '.join(args[:2])}:{err or out}")
    return out


def repo_root(start: Path) -> Path:
    return Path(git(start.resolve(), "rev-parse", "--show-toplevel")).resolve()


def git_common_dir(repo: Path) -> Path:
    raw = Path(git(repo, "rev-parse", "--git-common-dir"))
    return (raw if raw.is_absolute() else repo / raw).resolve()


def normalize_slug(url: str) -> str:
    value = (url or "").strip().rstrip("/")
    value = re.sub(r"^git@github\.com:", "", value, flags=re.I)
    value = re.sub(r"^ssh://git@github\.com/", "", value, flags=re.I)
    value = re.sub(r"^https?://github\.com/", "", value, flags=re.I)
    value = re.sub(r"\.git$", "", value, flags=re.I)
    return value


def load_config(path: Path) -> dict[str, Any]:
    try:
        cfg = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise NotReady(f"CONFIG_UNREADABLE:{path}") from exc
    if not isinstance(cfg, dict) or cfg.get("schema_version") != 1:
        raise NotReady("CONFIG_SCHEMA_VERSION")
    slug = str(cfg.get("repository_slug") or "").strip()
    if not slug or slug.endswith("/NEW-PROJECT"):
        raise NotReady("CONFIG_REPOSITORY_SLUG")
    return cfg


def runtime_dir(repo: Path, slug: str) -> Path:
    name = re.sub(r"[^A-Za-z0-9_.-]+", "-", slug).strip("-") + "-checker"
    out = git_common_dir(repo) / name
    out.mkdir(parents=True, exist_ok=True)
    return out


def read_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value
    except (OSError, ValueError):
        return default


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def headers(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in HEADER_RE.finditer(text or ""):
        key = match.group(1).upper().strip()
        if key not in out:
            out[key] = match.group(2).strip()
    return out


def truthy(value: str | None) -> bool:
    return (value or "").strip().upper() in {"YES", "TRUE", "1", "Y"}


def split_paths(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in re.split(r"[;|]", value) if x.strip()]


def remote_text(repo: Path, remote_ref: str, path: str, required: bool = True) -> str:
    cp = run(["git", "-C", str(repo), "show", f"{remote_ref}:{path}"], cwd=repo, timeout=30)
    if cp.returncode:
        if required:
            raise NotReady(f"REMOTE_FILE_MISSING:{path}")
        return ""
    return decode(cp.stdout)


def remote_blob(repo: Path, remote_ref: str, path: str) -> str:
    cp = run(["git", "-C", str(repo), "rev-parse", f"{remote_ref}:{path}"], cwd=repo, timeout=30)
    if cp.returncode:
        raise NotReady(f"REMOTE_BLOB_MISSING:{path}")
    return decode(cp.stdout).strip()


def remote_exists(repo: Path, remote_ref: str, path: str) -> bool:
    cp = run(["git", "-C", str(repo), "cat-file", "-e", f"{remote_ref}:{path}"], cwd=repo, timeout=30)
    return cp.returncode == 0


def report_blocks(report: dict[str, str], task_id: str, version: str) -> bool:
    if report.get("TASK_ID", "") != task_id:
        return False
    rv = report.get("TASK_VERSION", "").strip()
    if rv and rv != version:
        return False
    status = report.get("STATUS", "").upper()
    return any(word in status for word in TERMINAL_REPORT_WORDS)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class LeaseLock:
    """Short one-shot lock with orphan/stale recovery.

    A historical lock file can never permanently block future polls. Since a normal
    checker tick is bounded by subprocess timeouts, a lock older than stale_seconds
    is recoverable even if a PID was reused.
    """

    def __init__(self, path: Path, stale_seconds: int):
        self.path = path
        self.stale_seconds = max(60, int(stale_seconds))
        self.owned = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            payload = {"pid": os.getpid(), "created_epoch": time.time(), "created_at": now_iso()}
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                try:
                    os.write(fd, json.dumps(payload).encode("utf-8"))
                finally:
                    os.close(fd)
                self.owned = True
                return True
            except FileExistsError:
                old = read_json(self.path, {})
                age = time.time() - float(old.get("created_epoch") or 0)
                old_pid = int(old.get("pid") or 0)
                if age <= self.stale_seconds and pid_alive(old_pid):
                    return False
                try:
                    self.path.unlink()
                except OSError:
                    return False
        return False

    def release(self) -> None:
        if self.owned:
            try:
                self.path.unlink(missing_ok=True)
            except OSError:
                pass
            self.owned = False


def orca_command() -> list[str]:
    direct = shutil.which("orca") or shutil.which("orca.exe")
    if direct:
        return [direct]
    node = shutil.which("node")
    local = os.environ.get("LOCALAPPDATA")
    if node and local:
        cli = Path(local) / "Programs" / "orca" / "resources" / "app.asar.unpacked" / "out" / "cli" / "index.js"
        if cli.is_file():
            return [node, str(cli)]
    raise NotReady("ORCA_CLI_NOT_FOUND")


def orca_raw(repo: Path, args: list[str], timeout: float = 30) -> tuple[int, dict[str, Any]]:
    cp = run(orca_command() + args + (["--json"] if "--json" not in args else []), cwd=repo, timeout=timeout)
    text = decode(cp.stdout)
    try:
        payload = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError as exc:
        raise NotReady("ORCA_CLI_BAD_JSON") from exc
    return cp.returncode, payload if isinstance(payload, dict) else {}


def orca_json(repo: Path, args: list[str], timeout: float = 30) -> dict[str, Any]:
    rc, payload = orca_raw(repo, args, timeout)
    if rc != 0 or payload.get("ok") is not True:
        detail = payload.get("error") if isinstance(payload, dict) else None
        code = str(detail.get("code") or "") if isinstance(detail, dict) else ""
        # Only publish an API error code: never expose local paths, tokens, or raw stderr.
        code = re.sub(r"[^A-Za-z0-9_-]", "", code)[:45]
        raise NotReady("ORCA_CLI_FAILED" + (":" + code if code else ":NO_ERROR_CODE"))
    return payload


def same_path(value: str | None, target: Path) -> bool:
    if not value:
        return False
    return os.path.normcase(os.path.abspath(value)) == os.path.normcase(os.path.abspath(str(target)))


def choose_terminal(repo: Path, preferred: str | None) -> str:
    try:
        payload = orca_json(repo, ["terminal", "list", "--worktree", f"path:{repo}", "--limit", "20"])
    except NotReady as original_error:
        if not str(original_error).startswith("ORCA_CLI_FAILED"):
            raise
        # The Orca CLI version might reject --worktree. Read-only list fallback;
        # all candidate terminals are STILL filtered by exact local worktree below.
        try:
            payload = orca_json(repo, ["terminal", "list", "--limit", "20"])
        except NotReady as fallback_error:
            raise NotReady(
                "ORCA_LIST_UNAVAILABLE:filtered=" + str(original_error).split(":")[-1]
                + ";fallback=" + str(fallback_error).split(":")[-1]
            ) from fallback_error
    terms = payload.get("result", {}).get("terminals", [])
    candidates = [
        t for t in terms
        if isinstance(t, dict)
        and t.get("agentIdentity") == "opencode"
        and t.get("connected") is True
        and t.get("writable") is True
        and t.get("orphaned") is not True
        and same_path(t.get("worktreePath"), repo)
        and isinstance(t.get("handle"), str)
    ]
    if preferred:
        for term in candidates:
            if term["handle"] == preferred:
                return preferred
    if len(candidates) == 1:
        return candidates[0]["handle"]
    if not candidates:
        raise NotReady("ORCA_OPENCODE_NOT_FOUND")
    raise NotReady("ORCA_OPENCODE_AMBIGUOUS")


def terminal_idle(repo: Path, handle: str, timeout_ms: int) -> bool:
    rc, payload = orca_raw(
        repo,
        ["terminal", "wait", "--terminal", handle, "--for", "tui-idle", "--timeout-ms", str(timeout_ms)],
        timeout=max(5, timeout_ms / 1000 + 3),
    )
    if rc != 0:
        # Orca timeout is a normal busy observation.
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        if isinstance(error, dict) and error.get("code") == "timeout":
            return False
        return False
    return payload.get("ok") is True and payload.get("result", {}).get("wait", {}).get("satisfied") is True


def focus_terminal(repo: Path, handle: str) -> dict[str, Any]:
    errors: list[str] = []
    for attempt in (1, 2):
        try:
            orca_json(repo, ["terminal", "switch", "--terminal", handle], timeout=10)
            return {
                "focus_status": "FOCUSED" if attempt == 1 else "FOCUS_RETRY_SUCCEEDED",
                "focus_attempts": attempt,
                "focus_error": None,
            }
        except Exception as exc:
            errors.append(str(exc)[:200])
    return {
        "focus_status": "FOCUS_FAILED",
        "focus_attempts": 2,
        "focus_error": errors[-1] if errors else "unknown",
    }


def send_continue(repo: Path, handle: str, text: str) -> dict[str, Any]:
    payload = orca_json(repo, ["terminal", "send", "--terminal", handle, "--text", text, "--enter"], timeout=15)
    if payload.get("result", {}).get("send", {}).get("accepted") is not True:
        raise NotReady("ORCA_CONTINUE_NOT_ACCEPTED")
    # The input is already accepted. Focus failure must never trigger a resend.
    return focus_terminal(repo, handle)


def save_last(runtime: Path, result: dict[str, Any]) -> None:
    atomic_json(runtime / "last_check.json", {"checked_at": now_iso(), **result})


def check_once(start: Path, config_path: Path, check_only: bool = False) -> dict[str, Any]:
    cfg = load_config(config_path)
    repo = repo_root(start)
    slug = str(cfg["repository_slug"])
    runtime = runtime_dir(repo, slug)
    lock = LeaseLock(runtime / "checker.lock", int(cfg.get("lock_stale_seconds") or 180))
    if not lock.acquire():
        result = {"status": "CHECKER_BUSY"}
        save_last(runtime, result)
        return result

    try:
        origin = git(repo, "remote", "get-url", "origin")
        if normalize_slug(origin).lower() != slug.lower():
            result = {"status": "NOT_READY_REPOSITORY_MISMATCH", "origin": normalize_slug(origin), "expected": slug}
            save_last(runtime, result)
            return result

        branch = str(cfg.get("branch") or "main")
        git(repo, "fetch", "--no-tags", "origin", branch)
        remote_ref = f"refs/remotes/origin/{branch}"
        remote_head = git(repo, "rev-parse", remote_ref)
        current_file = str(cfg.get("current_task_file") or "CURRENT_TASK.md")
        task_file = str(cfg.get("task_file") or "OPENCODE_TASK.md")
        report_file = str(cfg.get("report_file") or "OPENCODE_REPORT.md")
        current_text = remote_text(repo, remote_ref, current_file)
        task_text = remote_text(repo, remote_ref, task_file)
        report_text = remote_text(repo, remote_ref, report_file, required=False)
        cur, task, report = headers(current_text), headers(task_text), headers(report_text)

        task_id = cur.get("TASK_ID", "")
        version = cur.get("TASK_VERSION", "")
        base = {"task_id": task_id, "task_version": version, "remote_head": remote_head}
        status = cur.get("STATUS", "").upper()
        if not task_id or not version:
            result = {"status": "NOT_READY_TASK_METADATA", **base}
            save_last(runtime, result)
            return result
        if status not in CLAIMABLE or cur.get("NEXT_ACTOR", "").upper() != "OPENCODE" or cur.get("EXECUTOR", "").upper() != "OPENCODE" or not truthy(cur.get("AUTOMATION_READY")):
            result = {"status": "IDLE_NO_EXECUTABLE_TASK", **base}
            save_last(runtime, result)
            return result

        for key in ("TASK_ID", "TASK_VERSION"):
            if task.get(key, "") != cur.get(key, ""):
                result = {"status": f"NOT_READY_{key}_MISMATCH", **base}
                save_last(runtime, result)
                return result
        if task.get("STATUS", "").upper() not in CLAIMABLE or task.get("EXECUTOR", "").upper() != "OPENCODE" or task.get("NEXT_ACTOR", "").upper() != "OPENCODE" or not truthy(task.get("AUTOMATION_READY")):
            result = {"status": "NOT_READY_TASK_CONTRACT_MISMATCH", **base}
            save_last(runtime, result)
            return result

        current_required = split_paths(cur.get("AUTOMATION_REQUIRED_FILES"))
        task_required = split_paths(task.get("AUTOMATION_REQUIRED_FILES"))
        if not current_required:
            result = {"status": "NOT_READY_REQUIRED_FILES_MISSING", **base}
            save_last(runtime, result)
            return result
        if task_required and task_required != current_required:
            result = {"status": "NOT_READY_REQUIRED_FILES_MISMATCH", **base}
            save_last(runtime, result)
            return result
        missing = [p for p in current_required if not remote_exists(repo, remote_ref, p)]
        if missing:
            result = {"status": "NOT_READY_REQUIRED_REMOTE_FILE_MISSING", "missing": missing, **base}
            save_last(runtime, result)
            return result

        if report_blocks(report, task_id, version):
            result = {"status": "IDLE_TASK_ALREADY_ATTEMPTED", "report_status": report.get("STATUS", ""), **base}
            save_last(runtime, result)
            return result

        current_blob = remote_blob(repo, remote_ref, current_file)
        task_blob = remote_blob(repo, remote_ref, task_file)
        fingerprint = hashlib.sha256((task_id + "\n" + version + "\n" + current_blob + "\n" + task_blob).encode("utf-8")).hexdigest()
        trigger_key = f"{task_id}|{version}|{fingerprint}"

        state_path = runtime / "state.json"
        state = read_json(state_path, {"schema_version": 1, "sent": {}})
        if not isinstance(state, dict):
            state = {"schema_version": 1, "sent": {}}
        sent = state.get("sent") if isinstance(state.get("sent"), dict) else {}
        if trigger_key in sent:
            result = {"status": "IDLE_ALREADY_CONTINUED", "task_fingerprint": fingerprint, **base}
            save_last(runtime, result)
            return result

        if check_only or cfg.get("enabled") is False:
            result = {"status": "READY_CHECK_ONLY", "task_fingerprint": fingerprint, **base}
            save_last(runtime, result)
            return result

        preferred = str(state.get("preferred_terminal_handle") or "").strip() or None
        handle = choose_terminal(repo, preferred)
        if not terminal_idle(repo, handle, int(cfg.get("orca_idle_timeout_ms") or 1200)):
            result = {"status": "ORCA_OPENCODE_BUSY", "terminal_handle": handle, "task_fingerprint": fingerprint, **base}
            save_last(runtime, result)
            return result

        focus = send_continue(repo, handle, str(cfg.get("continue_text") or "继续"))
        sent[trigger_key] = {
            "sent_at": now_iso(),
            "task_id": task_id,
            "task_version": version,
            "task_fingerprint": fingerprint,
            "remote_head": remote_head,
            "terminal_handle": handle,
            **focus,
        }
        if len(sent) > 100:
            sent = dict(list(sent.items())[-100:])
        state.update(
            schema_version=1,
            preferred_terminal_handle=handle,
            last_trigger_key=trigger_key,
            last_sent_at=now_iso(),
            sent=sent,
        )
        atomic_json(state_path, state)
        result = {
            "status": "ORCA_CONTINUE_SENT",
            "terminal_handle": handle,
            "task_fingerprint": fingerprint,
            **focus,
            **base,
        }
        save_last(runtime, result)
        return result
    finally:
        lock.release()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--config", default=None)
    parser.add_argument("--check", action="store_true")
    ns = parser.parse_args(argv)
    script_dir = Path(__file__).resolve().parent
    config = Path(ns.config).resolve() if ns.config else script_dir / "config.json"
    try:
        result = check_once(Path(ns.repo), config, ns.check)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("status") not in {
            "NOT_READY_REPOSITORY_MISMATCH",
            "NOT_READY_TASK_METADATA",
            "NOT_READY_TASK_ID_MISMATCH",
            "NOT_READY_TASK_VERSION_MISMATCH",
            "NOT_READY_TASK_CONTRACT_MISMATCH",
            "NOT_READY_REQUIRED_FILES_MISSING",
            "NOT_READY_REQUIRED_FILES_MISMATCH",
            "NOT_READY_REQUIRED_REMOTE_FILE_MISSING",
        } else 2
    except NotReady as exc:
        print(json.dumps({"status": str(exc)}, ensure_ascii=False))
        return 2
    except Exception as exc:
        print(json.dumps({"status": "CHECKER_ERROR", "error": f"{type(exc).__name__}:{exc}"}, ensure_ascii=False))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
