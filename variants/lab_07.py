"""Задача 7. Ієрархії та підтипи -> три стратегії.

Прочитайте опис задачі 7 в інструкції (розділ 7) і картку свого варіанта (розділ 8).
Не змінюйте вхідні дані: працюйте з копіями (copy.deepcopy). Використовуйте лише стандартну бібліотеку Python.
"""
import copy  # noqa: F401

# Відповідність типів ER -> PostgreSQL (розділ 6 інструкції)
SQL_TYPES = {"int": "integer", "string": "text", "text": "text", "decimal": "numeric(12,2)",
             "date": "date", "bool": "boolean", "timestamp": "timestamptz"}


def map_hierarchy(schema: dict, model: dict, strategy: str) -> dict:
    """Повертає нову схему з відображеною ієрархією за стратегією single_table, per_type або concrete (задача 7)."""
    raise NotImplementedError("Реалізуйте функцію map_hierarchy за описом задачі 7")
