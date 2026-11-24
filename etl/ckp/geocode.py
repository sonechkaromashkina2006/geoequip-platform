import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
import requests

# Базовый справочник координат регионов РФ (широта, долгота)
REGION_COORDS: Dict[str, Tuple[float, float]] = {
    "г. москва": (55.7558, 37.6173),
    "москва": (55.7558, 37.6173),
    "московская область": (55.7558, 37.6173),
    "г. санкт-петербург": (59.9311, 30.3609),
    "санкт-петербург": (59.9311, 30.3609),
    "ленинградская область": (59.9311, 30.3609),
    "республика татарстан": (55.7961, 49.1064),
    "ульяновская область": (54.3142, 48.4031),
    "республика башкортостан": (54.7388, 55.9721),
    "новосибирская область": (55.0084, 82.9357),
    "хабаровский край": (48.4802, 135.0719),
    "свердловская область": (56.8389, 60.6057),
    "нижегородская область": (56.2965, 43.9361),
    "самарская область": (53.1959, 50.1002),
    "томская область": (56.4846, 84.9476),
    "ростовская область": (47.2357, 39.7015),
    "краснодарский край": (45.0355, 38.9753),
    "пермский край": (58.0105, 56.2502),
    "челябинская область": (55.1644, 61.4368),
    "республика крым": (44.9521, 34.1024),
}

CACHE_PATH = Path("data/cache/geocode_cache.json")


def load_cache(path: Path = CACHE_PATH) -> Dict[str, Optional[Tuple[float, float]]]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {k: tuple(v) if v is not None else None for k, v in data.items()}


def save_cache(cache: Dict[str, Optional[Tuple[float, float]]], path: Path = CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serializable = {k: list(v) if v is not None else None for k, v in cache.items()}
    path.write_text(json.dumps(serializable, ensure_ascii=False, indent=2), encoding="utf-8")


def geocode_nominatim(query: str) -> Optional[Tuple[float, float]]:
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{query}, Россия", "format": "json", "limit": 1},
            headers={"User-Agent": "GeoEquipPlatform/0.1 (academic prototype)"},
            timeout=15,
        )
        r.raise_for_status()
        items = r.json()
        if items:
            return float(items[0]["lat"]), float(items[0]["lon"])
    except Exception:
        return None
    return None


def resolve_coords(
    region: Optional[str],
    cache: Dict[str, Optional[Tuple[float, float]]],
    use_online_fallback: bool = True,
) -> Optional[Tuple[float, float]]:
    if not region:
        return None
    key = region.strip().lower()
    if key in REGION_COORDS:
        return REGION_COORDS[key]
    if key in cache:
        return cache[key]

    coords = geocode_nominatim(region) if use_online_fallback else None
    cache[key] = coords
    if use_online_fallback:
        time.sleep(1.1)
    return coords


def enrich_geo(records: Iterable[Dict[str, Any]], use_online_fallback: bool = True) -> List[Dict[str, Any]]:
    cache = load_cache()
    enriched: List[Dict[str, Any]] = []

    for rec in records:
        item = dict(rec)
        coords = resolve_coords(item.get("region"), cache=cache, use_online_fallback=use_online_fallback)
        item["lat"] = coords[0] if coords else None
        item["lon"] = coords[1] if coords else None
        item.setdefault("enterprise_type", "ЦКП")
        item.setdefault("accessibility", 0.7)
        item.setdefault("cost", 0.5)
        enriched.append(item)

    save_cache(cache)
    return enriched


if __name__ == "__main__":
    from normalize import load_jsonl, save_jsonl

    src = Path("data/processed/equipment_normalized.jsonl")
    dst = Path("data/processed/equipment_geo.jsonl")
    rows = load_jsonl(src)
    geo_rows = enrich_geo(rows, use_online_fallback=True)
    save_jsonl(dst, geo_rows)
    missing = sum(1 for r in geo_rows if r["lat"] is None or r["lon"] is None)
    print(f"Обработано записей: {len(geo_rows)}, без координат: {missing}")