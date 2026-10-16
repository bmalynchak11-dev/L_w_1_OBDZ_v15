"""Заготовка словника даних: читає таблиці з PostgreSQL і друкує Markdown з порожніми описами.

Використання (схему спершу завантажте командою python project_check/load_schema.py):
    python project_check/dictionary_skeleton.py project  > project/data_dictionary.md
Далі замініть «ЗАПОВНІТЬ» на змістовні описи й виберіть нормальну форму кожної таблиці.
"""
import sys

import check_project


def main(schema="public"):
    conn, _ = check_project._connect()
    cur = conn.cursor()
    cur.execute(f'SET search_path = "{schema}"')
    catalog = check_project.read_catalog(cur)
    print("# Словник даних\n")
    for name in sorted(catalog):
        t = catalog[name]
        print(f"## Таблиця {name}\n")
        print("Опис: ЗАПОВНІТЬ\n")
        print("Нормальна форма: ЗАПОВНІТЬ\n")
        print("| Стовпець | Тип | Обов'язковий | Ключі | Опис |")
        print("|---|---|---|---|---|")
        for col, typ, notnull in t["columns"]:
            keys = []
            if col in t["pk"]:
                keys.append("PK")
            for fk in t["fks"]:
                if col in fk["columns"]:
                    keys.append(f"FK → {fk['ref_table']}.{fk['ref_columns'][fk['columns'].index(col)]}")
            for u in t["unique"]:
                if col in u:
                    keys.append("UK" if len(u) == 1 else "UK(" + ",".join(u) + ")")
            print(f"| {col} | {typ} | {'так' if notnull else 'ні'} | {', '.join(keys)} | ЗАПОВНІТЬ |")
        print()


if __name__ == "__main__":
    main(*sys.argv[1:2])
