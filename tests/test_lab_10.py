"""Відкриті тести задачі 10: Словник даних.

Запуск: pytest tests/test_lab_10.py            (усі відкриті випадки)
        pytest tests/test_lab_10.py -k S2     (лише ваш набір, наприклад другий)
Тут лише приклади з карток варіантів; повний набір перевірок є у викладача.
"""
import pytest
from labtools import run


def _ids(cases, prefix):
    return [f"{prefix}-{c[0]}-{i}" for i, c in enumerate(cases)]


# ---- Задача 10. Словник даних

T10 = [('S1',
  'build_dictionary',
  ({'tables': {'patient': {'columns': [{'name': 'id', 'type': 'integer', 'nullable': False},
                                       {'name': 'full_name', 'type': 'text', 'nullable': False},
                                       {'name': 'phone', 'type': 'text', 'nullable': True}],
                           'pk': ['id'],
                           'unique': [['phone']],
                           'fks': [],
                           'checks': []}}},
   {'patient': 'Пацієнти клініки',
    'patient.id': 'Ідентифікатор',
    'patient.full_name': 'ПІБ',
    'patient.phone': 'Телефон'}),
  '# Словник даних\n'
  '\n'
  '## Таблиця patient\n'
  '\n'
  'Опис: Пацієнти клініки\n'
  '\n'
  "| Стовпець | Тип | Обов'язковий | Ключі | Опис |\n"
  '|---|---|---|---|---|\n'
  '| id | integer | так | PK | Ідентифікатор |\n'
  '| full_name | text | так |  | ПІБ |\n'
  '| phone | text | ні | UK | Телефон |\n'),
 ('S1',
  'build_dictionary',
  ({'tables': {'zeta': {'columns': [{'name': 'a', 'type': 'integer', 'nullable': False}],
                        'pk': ['a'],
                        'unique': [],
                        'fks': [],
                        'checks': []},
               'alpha': {'columns': [{'name': 'b', 'type': 'text', 'nullable': True}],
                         'pk': [],
                         'unique': [],
                         'fks': [],
                         'checks': []}}},
   {}),
  '# Словник даних\n'
  '\n'
  '## Таблиця alpha\n'
  '\n'
  'Опис: —\n'
  '\n'
  "| Стовпець | Тип | Обов'язковий | Ключі | Опис |\n"
  '|---|---|---|---|---|\n'
  '| b | text | ні |  | — |\n'
  '\n'
  '## Таблиця zeta\n'
  '\n'
  'Опис: —\n'
  '\n'
  "| Стовпець | Тип | Обов'язковий | Ключі | Опис |\n"
  '|---|---|---|---|---|\n'
  '| a | integer | так | PK | — |\n'),
 ('S2',
  'build_dictionary',
  ({'tables': {'order_line': {'columns': [{'name': 'orders_id', 'type': 'integer', 'nullable': False},
                                          {'name': 'line_no', 'type': 'integer', 'nullable': False},
                                          {'name': 'sku', 'type': 'text', 'nullable': False},
                                          {'name': 'qty', 'type': 'integer', 'nullable': False}],
                              'pk': ['orders_id', 'line_no'],
                              'unique': [['orders_id', 'sku']],
                              'fks': [{'columns': ['orders_id'],
                                       'ref_table': 'orders',
                                       'ref_columns': ['id'],
                                       'on_delete': 'CASCADE'},
                                      {'columns': ['sku'],
                                       'ref_table': 'product',
                                       'ref_columns': ['sku'],
                                       'on_delete': 'RESTRICT'}],
                              'checks': []}}},
   {'order_line.qty': 'Кількість'}),
  '# Словник даних\n'
  '\n'
  '## Таблиця order_line\n'
  '\n'
  'Опис: —\n'
  '\n'
  "| Стовпець | Тип | Обов'язковий | Ключі | Опис |\n"
  '|---|---|---|---|---|\n'
  '| orders_id | integer | так | PK, FK → orders.id, UK(orders_id,sku) | — |\n'
  '| line_no | integer | так | PK | — |\n'
  '| sku | text | так | FK → product.sku, UK(orders_id,sku) | — |\n'
  '| qty | integer | так |  | Кількість |\n'),
 ('S2',
  'build_dictionary',
  ({'tables': {'att': {'columns': [{'name': 'lesson_id', 'type': 'integer', 'nullable': False},
                                   {'name': 'student_id', 'type': 'integer', 'nullable': False},
                                   {'name': 'present', 'type': 'boolean', 'nullable': False}],
                       'pk': ['lesson_id', 'student_id'],
                       'unique': [],
                       'fks': [{'columns': ['lesson_id', 'student_id'],
                                'ref_table': 'enrollment',
                                'ref_columns': ['lesson_id', 'student_id'],
                                'on_delete': 'CASCADE'}],
                       'checks': []}}},
   {}),
  '# Словник даних\n'
  '\n'
  '## Таблиця att\n'
  '\n'
  'Опис: —\n'
  '\n'
  "| Стовпець | Тип | Обов'язковий | Ключі | Опис |\n"
  '|---|---|---|---|---|\n'
  '| lesson_id | integer | так | PK, FK → enrollment.lesson_id | — |\n'
  '| student_id | integer | так | PK, FK → enrollment.student_id | — |\n'
  '| present | boolean | так |  | — |\n'),
 ('S3',
  'build_dictionary',
  ({'tables': {'room': {'columns': [{'name': 'id', 'type': 'integer', 'nullable': False, 'identity': True},
                                    {'name': 'seats', 'type': 'integer', 'nullable': False}],
                        'pk': ['id'],
                        'unique': [],
                        'fks': [],
                        'checks': ['seats > 0', 'seats < 500']}}},
   {'room.seats': 'Місць | максимум 499', 'room': 'Аудиторії | корпуси'}),
  '# Словник даних\n'
  '\n'
  '## Таблиця room\n'
  '\n'
  'Опис: Аудиторії \\| корпуси\n'
  '\n'
  "| Стовпець | Тип | Обов'язковий | Ключі | Опис |\n"
  '|---|---|---|---|---|\n'
  '| id | integer | так | PK | — |\n'
  '| seats | integer | так |  | Місць \\| максимум 499 |\n'
  '\n'
  'Обмеження CHECK:\n'
  '- `seats > 0`\n'
  '- `seats < 500`\n'),
 ('S3',
  'build_dictionary',
  ({'tables': {'room': {'columns': [{'name': 'id', 'type': 'integer', 'nullable': False}],
                        'pk': ['id'],
                        'unique': [],
                        'fks': [],
                        'checks': []}}},
   {'room.floor': 'Поверх'}),
  ValueError('Опис для невідомого елемента: room.floor'))]


@pytest.mark.parametrize("case", T10, ids=_ids(T10, "T10"))
def test_task_10(case):
    run(10, *case[1:])
