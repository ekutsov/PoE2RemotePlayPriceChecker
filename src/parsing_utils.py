import json
import re
import os
from functools import lru_cache

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

@lru_cache(maxsize=1)
def load_ndjson(file_name):
    """
    Загружает ndjson-файл из папки data и возвращает список словарей.
    Использует кэширование для ускорения повторных вызовов.
    """
    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, "r", encoding="utf-8") as file:
        return [json.loads(line) for line in file]

def build_item_lookup(items):
    """
    Создаёт словарь для быстрого поиска предметов по названию.
    """
    lookup = {}
    for item in items:
        name = item.get("name", "").lower()
        ref_name = item.get("refName", "").lower()
        if name:
            lookup[name] = item
        if ref_name:
            lookup[ref_name] = item
    return lookup

def build_stat_lookup(stats):
    """
    Создаёт словарь для быстрого поиска статов по матчерам.
    """
    lookup = {}
    for stat in stats:
        for matcher in stat.get("matchers", []):
            pattern = re.escape(matcher["string"]).replace(r"\#", r"(\d+)")
            lookup[pattern] = stat
    return lookup


def find_item_by_name(item_lookup, name):
    """
    Находит предмет в словаре по названию.
    Поддерживает очистку имени и поиск по частичному совпадению.
    """
    cleaned_name = clean_item_name(name)
    # Сначала пытаемся найти точное совпадение
    if cleaned_name in item_lookup:
        return item_lookup[cleaned_name]

    # Если точное совпадение не найдено, ищем по частичному совпадению
    for item_name, item in item_lookup.items():
        if item_name in cleaned_name or cleaned_name in item_name:
            return item
    return None


def find_stat_by_line(stat_lookup, line):
    """
    Находит стат в словаре по строке.
    """
    for pattern, stat in stat_lookup.items():
        if re.match(pattern, line, re.IGNORECASE):
            return stat
    return None

def clean_item_name(name):
    """
    Очищает имя предмета от лишних символов, префиксов и суффиксов.
    """
    # Удаляем неалфавитные символы в начале и конце строки
    name = re.sub(r"^[^a-zA-Z]*", "", name)
    name = re.sub(r"[^a-zA-Z]*$", "", name)
    return name.strip().lower()


def parse_item(lines, item_lookup, stat_lookup):
    """
    Парсит строку с переносами и возвращает JSON с характеристиками предмета.
    """
    lines = [line.strip() for line in lines.split("\n") if line.strip()]

    # Первая строка — название предмета
    item_name = lines[0]
    item = find_item_by_name(item_lookup, item_name)
    if not item:
        return json.dumps({"error": "Item not found"}, indent=4)

    # Собираем результат
    result = item.copy()
    result["stats"] = []

    # Парсим остальные строки
    for line in lines[1:]:
        stat = find_stat_by_line(stat_lookup, line)
        if stat:
            # Извлекаем числовое значение из строки
            pattern = re.escape(stat["matchers"][0]["string"]).replace(r"\#", r"(\d+)")
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                value = int(match.group(1))
                result["stats"].append({
                    "id": stat["id"],
                    "value": value,
                    "ref": stat["ref"],
                })

    return json.dumps(result, indent=4)