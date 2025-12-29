"""
Created December 26, 2025

@author montreal91
"""
import sqlite3
import tomllib
from pathlib import Path
from time import time_ns
from typing import NamedTuple

from persistence.sql import read_sql_file


class Migration(NamedTuple):
    migration_id: int
    file: str
    name: str


def load_migrations(index_file):
    index_file = Path(index_file)

    with index_file.open("rb") as f:
        data = tomllib.load(f)

    migrations = []
    for entry in data.get("migration", []):
        migrations.append(
            Migration(
                migration_id=int(entry["id"]),
                file=str(entry["file"]),
                name=str(entry.get("name", "")),
            )
        )

    return migrations



def get_applied_migrations(conn):
    # res = []

    query_res = conn.execute(read_sql_file("data/migrations/_get_migrations.sql")).fetchall()
    # print(query_res)
    return set([row[0] for row in query_res])


def save_applied_migration(conn, migration):
    sql = read_sql_file("data/migrations/_insert_schema_history.sql")
    params = {
        "migration_id": migration.migration_id,
        "filename": migration.file,
        "name": migration.name,
        "applied_at_timestamp": time_ns() // 1_000_000,
    }
    conn.execute(sql, params)


def apply_migrations(migrations, connection):
    applied_migrations = get_applied_migrations(connection)
    for migration in migrations:

        if migration.migration_id in applied_migrations:
            continue

        connection.execute("BEGIN TRANSACTION;")
        sql = read_sql_file(f"data/migrations/{migration.file}")
        connection.executescript(sql)
        save_applied_migration(connection, migration)
        connection.execute("COMMIT;")


def init_db(db_path):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(read_sql_file("data/migrations/_schema_history.sql"))
        apply_migrations(load_migrations("data/migrations/index.toml"), conn)
        conn.commit()
    finally:
        conn.close()
