# 🤖 Telegram Support Bot

Профессиональный бот для службы поддержки с продвинутой системой тикетов, автоматическим распределением обращений и многоязычной поддержкой.

## ✨ Основные возможности

### Для пользователей:
- 🌍 **Многоязычная поддержка**: Русский, Английский, Испанский, Украинский
- 🎫 **Система тикетов**: Создание обращений с автоматической нумерацией
- 💬 **История общения**: Полное сохранение всех сообщений
- 📊 **Отслеживание статуса**: Открыт → В обработке → Ожидает ответа → Закрыт
- ⚡ **Быстрые ответы**: Мгновенные уведомления при ответе менеджера
- 📱 **Удобный интерфейс**: Интуитивные кнопки и команды

### Для менеджеров:
- 🎯 **Автоматическое распределение**: Случайное назначение тикетов доступным менеджерам
- 📋 **Панель управления**: Удобный интерфейс для работы с обращениями
- 🔔 **Уведомления**: Мгновенные оповещения о новых тикетах
- ⏱️ **Автозакрытие**: Автоматическое закрытие неактивных тикетов (настраивается)
- 📈 **Статистика**: Просмотр всех активных и закрытых обращений
- 🔄 **Множественная обработка**: Работа с несколькими тикетами одновременно

## 🛠 Технологический стек

- **Python 3.13** - современная версия Python
- **aiogram 3.15** - мощный асинхронный фреймворк для Telegram Bot API
- **PostgreSQL 16** - надежная реляционная база данных
- **Redis 7** - быстрое хранилище FSM состояний
- **SQLAlchemy 2.0** - современная асинхронная ORM
- **Alembic** - система миграций базы данных
- **APScheduler** - планировщик задач для автозакрытия тикетов
- **Docker & Docker Compose** - контейнеризация и оркестрация
- **pgAdmin 4** - веб-интерфейс для управления PostgreSQL

## 📋 Требования

- Docker (версия 20.10+)
- Docker Compose (версия 2.0+)
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))


## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd telegram-support-bot
```

### 2. Создание Telegram бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям и получите **Bot Token**
4. Узнайте свой Telegram ID у [@userinfobot](https://t.me/userinfobot)

### 3. Настройка переменных окружения

Скопируйте файл-пример и отредактируйте его:

```bash
cp .env.example .env
```

Откройте `.env` и заполните необходимые данные:

```env
# Обязательные параметры
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz  # Ваш токен от BotFather
ADMIN_IDS=123456789,987654321                    # Ваш Telegram ID (можно несколько через запятую)

# База данных (можно оставить по умолчанию)
POSTGRES_PASSWORD=your_secure_password_here      # Придумайте надежный пароль

# Остальные параметры можно оставить как есть
```

### 4. Запуск приложения

Запустите все сервисы одной командой:

```bash
docker-compose up -d
```

Дождитесь загрузки и запуска контейнеров (обычно 30-60 секунд).

### 5. Применение миграций базы данных

После первого запуска выполните миграции:

```bash
docker-compose exec bot alembic upgrade head
```

### 6. Готово! 🎉

Ваш бот запущен и готов к работе! Найдите его в Telegram и отправьте `/start`.

## 📱 Использование бота

### Для пользователей игры

**Первый запуск:**
1. Найдите вашего бота в Telegram
2. Нажмите `Start` или отправьте `/start`
3. Выберите предпочитаемый язык 🌐
4. Готово! Можно создавать обращения

**Создание обращения:**
1. В главном меню нажмите **📝 Создать обращение**
2. Опишите вашу проблему или вопрос
3. Дождитесь ответа менеджера (вы получите уведомление)
4. Продолжайте диалог в том же тикете

**Доступные команды:**
- `/start` - Главное меню и справка
- **📝 Создать обращение** - Новый тикет в поддержку
- **📋 Мои обращения** - Список ваших активных тикетов
- **🌐 Изменить язык** - Сменить язык интерфейса

### Для менеджеров поддержки

**Получение доступа:**
1. Убедитесь, что ваш Telegram ID добавлен в переменную `ADMIN_IDS` в `.env`
2. Перезапустите бота: `docker-compose restart bot`
3. Используйте команду `/manager` для доступа к панели менеджера

**Работа с тикетами:**
1. Новые тикеты автоматически распределяются между доступными менеджерами
2. Вы получите уведомление о новом тикете
3. Нажмите **📋 Активные тикеты** для просмотра обращений
4. Выберите тикет и отвечайте на сообщения пользователя
5. Закройте тикет кнопкой **✅ Закрыть тикет** после решения проблемы

**Панель менеджера:**
- **📋 Активные тикеты** - Все открытые обращения
- **🆕 Новые тикеты** - Нераспределенные обращения
- **📊 Статистика** - Общая информация (планируется)

## 🔧 Управление сервисами

### Основные команды Docker Compose

```bash
# Запуск всех сервисов
docker-compose up -d

