# GeoEquip Intelligence

Гибридная геоинформационная система подбора организаций и лабораторно-производственного оборудования на основе семантического поиска, графовой модели знаний и географической привязки.

## Архитектура и стек

* **Backend API**: FastAPI (`server/app/main.py`)
* **Графовая база данных и векторный индекс**: Neo4j (`neo4j:5.23-community`, индекс `equipment_embeddings`)
* **Векторное представление текста**: Sentence-BERT (`paraphrase-multilingual-MiniLM-L12-v2`)
* **ETL-пайплайн**: скрипты сбора, нормализации, геокодирования, категоризации и загрузки данных (`etl/ckp/`)
* **Веб-интерфейс**: клиентская панель поиска и карта на базе Яндекс Карт (`web/index.html`)

## Структура репозитория

```text
.
├── docker-compose.yml       # Конфигурация запуска сервисов (Neo4j)
├── etl/ckp/                 # Этапы ETL-обработки данных
│   ├── fetch.py
│   ├── parse.py
│   ├── normalize.py
│   ├── geocode.py
│   ├── categorize.py
│   └── load.py
├── server/                  # FastAPI-приложение и сервисы поиска/ранжирования
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
├── web/
│   └── index.html           # Веб-интерфейс поиска и визуализации на карте
└── data/
    └── seed/data.json       # Базовые демонстрационные данные
```

## Запуск проекта

### 1. Запуск Neo4j

```bash
docker compose up -d
```

Проверьте доступность Neo4j Browser (`http://localhost:7474`) и Bolt-порта (`7687`). При необходимости примените схему и ограничения из `server/scripts/init_schema.cypher`.

### 2. Подготовка окружения Python

```bash
python3 -m venv geoequip-venv
source geoequip-venv/bin/activate
pip install -r server/requirements.txt
```

### 3. Выполнение ETL и загрузка в Neo4j

Скрипты ETL запускаются из корня репозитория при активированном виртуальном окружении:

```bash
python etl/ckp/normalize.py
python etl/ckp/geocode.py
python etl/ckp/categorize.py
python etl/ckp/load.py
```

### 4. Запуск API и веб-интерфейса

```bash
cd server
uvicorn app.main:app --reload
```

После запуска интерфейс доступен по адресу `http://localhost:8000/`.

## Основные эндпоинты

* `GET /healthz` — проверка состояния сервиса и подключения к БД
* `GET /api/database/all` — получение данных организаций с координатами
* `POST /search` — семантический поиск оборудования и ранжирование организаций с учетом доступности и стоимости
* `GET /similar/{enterprise_name}` — получение связанных организаций по общим категориям и задачам в графе
