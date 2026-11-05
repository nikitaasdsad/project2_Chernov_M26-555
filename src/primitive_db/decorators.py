import functools
import time


def handle_db_errors(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError, FileNotFoundError) as e:
            print(f"Ошибка: {e}")
            return None
    return wrapper


def confirm_action(action_name):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')
            if answer.lower() != 'y':
                print("Операция отменена.")
                # Возвращаем первый аргумент (metadata или data) без изменений
                return args[0] if args else None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result
    return wrapper


def create_cacher():

    cache = {}
    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result
    # Добавляем метод для очистки кэша (полезно при изменении данных)
    cache_result.cache_clear = lambda: cache.clear()
    return cache_result