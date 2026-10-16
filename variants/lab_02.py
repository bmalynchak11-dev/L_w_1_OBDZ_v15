"""Задача 2. Багатозначні атрибути -> окремі таблиці.

Прочитайте опис задачі 2 в інструкції (розділ 7) і картку свого варіанта (розділ 8).
Не змінюйте вхідні дані: працюйте з копіями (copy.deepcopy). Використовуйте лише стандартну бібліотеку Python.
"""
import copy  # noqa: F401

# Відповідність типів ER -> PostgreSQL (розділ 6 інструкції)
SQL_TYPES = {"int": "integer", "string": "text", "text": "text", "decimal": "numeric(12,2)",
             "date": "date", "bool": "boolean", "timestamp": "timestamptz"}


def multivalued_tables(model: dict) -> dict:
    """Повертає схему лише з новими таблицями для багатозначних атрибутів (задача 2)."""
    raise NotImplementedError("Реалізуйте функцію multivalued_tables за описом задачі 2")
