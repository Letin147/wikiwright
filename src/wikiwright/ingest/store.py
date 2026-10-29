"""SQLite + FTS5 chunk store with content-addressed ids and per-source file hashes."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from wikiwright.ingest.chunker import Chunk

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(
    source TEXT PRIMARY KEY,
    repo_dir TEXT NOT NULL,
    license_family TEXT,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS files(
    source TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    PRIMARY KEY (source, path)
);
CREATE TABLE IF NOT EXISTS chunks(
    chunk_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    lang TEXT NOT NULL,
    size INTEGER NOT NULL
);
"""


class ChunkStore:
    """All persisted state for one cache dir lives in a single SQLite file.

    Rows are keyed by ``source:chunk_id``: the content hash alone is NOT unique
    across sources (two repos can contain an identical file), and letting one
    source overwrite another's rows silently steals chunks (bug found in the
    EXP-02 acceptance run: click 622 -> 621).
    """

    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.executescript(_SCHEMA)
        try:
            self.conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(text, chunk_id UNINDEXED)"
            )
        except sqlite3.OperationalError as exc:  # explicit degradation, never silent
            raise RuntimeError(
                "this SQLite build lacks FTS5; install a Python bundled with FTS5 "
                "(python.org / conda builds have it)"
            ) from exc
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # -- metadata ---------------------------------------------------------

    def file_hashes(self, source: str) -> dict[str, str]:
        rows = self.conn.execute(
            "SELECT path, sha256 FROM files WHERE source = ?", (source,)
        ).fetchall()
        return dict(rows)

    def save_source_meta(
        self, source: str, repo_dir: str, license_family: str | None
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?)",
            (source, repo_dir, license_family, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def count_chunks(self, source: str) -> int:
        return int(
            self.conn.execute(
                "SELECT COUNT(*) FROM chunks WHERE source = ?", (source,)
            ).fetchone()[0]
        )

    # -- chunk writes -----------------------------------------------------

    def _row_key(self, source: str, chunk_id: str) -> str:
        return f"{source}:{chunk_id}"

    def replace_file_chunks(
        self, source: str, path: str, sha256: str, chunks: list[Chunk]
    ) -> None:
        """Idempotent write: a file's old chunks are fully replaced by the new set."""
        self.drop_file_chunks(source, path)
        self.conn.execute(
            "INSERT OR REPLACE INTO files VALUES (?, ?, ?)", (source, path, sha256)
        )
        for chunk in chunks:
            key = self._row_key(source, chunk.chunk_id)
            self.conn.execute(
                "INSERT OR REPLACE INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    key,
                    source,
                    chunk.path,
                    chunk.start_line,
                    chunk.end_line,
                    chunk.lang,
                    len(chunk.text),
                ),
            )
            self.conn.execute(
                "INSERT OR REPLACE INTO chunks_fts (text, chunk_id) VALUES (?, ?)",
                (chunk.text, key),
            )
        self.conn.commit()

    def drop_file_chunks(self, source: str, path: str) -> None:
        ids = [
            row[0]
            for row in self.conn.execute(
                "SELECT chunk_id FROM chunks WHERE source = ? AND path = ?", (source, path)
            )
        ]
        if not ids:
            self.conn.execute(
                "DELETE FROM files WHERE source = ? AND path = ?", (source, path)
            )
            self.conn.commit()
            return
        marks = ",".join("?" * len(ids))
        self.conn.execute(f"DELETE FROM chunks_fts WHERE chunk_id IN ({marks})", ids)
        self.conn.execute(f"DELETE FROM chunks WHERE chunk_id IN ({marks})", ids)
        self.conn.execute("DELETE FROM files WHERE source = ? AND path = ?", (source, path))
        self.conn.commit()

    def chunks_for_path(self, source: str, path: str) -> list[dict]:
        """All chunks of one file, in reading order (Analyst context source)."""
        rows = self.conn.execute(
            "SELECT c.start_line, c.end_line, f.text FROM chunks_fts f "
            "JOIN chunks c ON c.chunk_id = f.chunk_id "
            "WHERE c.source = ? AND c.path = ? ORDER BY c.start_line",
            (source, path),
        ).fetchall()
        return [
            {"start_line": start, "end_line": end, "text": text}
            for start, end, text in rows
        ]

    # -- search -----------------------------------------------------------

    def search(
        self, query: str, source: str | None = None, limit: int = 10
    ) -> list[dict]:
        """FTS5 MATCH search; each term is quoted, terms are ANDed."""
        terms = [f'"{part}"' for part in query.split() if part]
        if not terms:
            return []
        match = " AND ".join(terms)
        sql = (
            "SELECT c.path, c.start_line, c.end_line, c.lang, "
            "snippet(chunks_fts, 0, '«', '»', '…', 12) "
            "FROM chunks_fts f JOIN chunks c ON c.chunk_id = f.chunk_id "
            "WHERE chunks_fts MATCH ?"
        )
        params: list = [match]
        if source:
            sql += " AND c.source = ?"
            params.append(source)
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        rows = self.conn.execute(sql, params).fetchall()
        return [
            {
                "path": path,
                "start_line": start,
                "end_line": end,
                "lang": lang,
                "snippet": snippet,
            }
            for path, start, end, lang, snippet in rows
        ]
