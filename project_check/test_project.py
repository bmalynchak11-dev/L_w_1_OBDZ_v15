"""Тести частини Б: перевірка наскрізного проєкту. Запуск: pytest project_check (з кореня стартового проєкту)."""
import os
from pathlib import Path

import pytest

import check_project

PROJECT = Path(os.environ.get("PROJECT_DIR", Path(__file__).resolve().parent.parent / "project"))


@pytest.fixture(scope="module")
def loaded():
    return check_project.load_schema(PROJECT)


def _assert_clean(problems):
    assert not problems, "\n" + "\n".join(problems)


def test_er_model():
    _assert_clean(check_project.check_er(PROJECT))


def test_schema_sql(loaded):
    catalog, problems = loaded
    _assert_clean(problems + (check_project.check_schema(PROJECT, catalog) if catalog is not None else []))


def test_data_dictionary(loaded):
    _assert_clean(check_project.check_dictionary(PROJECT, loaded[0]))


def test_git_history():
    _assert_clean(check_project.check_git(PROJECT))
