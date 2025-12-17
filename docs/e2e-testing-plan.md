# План E2E тестирования FlickToPick

## Введение

Данный документ описывает сценарии сквозного (end-to-end) тестирования MVP системы «FlickToPick» — приложения для совместного выбора фильмов.

**Охват MVP**: 
- Создание и управление сессиями выбора фильмов
- Получение рекомендаций фильмов на основе жанров и рейтинга
- Обнаружение совпадений (матчей) когда все участники проголосовали "нравится"

**Предусловия для всех тестов**:
- Все сервисы системы развернуты и доступны
- API Gateway доступен по адресу `http://localhost:8080`
- Система инициализирована с тестовыми данными о фильмах

**Способ выполнения тестов**: REST API через HTTP-запросы

---

# ЧАСТЬ 1: СЦЕНАРИИ УПРАВЛЕНИЯ СЕССИЯМИ

## 1.1. Основная функциональность сессий

### Тест 1.1.1: Успешное создание новой сессии

**Цель**: проверить полный цикл создания сессии и получение кода приглашения.

**Предусловия**:
- Session Service доступен на http://localhost:8001
- Base данные инициализирована

**Шаги**:
1. Отправить HTTP-запрос:
   ```
   POST http://localhost:8001/sessions/create
   Headers:
     Content-Type: application/json
   Body:
   {
     "creator_id": "user-001"
   }
   ```

**Ожидаемый результат**:
- HTTP статус: 200 OK
- Тело ответа содержит:
  ```json
  {
    "session_id": 1,
    "session_code": "ABC123def",
    "creator_id": "user-001",
    "status": "active",
    "current_movie_id": null,
    "participants": ["user-001"],
    "created_at": "2025-12-12T10:00:00"
  }
  ```
- Сессия создана в БД с статусом "active"
- Код сессии состоит из 6 символов (буквы и цифры)
- Создатель сессии добавлен как первый участник

### Тест 1.1.2: Подключение пользователя к существующей сессии по коду

**Цель**: проверить корректное добавление нового пользователя в существующую сессию.

**Предусловия**:
- Сессия существует с кодом "ABC123"
- Сессия имеет статус "active"
- Пользователь "user-002" еще не является участником

**Шаги**:
1. Отправить HTTP-запрос:
   ```
   POST http://localhost:8001/sessions/join
   Headers:
     Content-Type: application/json
   Body:
   {
     "session_code": "ABC123",
     "user_id": "user-002"
   }
   ```

**Ожидаемый результат**:
- HTTP статус: 200 OK
- Тело ответа содержит:
  ```json
  {
    "session_id": 1,
    "session_code": "ABC123",
    "creator_id": "user-001",
    "status": "active",
    "current_movie_id": null,
    "participants": ["user-001", "user-002"],
    "created_at": "2025-12-12T10:00:00"
  }
  ```
- Пользователь добавлен в список participants
- Пользователь отмечен как active (is_active=true)

### Тест 1.1.3: Завершение сессии

**Цель**: проверить обновление статуса сессии.

**Предусловия**:
- Сессия существует с кодом "ABC123"
- Статус сессии: "active"

**Шаги**:
1. Отправить HTTP-запрос на завершение сессии:
   ```
   POST http://localhost:8001/sessions/ABC123/complete
   ```

**Ожидаемый результат**:
- HTTP статус: 200 OK
- Тело ответа содержит:
  ```json
  {
    "status": "completed",
    "session_code": "ABC123"
  }
  ```
- Статус сессии в БД изменился на "completed"

---

# ЧАСТЬ 2: СЦЕНАРИИ ПОЛУЧЕНИЯ РЕКОМЕНДАЦИЙ

## 2.1. Основная функциональность рекомендаций

### Тест 2.1.1: Успешное получение списка фильмов для сессии

**Цель**: проверить получение списка доступных фильмов для новой сессии.

**Предусловия**:
- Сессия существует с кодом "ABC123"
- В базе данных существует минимум 5 доступных фильмов
- Сессия активна в Session Service

**Шаги**:
1. Отправить HTTP-запрос:
   ```
   GET http://localhost:8002/movies?session=ABC123
   Headers:
     Content-Type: application/json
   ```

**Ожидаемый результат**:
- HTTP статус: 200 OK
- Тело ответа содержит массив фильмов:
  ```json
  [
    {
      "id": 1,
      "title": "The Matrix",
      "genre": "sci-fi",
      "duration_minutes": 136,
      "rating": 8.7,
      "description": "A hacker discovers the true nature of his reality",
      "poster_url": "https://...",
      "is_available": true
    },
    {
      "id": 2,
      "title": "Inception",
      "genre": "sci-fi",
      "duration_minutes": 148,
      "rating": 8.8,
      "description": "...",
      "poster_url": "https://...",
      "is_available": true
    },
    ...
  ]
  ```
- Возвращены все доступные фильмы (is_available = true)
- Каждый фильм содержит обязательные поля (id, title, genre, duration_minutes, rating, description, poster_url, is_available)
- Фильмы отсортированы по рейтингу (убывание)

---

# ЧАСТЬ 3: СЦЕНАРИИ ГОЛОСОВАНИЯ И МЭТЧИНГА

