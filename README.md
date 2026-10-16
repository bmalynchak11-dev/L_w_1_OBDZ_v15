# Стартовий проєкт OBDZ-LAB01

1. Відкрийте проєкт у GitHub Codespaces (Code → Codespaces → Create codespace): разом із середовищем стартує сервер PostgreSQL 18. Локально: `python3 -m venv .venv`, `source .venv/bin/activate`, `pip install -r requirements.txt` і окремо запустіть PostgreSQL 18, наприклад `docker run --name lab-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:18`.
2. Визначте свою задачу й набір за номером варіанта: задача = `(номер - 1) // 3 + 1`, набір = `(номер - 1) % 3 + 1`. Реалізуйте функції у файлі `variants/lab_NN.py` за карткою варіанта.
3. Запускайте відкриті тести своєї задачі й свого набору: `pytest tests/test_lab_NN.py -k S2` (замініть `S2` на `S1`, `S2` або `S3`). Задача 8 звертається до PostgreSQL: перевірте змінні PGHOST, PGPORT, PGUSER, PGPASSWORD (у Codespaces вони вже задані; типові значення localhost, 5432, postgres, postgres).
4. Змінюйте лише свій файл у `variants/` і теку `project/` (за бажанням додавайте `tests/test_my.py`).
5. Частина Б: заповніть `project/er_model.json`, `project/schema.sql`, `project/data_dictionary.md` для бази даних власного дипломного проєкту (запасний шлях: ідея власного проєкту або навчальний кейс) й перевірте командою `pytest project_check`.
