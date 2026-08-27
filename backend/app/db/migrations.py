from app.db.schema_migrations import run_schema_migrations

EQUIPMENT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    git_path TEXT NOT NULL,
    document_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

GIT_COMMIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS git_commit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    commit_hash TEXT NOT NULL,
    commit_date TEXT NOT NULL,
    author TEXT NOT NULL,
    message TEXT NOT NULL,
    parent_hash TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    UNIQUE (equipment_id, commit_hash)
);
"""

GIT_CHANGE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS git_change (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    commit_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL,
    additions INTEGER,
    deletions INTEGER,
    diff TEXT,
    FOREIGN KEY (commit_id) REFERENCES git_commit(id) ON DELETE CASCADE
);
"""

DOCUMENT_CACHE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS document_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    modified_at TEXT NOT NULL,
    parsed_at TEXT NOT NULL,
    slide_count INTEGER NOT NULL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE,
    UNIQUE (equipment_id, file_path)
);
"""

SLIDE_CACHE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS slide_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_cache_id INTEGER NOT NULL,
    slide_number INTEGER NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    FOREIGN KEY (document_cache_id) REFERENCES document_cache(id) ON DELETE CASCADE,
    UNIQUE (document_cache_id, slide_number)
);
"""

CHANGE_ITEM_CACHE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS change_item_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_cache_id INTEGER NOT NULL,
    slide_no INTEGER NOT NULL,
    item_no TEXT,
    change_title TEXT,
    csr_no TEXT,
    business_background TEXT,
    current_status TEXT,
    as_is TEXT,
    to_be TEXT,
    source_functions_json TEXT NOT NULL DEFAULT '[]',
    test_cases_json TEXT NOT NULL DEFAULT '[]',
    applicable_scopes_json TEXT NOT NULL DEFAULT '[]',
    raw_text TEXT NOT NULL DEFAULT '',
    parser_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_cache_id) REFERENCES document_cache(id) ON DELETE CASCADE
);
"""

CHANGE_ITEM_CACHE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_change_item_document
    ON change_item_cache(document_cache_id);
"""

# STEP 7: Evidence Link cache. Keyed by (git_commit_id, git_file_path,
# change_item_cache_id, linker_version) rather than commit-only, because a
# single commit can touch multiple files and each (commit, file) pair is a
# distinct Git Candidate with its own diff/file_path evidence — collapsing
# them to commit-only would let one file's score silently overwrite another's.
# Cascade delete on both FKs gives stale-link cleanup for free (git_commit
# removed on repo/equipment delete, change_item_cache removed on document
# re-parse/hash change) — no manual invalidation code needed.
CHANGE_LINK_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS change_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    git_commit_id INTEGER NOT NULL,
    git_file_path TEXT NOT NULL,
    change_item_cache_id INTEGER NOT NULL,
    link_score INTEGER NOT NULL,
    match_reasons_json TEXT NOT NULL DEFAULT '[]',
    linker_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (git_commit_id) REFERENCES git_commit(id) ON DELETE CASCADE,
    FOREIGN KEY (change_item_cache_id) REFERENCES change_item_cache(id) ON DELETE CASCADE,
    UNIQUE (git_commit_id, git_file_path, change_item_cache_id, linker_version)
);
"""

CHANGE_LINK_INDEX_COMMIT_SQL = """
CREATE INDEX IF NOT EXISTS idx_change_link_commit
    ON change_link(git_commit_id);
"""

CHANGE_LINK_INDEX_ITEM_SQL = """
CREATE INDEX IF NOT EXISTS idx_change_link_item
    ON change_link(change_item_cache_id);
"""

MIGRATIONS = [
    EQUIPMENT_TABLE_SQL,
    GIT_COMMIT_TABLE_SQL,
    GIT_CHANGE_TABLE_SQL,
    DOCUMENT_CACHE_TABLE_SQL,
    SLIDE_CACHE_TABLE_SQL,
    CHANGE_ITEM_CACHE_TABLE_SQL,
    CHANGE_ITEM_CACHE_INDEX_SQL,
    CHANGE_LINK_TABLE_SQL,
    CHANGE_LINK_INDEX_COMMIT_SQL,
    CHANGE_LINK_INDEX_ITEM_SQL,
]


def run_migrations(conn) -> None:
    for sql in MIGRATIONS:
        conn.execute(sql)
    run_schema_migrations(conn)
    conn.commit()
