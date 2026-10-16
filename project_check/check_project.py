"""Перевірник наскрізного проєкту (частина Б): ER-модель, схема SQL, словник даних, історія в Git.

Запуск:  python project_check/check_project.py [тека_проєкту]   або   pytest project_check
Тека проєкту за замовчуванням: project/ (поруч із цим файлом на рівень вище). Змінна PROJECT_DIR задає іншу теку.
Для перевірки схеми потрібен PostgreSQL (змінні PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE).
Кожне зауваження має код (ER01, SQL02, DICT03, GIT01 тощо) і пояснення.
"""
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

try:
    import psycopg as _driver
except ImportError:
    import psycopg2 as _driver

ROOT = Path(__file__).resolve().parent
ER_TYPES = {"int", "string", "text", "decimal", "date", "bool", "timestamp", "composite"}
CARDS = {"one", "zero_one", "zero_many", "one_many"}
ONE, MANY = {"one", "zero_one"}, {"zero_many", "one_many"}
MIN_ENTITIES = 7
MIN_TABLES = 6
MIN_COMMITS = 3
PLACEHOLDERS = {"", "—", "-", "...", "ЗАПОВНІТЬ", "TBD"}

# ---------------------------------------------------------------- ER-модель


def check_er(project):
    out = []
    path = project / "er_model.json"
    if not path.exists():
        return ["ER00: немає файлу er_model.json"]
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"ER00: er_model.json не є коректним JSON: {exc}"]
    entities = model.get("entities")
    rels = model.get("relationships")
    if not isinstance(entities, dict) or not isinstance(rels, list):
        return ["ER00: у er_model.json мають бути ключі entities (словник) і relationships (список)"]
    hierarchies = model.get("hierarchies", [])
    subtypes = {s for h in hierarchies for s in h.get("subs", [])}
    if len(entities) < MIN_ENTITIES:
        out.append(f"ER01: сутностей {len(entities)}, потрібно щонайменше {MIN_ENTITIES}")
    weak, kinds = set(), []
    for number, rel in enumerate(rels, 1):
        a, b = rel.get("a"), rel.get("b")
        ac, bc = rel.get("a_card"), rel.get("b_card")
        if a not in entities or b not in entities:
            out.append(f"ER03: зв'язок {number} посилається на невідому сутність ({a}, {b})")
            continue
        if ac not in CARDS or bc not in CARDS:
            out.append(f"ER04: зв'язок {number} ({a}-{b}) має неправильну кардинальність ({ac}, {bc})")
            continue
        if ac in MANY and bc in MANY:
            kinds.append("MN")
        elif ac in ONE and bc in ONE:
            kinds.append("11")
        else:
            kinds.append("1N")
        if rel.get("identifying"):
            if ac in ONE and bc in MANY:
                weak.add(b)
            elif ac in MANY and bc in ONE:
                weak.add(a)
    multi = False
    for name, attrs in entities.items():
        if not isinstance(attrs, list) or not attrs:
            out.append(f"ER02: сутність {name} не має атрибутів")
            continue
        for at in attrs:
            if not isinstance(at, dict) or "name" not in at or "type" not in at:
                out.append(f"ER02: сутність {name} має атрибут без полів name і type")
                continue
            base = at["type"][:-2] if at["type"].endswith("[]") else at["type"]
            if base not in ER_TYPES:
                out.append(f"ER02: сутність {name}, атрибут {at['name']}: невідомий тип {at['type']}")
            if at["type"].endswith("[]") or at["type"] == "composite":
                multi = True
        has_pk = any("PK" in at.get("keys", []) for at in attrs if isinstance(at, dict))
        if not has_pk and name not in subtypes and name not in weak:
            out.append(f"ER05: сутність {name} не має первинного ключа (PK)")
    if "MN" not in kinds:
        out.append("ER06: у моделі немає жодного зв'язку M:N")
    if "1N" not in kinds:
        out.append("ER07: у моделі немає жодного зв'язку 1:N")
    if not weak and not hierarchies:
        out.append("ER08: потрібна слабка сутність (ідентифікуючий зв'язок) або ієрархія підтипів")
    if not multi:
        out.append("ER09: потрібен хоча б один багатозначний (тип з []) або складений (composite) атрибут")
    return out


# ---------------------------------------------------------------- схема SQL


def _connect():
    cfg = dict(host=os.environ.get("PGHOST", "localhost"), port=int(os.environ.get("PGPORT", "5432")),
               user=os.environ.get("PGUSER", "postgres"), password=os.environ.get("PGPASSWORD", "postgres"),
               dbname=os.environ.get("PGDATABASE", "postgres"))
    conn = _driver.connect(connect_timeout=5, **cfg)
    conn.autocommit = True
    return conn, cfg