# Остановка всех сервисов
docker-compose down

# Перезапуск бота
docker-compose restart bot

# Просмотр логов всех сервисов
docker-compose logs -f

# Просмотр логов только бота
docker-compose logs -f bot

# Пересборка и запуск (после изменения кода)
docker-compose up -d --build

# Полная очистка (удаление данных БД!)
docker-compose down -v
```

### Работа с базой данных

```bash
# Применить миграции
docker-compose exec bot alembic upgrade head

# Откатить последнюю миграцию
docker-compose exec bot alembic downgrade -1

# Посмотреть текущую версию БД
docker-compose exec bot alembic current

# Создать новую миграцию
docker-compose exec bot alembic revision --autogenerate -m "описание изменений"
```

## 🗄️ Управление базой данных через pgAdmin

pgAdmin предоставляет удобный веб-интерфейс для работы с PostgreSQL.

**Доступ к pgAdmin:**
1. Откройте в браузере: http://localhost:5050
2. Войдите с учетными данными из `.env`:
   - Email: значение из `PGADMIN_EMAIL` (по умолчанию: admin@admin.com)
   - Password: значение из `PGADMIN_PASSWORD` (по умолчанию: admin)

**Добавление сервера PostgreSQL:**
1. Правый клик на **Servers** → **Register** → **Server**
2. Вкладка **General**:
   - Name: `Support Bot DB` (любое имя)
3. Вкладка **Connection**:
   - Host: `postgres`
   - Port: `5432`
   - Database: значение из `POSTGRES_DB` (по умолчанию: `support_bot`)
   - Username: значение из `POSTGRES_USER` (по умолчанию: `postgres`)
   - Password: значение из `POSTGRES_PASSWORD`
   - ✅ Save password
4. Нажмите **Save**

Теперь вы можете:
- Просматривать таблицы и данные
- Выполнять SQL запросы
- Экспортировать/импортировать данные
- Создавать бэкапы
- Мониторить активность

## 📁 Структура проекта

```
telegram-support-bot/
├── 📄 main.py                      # Точка входа приложения
├── 📄 requirements.txt             # Python зависимости
├── 📄 Dockerfile                   # Конфигурация Docker образа
├── 📄 docker-compose.yml           # Оркестрация сервисов
├── 📄 alembic.ini                  # Конфигурация Alembic
├── 📄 .env.example                 # Пример переменных окружения
├── 📄 .env                         # Ваши переменные окружения (не в git)
├── 📄 README.md                    # Документация
│
├── 📂 bot/                         # Основной код бота
│   ├── 📄 config.py                # Конфигурация и настройки
│   │
│   ├── 📂 database/                # Работа с базой данных
│   │   ├── 📄 database.py          # Инициализация подключения
│   │   ├── 📄 models.py            # SQLAlchemy модели (User, Manager, Ticket, Message)
│   │   └── 📄 repositories.py      # Репозитории для работы с данными
│   │
│   ├── 📂 handlers/                # Обработчики событий бота
│   │   ├── 📄 user_handlers.py     # Обработчики для обычных пользователей
│   │   └── 📄 manager_handlers.py  # Обработчики для менеджеров
│   │
│   ├── 📂 keyboards/               # Клавиатуры Telegram
│   │   └── 📄 keyboards.py         # Генераторы клавиатур
│   │
│   ├── 📂 locales/                 # Файлы переводов
│   │   ├── 📄 ru.json              # Русский 🇷🇺
│   │   ├── 📄 en.json              # English 🇬🇧
│   │   ├── 📄 es.json              # Español 🇪🇸
│   │   └── 📄 uk.json              # Українська 🇺🇦
│   │
│   ├── 📂 middlewares/             # Middleware слой
│   │   └── 📄 db_middleware.py     # Middleware для сессий БД
│   │
│   ├── 📂 states/                  # FSM состояния
│   │   └── 📄 states.py            # Определение состояний диалога
│   │
│   └── 📂 utils/                   # Утилиты и хелперы
│       ├── 📄 i18n.py              # Система интернационализации
│       ├── 📄 notifications.py     # Отправка уведомлений
│       └── 📄 scheduler.py         # Планировщик задач
│
├── 📂 alembic/                     # Миграции базы данных
│   ├── 📄 env.py                   # Конфигурация окружения Alembic
│   └── 📂 versions/                # Файлы миграций
│       └── 📄 001_initial_migration.py
│
└── 📂 logs/                        # Логи приложения (создается автоматически)
```

## 🗂️ База данных

### Схема таблиц

**users** - Пользователи бота
```sql
- id (BigInteger, PK) - Telegram ID пользователя
- username (String) - Telegram username
- first_name (String) - Имя
- language (String) - Выбранный язык
- created_at (DateTime) - Дата регистрации
- updated_at (DateTime) - Последнее обновление
```

**managers** - Менеджеры поддержки
```sql
- id (BigInteger, PK) - Telegram ID менеджера
- username (String) - Telegram username
- first_name (String) - Имя
- is_active (Boolean) - Доступен ли для назначения тикетов
- created_at (DateTime) - Дата добавления
```

**tickets** - Тикеты обращений
```sql
- id (Integer, PK) - ID тикета
- user_id (BigInteger, FK) - ID пользователя
- manager_id (BigInteger, FK, nullable) - ID назначенного менеджера
- subject (Text) - Тема обращения
- status (String) - Статус: open, in_progress, waiting_user, closed
- created_at (DateTime) - Дата создания
- updated_at (DateTime) - Последнее обновление
- closed_at (DateTime, nullable) - Дата закрытия
```

**messages** - Сообщения в тикетах
```sql
- id (Integer, PK) - ID сообщения
- ticket_id (Integer, FK) - ID тикета
- sender_id (BigInteger) - ID отправителя
- sender_type (String) - Тип отправителя: user или manager
- message_text (Text) - Текст сообщения
- created_at (DateTime) - Дата отправки
```

### Связи между таблицами
- User → Tickets (1:N)
- Manager → Tickets (1:N)
- Ticket → Messages (1:N)

## ⚙️ Конфигурация

### Переменные окружения

Полный список переменных с описанием доступен в `.env.example`.

**Обязательные:**
- `BOT_TOKEN` - токен Telegram бота
- `ADMIN_IDS` - ID менеджеров через запятую
- `POSTGRES_PASSWORD` - пароль для PostgreSQL

**Опциональные:**
- `DEFAULT_LANGUAGE` - язык по умолчанию (ru)
- `MAX_ACTIVE_TICKETS_PER_USER` - лимит тикетов на пользователя (3)
- `AUTO_CLOSE_TIMEOUT` - таймаут автозакрытия в минутах (60)
- `LOG_LEVEL` - уровень логирования (INFO)

### Добавление нового языка

1. Создайте файл `bot/locales/язык.json` (например, `fr.json`)
2. Скопируйте структуру из существующего файла
3. Переведите все ключи на новый язык
4. Добавьте код языка в `SUPPORTED_LANGUAGES` в `.env`
5. Перезапустите бота

Пример структуры перевода:
```json
{
  "start_message": "Привет! Я бот поддержки.",
  "choose_language": "Выберите язык",
  "create_ticket": "📝 Создать обращение",
  ...
}
```

## 🔍 Мониторинг и отладка

### Просмотр логов

```bash
# Логи всех сервисов
docker-compose logs -f

