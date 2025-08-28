#!/usr/bin/env python3
import os
import sys
import re
import time
import base64
import requests
from pathlib import Path
from typing import List, Dict, Optional

API_BASE = "https://api.github.com"
MAX_WAIT_SECONDS = 180  # 3 minutes

class RateLimitTooLong(Exception):
    def __init__(self, wait_seconds: int):
        super().__init__(f"Rate limit wait {wait_seconds}s exceeds {MAX_WAIT_SECONDS}s")
        self.wait_seconds = wait_seconds

def get_auth_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        token_path = Path.home() / ".github-token"
        if token_path.exists():
            token = token_path.read_text().strip()
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def parse_github_url(url: str):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$)", url.strip())
    if not m:
        raise ValueError(f"Unrecognized GitHub URL: {url}")
    owner, repo = m.group(1), m.group(2)
    return owner, repo

def parse_rate_limit_wait_seconds(resp: requests.Response) -> Optional[int]:
    # Prefer Retry-After if present
    ra = resp.headers.get("Retry-After")
    if ra:
        try:
            return int(float(ra))
        except Exception:
            pass
    # Fallback to X-RateLimit-Reset (epoch seconds)
    reset = resp.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            reset_ts = int(float(reset))
            now = int(time.time())
            wait = max(0, reset_ts - now)
            return wait
        except Exception:
            pass
    return None

def do_get(session: requests.Session, url: str, *, params=None, stream=False) -> requests.Response:
    # At most one retry if wait <= MAX_WAIT_SECONDS
    for attempt in range(2):
        resp = session.get(url, params=params, stream=stream)
        if resp.status_code in (403, 429):
            wait = parse_rate_limit_wait_seconds(resp)
            # Only treat as rate-limit if we have a parseable wait
            if wait is not None:
                if wait > MAX_WAIT_SECONDS:
                    raise RateLimitTooLong(wait)
                # Basic sleep-and-retry once
                if attempt == 0:
                    time.sleep(wait)
                    continue
        # If not rate-limited (or after retry), return or raise
        if 200 <= resp.status_code < 300:
            return resp
        resp.raise_for_status()
    # If loop exits unexpectedly
    resp.raise_for_status()
    return resp  # unreachable

def get_default_branch(session: requests.Session, owner: str, repo: str) -> str:
    try:
        r = do_get(session, f"{API_BASE}/repos/{owner}/{repo}")
    except RateLimitTooLong as e:
        print(f"Rate limit too long while fetching repo metadata (wait {e.wait_seconds}s). Exiting.", file=sys.stderr)
        sys.exit(2)
    data = r.json()
    return data["default_branch"]

def is_text_bytes(b: bytes) -> bool:
    if not b:
        return True
    if b'\x00' in b:
        return False
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        return False
    printable = sum(
        (31 < ord(ch) < 127) or ch in "\n\r\t\f\b" or ord(ch) >= 0xA0
        for ch in s
    )
    ratio = printable / max(1, len(s))
    return ratio > 0.90

def fetch_file_bytes(session: requests.Session, owner: str, repo: str, path: str, ref: str) -> Optional[bytes]:
    # Try contents API first (may include base64 'content')
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    try:
        r = do_get(session, url, params={"ref": ref})
    except RateLimitTooLong:
        # Signal to caller to print "rate-limit error" for this file
        return None
    info = r.json()

    content_b64 = info.get("content")
    encoding = info.get("encoding")
    download_url = info.get("download_url")

    if content_b64 and encoding == "base64":
        try:
            return base64.b64decode(content_b64, validate=False)
        except Exception:
            pass  # fallback

    # For large files or missing 'content', try raw download; may not have RL headers
    if download_url:
        r2 = session.get(download_url, stream=True)
        if r2.status_code in (403, 429):
            # Try to parse wait; if too long, indicate None; else sleep and retry once
            wait = parse_rate_limit_wait_seconds(r2)
            if wait is not None and wait > MAX_WAIT_SECONDS:
                return None
            if wait is not None:
                time.sleep(wait)
                r2 = session.get(download_url, stream=True)
        r2.raise_for_status()
        return r2.content

    # Fallback to git blob by sha
    sha = info.get("sha")
    if sha:
        try:
            r3 = do_get(session, f"{API_BASE}/repos/{owner}/{repo}/git/blobs/{sha}")
        except RateLimitTooLong:
            return None
        data = r3.json()
        if data.get("encoding") == "base64" and data.get("content"):
            return base64.b64decode(data["content"], validate=False)

    # Give up; treat as binary empty
    return b""

def print_text_file(path: str, text: str):
    sys.stdout.write(f"<{path}>\n")
    sys.stdout.write(text if text.endswith("\n") else text + "\n")
    sys.stdout.write(f"</{path}>\n")

def print_binary_file(path: str):
    sys.stdout.write(f"<{path}/>\n")

def dfs_dir(session: requests.Session, owner: str, repo: str, path: str, ref: str):
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}" if path else f"{API_BASE}/repos/{owner}/{repo}/contents"
    try:
        r = do_get(session, url, params={"ref": ref})
    except RateLimitTooLong as e:
        print(f"Rate limit too long while listing directory '{path or '/'}' (wait {e.wait_seconds}s). Exiting.", file=sys.stderr)
        sys.exit(2)

    items: List[Dict] = r.json()
    if isinstance(items, dict) and items.get("type") == "file":
        items = [items]

    # Depth-first: directories first, then files, sorted by name
    items.sort(key=lambda it: (0 if it.get("type") == "dir" else 1, it.get("name", "")))

    for it in items:
        it_type = it.get("type")
        it_path = it.get("path")
        if it_type == "dir":
            dfs_dir(session, owner, repo, it_path, ref)
        elif it_type == "file":
            b = fetch_file_bytes(session, owner, repo, it_path, ref)
            if b is None:
                # Replace file contents with literal "rate-limit error"
                print_text_file(it_path, "rate-limit error")
            else:
                if is_text_bytes(b):
                    try:
                        text = b.decode("utf-8")
                    except UnicodeDecodeError:
                        text = b.decode("latin-1")
                    print_text_file(it_path, text)
                else:
                    print_binary_file(it_path)
        else:
            # symlink, submodule, etc.
            if it_path:
                print_binary_file(it_path)

def main(url=None):
    if not url and len(sys.argv) != 2:
        print("Usage: python3 print_repo_files.py <github_repo_url>", file=sys.stderr)
        sys.exit(1)
    url = url or sys.argv[1]
    owner, repo = parse_github_url(url)
    headers = get_auth_headers()

    with requests.Session() as session:
        session.headers.update(headers)
        ref = get_default_branch(session, owner, repo)
        dfs_dir(session, owner, repo, "", ref)

if __name__ == "__main__":
    main("https://github.com/TypingMind/awesome-typingmind")
