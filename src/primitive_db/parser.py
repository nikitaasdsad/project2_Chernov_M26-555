
def parse_value(s: str): #Преобразует строку в Python-значение
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        return s[1:-1]
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        return int(s)
    except ValueError:
        return s


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