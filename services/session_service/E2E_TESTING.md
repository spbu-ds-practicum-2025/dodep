# E2E Тестирование Session Service

Этот документ описывает e2e тесты для Session Service в соответствии с планом из `docs/e2e-testing-plan.md`.

## Структура тестов

Тесты расположены в файле `tests/test_e2e.py` и покрывают следующие сценарии:

### Часть 1: Управление сессиями

#### TestSessionCreation
- ✅ **test_create_session_success** - Проверка успешного создания новой сессии
  - Проверяет генерацию уникального кода (6 символов)
  - Проверяет структуру ответа согласно e2e плану
  - Проверяет, что создатель добавлен как первый участник

- ✅ **test_create_session_unique_codes** - Проверка уникальности кодов сессий

#### TestSessionJoin  
- ✅ **test_join_session_success** - Проверка успешного подключения к сессии
  - Проверяет добавление нового участника
  - Проверяет обновление списка участников

- ✅ **test_join_nonexistent_session** - Ошибка при подключении к несуществующей сессии (404)

- ✅ **test_join_completed_session** - Ошибка при подключении к завершённой сессии (400)

- ✅ **test_rejoin_existing_user** - Проверка переподключения отключённого пользователя

#### TestSessionCompletion
- ✅ **test_complete_session_success** - Проверка завершения сессии
  - Проверяет изменение статуса на "completed"

- ✅ **test_complete_nonexistent_session** - Ошибка при завершении несуществующей сессии (404)

- ✅ **test_get_completed_session** - Проверка получения завершённой сессии

#### TestSessionRetrieval
- ✅ **test_get_session_by_code** - Получение сессии по коду
- ✅ **test_validate_session** - Валидация сессии и получение деталей

#### TestMultipleParticipants
- ✅ **test_session_with_three_participants** - Проверка сессии с 3 участниками
- ✅ **test_disconnect_and_check_participants** - Проверка отключения участника

#### TestUpdateCurrentMovie
- ✅ **test_update_current_movie** - Обновление текущего фильма
- ✅ **test_update_current_movie_nonexistent_session** - Ошибка при обновлении в несуществующей сессии
- ✅ **test_update_current_movie_multiple_times** - Проверка множественного обновления

#### TestSessionHealthCheck
- ✅ **test_health_check** - Проверка health check эндпоинта

## Запуск тестов

### Установка зависимостей
```bash
cd /workspaces/dodep/services/session_service
pip install -r requirements.txt
```

### Запуск всех тестов
```bash
python -m pytest tests/test_e2e.py -v
```

### Запуск конкретного тестового класса
```bash
python -m pytest tests/test_e2e.py::TestSessionCreation -v
```

### Запуск конкретного теста
```bash
python -m pytest tests/test_e2e.py::TestSessionCreation::test_create_session_success -v
```

### Запуск с подробным выводом
```bash
python -m pytest tests/test_e2e.py -vv
```

## Результаты тестирования

Все 17 тестов успешно проходят ✅

```
============================= test session starts ==============================
tests/test_e2e.py::TestSessionCreation::test_create_session_success PASSED
tests/test_e2e.py::TestSessionCreation::test_create_session_unique_codes PASSED
tests/test_e2e.py::TestSessionJoin::test_join_session_success PASSED
tests/test_e2e.py::TestSessionJoin::test_join_nonexistent_session PASSED
tests/test_e2e.py::TestSessionJoin::test_join_completed_session PASSED
tests/test_e2e.py::TestSessionJoin::test_rejoin_existing_user PASSED
tests/test_e2e.py::TestSessionCompletion::test_complete_session_success PASSED
tests/test_e2e.py::TestSessionCompletion::test_complete_nonexistent_session PASSED
tests/test_e2e.py::TestSessionCompletion::test_get_completed_session PASSED
tests/test_e2e.py::TestSessionRetrieval::test_get_session_by_code PASSED
tests/test_e2e.py::TestSessionRetrieval::test_validate_session PASSED
tests/test_e2e.py::TestMultipleParticipants::test_session_with_three_participants PASSED
tests/test_e2e.py::TestMultipleParticipants::test_disconnect_and_check_participants PASSED
tests/test_e2e.py::TestUpdateCurrentMovie::test_update_current_movie PASSED
tests/test_e2e.py::TestUpdateCurrentMovie::test_update_current_movie_nonexistent_session PASSED
tests/test_e2e.py::TestUpdateCurrentMovie::test_update_current_movie_multiple_times PASSED
tests/test_e2e.py::TestSessionHealthCheck::test_health_check PASSED

======================= 17 passed in 1.19s ========================
```

## Отображение покрытия тестами требований e2e плана

### Часть 1: Сценарии управления сессиями ✅

| Тест | Статус | Примечание |
|------|--------|-----------|
| 1.1.1 Успешное создание новой сессии | ✅ | Полностью реализовано |
| 1.1.2 Подключение пользователя к сессии | ✅ | Полностью реализовано |
| 1.1.3 Завершение сессии | ✅ | Полностью реализовано |

## Эндпоинты Session Service

### Создание сессии
```
POST /sessions/create
Body: {"creator_id": "user-001"}
Response: {session_id, session_code, creator_id, status, current_movie_id, participants, created_at}
```

### Подключение к сессии
```
POST /sessions/join
Body: {"session_code": "ABC123", "user_id": "user-002"}
Response: {session_id, session_code, creator_id, status, current_movie_id, participants, created_at}
```

### Получение сессии
```
GET /sessions/{session_code}
Response: {session_id, session_code, creator_id, status, current_movie_id, participants, created_at}
```

### Валидация сессии
```
GET /sessions/{session_code}/validate
Response: {is_valid, session_id, status, participants, current_movie_id}
```

### Обновление текущего фильма
```
PUT /sessions/{session_code}/movie
Body: {"current_movie_id": 1}
Response: {session_id, session_code, creator_id, status, current_movie_id, participants, created_at}
```

### Отключение пользователя
```
POST /sessions/{session_code}/disconnect/{user_id}
Response: {status, session_code, user_id}
```

### Завершение сессии
```
POST /sessions/{session_code}/complete
Response: {status, session_code}
```

### Health check
```
GET /health
Response: {status: "ok"}
```

## Примечания

- Все тесты используют SQLite in-memory базу данных для изоляции
- Тесты автоматически создают и удаляют таблицы перед и после выполнения
- Сессионные коды генерируются как 6-символьные буквенно-цифровые строки
- Все временные метки используют UTC