_COLUMNS = """
SELECT c.relname::text, a.attname::text, format_type(a.atttypid, a.atttypmod), a.attnotnull
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace JOIN pg_attribute a ON a.attrelid = c.oid
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
WHERE n.nspname = current_schema() AND con.contype IN ('p', 'u', 'f')
"""


def read_catalog(cur):
    """{таблиця: {"columns": [(ім'я, тип, обов'язковий)], "pk": [...], "unique": [...], "fks": [...]}}."""
    tables = {}
    cur.execute(_COLUMNS)
    for table, col, typ, notnull in cur.fetchall():
        tables.setdefault(table, {"columns": [], "pk": [], "unique": [], "fks": []})["columns"].append((col, typ, notnull))
    cur.execute(_CONSTRAINTS)
    for table, kind, cols, ftable, fcols, action in cur.fetchall():
        t = tables[table]
        if kind == "p":
            t["pk"] = list(cols)
        elif kind == "u":
            t["unique"].append(list(cols))
        else:
            t["fks"].append({"columns": list(cols), "ref_table": ftable, "ref_columns": list(fcols), "action": action})
    return tables


def load_schema(project):
    """Виконує schema.sql у тимчасовій схемі й повертає (каталог, зауваження). Схема видаляється."""
    path = project / "schema.sql"
    if not path.exists():
        return None, ["SQL00: немає файлу schema.sql"]
    sql = path.read_text(encoding="utf-8")
    if not sql.strip() or not re.search(r"create\s+table", sql, re.I):
        return None, ["SQL00: schema.sql не містить жодного CREATE TABLE"]
    try:
        conn, cfg = _connect()
    except Exception as exc:  # noqa: BLE001
        return None, [f"SQL00: немає з'єднання з PostgreSQL ({exc}); запустіть сервер і задайте PGHOST, PGPORT тощо"]
    name = "proj_" + uuid.uuid4().hex[:10]
    cur = conn.cursor()
    try:
        cur.execute(f'CREATE SCHEMA "{name}"')
        cur.execute(f'SET search_path = "{name}"')
        try:
            cur.execute(sql)
        except Exception as exc:  # noqa: BLE001
            return None, [f"SQL01: сервер відхилив schema.sql: {str(exc).splitlines()[0]}"]
        return read_catalog(cur), []
    finally:
        try:
            cur.execute("SET search_path = public")
            cur.execute(f'DROP SCHEMA IF EXISTS "{name}" CASCADE')
        finally:
            conn.close()


def check_schema(project, catalog=None):
    if catalog is None:
        catalog, problems = load_schema(project)
        if catalog is None:
            return problems
    out = []
    er_count = 0
    try:
        model = json.loads((project / "er_model.json").read_text(encoding="utf-8"))
        subs = {s for h in model.get("hierarchies", []) for s in h.get("subs", [])}
        er_count = len([e for e in model["entities"] if e not in subs])
    except (OSError, ValueError, KeyError, AttributeError, TypeError):
        pass
    need = max(MIN_TABLES, er_count)
    if len(catalog) < need:
        out.append(f"SQL02: таблиць {len(catalog)}, потрібно щонайменше {need} (кожна сутність, що не є підтипом, має таблицю)")
    for name, t in catalog.items():
        if not t["pk"]:
            out.append(f"SQL03: таблиця {name} не має первинного ключа")
    if not any(len(t["pk"]) > 1 for t in catalog.values()):
        out.append("SQL04: немає жодної таблиці зі складеним первинним ключем (таблиця зв'язку M:N або слабка сутність)")
    if not any(fk["action"] == "c" for t in catalog.values() for fk in t["fks"]):
        out.append("SQL05: немає жодного зовнішнього ключа з ON DELETE CASCADE")
    if not any(t["unique"] for t in catalog.values()):
        out.append("SQL06: немає жодного обмеження UNIQUE")
    linked = set()
    for name, t in catalog.items():
        for fk in t["fks"]:
            linked |= {name, fk["ref_table"]}
            types = {c[0]: c[1] for c in t["columns"]}
            rtypes = {c[0]: c[1] for c in catalog[fk["ref_table"]]["columns"]}
            for c, rc in zip(fk["columns"], fk["ref_columns"]):
                if types[c] != rtypes[rc]:
                    out.append(f"SQL07: {name}.{c} має тип {types[c]}, а {fk['ref_table']}.{rc} має тип {rtypes[rc]}")
    isolated = sorted(set(catalog) - linked)
    if len(catalog) > 1 and isolated:
        out.append("SQL08: таблиці без жодного зв'язку (зовнішнього ключа): " + ", ".join(isolated))
    return out


