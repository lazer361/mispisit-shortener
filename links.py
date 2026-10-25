import ipaddress
import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from threading import RLock
from urllib.parse import urlsplit


class LinkError(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def valid_url(value):
    if not value or len(value) > 2048 or "\\" in value:
        return False
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        parts = urlsplit(value)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            return False
        if parts.username is not None or parts.password is not None:
            return False
        if parts.port is not None and not 1 <= parts.port <= 65535:
            return False
        host = parts.hostname.encode("idna").decode("ascii")
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if ":" in host or len(host) > 253:
                return False
            if not all(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", part)
                       for part in host.rstrip(".").split(".")):
                return False
    except (ValueError, UnicodeError):
        return False
    return True


class LinkStore:
    def __init__(self, filename):
        self.filename = Path(filename)
        self.lock = RLock()
        self.filename.parent.mkdir(parents=True, exist_ok=True)
        if not self.filename.exists():
            self._write([])

    def _read(self):
        return json.loads(self.filename.read_text(encoding="utf-8"))

    def _write(self, records):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.filename.parent,
                                             delete=False) as file:
                temporary = file.name
                json.dump(records, file, ensure_ascii=False, indent=2)
            os.replace(temporary, self.filename)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    def all(self):
        with self.lock:
            return sorted(self._read(), key=lambda item: item["id"], reverse=True)

    def find(self, record_id):
        return next((item for item in self.all() if item["id"] == record_id), None)

    def by_code(self, code):
        return next((item for item in self.all() if item["short_code"] == code), None)

    def create(self, original_url, title="", alias=""):
        original_url, title, alias = original_url.strip(), title.strip(), alias.strip()
        if not valid_url(original_url):
            raise LinkError("invalid_url")
        if len(title) > 100:
            raise LinkError("invalid_title")
        if alias and not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", alias):
            raise LinkError("invalid_alias")
        with self.lock:
            records = self._read()
            used_codes = {item["short_code"] for item in records}
            if alias in used_codes:
                raise LinkError("alias_taken")
            code = alias or secrets.token_urlsafe(5)
            while code in used_codes:
                code = secrets.token_urlsafe(5)
            record = {
                "id": max((item["id"] for item in records), default=0) + 1,
                "title": title or urlsplit(original_url).hostname,
                "original_url": original_url,
                "short_code": code,
                "created_at": datetime.now(timezone(timedelta(hours=4))).strftime("%d.%m.%Y %H:%M"),
            }
            records.append(record)
            self._write(records)
            return record
