"""Спільні засоби відкритих і повних тестів: порівняння схем, виклик функції, перевірка DDL на сервері."""
import copy

import pytest
from conftest import load


def same(a, b):
    """Рівність; список і кортеж вважаються однаковими послідовностями."""
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) < 1e-9
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


def canon(schema, checks_as_count=False):
    """Канонічний вигляд схеми: порядок таблиць, стовпців і обмежень не важливий, порядок у ключах важливий."""
    out = {}
    for name, t in schema["tables"].items():
        checks = [" ".join(c.split()) for c in t.get("checks", [])]
        out[name] = {
            "columns": sorted((c["name"], c["type"], bool(c["nullable"]), bool(c.get("identity", False)))
                              for c in t["columns"]),
            "pk": list(t["pk"]),
            "unique": sorted(tuple(sorted(u)) for u in t.get("unique", [])),
            "fks": sorted((tuple(sorted(zip(f["columns"], f["ref_columns"]))), f["ref_table"],
                           f.get("on_delete") or "NO ACTION") for f in t.get("fks", [])),
            "checks": len(checks) if checks_as_count else sorted(checks),
        }
    return out


def diff(got, want):
    """Короткий опис розбіжностей між двома канонічними схемами."""
    lines = []
    for name in sorted(set(got) | set(want)):
        if name not in got:
            lines.append(f"немає таблиці {name}")
        elif name not in want:
            lines.append(f"зайва таблиця {name}")
        else:
            for part in ("columns", "pk", "unique", "fks", "checks"):
                if got[name][part] != want[name][part]:
                    lines.append(f"{name}.{part}: отримано {got[name][part]!r}, очікувалось {want[name][part]!r}")
    return "\n".join(lines)


def run(task, fn, args, expected):
    """Викликає функцію задачі на копії аргументів і порівнює результат; вхідні дані змінювати не можна."""
    func = getattr(load(task), fn)
    given = copy.deepcopy(args)
    if isinstance(expected, ValueError):
        with pytest.raises(ValueError) as info:
            func(*given)
        assert str(info.value) == str(expected)
    else:
        got = func(*given)
        if isinstance(expected, dict) and "tables" in expected:
            assert isinstance(got, dict) and isinstance(got.get("tables"), dict), \
                f"результат має бути словником з ключем 'tables', отримано {got!r}"
            try:
                got_c = canon(got)
            except (KeyError, TypeError, AttributeError) as exc:
                pytest.fail(f"неправильна структура таблиці у результаті: {exc!r}", pytrace=False)
            want_c = canon(expected)
            assert got_c == want_c, "розбіжності зі схемою:\n" + diff(got_c, want_c)
        else:
            assert same(got, expected), f"отримано {got!r}, очікувалось {expected!r}"
    assert given == args, "функція не повинна змінювати вхідні дані"


def run_ddl(fn, schema, probes):
    """Задача 8: виконує згенерований DDL у PostgreSQL, порівнює структуру з каталогу зі схемою й запускає запити."""
    import dbtools
    func = getattr(load(8), fn)
    given = copy.deepcopy(schema)
    ddl = func(given)
    assert given == schema, "функція не повинна змінювати вхідні дані"
    assert isinstance(ddl, str), f"функція має повернути рядок із DDL, отримано {type(ddl).__name__}"
    with dbtools.scratch_schema() as cur:
        try:
            cur.execute(ddl)
        except Exception as exc:  # noqa: BLE001
            pytest.fail(f"Сервер відхилив DDL: {str(exc).splitlines()[0]}\n--- DDL ---\n{ddl}", pytrace=False)
        got = dbtools.introspect(cur)
        want = {}
        for name, t in canon(schema, checks_as_count=True).items():
            want[name] = {"columns": t["columns"], "pk": t["pk"], "unique": t["unique"], "fks": t["fks"],
                          "checks": t["checks"]}
        got_c = {n: {"columns": sorted(v["columns"]), "pk": v["pk"], "unique": v["unique"],
                     "fks": v["fks"], "checks": v["checks"]} for n, v in got.items()}
        assert got_c == want, "структура в базі не збігається зі схемою:\n" + diff(got_c, want) + "\n--- DDL ---\n" + ddl
        problems = dbtools.run_probes(cur, probes)
        assert not problems, "\n".join(problems) + "\n--- DDL ---\n" + ddl
