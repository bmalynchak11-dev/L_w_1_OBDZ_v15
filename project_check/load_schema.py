"""Завантажує project/schema.sql у схему project бази даних (стара схема з такою назвою видаляється).

Використання:  python project_check/load_schema.py [шлях_до_schema.sql]
Після цього таблиці видно в клієнті PostgreSQL (схема project), а заготовку словника можна отримати командою
    python project_check/dictionary_skeleton.py project > project/data_dictionary.md
"""
import sys
from pathlib import Path

import check_project


def main(path):
    sql = Path(path).read_text(encoding="utf-8")
    conn, cfg = check_project._connect()
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS project CASCADE")
    cur.execute("CREATE SCHEMA project")
    cur.execute("SET search_path = project")
    try:
        cur.execute(sql)
    except Exception as exc:  # noqa: BLE001
        print("Сервер відхилив схему:", str(exc).splitlines()[0])
        return 1
    tables = sorted(check_project.read_catalog(cur))
    print(f"Створено таблиць: {len(tables)} у схемі project бази {cfg['dbname']}: " + ", ".join(tables))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "project" / "schema.sql"))
