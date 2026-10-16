"""
Лабораторна робота OBDZ-LAB01.
Задача 5: Зв'язки M:N і таблиці зв'язку.
Варіант 15 (Набір умов S3).
"""
import copy


TYPE_MAP = {
    "int": "integer",
    "string": "text",
    "text": "text",
    "decimal": "numeric(12,2)",
    "date": "date",
    "bool": "boolean",
    "timestamp": "timestamptz",
}


def many_to_many(schema: dict, model: dict) -> dict:
    """
    Трансформує неідентифікуючі зв'язки M:N у сполучні таблиці (junction tables).
    """
    res_schema = copy.deepcopy(schema)
    tables = res_schema.setdefault("tables", {})
    relationships = model.get("relationships", [])

    for rel in relationships:
        a_card = rel.get("a_card")
        b_card = rel.get("b_card")

        # Перевіряємо, чи є зв'язок M:N (обидві сторони багато)
        is_m_n = (a_card in ("zero_many", "one_many")) and (b_card in ("zero_many", "one_many"))
        if not is_m_n:
            continue

        a_name = rel.get("a")
        b_name = rel.get("b")

        # 1. Помилка: Рекурсивний зв'язок M:N
        if a_name == b_name:
            raise ValueError(f"Рекурсивний зв'язок M:N не підтримується: {a_name}")

        a_tbl_name = a_name.lower()
        b_tbl_name = b_name.lower()

        # 2. Помилки перевірки сутності A
        if a_tbl_name not in tables:
            raise ValueError(f"Немає таблиці: {a_tbl_name}")
        if not tables[a_tbl_name].get("pk"):
            raise ValueError(f"У таблиці {a_tbl_name} немає первинного ключа")

        # 3. Помилки перевірки сутності B
        if b_tbl_name not in tables:
            raise ValueError(f"Немає таблиці: {b_tbl_name}")
        if not tables[b_tbl_name].get("pk"):
            raise ValueError(f"У таблиці {b_tbl_name} немає первинного ключа")

        # 4. Ім'я нової сполучної таблиці: <a>_<b>
        junction_table_name = f"{a_tbl_name}_{b_tbl_name}"
        if junction_table_name in tables:
            raise ValueError(f"Таблиця {junction_table_name} вже існує")

        table_a = tables[a_tbl_name]
        table_b = tables[b_tbl_name]

        # Допоміжний словник для пошуку типів за назвою стовпця
        col_types_a = {col["name"]: col["type"] for col in table_a.get("columns", [])}
        col_types_b = {col["name"]: col["type"] for col in table_b.get("columns", [])}

        junction_cols = []
        col_names_seen = set()
        pk_cols = []

        # Стовпці від таблиці A
        fk_a_cols = []
        for pk_col in table_a["pk"]:
            col_name = f"{a_tbl_name}_{pk_col}"
            junction_cols.append({
                "name": col_name,
                "type": col_types_a[pk_col],
                "nullable": False
            })
            col_names_seen.add(col_name)
            pk_cols.append(col_name)
            fk_a_cols.append(col_name)

        # Стовпці від таблиці B
        fk_b_cols = []
        for pk_col in table_b["pk"]:
            col_name = f"{b_tbl_name}_{pk_col}"
            junction_cols.append({
                "name": col_name,
                "type": col_types_b[pk_col],
                "nullable": False
            })
            col_names_seen.add(col_name)
            pk_cols.append(col_name)
            fk_b_cols.append(col_name)

        # Власні атрибути зв'язку (rel.attrs)
        for attr in rel.get("attrs", []):
            attr_name = attr.get("name")
            if attr_name in col_names_seen:
                raise ValueError(f"Дубльований стовпець: {junction_table_name}.{attr_name}")
            col_names_seen.add(attr_name)

            attr_type_raw = attr.get("type")
            if attr_type_raw not in TYPE_MAP:
                raise ValueError(f"Невідомий тип: {attr_type_raw}")

            is_opt = "OPT" in attr.get("keys", [])
            junction_cols.append({
                "name": attr_name,
                "type": TYPE_MAP[attr_type_raw],
                "nullable": is_opt
            })

        fks = [
            {
                "columns": fk_a_cols,
                "ref_table": a_tbl_name,
                "ref_columns": list(table_a["pk"]),
                "on_delete": "CASCADE"
            },
            {
                "columns": fk_b_cols,
                "ref_table": b_tbl_name,
                "ref_columns": list(table_b["pk"]),
                "on_delete": "CASCADE"
            }
        ]

        tables[junction_table_name] = {
            "columns": junction_cols,
            "pk": pk_cols,
            "unique": [],
            "fks": fks,
            "checks": []
        }

    return res_schema