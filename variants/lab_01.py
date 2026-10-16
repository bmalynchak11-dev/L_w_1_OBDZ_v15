"""Задача 1. Сильні сутності та їхні атрибути -> таблиці.

Прочитайте опис задачі 1 в інструкції (розділ 7) і картку свого варіанта (розділ 8).
Не змінюйте вхідні дані: працюйте з копіями (copy.deepcopy). Використовуйте лише стандартну бібліотеку Python.
"""
import copy  # noqa: F401

# Відповідність типів ER -> PostgreSQL (розділ 6 інструкції)
SQL_TYPES = {"int": "integer", "string": "text", "text": "text", "decimal": "numeric(12,2)",
             "date": "date", "bool": "boolean", "timestamp": "timestamptz"}


def entities_to_tables(model: dict) -> dict:
    """Повертає схему {"tables": {...}} з таблицею для кожної сутності (правила — задача 1 в інструкції)."""
    raise NotImplementedError("Реалізуйте функцію entities_to_tables за описом задачі 1")
