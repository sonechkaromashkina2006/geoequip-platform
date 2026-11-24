import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

EMPTY_VALUES = {"", "-", "—", "–", "none", "null", "nan", "н/д", "нет"}


def clean_str(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = re.sub(r"\s+", " ", str(val)).strip()
    if s.lower() in EMPTY_VALUES:
        return None
    return s


def build_description(item: Dict[str, Optional[str]]) -> str:
    parts: List[str] = []
    if item.get("name"):
        parts.append(item["name"])
    if item.get("manufacturer"):
        parts.append(f"Производитель: {item['manufacturer']}")
    if item.get("model"):
        parts.append(f"Модель: {item['model']}")
    if item.get("year"):
        parts.append(f"Год выпуска: {item['year']}")
    if item.get("ckp"):
        parts.append(f"ЦКП / организация: {item['ckp']}")
    if item.get("region"):
        parts.append(f"Регион: {item['region']}")
    return ". ".join(parts) + ("." if parts else "")


def normalize_records(raw_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_ids = set()
    seen_keys = set()
    normalized: List[Dict[str, Any]] = []

    for row in raw_records:
        eq_id = clean_str(row.get("eq_id"))
        name = clean_str(row.get("name"))
        if not name:
            continue

        manufacturer = clean_str(row.get("manufacturer"))
        model = clean_str(row.get("model"))
        year = clean_str(row.get("year"))
        region = clean_str(row.get("region"))
        ckp = clean_str(row.get("ckp")) or "Неизвестный ЦКП"
        source_url = clean_str(row.get("source_url"))

        if eq_id:
            if eq_id in seen_ids:
                continue
            seen_ids.add(eq_id)
        else:
            dedup_key = (ckp.lower(), name.lower(), (model or "").lower(), (region or "").lower())
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

        enterprise_name = f"{ckp} ({region})" if region and region.lower() not in ckp.lower() else ckp

        record = {
            "eq_id": eq_id,
            "name": name,
            "manufacturer": manufacturer,
            "model": model,
            "year": year,
            "region": region,
            "ckp": ckp,
            "enterprise_name": enterprise_name,
            "source_url": source_url,
        }
        record["description"] = build_description(record)
        normalized.append(record)

    return normalized


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    src = Path("data/processed/equipment.jsonl")
    dst = Path("data/processed/equipment_normalized.jsonl")
    raw = load_jsonl(src)
    cleaned = normalize_records(raw)
    save_jsonl(dst, cleaned)
    print(f"Было: {len(raw)}, стало после очистки: {len(cleaned)}")