## 3.1. Основная функциональность Match Service

### Тест 3.1.1: Успешное обнаружение совпадения (матча)

**Цель**: проверить полный цикл обнаружения совпадения когда все участники проголосовали "хотим смотреть".

**Предусловия**:
- Сессия существует с session_id = 1 и 3 активными участниками
- Все участники могут голосовать
- Текущий фильм: movie_id = 1

**Шаги**:
1. Участник user-001 голосует "want_now" для movie_id=1:
   ```
   POST http://localhost:8000/swipe
   Headers:
     Content-Type: application/json
   Body:
   {
     "session_id": 1,
     "user_id": "user-001",
     "movie_id": 1,
     "swipe_value": "want_now",
     "participants": ["user-001", "user-002", "user-003"]
   }
   ```
2. Участник user-002 голосует "want_now" для movie_id=1 с теми же participants
3. Участник user-003 голосует "want_now" для movie_id=1 с теми же participants

**Ожидаемый результат**:
- Первый голос (user-001): HTTP 200, тело:
  ```json
  {
    "status": "vote_recorded",
    "session_id": 1,
    "movie_id": 1,
    "votes_count": 1,
    "required_votes": 3
  }
  ```
- Второй голос (user-002): HTTP 200, тело:
  ```json
  {
    "status": "vote_recorded",
    "session_id": 1,
    "movie_id": 1,
    "votes_count": 2,
    "required_votes": 3
  }
  ```
- Третий голос (user-003): HTTP 200, тело содержит:
  ```json
  {
    "status": "match_found",
    "session_id": 1,
    "movie_id": 1,
    "matched_movie": {
      "id": 1,
      "title": "..."
    }
  }
  ```
- Матч обнаружен

### Тест 3.1.2: Отсутствие совпадения при пропуске одного участника

**Цель**: проверить, что матча нет, если хотя бы один участник проголосовал "skip".

**Предусловия**:
- Сессия существует с session_id = 2 и 3 участниками
- Текущий фильм: movie_id = 2

**Шаги**:
1. Участник user-001 голосует "want_now" для movie_id=2:
   ```
   POST http://localhost:8000/swipe
   Body: {"session_id": 2, "user_id": "user-001", "movie_id": 2, "swipe_value": "want_now", "participants": ["user-001", "user-002", "user-003"]}
   ```
2. Участник user-002 голосует "want_now" для movie_id=2
3. Участник user-003 голосует "skip" для movie_id=2

**Ожидаемый результат**:
- Первый голос: HTTP 200, status: "vote_recorded"
- Второй голос: HTTP 200, status: "vote_recorded"
- Третий голос: HTTP 200, содержит:
  ```json
  {
    "status": "next_movie",
    "session_id": 2,
    "movie_id": 2,
    "message": "Not all participants wanted this movie"
  }
  ```
- Матч НЕ создается
- Рекомендуется перейти к следующему фильму

---

# ЧАСТЬ 4: ПОЛНЫЕ ПОЛЬЗОВАТЕЛЬСКИЕ СЦЕНАРИИ (E2E)

## 4.1. Полный жизненный цикл сессии выбора фильма

### Тест 4.1.1: Полный сценарий от создания сессии до матча

**Цель**: проверить полный цикл работы системы: создание сессии, получение фильмов, голосование, матч.

**Предусловия**:
- Все сервисы развернуты (Session Service:8001, Recommendation Service:8002, Match Service:8000)
- В базе данных MovieDB минимум 5 фильмов с рейтингом выше 7.0

**Шаги**:
1. Создать новую сессию:
   ```
   POST http://localhost:8001/sessions/create
   Body: {"creator_id": "user-001"}
   → Получить session_id (int), session_code (6 символов)
   ```
2. Добавить 2 участников к сессии:
   ```
   POST http://localhost:8001/sessions/join
   Body: {"session_code": "<code>", "user_id": "user-002"}
   
   POST http://localhost:8001/sessions/join
   Body: {"session_code": "<code>", "user_id": "user-003"}
   ```
3. Получить список фильмов для сессии:
   ```
   GET http://localhost:8002/movies?session=<session_code>
   → Получить массив Movie объектов
   ```
4. Все участники голосуют "want_now" за первый фильм (movie_id=1):
   ```
   POST http://localhost:8000/swipe
   Body: {"session_id": <session_id>, "user_id": "user-001", "movie_id": 1, "swipe_value": "want_now", "participants": ["user-001", "user-002", "user-003"]}
   
   POST http://localhost:8000/swipe (user-002)
   POST http://localhost:8000/swipe (user-003)
   ```
5. Проверить результат матча после третьего голоса
6. Завершить сессию:
   ```
   POST http://localhost:8001/sessions/<session_code>/complete
   ```

**Ожидаемый результат**:
- Сессия создана, код получен (200 OK)
- Оба пользователя добавлены (200 OK, 200 OK)
- Получены фильмы из базы данных (200 OK)
- Первые два голоса: status="vote_recorded"
- Третий голос: status="match_found" с данными о фильме
- Сессия завершена, status="completed" (200 OK)
