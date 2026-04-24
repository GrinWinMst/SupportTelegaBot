from mcrcon import MCRcon
from config import RCON_HOST, RCON_PORT, RCON_PASSWORD
import logging

logger = logging.getLogger(__name__)


class RconManager:
    """Менеджер для работы с RCON сервера Minecraft"""
    
    @staticmethod
    async def execute_command(command: str) -> bool:
        """
        Выполнить команду на сервере через RCON
        
        Args:
            command: Команда для выполнения
            
        Returns:
            bool: True если команда выполнена успешно, False в противном случае
        """
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                response = mcr.command(command)
                logger.info(f"RCON command executed: {command} | Response: {response}")
                return True
        except Exception as e:
            logger.error(f"RCON error: {e}")
            return False
    
    @staticmethod
    async def give_reward(minecraft_nickname: str, command_template: str) -> bool:
        """
        Выдать награду игроку
        
        Args:
            minecraft_nickname: Ник игрока в Minecraft
            command_template: Шаблон команды с {nickname} (поддерживает несколько команд через ;)
            
        Returns:
            bool: True если награда выдана успешно
        """
        # Поддержка множественных команд разделенных точкой с запятой
        commands = [cmd.strip() for cmd in command_template.split(';') if cmd.strip()]
        
        for cmd_template in commands:
            command = cmd_template.format(nickname=minecraft_nickname)
            success = await RconManager.execute_command(command)
            if not success:
                logger.error(f"Failed to execute command: {command}")
                return False
        
        return True