# Только бот
docker-compose logs -f bot

# Только PostgreSQL
docker-compose logs -f postgres

# Только Redis
docker-compose logs -f redis

# Последние 100 строк
docker-compose logs --tail=100 bot
```

### Проверка статуса сервисов

```bash
# Статус всех контейнеров
docker-compose ps

# Проверка PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Проверка Redis
docker-compose exec redis redis-cli ping

# Вход в контейнер бота
docker-compose exec bot /bin/bash
```

### Резервное копирование

**Бэкап базы данных:**
```bash
# Создать бэкап
docker-compose exec postgres pg_dump -U postgres support_bot > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из бэкапа
docker-compose exec -T postgres psql -U postgres support_bot < backup_20240115_120000.sql
```

**Через pgAdmin:**
1. Правый клик на базе данных
2. Backup... → укажите параметры
3. Для восстановления: Restore... → выберите файл

## 🐛 Решение проблем

### Бот не запускается

```bash
# Проверьте корректность .env файла
cat .env

# Проверьте логи бота
docker-compose logs bot

# Убедитесь, что все контейнеры запущены
docker-compose ps

# Пересоберите контейнер
docker-compose up -d --build bot
```

### Ошибки подключения к БД

```bash
# Проверьте, что PostgreSQL готов
docker-compose exec postgres pg_isready

