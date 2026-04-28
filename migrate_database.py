"""
Скрипт миграции базы данных
Добавляет недостающие колонки в существующую базу данных
"""
import asyncio
import aiosqlite
from config import DATABASE_PATH

async def migrate_database():
    """Применить все миграции к базе данных"""
    print("🔄 Начало миграции базы данных...")
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Проверяем и добавляем колонки в таблицу support_tickets
        print("📋 Проверка таблицы support_tickets...")
        
        # Получаем список существующих колонок
        cursor = await db.execute("PRAGMA table_info(support_tickets)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Добавляем assigned_to если её нет
        if 'assigned_to' not in column_names:
            print("  ➕ Добавление колонки 'assigned_to'...")
            await db.execute("""
                ALTER TABLE support_tickets 
                ADD COLUMN assigned_to INTEGER
            """)
            print("  ✅ Колонка 'assigned_to' добавлена")
        else:
            print("  ✓ Колонка 'assigned_to' уже существует")
        
        # Добавляем closed_by если её нет
        if 'closed_by' not in column_names:
            print("  ➕ Добавление колонки 'closed_by'...")
            await db.execute("""
                ALTER TABLE support_tickets 
                ADD COLUMN closed_by INTEGER
            """)
            print("  ✅ Колонка 'closed_by' добавлена")
        else:
            print("  ✓ Колонка 'closed_by' уже существует")
        
        await db.commit()
    
    print("✅ Миграция завершена успешно!\n")
    print("Теперь можете запустить бота командой: run_bot.bat")

if __name__ == "__main__":
    asyncio.run(migrate_database())


