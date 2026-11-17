import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

# Загружаем переменные из .env в корне проекта
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SQL_SCHEMA = """
-- 1. Сессии пользователей (Конечный автомат режимов ИИ и визарда)
CREATE TABLE IF NOT EXISTS user_session (
    user_id BIGINT PRIMARY KEY,
    current_mode INT DEFAULT 1,
    pending_task_id INT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Долгосрочные и краткосрочные цели
CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    period_type VARCHAR(10) CHECK (period_type IN ('year', 'month', 'week')),
    period_value VARCHAR(20) NOT NULL,
    text_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_goals_user FOREIGN KEY (user_id) REFERENCES user_session(user_id) ON DELETE CASCADE
);

-- 3. Оперативное расписание, задачи и точечные замены
CREATE TABLE IF NOT EXISTS schedule (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    event_date DATE NOT NULL,
    time_start TIME NULL,          
    time_end TIME NULL,
    item_type VARCHAR(20) CHECK (item_type IN ('university', 'task', 'note')),
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    is_important BOOLEAN DEFAULT FALSE,
    is_notified BOOLEAN DEFAULT FALSE,
    is_completed BOOLEAN DEFAULT FALSE,
    is_reviewed_today BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_schedule_user FOREIGN KEY (user_id) REFERENCES user_session(user_id) ON DELETE CASCADE
);

-- 4. Регулярное циклическое расписание (базовая сетка недели)
CREATE TABLE IF NOT EXISTS regular_schedule (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
    time_start TIME NOT NULL,
    time_end TIME NULL,
    item_type VARCHAR(20) DEFAULT 'university' CHECK (item_type IN ('university', 'task', 'note')),
    title VARCHAR(255) NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_regular_user FOREIGN KEY (user_id) REFERENCES user_session(user_id) ON DELETE CASCADE
);

-- 5. История диалогов для контекста первой LLM-модели
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    mode_context INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES user_session(user_id) ON DELETE CASCADE
);

-- Индексы для ускорения выборок n8n
CREATE INDEX IF NOT EXISTS idx_schedule_user_date ON schedule(user_id, event_date);
CREATE INDEX IF NOT EXISTS idx_schedule_notify ON schedule(event_date, is_important, is_notified) WHERE is_important = TRUE AND is_notified = FALSE;
CREATE INDEX IF NOT EXISTS idx_regular_user_day ON regular_schedule(user_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_goals_user_period ON goals(user_id, period_type, period_value);
CREATE INDEX IF NOT EXISTS idx_chat_history_user ON ai_chat_history(user_id, created_at DESC);
"""

async def main():
    host = os.getenv("POSTGRES_HOST")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    port_raw = os.getenv("POSTGRES_PORT")

    if not all([host, user, password, database, port_raw]):
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА БЕЗОПАСНОСТИ:")
        print("В файле .env отсутствуют обязательные переменные для подключения к БД!")
        print("Проверь, что заполнены: POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT.\n")
        return

    port = int(port_raw)

    print("📡 Скрипт использует креды из .env:")
    print(f"   Пользователь: {user}")
    print(f"   База данных: {database}")
    print(f"   Адрес: {host}:{port}\n")
    print("🔄 Пробуем подключиться к PostgreSQL...")

    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port,
            timeout=5
        )
        print("✅ Соединение УСТАНОВЛЕНО!")
        print("🛠 Создаем и обновляем структуру таблиц...")
        await conn.execute(SQL_SCHEMA)
        print(f"🎉 УСПЕХ: Все 5 таблиц и индексы готовы к работе в базе '{database}'!")
        await conn.close()
    except Exception as e:
        print(f"❌ Ошибка подключения или выполнения SQL: {e}")

if __name__ == "__main__":
    asyncio.run(main())
