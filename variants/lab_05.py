"""Задача 5. Зв'язки M:N -> таблиці зв'язку.

Прочитайте опис задачі 5 в інструкції (розділ 7) і картку свого варіанта (розділ 8).
Не змінюйте вхідні дані: працюйте з копіями (copy.deepcopy). Використовуйте лише стандартну бібліотеку Python.
"""
import copy  # noqa: F401

# Відповідність типів ER -> PostgreSQL (розділ 6 інструкції)
SQL_TYPES = {"int": "integer", "string": "text", "text": "text", "decimal": "numeric(12,2)",
             "date": "date", "bool": "boolean", "timestamp": "timestamptz"}


def many_to_many(schema: dict, model: dict) -> dict:
    """Повертає нову схему з таблицями зв'язку для зв'язків M:N (задача 5)."""
    raise NotImplementedError("Реалізуйте функцію many_to_many за описом задачі 5")
