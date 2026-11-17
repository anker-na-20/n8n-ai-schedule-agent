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
CREATE TABLE IF NOT EXISTS user_session (
    user_id BIGINT PRIMARY KEY,
    current_mode INT DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    period_type VARCHAR(10) CHECK (period_type IN ('year', 'month', 'week')),
    period_value VARCHAR(20) NOT NULL,
    text_content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_schedule_user_date ON schedule(user_id, event_date);
CREATE INDEX IF NOT EXISTS idx_goals_user_period ON goals(user_id, period_type, period_value);
"""

async def main():
    # Жестко прописываем те самые креды, по которым ты успешно зашел через GUI
    host = os.getenv("POSTGRES_HOST")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    port = int(os.getenv("POSTGRES_PORT"))



    if not all([host, user, password, database, port]):
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА БЕЗОПАСНОСТИ:")
        print("В файле .env отсутствуют обязательные переменные для подключения к БД!")
        print("Проверь, что заполнены: POSTGRES_HOST, USER, PASSWORD, DB, PORT.\n")
        return

    print(f"📡 Скрипт использует креды для Docker:")
    print(f"   Пользователь: {user}")
    print(f"   База данных: {database}")
    print(f"   Адрес: {host}:{port}\n")
    print(f"🔄 Пробуем подключиться напрямую...")

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
        print("🛠 Создаем таблицы в базе данных...")
        await conn.execute(SQL_SCHEMA)
        print("🎉 УСПЕХ: Структура таблиц полностью создана в ai_assistant_platform!")
        await conn.close()
    except Exception as e:
        print(f"❌ Ошибка прямого подключения: {e}")

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
