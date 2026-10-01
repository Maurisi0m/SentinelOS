"""Hidden Windows watchdog for the SentinelOS HTTP backend."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from typing import BinaryIO

from .service_config import get_node_role, get_service_port


def _log(root_dir: str, message: str) -> None:
    try:
        with open(os.path.join(root_dir, "sentinel_backend.log"), "a", encoding="utf-8") as log:
            log.write(f"[service-manager] {time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


def is_backend_healthy(port: int, timeout: float = 1.0) -> bool:
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/health",
            headers={"User-Agent": "SentinelServiceManager"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError, TimeoutError):
        return False


def wait_for_health(port: int, timeout: float = 45.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_backend_healthy(port):
            return True
        time.sleep(0.5)
    return False


def _manager_lock(root_dir: str) -> BinaryIO | None:
    lock_path = os.path.join(root_dir, "config", "service-manager.lock")
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    handle = open(lock_path, "a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, ImportError):
        handle.close()
        return None
    return handle


def _python_for_backend(root_dir: str) -> str:
    if os.name == "nt":
        candidates = [
            os.path.join(root_dir, ".venv", "Scripts", "python.exe"),
            sys.executable.replace("pythonw.exe", "python.exe"),
        ]
    else:
        candidates = [
            os.path.join(root_dir, ".venv", "bin", "python3"),
            os.path.join(root_dir, ".venv", "bin", "python"),
            sys.executable,
        ]
    return next((path for path in candidates if path and os.path.isfile(path)), sys.executable)


def _spawn_backend(root_dir: str, port: int) -> subprocess.Popen:
    backend_dir = os.path.join(root_dir, "labsentinel_backend")
    log_handle = open(os.path.join(root_dir, "sentinel_backend.log"), "ab")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        return subprocess.Popen(
            [
                _python_for_backend(root_dir),
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(port),
            ],
            cwd=backend_dir,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            close_fds=True,
        )
    finally:
        log_handle.close()


def launch_service_manager(root_dir: str, suppress_ui: bool = True) -> subprocess.Popen | None:
    """Start one hidden watchdog process; its file lock prevents duplicate managers."""
    root_dir = os.path.abspath(root_dir)
    if os.name == "nt":
        candidates = [
            os.path.join(root_dir, ".venv", "Scripts", "pythonw.exe"),
            os.path.join(root_dir, ".venv", "Scripts", "python.exe"),
        ]
        flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        candidates = [
            os.path.join(root_dir, ".venv", "bin", "python3"),
            os.path.join(root_dir, ".venv", "bin", "python"),
        ]
        flags = 0
    launcher = next((path for path in candidates if os.path.isfile(path)), sys.executable)
    args = [launcher, "-m", "installer.background_service"]
    if suppress_ui:
        args.append("--no-open-ui")
    log_handle = open(os.path.join(root_dir, "sentinel_backend.log"), "ab")
    try:
        return subprocess.Popen(
            args,
            cwd=root_dir,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            creationflags=flags,
            close_fds=True,
        )
    finally:
        log_handle.close()


def run_manager(root_dir: str, open_ui: bool = True) -> int:
    root_dir = os.path.abspath(root_dir)
    lock_handle = _manager_lock(root_dir)
    if lock_handle is None:
        return 0

    port = get_service_port(root_dir)
    should_open_ui = open_ui and get_node_role(root_dir) == "master"
    browser_opened = False
    process = None
    retry_delay = 2.0
    next_attempt = 0.0
    started_at = 0.0
    last_healthy = 0.0
    _log(root_dir, f"supervisor iniciado para puerto {port}")

    try:
        while True:
            now = time.monotonic()
            healthy = is_backend_healthy(port)

            if process is not None:
                exit_code = process.poll()
                if exit_code is not None:
                    _log(root_dir, f"backend terminó con código {exit_code}; reintento en {retry_delay:.0f}s")
                    process = None
                    next_attempt = now + retry_delay
                    retry_delay = min(retry_delay * 2, 30.0)
                elif healthy:
                    last_healthy = now
                    retry_delay = 2.0
                elif now - max(started_at, last_healthy) > 90.0:
                    _log(root_dir, "backend sin respuesta saludable por 90s; reiniciando")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    process = None
                    next_attempt = now + retry_delay
                    retry_delay = min(retry_delay * 2, 30.0)

            if process is None and now >= next_attempt:
                if healthy:
                    last_healthy = now
                else:
                    try:
                        process = _spawn_backend(root_dir, port)
                        started_at = now
                        _log(root_dir, f"backend iniciado (PID {process.pid})")
                    except Exception as error:
                        _log(root_dir, f"no se pudo iniciar el backend: {error}")
                        next_attempt = now + retry_delay
                        retry_delay = min(retry_delay * 2, 30.0)

            if should_open_ui and not browser_opened and healthy:
                try:
                    webbrowser.open(f"http://127.0.0.1:{port}")
                    browser_opened = True
                except Exception as error:
                    _log(root_dir, f"no se pudo abrir el cockpit: {error}")

            time.sleep(2.0)
    except KeyboardInterrupt:
        if process is not None and process.poll() is None:
            process.terminate()
        return 0
    finally:
        lock_handle.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="SentinelOS hidden backend watchdog")
    parser.add_argument("--no-open-ui", action="store_true")
    args = parser.parse_args()
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return run_manager(root_dir, open_ui=not args.no_open_ui)


if __name__ == "__main__":
    raise SystemExit(main())
