"""Робота з PostgreSQL у тестах: з'єднання, тимчасова схема, читання каталогу, перевірка запитів.

Параметри з'єднання беруться зі змінних середовища PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
(у Codespaces вони вже задані). Типові значення: localhost, 5432, postgres, postgres, postgres.
"""
import os
import uuid
from contextlib import contextmanager

import pytest

try:
    import psycopg as _driver
except ImportError:  # запасний варіант: старший драйвер psycopg2
    import psycopg2 as _driver

_TYPE_ALIASES = {
    "timestamp with time zone": "timestamptz",
    "timestamp without time zone": "timestamp",
    "character varying": "varchar",
    "boolean": "boolean",
}


def _settings():
    return {
        "host": os.environ.get("PGHOST", "localhost"),
        "port": int(os.environ.get("PGPORT", "5432")),
        "user": os.environ.get("PGUSER", "postgres"),
        "password": os.environ.get("PGPASSWORD", "postgres"),
        "dbname": os.environ.get("PGDATABASE", "postgres"),
    }


def connect():
    cfg = _settings()
    try:
        conn = _driver.connect(connect_timeout=5, **cfg)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            f"Немає з'єднання з PostgreSQL ({cfg['host']}:{cfg['port']}): {exc}\n"
            "Запустіть сервер: у Codespaces він стартує разом із середовищем; локально виконайте\n"
            "  docker run --name lab-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:18\n"
            "і за потреби задайте PGHOST, PGPORT, PGUSER, PGPASSWORD.",
            pytrace=False)
    conn.autocommit = True
    return conn


@contextmanager
def scratch_schema():
    """Створює порожню схему, ставить її в search_path і видаляє після використання."""
    conn = connect()
    name = "lab01_" + uuid.uuid4().hex[:10]
    cur = conn.cursor()
    try:
        cur.execute(f'CREATE SCHEMA "{name}"')
        cur.execute(f'SET search_path = "{name}"')
        yield cur
    finally:
        try:
            cur.execute("SET search_path = public")
            cur.execute(f'DROP SCHEMA IF EXISTS "{name}" CASCADE')
        finally:
            conn.close()


def version(cur):
    cur.execute("SHOW server_version_num")
    return int(cur.fetchone()[0])


_COLUMNS = """
SELECT c.relname::text, a.attname::text, format_type(a.atttypid, a.atttypmod), a.attnotnull, a.attidentity::text
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_attribute a ON a.attrelid = c.oid
WHERE n.nspname = current_schema() AND c.relkind = 'r' AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY c.relname, a.attnum
"""

_CONSTRAINTS = """
SELECT rel.relname::text, con.contype::text,
  (SELECT array_agg(att.attname::text ORDER BY k.ord) FROM unnest(con.conkey) WITH ORDINALITY AS k(num, ord)
     JOIN pg_attribute att ON att.attrelid = con.conrelid AND att.attnum = k.num),
  frel.relname::text,
  (SELECT array_agg(att.attname::text ORDER BY k.ord) FROM unnest(con.confkey) WITH ORDINALITY AS k(num, ord)
     JOIN pg_attribute att ON att.attrelid = con.confrelid AND att.attnum = k.num),
  con.confdeltype::text
FROM pg_constraint con JOIN pg_class rel ON rel.oid = con.conrelid
JOIN pg_namespace n ON n.oid = rel.relnamespace LEFT JOIN pg_class frel ON frel.oid = con.confrelid
WHERE n.nspname = current_schema() AND con.contype IN ('p', 'u', 'f', 'c')
"""

_ACTIONS = {"a": "NO ACTION", "r": "RESTRICT", "c": "CASCADE", "n": "SET NULL", "d": "SET DEFAULT"}


def _type(name):
    base, _, rest = name.partition("(")
    base = _TYPE_ALIASES.get(base.strip(), base.strip())
    return base + ("(" + rest if rest else "")


def introspect(cur):
    """Читає з каталогу PostgreSQL поточної схеми структуру у вигляді, придатному для порівняння.

    Повертає {таблиця: {"columns": [(ім'я, тип, nullable, identity)], "pk": [...], "unique": [...],
    "fks": [...], "checks": кількість}}.
    """
    out = {}
    cur.execute(_COLUMNS)
    for table, col, typ, notnull, ident in cur.fetchall():
        t = out.setdefault(table, {"columns": [], "pk": [], "unique": [], "fks": [], "checks": 0})
        t["columns"].append((col, _type(typ), not notnull and ident == "", ident != ""))
    cur.execute(_CONSTRAINTS)
    for table, kind, cols, ftable, fcols, action in cur.fetchall():
        t = out[table]
        if kind == "p":
            t["pk"] = list(cols)
        elif kind == "u":
            t["unique"].append(tuple(sorted(cols)))
        elif kind == "f":
            t["fks"].append((tuple(sorted(zip(cols, fcols))), ftable, _ACTIONS[action]))
        else:
            t["checks"] += 1
    for t in out.values():
        t["columns"].sort()
        t["unique"].sort()
        t["fks"].sort()
    return out


def run_probes(cur, probes):
    """Виконує перевірні запити. Очікування: "ok", "error" або список рядків результату SELECT."""
    problems = []
    for number, (sql, expect) in enumerate(probes, 1):
        try:
            cur.execute(sql)
            rows = cur.fetchall() if cur.description else None
            failed = False
        except _driver.Error as exc:
            rows, failed, err = None, True, str(exc).splitlines()[0]
        if expect == "ok":
            if failed:
                problems.append(f"запит {number} мав виконатися, але сервер відхилив: {sql} -> {err}")
        elif expect == "error":
            if not failed:
                problems.append(f"запит {number} мав бути відхилений сервером (порушення обмеження), але виконався: {sql}")
        else:
            if failed:
                problems.append(f"запит {number} не виконався: {sql} -> {err}")
            elif [list(r) for r in rows] != expect:
                problems.append(f"запит {number}: {sql} -> отримано {[list(r) for r in rows]!r}, очікувалось {expect!r}")
    return problems
