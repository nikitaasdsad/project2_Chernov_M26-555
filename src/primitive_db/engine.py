import os
import re
import shlex

from prettytable import PrettyTable

from .constants import META_FILE
from .core import create_table, delete, drop_table, insert, select, update
from .decorators import create_cacher
from .parser import parse_value
from .utils import load_metadata, load_table_data, save_metadata, save_table_data

cacher = create_cacher()



def print_help():
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table "
          "<имя_таблицы> <столбец1:тип> .. - создать таблицу"
          )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print(
        "<command> insert into <имя_таблицы> values"
        "(<значение1>, <значение2>, ...) - добавить запись"
    )
    print("<command> select * from <имя_таблицы> "
          "[where <столбец> = <значение>] - выбрать записи"
          )
    print("<command> update <имя_таблицы> set <столбец> = "
          "<значение> where <столбец> = <значение> - обновить"
          )
    print("<command> delete from <имя_таблицы> "
          "[where <столбец> = <значение>] - удалить записи")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

def parse_where(where_str: str) -> dict:
    parts = where_str.split("=", 1)
    if len(parts) != 2:
        raise ValueError("Неверный формат условия where")
    key = parts[0].strip()
    val = parse_value(parts[1])
    return {key: val}


def parse_set(set_str: str) -> dict:
    parts = set_str.split("=", 1)
    if len(parts) != 2:
        raise ValueError("Неверный формат условия set")
    key = parts[0].strip()
    val = parse_value(parts[1])
    return {key: val}


def run():
    print("Для вывода списка всех команд введите help")
    while True:
        metadata = load_metadata(META_FILE)
        user_input = input("Введите команду: ").strip()
        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Выход из программы.")
            break
        elif user_input.lower() == "help":
            print_help()
            continue
        elif user_input.lower() == "list_tables":
            if not metadata:
                print("Список таблиц пуст.")
            else:
                print("Таблицы:")
                for table_name, table_info in metadata.items():
                    cols = ", ".join(
                        f"{c['name']}:{c['type']}" for c in table_info["columns"]
                    )
                    print(f"  - {table_name} ({cols})")
            continue

        # create_table
        if user_input.startswith("create_table "):
            parts = shlex.split(user_input)
            if len(parts) < 2:
                print("Ошибка: Укажите имя таблицы и столбцы.")
                continue
            table_name = parts[1]
            columns = parts[2:]
            new_metadata = create_table(metadata, table_name, columns)
            if new_metadata is not None:
                save_metadata(META_FILE, new_metadata)
                cacher.cache_clear()
            continue

        # drop_table
        if user_input.startswith("drop_table "):
            parts = shlex.split(user_input)
            if len(parts) < 2:
                print("Ошибка: Укажите имя таблицы.")
                continue
            table_name = parts[1]
            new_metadata = drop_table(metadata, table_name)
            if new_metadata is not None:
                save_metadata(META_FILE, new_metadata)
                # Удаляем файл данных
                filepath = os.path.join("data", f"{table_name}.json")
                if os.path.exists(filepath):
                    os.remove(filepath)
                cacher.cache_clear()
            continue

        # insert
        match = re.match(
            r"insert\s+into\s+(\w+)\s+values\s+\((.*)\)", user_input, re.IGNORECASE
        )
        if match:
            table_name = match.group(1)
            values_str = match.group(2)
            values = [parse_value(v) for v in values_str.split(",")]
            data = load_table_data(table_name)
            new_data = insert(metadata, table_name, values, data)
            if new_data is not None:
                save_table_data(table_name, new_data)
                cacher.cache_clear()
            continue

        # select
        match = re.match(
            r"select\s+\*\s+from\s+(\w+)(?:\s+where\s+(\w+)\s*=\s*(.+))?",
            user_input,
            re.IGNORECASE,
        )
        if match:
            table_name = match.group(1)
            where_str = match.group(3)
            data = load_table_data(table_name)
            if where_str:
                where_clause = {match.group(2): parse_value(where_str)}
            else:
                where_clause = None
            key = (
                table_name,
                tuple(sorted(where_clause.items())) if where_clause else None,
            )
            result = cacher(key, lambda: select(data, where_clause))
            if result is None:
                print("Ошибка при выполнении запроса.")
                continue
            if not result:
                print("Нет данных.")
            else:
                table = PrettyTable()
                table.field_names = list(result[0].keys())
                for row in result:
                    table.add_row(list(row.values()))
                print(table)
            continue

        # update
        match = re.match(
            r"update\s+(\w+)\s+set\s+(\w+)\s*=\s*(.+?)\s+where\s+(\w+)\s*=\s*(.+)",
            user_input,
            re.IGNORECASE,
        )
        if match:
            table_name = match.group(1)
            set_key = match.group(2)
            set_val = parse_value(match.group(3))
            where_key = match.group(4)
            where_val = parse_value(match.group(5))
            data = load_table_data(table_name)
            new_data = update(data, {set_key: set_val}, {where_key: where_val})
            if new_data is not None:
                save_table_data(table_name, new_data)
                cacher.cache_clear()
                print("Данные обновлены.")
            continue

        # delete
        match = re.match(
            r"delete\s+from\s+(\w+)(?:\s+where\s+(\w+)\s*=\s*(.+))?",
            user_input,
            re.IGNORECASE,
        )
        if match:
            table_name = match.group(1)
            where_str = match.group(3)
            data = load_table_data(table_name)
            if where_str:
                where_clause = {match.group(2): parse_value(where_str)}
            else:
                where_clause = {}
            new_data = delete(data, where_clause)
            if new_data is not None:
                save_table_data(table_name, new_data)
                cacher.cache_clear()
                print("Данные удалены.")
            continue

        print(f"Неизвестная команда: {user_input}. Введите 'help' для справки.")