# ---------------------------------------------------------------- словник даних


def parse_dictionary(text):
    tables, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+Таблиця\s+(\S+)\s*$", line)
        if m:
            cur = tables.setdefault(m.group(1), {"desc": None, "nf": None, "columns": {}})
            continue
        if cur is None:
            continue
        m = re.match(r"^Опис:\s*(.*)$", line)
        if m:
            cur["desc"] = m.group(1).strip()
        m = re.match(r"^Нормальна форма:\s*(.*)$", line)
        if m:
            cur["nf"] = m.group(1).strip()
        if line.startswith("|"):
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if len(cells) < 2 or cells[0] == "Стовпець" or set(cells[0]) <= set("-: "):
                continue
            cur["columns"][cells[0]] = (cells[1], cells[-1])
    return tables


def check_dictionary(project, catalog):
    path = project / "data_dictionary.md"
    if not path.exists():
        return ["DICT00: немає файлу data_dictionary.md"]
    doc = parse_dictionary(path.read_text(encoding="utf-8"))
    out = []
    if catalog is None:
        return ["DICT00: словник неможливо звірити зі схемою, бо schema.sql не виконується"]
    for name in sorted(set(catalog) - set(doc)):
        out.append(f"DICT01: таблиці {name} немає у словнику (розділ «## Таблиця {name}»)")
    for name in sorted(set(doc) - set(catalog)):
        out.append(f"DICT02: у словнику є таблиця {name}, якої немає у схемі")
    for name in sorted(set(doc) & set(catalog)):
        entry = doc[name]
        db_cols = [c[0] for c in catalog[name]["columns"]]
        for c in sorted(set(db_cols) - set(entry["columns"])):
            out.append(f"DICT03: у словнику таблиці {name} немає стовпця {c}")
        for c in sorted(set(entry["columns"]) - set(db_cols)):
            out.append(f"DICT04: у словнику таблиці {name} є стовпець {c}, якого немає у схемі")
        if entry["desc"] is None or entry["desc"] in PLACEHOLDERS:
            out.append(f"DICT05: таблиця {name} не має опису (рядок «Опис: ...»)")
        for c, (_, desc) in sorted(entry["columns"].items()):
            if desc in PLACEHOLDERS:
                out.append(f"DICT06: стовпець {name}.{c} не має опису")
        nf = entry["nf"] or ""
        if not re.match(r"^(3NF|BCNF|денормалізовано\s*\(.{5,}\))\s*$", nf):
            out.append(f"DICT07: таблиця {name}: рядок «Нормальна форма: 3NF|BCNF|денормалізовано (причина)» "
                       f"відсутній або неправильний ({nf!r})")
    return out


# ---------------------------------------------------------------- Git


def _git(project, *args):
    return subprocess.run(["git", "-C", str(project), *args], capture_output=True, text=True)


def check_git(project):
    try:
        top = _git(project, "rev-parse", "--show-toplevel")
    except FileNotFoundError:
        return ["GIT00: команда git не знайдена"]
    if top.returncode != 0:
        return ["GIT01: теку проєкту не під керуванням Git (виконайте git init, git add, git commit)"]
    out = []
    count = _git(project, "rev-list", "--count", "HEAD")
    n = int(count.stdout.strip() or 0) if count.returncode == 0 else 0
    if n < MIN_COMMITS:
        out.append(f"GIT02: комітів {n}, потрібно щонайменше {MIN_COMMITS} (фіксуйте модель, схему і словник окремими комітами)")
    tracked = _git(project, "ls-files", "--", "er_model.json", "schema.sql", "data_dictionary.md").stdout.split()
    for f in ("er_model.json", "schema.sql", "data_dictionary.md"):
        if f not in tracked:
            out.append(f"GIT03: файл {f} не додано в Git")
    dirty = _git(project, "status", "--porcelain", "--", ".").stdout.strip()
    if dirty:
        out.append("GIT04: є незафіксовані зміни у теці проєкту (git status)")
    return out


def check_all(project, git=True):
    project = Path(project)
    out = check_er(project)
    catalog, problems = load_schema(project)
    out += problems + (check_schema(project, catalog) if catalog is not None else [])
    out += check_dictionary(project, catalog)
    if git:
        out += check_git(project)
    return out


def main(argv):
    project = Path(argv[1]) if len(argv) > 1 else Path(os.environ.get("PROJECT_DIR", ROOT.parent / "project"))
    problems = check_all(project)
    for p in problems:
        print(p)
    print(f"Зауважень: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
