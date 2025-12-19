# Match Service

Микросервис, отвечающий за логику голосования и определения совпадений (матчей) в приложении FlickToPick.

## Технологии

*   **Язык:** Python 3.11
*   **Фреймворк:** FastAPI
*   **База данных:** Redis (для хранения временных голосов)
*   **Тестирование:** Pytest

## Требования

*   Docker и Docker Compose (рекомендуется)
*   Python 3.11+ (для локального запуска)
*   Redis (для локального запуска)

## Запуск с использованием Docker

1.  Перейдите в директорию сервиса:
    ```bash
    cd services/match_service
    ```

2.  Соберите Docker-образ:
    ```bash
    docker build -t match-service .
    ```

3.  Запустите контейнер (убедитесь, что у вас запущен Redis, или используйте `docker-compose` для всего стека):
    ```bash
    # Пример запуска с подключением к Redis на хосте (для разработки)
    docker run -p 8000:8000 --env REDIS_HOST=host.docker.internal match-service
    ```

## Локальный запуск

1.  Установите зависимости:
    ```bash
    pip install -r requirements.txt
    ```

2.  Убедитесь, что Redis запущен локально на порту 6379.

3.  Запустите сервер:
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```

## Тестирование

Для запуска тестов выполните команду:

```bash
pytest tests/
```

## API Эндпоинты

### `POST /swipe`

Обработка свайпа пользователя.

**Тело запроса:**
```json
{
  "session_id": "string",
  "user_id": "string",
  "movie_id": "string",
  "swipe_value": "want_now" | "skip",
  "participants": ["user1", "user2"]
}
```

**Ответы:**

*   `vote_recorded`: Голос принят, ожидание остальных.
*   `match_found`: Все участники проголосовали "ЗА".
*   `next_movie`: Кто-то проголосовал "ПРОТИВ", переход к следующему фильму.

### `GET /health`

Проверка работоспособности сервиса.

### `GET /`

Корневой маршрут, возвращает статус сервиса.

## Конфигурация

Сервис настраивается через переменные окружения:

*   `REDIS_HOST`: Хост Redis (по умолчанию `localhost`)
*   `REDIS_PORT`: Порт Redis (по умолчанию `6379`)
*   `REC_SERVICE_URL`: URL сервиса рекомендаций (по умолчанию `http://recommendation-service:8000`)
*   `SESSION_SERVICE_URL`: URL сервиса сессий (по умолчанию `http://session-service:8000`)
