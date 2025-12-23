# Transaction API

API-сервис для обработки финансовых транзакций с поддержкой мультивалютности и системой двойной записи.

## Особенности

- **Система двойной записи** - полная интеграция бухгалтерского учета
- **Асинхронная обработка** - FastAPI + asyncpg + Celery
- **Мультивалютность** - поддержка 10 валют (USD, EUR, BTC, ETH и др.)
- **Транзакции** - депозиты, снятия, откаты с проверкой баланса
- **Отчетность** - еженедельные отчеты с аналитикой
- **Безопасность** - блокировка счетов, валидация операций
- **Docker** - полная контейнеризация
- **Тесты** - pytest с покрытием >70%
- **Pre-commit hooks** - автоматическая проверка кода (mypy, flake8, isort, black)

## Требования

- Python 3.11+
- Docker & Docker Compose
- Poetry (для локальной разработки)

## Быстрый старт с Docker

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd transaction-api
```

### 2. Настройка окружения

```bash
# Скопировать файл с переменными окружения
cp .env.example .env

# При необходимости отредактировать .env
nano .env
```

### 3. Запуск всех сервисов

```bash
# Запустить все сервисы (PostgreSQL, Redis, API, Celery)
docker-compose up -d

# Проверить статус сервисов
docker-compose ps
```

### 4. Применить миграции базы данных

```bash
# Выполнить миграции Alembic
docker-compose exec api alembic upgrade head
```

### 5. Заполнить БД тестовыми данными (опционально)

```bash
# Создать 10 пользователей с 5 транзакциями каждый
docker-compose exec api python scripts/seed_data.py 10 5

# Или создать 50 пользователей с 20 транзакциями
docker-compose exec api python scripts/seed_data.py 50 20
```

### 6. Проверить работу API

Откройте в браузере:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/



## Запуск тестов

```bash
# Запустить все тесты
docker-compose exec api pytest

# С покрытием
docker-compose exec api pytest --cov=app --cov-report=html

# Только unit тесты
docker-compose exec api pytest tests/unit/

# Только integration тесты
docker-compose exec api pytest tests/integration/
```



## Pre-commit hooks

### Установка

```bash
# Установить pre-commit hooks
pre-commit install

# Запустить вручную на всех файлах
pre-commit run --all-files
```

### Что проверяется:

- **black** - форматирование кода
- **isort** - сортировка импортов
- **flake8** - линтер (PEP8)
- **mypy** - проверка типов (требует дополнительной настройки)
- **trailing-whitespace** - удаление пробелов в конце строк
- **end-of-file-fixer** - новая строка в конце файла
- **check-yaml** - валидация YAML
- **check-json** - валидация JSON

## Структура проекта

```
transaction-api/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── reports.py         # Отчеты
│   │   ├── transactions.py    # Транзакции
│   │   └── users.py           # Пользователи
│   ├── models/
│   │   ├── db_models/         # SQLAlchemy модели
│   │   ├── schemas/           # Pydantic схемы
│   │   └── enums.py           # Enums
│   ├── repositories/          # Репозитории (data access)
│   ├── services/              # Бизнес-логика
│   ├── tasks/                 # Celery задачи
│   ├── middleware/            # Middleware
│   ├── dependencies/          # Зависимости FastAPI
│   ├── config.py              # Настройки
│   ├── database.py            # Подключение к БД
│   ├── exceptions.py          # Кастомные исключения
│   ├── logging.py             # Настройка логирования
│   └── main.py                # Точка входа
├── alembic/
│   ├── versions/              # Миграции
│   └── env.py                 # Конфигурация Alembic
├── scripts/
│   └── seed_data.py           # Скрипт заполнения БД
├── tests/
│   ├── unit/                  # Unit тесты
│   ├── integration/           # Integration тесты
│   └── conftest.py            # Fixtures
├── postman/
│   └── transaction_api.json   # Postman коллекция
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml             # Poetry dependencies
├── .pre-commit-config.yaml    # Pre-commit hooks
├── alembic.ini                # Alembic config
└── README.md
```

## API Endpoints

### Users (Пользователи)

- `POST /users` - Создать пользователя
- `GET /users` - Получить список пользователей (с фильтрами)
- `GET /users/{user_id}` - Получить пользователя по ID
- `PATCH /users/{user_id}` - Изменить статус пользователя

### Transactions (Транзакции)

- `POST /transactions/users/{user_id}` - Создать транзакцию
- `GET /transactions` - Получить список транзакций (с фильтрами)
- `PATCH /transactions/users/{user_id}/transactions/{transaction_id}/rollback` - Откатить транзакцию

### Reports (Отчеты)

- `GET /reports/weekly` - Получить недельный отчет (синхронно)
- `POST /reports/weekly/async` - Запустить генерацию отчета (асинхронно через Celery)

## Postman коллекция

Импортируйте `postman/transaction_api.json` в Postman для тестирования API.

**Коллекция включает:**
- Все эндпоинты с примерами
- Автоматическое сохранение ID в переменные
- Примеры работы со всеми валютами
- Тесты для проверки ответов

## Переменные окружения

```env
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=transaction_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_ECHO=false

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

## Логирование

Логи сохраняются в директории `logs/`:
- `app.log` - все логи приложения
- Ротация каждые 500 MB
- Хранение 10 дней
- Автоматическое сжатие в zip


## Автор
alhudnitski@gmail.com
