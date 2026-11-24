from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

RULES: List[Tuple[List[str], str, List[str]]] = [
    (
        ["микроскоп", "спектрометр", "дифрактометр", "томограф", "анализатор", "хроматограф"],
        "Аналитика и микроскопия",
        ["Анализ структуры и состава материалов", "Исследование образцов"],
    ),
    (
        ["испытани", "вибростенд", "трибометр", "микротвердомер", "удар", "толщиномер", "реактор"],
        "Испытания и диагностика",
        ["Механические и климатические испытания", "Неразрушающий контроль и диагностика"],
    ),
    (
        ["станок", "пресс", "дробилка", "измельчен", "шлифовальн", "отрезн", "фрезер", "токарн"],
        "Металлообработка и пробоподготовка",
        ["Пробоподготовка и обработка материалов", "Изготовление деталей и образцов"],
    ),
    (
        ["георадар", "почв", "влажност", "электропроводност", "метео", "аэрофотосъем", "gps", "радиостанц", "видеокамер", "тепловизор"],
        "Полевые и геофизические измерения",
        ["Полевые измерения и мониторинг среды", "Геопространственная и дистанционная съёмка"],
    ),
]

DEFAULT_CATEGORY = "Прочее лабораторное и производственное оборудование"
DEFAULT_TASKS = ["Исследовательские и технологические работы"]


def classify_equipment(record: Dict[str, Any]) -> Tuple[str, List[str]]:
    text = f"{record.get('name') or ''} {record.get('description') or ''}".lower()
    for keywords, category, tasks in RULES:
        if any(kw in text for kw in keywords):
            return category, tasks
    return DEFAULT_CATEGORY, DEFAULT_TASKS


def categorize_records(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for rec in records:
        item = dict(rec)
        category, tasks = classify_equipment(item)
        item["category"] = category
        item["tasks"] = tasks
        result.append(item)
    return result


if __name__ == "__main__":
    from normalize import load_jsonl, save_jsonl

    src = Path("data/processed/equipment_geo.jsonl")
    dst = Path("data/processed/equipment_ready.jsonl")
    rows = load_jsonl(src)
    categorized = categorize_records(rows)
    save_jsonl(dst, categorized)

    counts: Dict[str, int] = {}
    for r in categorized:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    print(f"Категоризировано записей: {len(categorized)}")
    for cat, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  - {cat}: {cnt}")