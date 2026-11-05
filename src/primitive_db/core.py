from .constants import VALID_TYPES
from .decorators import confirm_action, handle_db_errors, log_time


@handle_db_errors
def create_table(metadata: dict, table_name: str, columns: list[str]) -> dict:
    if table_name in metadata:
        raise ValueError(f"Таблица '{table_name}' уже существует.")

    parsed_columns = [{"name": "ID", "type": "int"}]

    for col in columns:
        if ":" not in col:
            raise ValueError(f"Неверный формат столбца '{col}'. Ожидается 'имя:тип'.")
        name, col_type = col.split(":", 1)
        if col_type not in VALID_TYPES: #используем константу
            raise ValueError(
                f"Недопустимый тип '{col_type}'. Разрешены: int, str, bool."
            )
        parsed_columns.append({"name": name, "type": col_type})

    metadata[table_name] = {"columns": parsed_columns}
    print(f"Таблица '{table_name}' успешно создана.")
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict:
    if table_name not in metadata:
        raise KeyError(f"Таблица '{table_name}' не найдена.")
    del metadata[table_name]
    print(f"Таблица '{table_name}' удалена.")
    return metadata


@handle_db_errors
@log_time
def insert(metadata: dict, table_name: str, values: list, data: list) -> list:
    if table_name not in metadata:
        raise KeyError(f"Таблица '{table_name}' не существует.")

    columns = metadata[table_name]["columns"]
    expected_columns = columns[1:]  # без ID

    if len(values) != len(expected_columns):
        raise ValueError(
            f"Ожидалось {len(expected_columns)} значений, получено {len(values)}."
        )

    for val, col in zip(values, expected_columns):
        expected_type = col["type"]
        if expected_type == "int" and not isinstance(val, int):
            raise ValueError(
                f"Значение '{val}' для столбца '{col['name']}' должно быть int."
            )
        elif expected_type == "str" and not isinstance(val, str):
            raise ValueError(
                f"Значение '{val}' для столбца '{col['name']}' должно быть str."
            )
        elif expected_type == "bool" and not isinstance(val, bool):
            raise ValueError(
                f"Значение '{val}' для столбца '{col['name']}' должно быть bool."
            )

    new_id = max((row["ID"] for row in data), default=0) + 1
    new_row = {"ID": new_id}
    for col, val in zip(expected_columns, values):
        new_row[col["name"]] = val

    data.append(new_row)
    print(f"Запись добавлена в '{table_name}'.")
    return data


@handle_db_errors
@log_time
def select(data: list, where_clause: dict = None) -> list:
    if where_clause is None:
        return data

    result = []
    for row in data:
        match = True
        for key, val in where_clause.items():
            if row.get(key) != val:
                match = False
                break
        if match:
            result.append(row)
    return result


@handle_db_errors
def update(data: list, set_clause: dict, where_clause: dict) -> list:
    for row in data:
        match = True
        for key, val in where_clause.items():
            if row.get(key) != val:
                match = False
                break
        if match:
            for key, val in set_clause.items():
                if key in row:
                    row[key] = val
    return data


@handle_db_errors
@confirm_action("удаление записей")
def delete(data: list, where_clause: dict) -> list:
    new_data = []
    for row in data:
        match = True
        for key, val in where_clause.items():
            if row.get(key) != val:
                match = False
                break
        if not match:
            new_data.append(row)
    return new_data