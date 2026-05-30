from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from language_tutor.errors import TutorError
from language_tutor.package_assets import REQUIRED_MIGRATION_FILES, package_assets_root


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str
    checksum: str


def migration_dir() -> Path:
    return package_assets_root() / "migrations"


def missing_migration_files(root: Path | None = None) -> tuple[str, ...]:
    base = root or package_assets_root()
    return tuple(rel for rel in REQUIRED_MIGRATION_FILES if not (base / rel).exists())


def load_migrations(root: Path | None = None) -> list[Migration]:
    if root is None:
        missing = missing_migration_files()
        if missing:
            joined = ", ".join(missing)
            raise TutorError(
                "missing_migrations",
                f"SQL migration file(s) missing from lingo-loop package: {joined}",
                f"Reinstall lingo-loop from a fixed package containing: {joined}.",
            )
        directory = migration_dir()
    else:
        directory = root
    migrations: list[Migration] = []
    for path in sorted(directory.glob("*.sql")):
        version_text, name = path.stem.split("_", 1)
        sql = path.read_text(encoding="utf-8")
        migrations.append(
            Migration(
                version=int(version_text),
                name=name,
                sql=sql,
                checksum=hashlib.sha256(sql.encode("utf-8")).hexdigest(),
            )
        )
    return migrations


def apply_migrations(conn: sqlite3.Connection, root: Path | None = None) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS migration_records (version INTEGER PRIMARY KEY, name TEXT NOT NULL, checksum TEXT NOT NULL, applied_at TEXT NOT NULL)"
    )
    rows = {
        int(row["version"]): row["checksum"]
        for row in conn.execute("SELECT version, checksum FROM migration_records ORDER BY version")
    }
    expected_next = 1
    for migration in load_migrations(root):
        if migration.version != expected_next:
            raise TutorError(
                "migration_order",
                "Migrations must be numbered without gaps.",
                "Rename migrations in strict order.",
            )
        expected_next += 1
        applied_checksum = rows.get(migration.version)
        if applied_checksum is not None:
            if applied_checksum != migration.checksum:
                raise TutorError(
                    "migration_checksum",
                    "Applied migration checksum changed.",
                    "Restore migration SQL or create a new migration.",
                )
            continue
        conn.executescript(migration.sql)
        conn.execute(
            "INSERT INTO migration_records(version, name, checksum, applied_at) VALUES (?, ?, ?, ?)",
            (
                migration.version,
                migration.name,
                migration.checksum,
                datetime.now(UTC).isoformat(),
            ),
        )
    conn.commit()
