# Session Service

Микросервис, отвечающий за управление жизненным циклом сессий в приложении FlickToPick.

## Технологии

*   **Язык:** Python 3.11
*   **Фреймворк:** FastAPI
*   **База данных:** PostgreSQL (для продакшена), SQLite (для разработки)
*   **Тестирование:** Pytest

## Требования

*   Docker и Docker Compose (рекомендуется)
*   Python 3.11+ (для локального запуска)
*   PostgreSQL (для продакшена)

## Запуск с использованием Docker

1.  Перейдите в директорию сервиса:
    ```bash
    cd services/session_service
    ```

2.  Соберите Docker-образ:
    ```bash
    docker build -t session-service .
    ```

3.  Запустите контейнер:
    ```bash
    docker run -p 8001:8000 -e DATABASE_URL=postgresql://user:password@postgres:5432/sessions session-service
    ```

## Локальный запуск

1.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

2.  Запустите сервер:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
    ```

## Тестирование

Для запуска тестов выполните команду:

```bash
pytest tests/
```

## API Эндпоинты

### `POST /sessions/create`

Создать новую сессию.

**Тело запроса:**
```json
{
  "creator_id": "string"
}
```

**Ответ (201 Created):**
```json
{
  "session_id": 1,
  "session_code": "ABC123",
  "creator_id": "user1",
  "status": "active",
  "current_movie_id": null,
  "participants": ["user1"],
  "created_at": "2024-12-11T10:00:00"
}
```

### `POST /sessions/join`

Присоединиться к существующей сессии по коду.

**Тело запроса:**
```json
{
  "session_code": "ABC123",
  "user_id": "string"
}
```

**Ответ (200 OK):**
```json
{
  "session_id": 1,
  "session_code": "ABC123",
  "creator_id": "user1",
  "status": "active",
  "current_movie_id": null,
  "participants": ["user1", "user2"],
  "created_at": "2024-12-11T10:00:00"
}
```

### `GET /sessions/{session_code}/validate`

Проверить валидность сессии (используется другими сервисами).

**Параметры:**
- `session_code`: Код сессии

**Ответ (200 OK):**
```json
{
  "is_valid": true,
  "session_id": 1,
  "status": "active",
  "participants": ["user1", "user2"],
  "current_movie_id": null
}
```

### `GET /sessions/{session_code}`

Получить информацию о сессии.

**Параметры:**
- `session_code`: Код сессии

**Ответ (200 OK):**
```json
{
  "session_id": 1,
  "session_code": "ABC123",
  "creator_id": "user1",
  "status": "active",
  "current_movie_id": null,
  "participants": ["user1", "user2"],
  "created_at": "2024-12-11T10:00:00"
}
```

### `PUT /sessions/{session_code}/movie`

Обновить текущий фильм для сессии (вызывается Match Service).

**Параметры:**
- `session_code`: Код сессии

**Тело запроса:**
```json
{
  "current_movie_id": 123
}
```

**Ответ (200 OK):**
```json
{
  "session_id": 1,
  "session_code": "ABC123",
  "creator_id": "user1",
  "status": "active",
  "current_movie_id": 123,
  "participants": ["user1", "user2"],
  "created_at": "2024-12-11T10:00:00"
}
```

### `POST /sessions/{session_code}/disconnect/{user_id}`

Отметить пользователя как отключённого от сессии.

**Параметры:**
- `session_code`: Код сессии
- `user_id`: ID пользователя

**Ответ (200 OK):**
```json
{
  "status": "disconnected",
  "session_code": "ABC123",
  "user_id": "user2"
}
```

### `POST /sessions/{session_code}/complete`

Завершить сессию.

**Параметры:**
- `session_code`: Код сессии

**Ответ (200 OK):**
```json
{
  "status": "completed",
  "session_code": "ABC123"
}
```

### `GET /health`

Проверка работоспособности сервиса.

### `GET /`

Корневой маршрут, возвращает статус сервиса.

## Конфигурация

Сервис настраивается через переменные окружения:

*   `DATABASE_URL`: URL базы данных (по умолчанию `sqlite:///./sessions.db`)

## Тестирование

Для детальной информации о E2E тестах см. [E2E_TESTING.md](E2E_TESTING.md).

### Запуск тестов

1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

2. Запустите тесты:
   ```bash
   python -m pytest tests/test_e2e.py -v
   ```

3. Для запуска конкретного теста:
   ```bash
   python -m pytest tests/test_e2e.py::TestSessionCreation::test_create_session_success -v
   ```

Все 17 тестов соответствуют плану тестирования из `docs/e2e-testing-plan.md` (Часть 1: Управление сессиями).
