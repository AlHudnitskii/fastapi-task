# Transaction API


## Особенности

- **Система двойной записи** - полная интеграция бухгалтерского учета
- **Асинхронная обработка** - FastAPI + asyncpg + Celery
- **Мультивалютность** - поддержка 10 валют (USD, EUR, BTC, ETH и др.)
- **Транзакции** - депозиты, снятия, откаты с проверкой баланса
- **Отчетность** - еженедельные отчеты с аналитикой
- **Безопасность** - блокировка счетов, валидация операций
- **Docker** - полная контейнеризация
- **Тесты** - pytest с покрытием
- **Pre-commit hooks** - автоматическая проверка кода

## Быстрый старт

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd transaction-api

# Установить зависимости
poetry install

# Активировать виртуальное окружение
poetry shell
```

### 2. Настройка окружения

```bash
# Скопировать файл с переменными окружения
cp .env.example .env

# Отредактировать .env под ваши настройки
nano .env
```

### 3. Запуск с Docker

```bash
# Запустить все сервисы
docker-compose up -d

# Применить миграции
docker-compose exec api alembic upgrade head

```

### 4. Запуск без Docker

```bash
# Запустить PostgreSQL и Redis локально
# Затем применить миграции
alembic upgrade head

# Запустить API
uvicorn app.main:app --reload

# В другом терминале запустить Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# В третьем терминале запустить Celery beat (опционально)
celery -A app.tasks.celery_app beat --loglevel=info
```

## Использование API

### Документация

После запуска доступна интерактивная документация:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Структура проекта

```
transaction-api/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── reports.py
│   │   ├── transactions.py
│   │   └── users.py
│   ├── models/
│   │   ├── db_models/          # SQLAlchemy модели
│   │   │   ├── accounting.py  # Система двойной записи
│   │   │   ├── transaction.py
│   │   │   └── user.py
│   │   ├── schemas/            # Pydantic схемы
│   │   │   ├── accounting.py
│   │   │   ├── transaction.py
│   │   │   └── user.py
│   │   └── enums.py
│   ├── repositories/           # Репозитории для работы с БД
│   ├── services/               # Бизнес-логика
│   ├── tasks/                  # Celery задачи
│   ├── middleware/             # Middleware
│   ├── config.py               # Настройки
│   ├── database.py             # Подключение к БД
│   ├── exceptions.py           # Исключения
│   └── main.py                 # Точка входа
├── alembic/
│   ├── versions/               # Миграции
│   └── env.py
├── scripts/
│   └── seed_data.py            # Скрипт для заполнения БД
├── tests/                      # Тесты
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## Postman коллекция

Импортируйте файл `postman/transaction_api.json` в Postman для быстрого тестирования API.

Коллекция включает:
- Все основные эндпоинты
- Примеры запросов
- Автоматическое сохранение ID в переменные
- Примеры работы со всеми валютами

## Логирование

Логи сохраняются в директорию `logs/`:
- `app.log` - все логи приложения
- Ротация каждые 500 MB
- Хранение 10 дней
- Сжатие в zip

## Переменные окружения

Основные переменные в `.env`:

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

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```
