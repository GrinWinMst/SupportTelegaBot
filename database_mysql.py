import aiomysql
import datetime
from typing import Optional, List, Dict
import os

# MySQL настройки из .env
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "thedawn_bot")


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Создать пул соединений с MySQL"""
        self.pool = await aiomysql.create_pool(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            db=MYSQL_DATABASE,
            autocommit=True,
            charset='utf8mb4'
        )

    async def close(self):
        """Закрыть пул соединений"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()

    async def init_db(self):
        """Инициализация базы данных"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Таблица пользователей
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id BIGINT PRIMARY KEY,
                        username VARCHAR(255),
                        minecraft_nickname VARCHAR(255),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица ежедневных наград
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_rewards (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        minecraft_nickname VARCHAR(255) NOT NULL,
                        reward_level INT NOT NULL,
                        claimed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        next_claim_available DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица текущего прогресса наград
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reward_progress (
                        user_id BIGINT PRIMARY KEY,
                        minecraft_nickname VARCHAR(255) NOT NULL,
                        current_level INT DEFAULT 0,
                        next_claim_available DATETIME,
                        last_claim_at DATETIME,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица обращений в поддержку
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        username VARCHAR(255),
                        ticket_type VARCHAR(255) NOT NULL,
                        form_data TEXT NOT NULL,
                        status VARCHAR(50) DEFAULT 'open',
                        assigned_to BIGINT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        closed_at DATETIME,
                        closed_by BIGINT,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица сообщений в тикетах
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ticket_messages (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ticket_id INT NOT NULL,
                        user_id BIGINT NOT NULL,
                        message TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (ticket_id) REFERENCES support_tickets(id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица обязательных каналов
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS required_channels (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        channel_id VARCHAR(255) NOT NULL UNIQUE,
                        channel_name VARCHAR(255) NOT NULL,
                        channel_url TEXT,
                        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        added_by BIGINT NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица банов пользователей
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_bans (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        banned_by BIGINT NOT NULL,
                        reason TEXT NOT NULL,
                        banned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        ban_until DATETIME,
                        is_permanent TINYINT(1) DEFAULT 0,
                        is_active TINYINT(1) DEFAULT 1,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица последних сообщений (антиспам)
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS last_messages (
                        user_id BIGINT PRIMARY KEY,
                        last_message_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица получения PvP-китов
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pvp_kit_claims (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        minecraft_nickname VARCHAR(255) NOT NULL,
                        claimed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        next_claim_available DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # Таблица настроек бота
                await cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bot_settings (
                        setting_key VARCHAR(255) PRIMARY KEY,
                        setting_value TEXT NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_by BIGINT
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

    # ===== User Management =====
    async def add_user(self, user_id: int, username: str = None):
        """Добавление пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "INSERT IGNORE INTO users (user_id, username) VALUES (%s, %s)",
                    (user_id, username)
                )

    async def update_user_nickname(self, user_id: int, minecraft_nickname: str):
        """Обновление ника Minecraft"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE users SET minecraft_nickname = %s WHERE user_id = %s",
                    (minecraft_nickname, user_id)
                )

    # ===== Daily Rewards =====
    async def get_reward_progress(self, user_id: int) -> Optional[Dict]:
        """Получить прогресс наград пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM reward_progress WHERE user_id = %s",
                    (user_id,)
                )
                return await cursor.fetchone()

    async def can_claim_reward(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Проверить, может ли пользователь забрать награду"""
        progress = await self.get_reward_progress(user_id)
        
        if not progress:
            return True, None  # Первая награда
        
        next_available = progress['next_claim_available']
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
            # После 7-го дня сбрасываем на 1-й
            reward_level = (progress['current_level'] % 7) + 1
        
        now = datetime.datetime.now()
        next_available = now + datetime.timedelta(hours=24)
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Записываем выдачу награды
                await cursor.execute(
                    """INSERT INTO daily_rewards 
                       (user_id, minecraft_nickname, reward_level, claimed_at, next_claim_available)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, minecraft_nickname, reward_level, now, next_available)
                )
                
                # Обновляем прогресс
                await cursor.execute(
                    """REPLACE INTO reward_progress 
                       (user_id, minecraft_nickname, current_level, next_claim_available, last_claim_at)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (user_id, minecraft_nickname, reward_level, next_available, now)
                )
        
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
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Общее количество наград
                await cursor.execute(
                    "SELECT COUNT(*) as total FROM daily_rewards WHERE claimed_at >= %s",
                    (start_date,)
                )
                total = (await cursor.fetchone())['total']
                
                # Количество наград 7 уровня
                await cursor.execute(
                    "SELECT COUNT(*) as max_level FROM daily_rewards WHERE reward_level = 7 AND claimed_at >= %s",
                    (start_date,)
                )
                max_level_count = (await cursor.fetchone())['max_level']
                
                # Список игроков с наградами
                await cursor.execute(
                    """SELECT u.username, dr.minecraft_nickname, dr.reward_level, dr.claimed_at
                       FROM daily_rewards dr
                       JOIN users u ON dr.user_id = u.user_id
                       WHERE dr.claimed_at >= %s
                       ORDER BY dr.reward_level DESC, dr.claimed_at DESC""",
                    (start_date,)
                )
                rewards = await cursor.fetchall()
        
        return {
            "total": total,
            "max_level_count": max_level_count,
            "rewards": rewards
        }

    # ===== Support Tickets =====
    async def create_ticket(self, user_id: int, username: str, ticket_type: str, form_data: str) -> int:
        """Создать обращение в поддержку"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """INSERT INTO support_tickets (user_id, username, ticket_type, form_data)
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, username, ticket_type, form_data)
                )
                return cursor.lastrowid

    async def add_ticket_message(self, ticket_id: int, user_id: int, message: str):
        """Добавить сообщение в тикет"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """INSERT INTO ticket_messages (ticket_id, user_id, message)
                       VALUES (%s, %s, %s)""",
                    (ticket_id, user_id, message)
                )

    async def get_open_tickets(self) -> List[Dict]:
        """Получить все открытые обращения"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT * FROM support_tickets 
                       WHERE status = 'open' 
                       ORDER BY created_at DESC"""
                )
                return await cursor.fetchall()

    async def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """Получить обращение по ID"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM support_tickets WHERE id = %s",
                    (ticket_id,)
                )
                return await cursor.fetchone()

    async def get_ticket_messages(self, ticket_id: int) -> List[Dict]:
        """Получить все сообщения тикета"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT tm.*, u.username 
                       FROM ticket_messages tm
                       JOIN users u ON tm.user_id = u.user_id
                       WHERE ticket_id = %s
                       ORDER BY created_at ASC""",
                    (ticket_id,)
                )
                return await cursor.fetchall()

    async def close_ticket(self, ticket_id: int, closed_by: int = None):
        """Закрыть обращение"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """UPDATE support_tickets 
                       SET status = 'closed', closed_at = %s, closed_by = %s
                       WHERE id = %s""",
                    (datetime.datetime.now(), closed_by, ticket_id)
                )

    async def get_user_active_ticket(self, user_id: int) -> Optional[int]:
        """Получить активный тикет пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """SELECT id FROM support_tickets 
                       WHERE user_id = %s AND status = 'open'
                       ORDER BY created_at DESC LIMIT 1""",
                    (user_id,)
                )
                row = await cursor.fetchone()
                return row[0] if row else None
    
    async def get_user_tickets(self, user_id: int) -> List[Dict]:
        """Получить все тикеты пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT * FROM support_tickets 
                       WHERE user_id = %s 
                       ORDER BY created_at DESC""",
                    (user_id,)
                )
                return await cursor.fetchall()
    
    async def assign_ticket(self, ticket_id: int, assigned_to: int):
        """Назначить обращение сотруднику"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE support_tickets SET assigned_to = %s WHERE id = %s",
                    (assigned_to, ticket_id)
                )
    
    async def unassign_ticket(self, ticket_id: int):
        """Снять назначение с обращения"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE support_tickets SET assigned_to = NULL WHERE id = %s",
                    (ticket_id,)
                )
    
    # ===== Ticket Logs & Statistics =====
    async def get_closed_tickets(self, limit: int = 50) -> List[Dict]:
        """Получить закрытые обращения"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT * FROM support_tickets 
                       WHERE status = 'closed' 
                       ORDER BY closed_at DESC
                       LIMIT %s""",
                    (limit,)
                )
                return await cursor.fetchall()
    
    async def get_all_tickets(self, limit: int = 50) -> List[Dict]:
        """Получить все обращения (открытые и закрытые)"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT * FROM support_tickets 
                       ORDER BY created_at DESC
                       LIMIT %s""",
                    (limit,)
                )
                return await cursor.fetchall()
    
    async def get_staff_statistics(self) -> Dict:
        """Получить статистику по сотрудникам"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT closed_by, COUNT(*) as closed_count
                       FROM support_tickets
                       WHERE status = 'closed' AND closed_by IS NOT NULL
                       GROUP BY closed_by
                       ORDER BY closed_count DESC"""
                )
                return await cursor.fetchall()
    
    async def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Получить информацию о пользователе по ID"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM users WHERE user_id = %s",
                    (user_id,)
                )
                return await cursor.fetchone()
    
    async def delete_closed_tickets(self):
        """Удалить все закрытые обращения и их сообщения"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Сначала получаем ID закрытых тикетов
                await cursor.execute("SELECT id FROM support_tickets WHERE status = 'closed'")
                ticket_ids = [row[0] for row in await cursor.fetchall()]
                
                # Удаляем сообщения из этих тикетов
                if ticket_ids:
                    placeholders = ','.join(['%s'] * len(ticket_ids))
                    await cursor.execute(
                        f"DELETE FROM ticket_messages WHERE ticket_id IN ({placeholders})",
                        ticket_ids
                    )
                
                # Удаляем сами тикеты
                await cursor.execute("DELETE FROM support_tickets WHERE status = 'closed'")
                return len(ticket_ids)
    
    async def delete_staff_tickets(self, staff_user_id: int):
        """Удалить все обращения конкретного сотрудника"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Получаем ID тикетов этого сотрудника
                await cursor.execute(
                    "SELECT id FROM support_tickets WHERE closed_by = %s",
                    (staff_user_id,)
                )
                ticket_ids = [row[0] for row in await cursor.fetchall()]
                
                # Удаляем сообщения
                if ticket_ids:
                    placeholders = ','.join(['%s'] * len(ticket_ids))
                    await cursor.execute(
                        f"DELETE FROM ticket_messages WHERE ticket_id IN ({placeholders})",
                        ticket_ids
                    )
                
                # Обнуляем closed_by в тикетах
                await cursor.execute(
                    "UPDATE support_tickets SET closed_by = NULL WHERE closed_by = %s",
                    (staff_user_id,)
                )
                return len(ticket_ids)
    
    async def delete_all_ticket_logs(self):
        """Удалить все логи (сообщения) из всех тикетов"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("DELETE FROM ticket_messages")
                await cursor.execute("DELETE FROM support_tickets")
    
    # ===== Required Channels =====
    async def add_required_channel(self, channel_id: str, channel_name: str, channel_url: str, added_by: int):
        """Добавить обязательный канал"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """REPLACE INTO required_channels 
                       (channel_id, channel_name, channel_url, added_by)
                       VALUES (%s, %s, %s, %s)""",
                    (channel_id, channel_name, channel_url, added_by)
                )
    
    async def remove_required_channel(self, channel_id: str):
        """Удалить обязательный канал"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "DELETE FROM required_channels WHERE channel_id = %s",
                    (channel_id,)
                )
    
    async def get_required_channels(self) -> List[Dict]:
        """Получить все обязательные каналы"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT * FROM required_channels ORDER BY added_at ASC")
                return await cursor.fetchall()
    
    async def get_all_user_ids(self) -> List[int]:
        """Получить все ID пользователей для рассылки"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT DISTINCT user_id FROM users")
                return [row[0] for row in await cursor.fetchall()]
    
    # ===== Bans =====
    async def ban_user(self, user_id: int, banned_by: int, reason: str, ban_duration: Optional[int] = None):
        """Забанить пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                ban_until = None
                is_permanent = ban_duration is None
                
                if ban_duration is not None:
                    ban_until = datetime.datetime.now() + datetime.timedelta(hours=ban_duration)
                
                await cursor.execute(
                    """INSERT INTO user_bans 
                       (user_id, banned_by, reason, ban_until, is_permanent, is_active)
                       VALUES (%s, %s, %s, %s, %s, 1)""",
                    (user_id, banned_by, reason, ban_until, is_permanent)
                )
    
    async def unban_user(self, user_id: int):
        """Разбанить пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "UPDATE user_bans SET is_active = 0 WHERE user_id = %s AND is_active = 1",
                    (user_id,)
                )
    
    async def is_user_banned(self, user_id: int) -> tuple[bool, Optional[Dict]]:
        """Проверить, забанен ли пользователь"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT * FROM user_bans 
                       WHERE user_id = %s AND is_active = 1
                       ORDER BY banned_at DESC LIMIT 1""",
                    (user_id,)
                )
                ban_info = await cursor.fetchone()
                
                if not ban_info:
                    return False, None
                
                # Проверяем, не истек ли временный бан
                if not ban_info['is_permanent'] and ban_info['ban_until']:
                    if datetime.datetime.now() > ban_info['ban_until']:
                        # Бан истек, снимаем его
                        await self.unban_user(user_id)
                        return False, None
                
                return True, ban_info
    
    async def get_banned_users(self) -> List[Dict]:
        """Получить список всех забаненных пользователей"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT ub.*, u.username 
                       FROM user_bans ub
                       JOIN users u ON ub.user_id = u.user_id
                       WHERE ub.is_active = 1
                       ORDER BY ub.banned_at DESC"""
                )
                return await cursor.fetchall()
    
    # ===== Anti-spam =====
    async def check_spam(self, user_id: int, cooldown_seconds: int = 3) -> tuple[bool, Optional[float]]:
        """Проверить, может ли пользователь отправить сообщение (антиспам)"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT last_message_at FROM last_messages WHERE user_id = %s",
                    (user_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    last_message = row[0]
                    time_passed = (datetime.datetime.now() - last_message).total_seconds()
                    
                    if time_passed < cooldown_seconds:
                        return False, cooldown_seconds - time_passed
                
                return True, None
    
    async def update_last_message(self, user_id: int):
        """Обновить время последнего сообщения"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                now = datetime.datetime.now()
                await cursor.execute(
                    """REPLACE INTO last_messages (user_id, last_message_at)
                       VALUES (%s, %s)""",
                    (user_id, now)
                )
    
    # ===== Progress Reset =====
    async def reset_reward_cooldown(self, user_id: int) -> bool:
        """Сбросить кулдаун награды (пользователь может забрать сразу)"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Проверяем, есть ли прогресс
                await cursor.execute(
                    "SELECT * FROM reward_progress WHERE user_id = %s",
                    (user_id,)
                )
                if not await cursor.fetchone():
                    return False
                
                # Обнуляем next_claim_available (можно забирать сразу)
                await cursor.execute(
                    """UPDATE reward_progress 
                       SET next_claim_available = %s
                       WHERE user_id = %s""",
                    (datetime.datetime.now(), user_id)
                )
                return True
    
    async def get_user_by_telegram_username(self, telegram_username: str) -> Optional[Dict]:
        """Найти пользователя по telegram username (без @)"""
        # Убираем @ если есть
        username = telegram_username.lstrip('@')
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    "SELECT * FROM users WHERE username = %s LIMIT 1",
                    (username,)
                )
                return await cursor.fetchone()
    
    # ===== PvP Kit Management =====
    async def can_claim_pvp_kit(self, user_id: int) -> tuple[bool, Optional[str]]:
        """Проверить, может ли пользователь получить PvP-кит"""
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(
                    """SELECT * FROM pvp_kit_claims 
                       WHERE user_id = %s 
                       ORDER BY claimed_at DESC LIMIT 1""",
                    (user_id,)
                )
                last_claim = await cursor.fetchone()
                
                if not last_claim:
                    return True, None  # Первый раз
                
                next_available = last_claim['next_claim_available']
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
        next_available = now + datetime.timedelta(hours=3)
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """INSERT INTO pvp_kit_claims 
                       (user_id, minecraft_nickname, claimed_at, next_claim_available)
                       VALUES (%s, %s, %s, %s)""",
                    (user_id, minecraft_nickname, now, next_available)
                )
        
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
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Общее количество выданных китов
                await cursor.execute(
                    "SELECT COUNT(*) as total FROM pvp_kit_claims WHERE claimed_at >= %s",
                    (start_date,)
                )
                total = (await cursor.fetchone())['total']
                
                # Список игроков с китами
                await cursor.execute(
                    """SELECT u.username, pk.minecraft_nickname, pk.claimed_at
                       FROM pvp_kit_claims pk
                       JOIN users u ON pk.user_id = u.user_id
                       WHERE pk.claimed_at >= %s
                       ORDER BY pk.claimed_at DESC""",
                    (start_date,)
                )
                claims = await cursor.fetchall()
        
        return {
            "total": total,
            "claims": claims
        }
    
    async def reset_pvp_kit_cooldown(self, user_id: int) -> bool:
        """Сбросить задержку PvP-кита для пользователя"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # Проверяем, есть ли записи
                await cursor.execute(
                    "SELECT COUNT(*) as count FROM pvp_kit_claims WHERE user_id = %s",
                    (user_id,)
                )
                result = await cursor.fetchone()
                if not result or result[0] == 0:
                    return False
                
                # Обновляем последнюю запись, чтобы можно было получить сразу
                await cursor.execute(
                    """UPDATE pvp_kit_claims 
                       SET next_claim_available = %s
                       WHERE user_id = %s 
                       ORDER BY claimed_at DESC 
                       LIMIT 1""",
                    (datetime.datetime.now(), user_id)
                )
                return True
    
    # ===== Bot Settings =====
    async def is_pvp_kit_enabled(self) -> bool:
        """Проверить, включена ли функция PvP-китов"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    "SELECT setting_value FROM bot_settings WHERE setting_key = 'pvp_kit_enabled'"
                )
                row = await cursor.fetchone()
                if row:
                    return row[0].lower() == "true"
                return False  # По умолчанию выключено
    
    async def set_pvp_kit_enabled(self, enabled: bool, admin_id: int):
        """Включить/выключить функцию PvP-китов"""
        value = "true" if enabled else "false"
        now = datetime.datetime.now()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(
                    """REPLACE INTO bot_settings 
                       (setting_key, setting_value, updated_at, updated_by)
                       VALUES ('pvp_kit_enabled', %s, %s, %s)""",
                    (value, now, admin_id)
                )