# Проверьте текущую версию миграций
docker-compose exec bot alembic current

# Попробуйте применить миграции снова
docker-compose exec bot alembic upgrade head

# Если не помогает - пересоздайте БД (ВНИМАНИЕ: удалит все данные!)
docker-compose down -v
docker-compose up -d
docker-compose exec bot alembic upgrade head
```

### Бот не отвечает на команды

1. Проверьте, что бот запущен: `docker-compose ps`
2. Убедитесь, что токен бота корректный в `.env`
3. Проверьте логи: `docker-compose logs -f bot`
4. Перезапустите бота: `docker-compose restart bot`

### Проблемы с Redis/FSM

```bash
# Проверьте Redis
docker-compose exec redis redis-cli ping

# Очистите Redis (сбросит все состояния FSM)
docker-compose exec redis redis-cli FLUSHALL

# Перезапустите Redis
docker-compose restart redis
```

## 🔐 Безопасность

### Рекомендации

- ✅ **НЕ коммитьте** файл `.env` в репозиторий
- ✅ Используйте **сильные пароли** для PostgreSQL
- ✅ Регулярно **обновляйте зависимости**: `pip list --outdated`
- ✅ Ограничьте доступ к **портам** (5432, 6379, 5050) на продакшене
- ✅ Используйте **HTTPS** для веб-интерфейсов
- ✅ Регулярно создавайте **бэкапы** базы данных
- ✅ Мониторьте **логи** на подозрительную активность

### Рекомендуемый .gitignore

```gitignore
.env
__pycache__/
*.pyc
*.pyo
logs/
*.sql
postgres_data/
redis_data/
pgadmin_data/
```

## 🚀 Деплой на продакшен

### Рекомендации для продакшена

1. **Используйте внешние сервисы БД** (например, Managed PostgreSQL)
2. **Настройте SSL/TLS** для всех соединений
3. **Ограничьте сетевой доступ** (firewall, security groups)
4. **Настройте автоматические бэкапы**
5. **Используйте secrets management** (Docker Secrets, Vault)
6. **Настройте мониторинг** (Prometheus, Grafana)
7. **Добавьте алерты** на критические ошибки
8. **Используйте reverse proxy** (nginx) с rate limiting

### Пример nginx конфигурации

```nginx
server {
    listen 80;
    server_name pgadmin.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
