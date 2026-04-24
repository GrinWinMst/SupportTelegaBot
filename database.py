import aiosqlite
import datetime
from typing import Optional, List, Dict
from config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация базы данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    minecraft_nickname TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица ежедневных наград
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    minecraft_nickname TEXT NOT NULL,
                    reward_level INTEGER NOT NULL,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_claim_available TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица текущего прогресса наград
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reward_progress (
                    user_id INTEGER PRIMARY KEY,
                    minecraft_nickname TEXT NOT NULL,
                    current_level INTEGER DEFAULT 0,
                    next_claim_available TIMESTAMP,
                    last_claim_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица обращений в поддержку
            await db.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    ticket_type TEXT NOT NULL,
                    form_data TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    assigned_to INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    closed_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица сообщений в тикетах
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
                )
            """)
            
            # Таблица обязательных каналов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS required_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL UNIQUE,
                    channel_name TEXT NOT NULL,
                    channel_url TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    added_by INTEGER NOT NULL
                )
            """)
            
            # Таблица банов пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_bans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    banned_by INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ban_until TIMESTAMP,
                    is_permanent BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица последних сообщений (антиспам)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS last_messages (
                    user_id INTEGER PRIMARY KEY,
                    last_message_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица получения PvP-китов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pvp_kit_claims (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    minecraft_nickname TEXT NOT NULL,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    next_claim_available TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            
            # Таблица настроек бота
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                )
            """)
            
            await db.commit()

    # ===== User Management =====
    async def add_user(self, user_id: int, username: str = None):
        """Добавление пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()

    async def update_user_nickname(self, user_id: int, minecraft_nickname: str):
        """Обновление ника Minecraft"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET minecraft_nickname = ? WHERE user_id = ?",
                (minecraft_nickname, user_id)
            )
            await db.commit()

    # ===== Daily Rewards =====
    async def get_reward_progress(self, user_id: int) -> Optional[Dict]:
        """Получить прогресс наград пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM reward_progress WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def can_claim_reward(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Проверить, может ли пользователь забрать награду"""
        progress = await self.get_reward_progress(user_id)
        
        if not progress:
            return True, None  # Первая награда
        
        next_available = datetime.datetime.fromisoformat(progress['next_claim_available'])
        now = datetime.datetime.now()
        
        if now >= next_available:
            # Проверяем, не прошло ли больше 48 часов (сброс прогресса)
            if now > next_available + datetime.timedelta(hours=24):
                return True, "reset"  # Награда доступна, но прогресс сброшен
            return True, "continue"  # Награда доступна, прогресс продолжается
        else:
            return False, next_available.strftime("%d.%m.%Y %H:%M")

    async def claim_reward(self, user_id: int, minecraft_nickname: str) -> int:
        """Забрать награду"""
        can_claim, status = await self.can_claim_reward(user_id)
        
        if not can_claim:
            return -1  # Не может забрать
        
        progress = await self.get_reward_progress(user_id)
        
        # Определяем уровень награды
        if not progress or status == "reset":
            reward_level = 1
        else:
            reward_level = min(progress['current_level'] + 1, 7)
        
        now = datetime.datetime.now()
        next_available = now + datetime.timedelta(hours=24)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Записываем выдачу награды
            await db.execute(
                """INSERT INTO daily_rewards 
                   (user_id, minecraft_nickname, reward_level, claimed_at, next_claim_available)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, minecraft_nickname, reward_level, now, next_available)
            )
            
            # Обновляем прогресс
            await db.execute(
                """INSERT OR REPLACE INTO reward_progress 
                   (user_id, minecraft_nickname, current_level, next_claim_available, last_claim_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, minecraft_nickname, reward_level, next_available, now)
            )
            
            await db.commit()
        
        return reward_level

    async def get_reward_stats(self, period: str = "today") -> Dict:
        """Получить статистику наград за период"""
        now = datetime.datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - datetime.timedelta(days=7)
        elif period == "month":
            start_date = now - datetime.timedelta(days=30)
        else:  # all_time
            start_date = datetime.datetime(2000, 1, 1)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Общее количество наград
            async with db.execute(
                "SELECT COUNT(*) as total FROM daily_rewards WHERE claimed_at >= ?",
                (start_date,)
            ) as cursor:
                total = (await cursor.fetchone())['total']
            
            # Количество наград 7 уровня
            async with db.execute(
                "SELECT COUNT(*) as max_level FROM daily_rewards WHERE reward_level = 7 AND claimed_at >= ?",
                (start_date,)
            ) as cursor:
                max_level_count = (await cursor.fetchone())['max_level']
            
            # Список игроков с наградами
            async with db.execute(
                """SELECT u.username, dr.minecraft_nickname, dr.reward_level, dr.claimed_at
                   FROM daily_rewards dr
                   JOIN users u ON dr.user_id = u.user_id
                   WHERE dr.claimed_at >= ?
                   ORDER BY dr.reward_level DESC, dr.claimed_at DESC""",
                (start_date,)
            ) as cursor:
                rewards = [dict(row) async for row in cursor]
        
        return {
            "total": total,
            "max_level_count": max_level_count,
            "rewards": rewards
        }

    # ===== Support Tickets =====
    async def create_ticket(self, user_id: int, username: str, ticket_type: str, form_data: str) -> int:
        """Создать обращение в поддержку"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO support_tickets (user_id, username, ticket_type, form_data)
                   VALUES (?, ?, ?, ?)""",
                (user_id, username, ticket_type, form_data)
            )
            await db.commit()
            return cursor.lastrowid

    async def add_ticket_message(self, ticket_id: int, user_id: int, message: str):
        """Добавить сообщение в тикет"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO ticket_messages (ticket_id, user_id, message)
                   VALUES (?, ?, ?)""",
                (ticket_id, user_id, message)
            )
            await db.commit()

    async def get_open_tickets(self) -> List[Dict]:
        """Получить все открытые обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM support_tickets 
                   WHERE status = 'open' 
                   ORDER BY created_at DESC"""
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """Получить обращение по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM support_tickets WHERE id = ?",
                (ticket_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_ticket_messages(self, ticket_id: int) -> List[Dict]:
        """Получить все сообщения тикета"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT tm.*, u.username 
                   FROM ticket_messages tm
                   JOIN users u ON tm.user_id = u.user_id
                   WHERE ticket_id = ?
                   ORDER BY created_at ASC""",
                (ticket_id,)
            ) as cursor:
                return [dict(row) async for row in cursor]

    async def close_ticket(self, ticket_id: int, closed_by: int = None):
        """
        Закрыть обращение
        
        Args:
            ticket_id: ID обращения
            closed_by: ID пользователя, закрывшего обращение. 
                      Если None - обращение не будет учитываться в логах/статистике
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE support_tickets 
                   SET status = 'closed', closed_at = ?, closed_by = ?
                   WHERE id = ?""",
                (datetime.datetime.now(), closed_by, ticket_id)
            )
            await db.commit()

    async def get_user_active_ticket(self, user_id: int) -> Optional[int]:
        """Получить активный тикет пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """SELECT id FROM support_tickets 
                   WHERE user_id = ? AND status = 'open'
                   ORDER BY created_at DESC LIMIT 1""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return None
    
    async def get_user_tickets(self, user_id: int) -> List[Dict]:
        """Получить все тикеты пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM support_tickets 
                   WHERE user_id = ? 
                   ORDER BY created_at DESC""",
                (user_id,)
            ) as cursor:
                return [dict(row) async for row in cursor]
    
    async def assign_ticket(self, ticket_id: int, assigned_to: int):
        """Назначить обращение сотруднику"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE support_tickets SET assigned_to = ? WHERE id = ?",
                (assigned_to, ticket_id)
            )
            await db.commit()
    
    async def unassign_ticket(self, ticket_id: int):
        """Снять назначение с обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE support_tickets SET assigned_to = NULL WHERE id = ?",
                (ticket_id,)
            )
            await db.commit()
    
    # ===== Ticket Logs & Statistics =====
    async def get_closed_tickets(self, limit: int = 50) -> List[Dict]:
        """Получить закрытые обращения"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM support_tickets 
                   WHERE status = 'closed' 
                   ORDER BY closed_at DESC
                   LIMIT ?""",
                (limit,)
            ) as cursor:
                return [dict(row) async for row in cursor]
    
    async def get_all_tickets(self, limit: int = 50) -> List[Dict]:
        """Получить все обращения (открытые и закрытые)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM support_tickets 
                   ORDER BY created_at DESC
                   LIMIT ?""",
                (limit,)
            ) as cursor:
                return [dict(row) async for row in cursor]
    
    async def get_staff_statistics(self) -> Dict:
        """Получить статистику по сотрудникам"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT closed_by, COUNT(*) as closed_count
                   FROM support_tickets
                   WHERE status = 'closed' AND closed_by IS NOT NULL
                   GROUP BY closed_by
                   ORDER BY closed_count DESC"""
            ) as cursor:
                return [dict(row) async for row in cursor]
    
    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    async def delete_closed_tickets(self):
        """Удалить все закрытые обращения и их сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            # Сначала получаем ID закрытых тикетов
            async with db.execute(
                "SELECT id FROM support_tickets WHERE status = 'closed'"
            ) as cursor:
                ticket_ids = [row[0] async for row in cursor]
            
            # Удаляем сообщения из этих тикетов
            if ticket_ids:
                placeholders = ','.join('?' * len(ticket_ids))
                await db.execute(
                    f"DELETE FROM ticket_messages WHERE ticket_id IN ({placeholders})",
                    ticket_ids
                )
            
            # Удаляем сами тикеты
            await db.execute("DELETE FROM support_tickets WHERE status = 'closed'")
            await db.commit()
            return len(ticket_ids)
    
    async def delete_staff_tickets(self, staff_user_id: int):
        """Удалить все обращения конкретного сотрудника"""
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем ID тикетов этого сотрудника
            async with db.execute(
                "SELECT id FROM support_tickets WHERE closed_by = ?",
                (staff_user_id,)
            ) as cursor:
                ticket_ids = [row[0] async for row in cursor]
            
            # Удаляем сообщения
            if ticket_ids:
                placeholders = ','.join('?' * len(ticket_ids))
                await db.execute(
                    f"DELETE FROM ticket_messages WHERE ticket_id IN ({placeholders})",
                    ticket_ids
                )
            
            # Обнуляем closed_by в тикетах
            await db.execute(
                "UPDATE support_tickets SET closed_by = NULL WHERE closed_by = ?",
                (staff_user_id,)
            )
            await db.commit()
            return len(ticket_ids)
    
    async def delete_all_ticket_logs(self):
        """Удалить все логи (сообщения) из всех тикетов"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM ticket_messages")
            await db.execute("DELETE FROM support_tickets")
            await db.commit()
    
    # ===== Required Channels =====
    async def add_required_channel(self, channel_id: str, channel_name: str, channel_url: str, added_by: int):
        """Добавить обязательный канал"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO required_channels 
                   (channel_id, channel_name, channel_url, added_by)
                   VALUES (?, ?, ?, ?)""",
                (channel_id, channel_name, channel_url, added_by)
            )
            await db.commit()
    
    async def remove_required_channel(self, channel_id: str):
        """Удалить обязательный канал"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM required_channels WHERE channel_id = ?",
                (channel_id,)
            )
            await db.commit()
    
    async def get_required_channels(self) -> List[Dict]:
        """Получить все обязательные каналы"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM required_channels ORDER BY added_at ASC"
            ) as cursor:
                return [dict(row) async for row in cursor]
    
    async def get_all_user_ids(self) -> List[int]:
        """Получить все ID пользователей для рассылки"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT DISTINCT user_id FROM users"
            ) as cursor:
                return [row[0] async for row in cursor]
    
    # ===== Bans =====
    async def ban_user(self, user_id: int, banned_by: int, reason: str, ban_duration: Optional[int] = None):
        """
        Забанить пользователя
        
        Args:
            user_id: ID пользователя
            banned_by: Кто забанил
            reason: Причина бана
            ban_duration: Длительность в часах (None = навсегда)
        """
        async with aiosqlite.connect(self.db_path) as db:
            ban_until = None
            is_permanent = ban_duration is None
            
            if ban_duration is not None:
                ban_until = datetime.datetime.now() + datetime.timedelta(hours=ban_duration)
            
            await db.execute(
                """INSERT INTO user_bans 
                   (user_id, banned_by, reason, ban_until, is_permanent, is_active)
                   VALUES (?, ?, ?, ?, ?, 1)""",
                (user_id, banned_by, reason, ban_until, is_permanent)
            )
            await db.commit()
    
    async def unban_user(self, user_id: int):
        """Разбанить пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE user_bans SET is_active = 0 WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            await db.commit()
    
    async def is_user_banned(self, user_id: int) -> tuple[bool, Optional[Dict]]:
        """
        Проверить, забанен ли пользователь
        
        Returns:
            (bool, dict): (забанен ли, информация о бане)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM user_bans 
                   WHERE user_id = ? AND is_active = 1
                   ORDER BY banned_at DESC LIMIT 1""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False, None
                
                ban_info = dict(row)
                
                # Проверяем, не истек ли временный бан
                if not ban_info['is_permanent'] and ban_info['ban_until']:
                    ban_until = datetime.datetime.fromisoformat(ban_info['ban_until'])
                    if datetime.datetime.now() > ban_until:
                        # Бан истек, снимаем его
                        await self.unban_user(user_id)
                        return False, None
                
                return True, ban_info
    
    async def get_banned_users(self) -> List[Dict]:
        """Получить список всех забаненных пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT ub.*, u.username 
                   FROM user_bans ub
                   JOIN users u ON ub.user_id = u.user_id
                   WHERE ub.is_active = 1
                   ORDER BY ub.banned_at DESC"""
            ) as cursor:
                return [dict(row) async for row in cursor]
    
    # ===== Anti-spam =====
    async def check_spam(self, user_id: int, cooldown_seconds: int = 3) -> tuple[bool, Optional[float]]:
        """
        Проверить, может ли пользователь отправить сообщение (антиспам)
        
        Returns:
            (bool, float): (может ли отправить, сколько секунд осталось ждать)
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT last_message_at FROM last_messages WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    last_message = datetime.datetime.fromisoformat(row[0])
                    time_passed = (datetime.datetime.now() - last_message).total_seconds()
                    
                    if time_passed < cooldown_seconds:
                        return False, cooldown_seconds - time_passed
                
                return True, None
    
    async def update_last_message(self, user_id: int):
        """Обновить время последнего сообщения"""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.datetime.now().isoformat()
            await db.execute(
                """INSERT OR REPLACE INTO last_messages (user_id, last_message_at)
                   VALUES (?, ?)""",
                (user_id, now)
            )
            await db.commit()
    
    # ===== Progress Reset =====
    async def reset_reward_cooldown(self, user_id: int) -> bool:
        """
        Сбросить кулдаун награды (пользователь может забрать сразу)
        
        Returns:
            bool: True если успешно, False если прогресс не найден
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли прогресс
            async with db.execute(
                "SELECT * FROM reward_progress WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                if not await cursor.fetchone():
                    return False
            
            # Обнуляем next_claim_available (можно забирать сразу)
            await db.execute(
                """UPDATE reward_progress 
                   SET next_claim_available = ?
                   WHERE user_id = ?""",
                (datetime.datetime.now(), user_id)
            )
            await db.commit()
            return True
    
    async def get_user_by_telegram_username(self, telegram_username: str) -> Optional[Dict]:
        """Найти пользователя по telegram username (без @)"""
        # Убираем @ если есть
        username = telegram_username.lstrip('@')
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Ищем в таблице users
            async with db.execute(
                "SELECT * FROM users WHERE username = ? LIMIT 1",
                (username,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None
    
    # ===== PvP Kit Management =====
    async def can_claim_pvp_kit(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Проверить, может ли пользователь получить PvP-кит"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """SELECT * FROM pvp_kit_claims 
                   WHERE user_id = ? 
                   ORDER BY claimed_at DESC LIMIT 1""",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    return True, None  # Первый раз
                
                last_claim = dict(row)
                next_available = datetime.datetime.fromisoformat(last_claim['next_claim_available'])
                now = datetime.datetime.now()
                
                if now >= next_available:
                    return True, None
                else:
                    return False, next_available.strftime("%d.%m.%Y %H:%M")
    
    async def claim_pvp_kit(self, user_id: int, minecraft_nickname: str) -> bool:
        """Зарегистрировать получение PvP-кита"""
        can_claim, _ = await self.can_claim_pvp_kit(user_id)
        
        if not can_claim:
            return False
        
        now = datetime.datetime.now()
        next_available = now + datetime.timedelta(hours=24)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO pvp_kit_claims 
                   (user_id, minecraft_nickname, claimed_at, next_claim_available)
                   VALUES (?, ?, ?, ?)""",
                (user_id, minecraft_nickname, now, next_available)
            )
            await db.commit()
        
        return True
    
    async def get_pvp_kit_stats(self, period: str = "today") -> Dict:
        """Получить статистику PvP-китов за период"""
        now = datetime.datetime.now()
        
        if period == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - datetime.timedelta(days=7)
        elif period == "month":
            start_date = now - datetime.timedelta(days=30)
        else:  # all_time
            start_date = datetime.datetime(2000, 1, 1)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Общее количество выданных китов
            async with db.execute(
                "SELECT COUNT(*) as total FROM pvp_kit_claims WHERE claimed_at >= ?",
                (start_date,)
            ) as cursor:
                total = (await cursor.fetchone())['total']
            
            # Список игроков с китами
            async with db.execute(
                """SELECT u.username, pk.minecraft_nickname, pk.claimed_at
                   FROM pvp_kit_claims pk
                   JOIN users u ON pk.user_id = u.user_id
                   WHERE pk.claimed_at >= ?
                   ORDER BY pk.claimed_at DESC""",
                (start_date,)
            ) as cursor:
                claims = [dict(row) async for row in cursor]
        
        return {
            "total": total,
            "claims": claims
        }
    
    async def reset_pvp_kit_cooldown(self, user_id: int) -> bool:
        """Сбросить задержку PvP-кита для пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            # Проверяем, есть ли записи
            async with db.execute(
                "SELECT * FROM pvp_kit_claims WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                if not await cursor.fetchone():
                    return False
            
            # Обновляем последнюю запись, чтобы можно было получить сразу
            await db.execute(
                """UPDATE pvp_kit_claims 
                   SET next_claim_available = ?
                   WHERE user_id = ? AND id = (
                       SELECT id FROM pvp_kit_claims 
                       WHERE user_id = ? 
                       ORDER BY claimed_at DESC 
                       LIMIT 1
                   )""",
                (datetime.datetime.now(), user_id, user_id)
            )
            await db.commit()
            return True
    
    # ===== Bot Settings =====
    async def is_pvp_kit_enabled(self) -> bool:
        """Проверить, включена ли функция PvP-китов"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT setting_value FROM bot_settings WHERE setting_key = 'pvp_kit_enabled'",
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0].lower() == "true"
                return False  # По умолчанию выключено
    
    async def set_pvp_kit_enabled(self, enabled: bool, admin_id: int):
        """Включить/выключить функцию PvP-китов"""
        value = "true" if enabled else "false"
        now = datetime.datetime.now()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR REPLACE INTO bot_settings 
                   (setting_key, setting_value, updated_at, updated_by)
                   VALUES ('pvp_kit_enabled', ?, ?, ?)""",
                (value, now, admin_id)
            )
            await db.commit()
