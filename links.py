import ipaddress
import re
import secrets
import time
from datetime import timedelta, timezone
from urllib.parse import urlsplit

import psycopg
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row


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
    def __init__(self, database_url):
        self.database_url = database_url
        for attempt in range(20):
            try:
                self._create_schema()
                break
            except psycopg.OperationalError:
                if attempt == 19:
                    raise
                time.sleep(1)

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row, connect_timeout=3)

    def _create_schema(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    title VARCHAR(100) NOT NULL,
                    original_url TEXT NOT NULL CHECK (char_length(original_url) BETWEEN 1 AND 2048),
                    short_code VARCHAR(32) NOT NULL UNIQUE
                        CHECK (short_code ~ '^[A-Za-z0-9_-]{3,32}$'),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    @staticmethod
    def _record(row):
        if row is not None:
            row["created_at"] = row["created_at"].astimezone(
                timezone(timedelta(hours=4))
            ).strftime("%d.%m.%Y %H:%M")
        return row

    def all(self):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, title, original_url, short_code, created_at FROM links ORDER BY id DESC"
            ).fetchall()
        return [self._record(row) for row in rows]

    def find(self, record_id):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, original_url, short_code, created_at FROM links WHERE id = %s",
                (record_id,),
            ).fetchone()
        return self._record(row)

    def by_code(self, code):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, title, original_url, short_code, created_at FROM links WHERE short_code = %s",
                (code,),
            ).fetchone()
        return self._record(row)

    def create(self, original_url, title="", alias=""):
        original_url, title, alias = original_url.strip(), title.strip(), alias.strip()
        if not valid_url(original_url):
            raise LinkError("invalid_url")
        if len(title) > 100:
            raise LinkError("invalid_title")
        if alias and not re.fullmatch(r"[A-Za-z0-9_-]{3,32}", alias):
            raise LinkError("invalid_alias")
        title = title or urlsplit(original_url).hostname[:100]
        for _ in range(12):
            code = alias or secrets.token_urlsafe(5)
            try:
                with self._connect() as connection:
                    row = connection.execute(
                        """INSERT INTO links (title, original_url, short_code)
                           VALUES (%s, %s, %s)
                           RETURNING id, title, original_url, short_code, created_at""",
                        (title, original_url, code),
                    ).fetchone()
                return self._record(row)
            except UniqueViolation:
                if alias:
                    raise LinkError("alias_taken") from None
        raise RuntimeError("Не удалось создать уникальное короткое имя")
