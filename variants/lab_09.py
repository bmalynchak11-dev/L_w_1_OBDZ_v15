"""Задача 9. Ключі й нормальні форми таблиці.

Прочитайте опис задачі 9 в інструкції (розділ 7) і картку свого варіанта (розділ 8).
Не змінюйте вхідні дані: працюйте з копіями (copy.deepcopy). Використовуйте лише стандартну бібліотеку Python.
"""
import copy  # noqa: F401


def audit_table(table: dict, fds: list) -> dict:
    """Повертає словник {keys, pk_status, missing_unique, nf, violations} (задача 9)."""
    raise NotImplementedError("Реалізуйте функцію audit_table за описом задачі 9")
