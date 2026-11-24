import json, math, sys, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = "https://ckp-rf.ru"
URL = BASE + "/equipment/search/list.php"
RAW = Path("data/raw/ckp"); RAW.mkdir(parents=True, exist_ok=True)
OUT = Path("data/processed/equipment.jsonl"); OUT.parent.mkdir(parents=True, exist_ok=True)
HEADERS_GET = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

HEADERS_POST = {
    **HEADERS_GET,
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://ckp-rf.ru",
    "Referer": "https://ckp-rf.ru/equipment/search/",
    "X-Requested-With": "XMLHttpRequest",
}
DELAY = 2.0
PAGE_SIZE = 48

def fetch_page(s, page):
    path = RAW / f"page_{page:05d}.html"
    if path.exists():
        return path.read_text("utf-8")
    time.sleep(DELAY)
    # Используем HEADERS_POST
    r = s.post(URL, data={"page": page, "size": PAGE_SIZE}, headers=HEADERS_POST, timeout=30)
    r.raise_for_status()
    path.write_text(r.text, "utf-8")
    return r.text

def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    for it in soup.select(".equipments-item"):
        sub = it.select_one(".equipments-item-subtitle")
        year = sub.select_one("strong")
        year_text = year.get_text(strip=True) if year else None
        if year:
            year.extract()
        maker, _, model = sub.get_text(" ", strip=True).partition("|")
        yield {
            "eq_id": it.select_one(".equipments-item-code").get_text(strip=True),
            "name": it.select_one(".equipments-item-title").get_text(strip=True),
            "manufacturer": maker.strip(),
            "model": model.strip(),
            "year": year_text,
            "region": it.select_one(".services-item-city").get_text(strip=True),
            "ckp": it.select_one(".services-item-ckp").get_text(strip=True),
            "source_url": BASE + it.select_one("a")["href"],
        }

def main(limit=None):
    s = requests.Session()
    r_init = s.get(BASE + "/equipment/search/", headers=HEADERS_GET, timeout=30)
    r_init.raise_for_status()
    first = fetch_page(s, 1)
    total = int(BeautifulSoup(first, "html.parser").select_one("#ownd-total")["value"])
    per_page = len(list(parse(first)))
    pages = math.ceil(total / per_page)
    print("всего:", total, "на странице:", per_page, "страниц:", pages)
    if limit:
        pages = min(pages, limit)
    with OUT.open("w", encoding="utf-8") as f:
        for p in range(1, pages + 1):
            for rec in parse(fetch_page(s, p)):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print("страница", p, "из", pages)

if __name__ == "__main__":
    main(limit=int(sys.argv[1]) if len(sys.argv) > 1 else None)