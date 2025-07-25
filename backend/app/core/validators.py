"""
Validators - Sistema de validação robusta para dados do sistema
"""

import re
import asyncio
from typing import List, Tuple, Optional, Dict, Any
from telegram import Bot
from telegram.error import TelegramError
import structlog

logger = structlog.get_logger(__name__)

class TelegramValidator:
    """Validadores para dados do Telegram"""
    
    @staticmethod
    def validate_bot_token_format(token: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato do token do bot Telegram
        
        Args:
            token: Token a ser validado
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not token or not isinstance(token, str):
            return False, "Token deve ser uma string não vazia"
        
        if len(token) < 40:
            return False, "Token muito curto"
        
        if len(token) > 50:
            return False, "Token muito longo"
        
        # Formato: 123456789:ABCDEF1234567890abcdef1234567890abcdef
        pattern = r'^\d{8,10}:[a-zA-Z0-9_-]{35}$'
        if not re.match(pattern, token):
            return False, "Formato de token inválido. Deve ser: 123456789:ABC..."
        
        return True, None
    
    @staticmethod
    async def validate_bot_token_api(token: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Valida token fazendo chamada à API do Telegram
        
        Args:
            token: Token a ser validado
            
        Returns:
            Tuple (is_valid, error_message, bot_info)
        """
        # Primeiro valida formato
        format_valid, format_error = TelegramValidator.validate_bot_token_format(token)
        if not format_valid:
            return False, format_error, None
        
        try:
            bot = Bot(token=token)
            me = await bot.get_me()
            
            bot_info = {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
                "supports_inline_queries": me.supports_inline_queries
            }
            
            logger.info(
                "Token validado com sucesso",
                bot_username=me.username,
                bot_id=me.id
            )
            
            return True, None, bot_info
            
        except TelegramError as e:
            error_msg = f"Token inválido: {str(e)}"
            logger.error("Erro na validação do token", error=str(e))
            return False, error_msg, None
            
        except Exception as e:
            error_msg = f"Erro inesperado na validação: {str(e)}"
            logger.error("Erro inesperado na validação", error=str(e))
            return False, error_msg, None
    
    @staticmethod
    def validate_chat_id_format(chat_id: str) -> Tuple[bool, Optional[str]]:
        """
        Valida formato do chat_id
        
        Args:
            chat_id: Chat ID a ser validado
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not chat_id or not isinstance(chat_id, str):
            return False, "Chat ID deve ser uma string não vazia"
        
        # Formato: -1001234567890 (grupos/canais) ou 123456789 (privado)
        pattern = r'^-?\d+$'
        if not re.match(pattern, chat_id):
            return False, "Chat ID deve conter apenas números e opcionalmente começar com -"
        
        chat_id_int = int(chat_id)
        
        # Validações específicas
        if chat_id_int == 0:
            return False, "Chat ID não pode ser 0"
        
        # Chat IDs de grupos/canais começam com -100
        if chat_id.startswith("-100"):
            if len(chat_id) < 10:
                return False, "Chat ID de grupo/canal muito curto"
        
        # Chat IDs privados são positivos
        elif chat_id_int > 0:
            if len(chat_id) < 5:
                return False, "Chat ID privado muito curto"
        
        return True, None
    
    @staticmethod
    async def validate_chat_access(token: str, chat_id: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Valida se o bot tem acesso ao chat
        
        Args:
            token: Token do bot
            chat_id: ID do chat
            
        Returns:
            Tuple (has_access, error_message, chat_info)
        """
        try:
            bot = Bot(token=token)
            chat = await bot.get_chat(chat_id=chat_id)
            
            chat_info = {
                "id": chat.id,
                "title": chat.title,
                "type": chat.type,
                "description": chat.description
            }
            
            logger.info(
                "Acesso ao chat validado",
                chat_id=chat_id,
                chat_title=chat.title,
                chat_type=chat.type
            )
            
            return True, None, chat_info
            
        except TelegramError as e:
            if "chat not found" in str(e).lower():
                return False, "Chat não encontrado ou bot não tem acesso", None
            elif "forbidden" in str(e).lower():
                return False, "Bot não tem permissão para acessar este chat", None
            else:
                return False, f"Erro do Telegram: {str(e)}", None
                
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}", None

class StrategyValidator:
    """Validadores para estratégias"""
    
    @staticmethod
    def validate_conditions(conditions: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Valida condições de uma estratégia
        
        Args:
            conditions: Lista de condições
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not conditions or not isinstance(conditions, list):
            return False, "Condições devem ser uma lista não vazia"
        
        if len(conditions) == 0:
            return False, "Estratégia deve ter pelo menos uma condição"
        
        if len(conditions) > 10:
            return False, "Estratégia não pode ter mais de 10 condições"
        
        # Valores válidos: cores (V, P, B), números (0-14), wildcard (X)
        valid_values = {"V", "P", "B", "X"} | {str(i) for i in range(15)}
        
        for i, condition in enumerate(conditions):
            if not isinstance(condition, str):
                return False, f"Condição {i+1} deve ser uma string"
            
            if condition not in valid_values:
                return False, f"Condição {i+1} inválida: '{condition}'. Valores válidos: V, P, B, X, 0-14"
        
        return True, None
    
    @staticmethod
    def validate_bet_direction(bet_direction: str) -> Tuple[bool, Optional[str]]:
        """
        Valida direção da aposta
        
        Args:
            bet_direction: Direção da aposta
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not bet_direction or not isinstance(bet_direction, str):
            return False, "Direção da aposta deve ser uma string não vazia"
        
        valid_directions = {"V", "P", "B"}
        if bet_direction not in valid_directions:
            return False, f"Direção inválida: '{bet_direction}'. Valores válidos: V (Vermelho), P (Preto), B (Branco)"
        
        return True, None
    
    @staticmethod
    def validate_strategy_logic(conditions: List[str], bet_direction: str) -> Tuple[bool, Optional[str]]:
        """
        Valida lógica da estratégia (análise semântica)
        
        Args:
            conditions: Lista de condições
            bet_direction: Direção da aposta
            
        Returns:
            Tuple (is_valid, error_message)
        """
        # Validar condições básicas
        conditions_valid, conditions_error = StrategyValidator.validate_conditions(conditions)
        if not conditions_valid:
            return False, conditions_error
        
        # Validar direção
        direction_valid, direction_error = StrategyValidator.validate_bet_direction(bet_direction)
        if not direction_valid:
            return False, direction_error
        
        # Análises semânticas
        
        # 1. Verificar se a última condição faz sentido com a aposta
        last_condition = conditions[-1]
        if last_condition == bet_direction:
            return False, "A última condição não pode ser igual à direção da aposta (seria redundante)"
        
        # 2. Verificar se não há muitos wildcards
        wildcard_count = conditions.count("X")
        if wildcard_count > len(conditions) // 2:
            return False, "Muitos wildcards (X) na estratégia. Use no máximo 50% de wildcards"
        
        # 3. Verificar se a estratégia não é muito específica (só números específicos)
        specific_numbers = [c for c in conditions if c.isdigit()]
        if len(specific_numbers) == len(conditions) and len(conditions) > 3:
            return False, "Estratégia muito específica (só números). Considere usar cores (V, P, B)"
        
        return True, None

class RoomValidator:
    """Validadores para salas de sinais"""
    
    @staticmethod
    def validate_room_config(name: str, 
                           bot_token: str, 
                           chat_id: str,
                           max_gales: int,
                           protection: bool) -> Tuple[bool, Optional[str]]:
        """
        Valida configuração completa de uma sala
        
        Args:
            name: Nome da sala
            bot_token: Token do bot
            chat_id: ID do chat
            max_gales: Máximo de gales
            protection: Se tem proteção no branco
            
        Returns:
            Tuple (is_valid, error_message)
        """
        # Validar nome
        if not name or not isinstance(name, str):
            return False, "Nome da sala é obrigatório"
        
        if len(name.strip()) < 3:
            return False, "Nome da sala deve ter pelo menos 3 caracteres"
        
        if len(name) > 100:
            return False, "Nome da sala não pode ter mais de 100 caracteres"
        
        # Validar token
        token_valid, token_error = TelegramValidator.validate_bot_token_format(bot_token)
        if not token_valid:
            return False, f"Token inválido: {token_error}"
        
        # Validar chat_id
        chat_valid, chat_error = TelegramValidator.validate_chat_id_format(chat_id)
        if not chat_valid:
            return False, f"Chat ID inválido: {chat_error}"
        
        # Validar max_gales
        if not isinstance(max_gales, int):
            return False, "Máximo de gales deve ser um número inteiro"
        
        if max_gales < 0:
            return False, "Máximo de gales não pode ser negativo"
        
        if max_gales > 5:
            return False, "Máximo de gales não pode ser maior que 5"
        
        # Validar protection
        if not isinstance(protection, bool):
            return False, "Proteção deve ser um valor booleano (true/false)"
        
        return True, None

class DataValidator:
    """Validadores genéricos para dados"""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Valida formato de email"""
        if not email or not isinstance(email, str):
            return False, "Email é obrigatório"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Formato de email inválido"
        
        if len(email) > 254:
            return False, "Email muito longo"
        
        return True, None
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """Valida força da senha"""
        if not password or not isinstance(password, str):
            return False, "Senha é obrigatória"
        
        if len(password) < 6:
            return False, "Senha deve ter pelo menos 6 caracteres"
        
        if len(password) > 128:
            return False, "Senha muito longa (máximo 128 caracteres)"
        
        # Verificar se tem pelo menos uma letra e um número
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not (has_letter and has_number):
            return False, "Senha deve conter pelo menos uma letra e um número"
        
        return True, None
    
    @staticmethod
    def validate_blaze_results(results: List[int]) -> Tuple[bool, Optional[str]]:
        """Valida resultados da Blaze"""
        if not results or not isinstance(results, list):
            return False, "Resultados devem ser uma lista não vazia"
        
        if len(results) == 0:
            return False, "Lista de resultados não pode estar vazia"
        
        for i, result in enumerate(results):
            if not isinstance(result, int):
                return False, f"Resultado {i+1} deve ser um número inteiro"
            
            if result < 0 or result > 14:
                return False, f"Resultado {i+1} inválido: {result}. Deve estar entre 0 e 14"
        
        return True, None

# Função helper para validação completa de sala
async def validate_complete_room(name: str, 
                               bot_token: str, 
                               chat_id: str,
                               max_gales: int,
                               protection: bool) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Validação completa de uma sala (formato + API)
    
    Returns:
        Tuple (is_valid, error_message, validation_info)
    """
    # Validar configuração básica
    config_valid, config_error = RoomValidator.validate_room_config(
        name, bot_token, chat_id, max_gales, protection
    )
    if not config_valid:
        return False, config_error, None
    
    # Validar token via API
    token_valid, token_error, bot_info = await TelegramValidator.validate_bot_token_api(bot_token)
    if not token_valid:
        return False, token_error, None
    
    # Validar acesso ao chat
    chat_valid, chat_error, chat_info = await TelegramValidator.validate_chat_access(bot_token, chat_id)
    if not chat_valid:
        return False, chat_error, None
    
    validation_info = {
        "bot_info": bot_info,
        "chat_info": chat_info
    }
    
    return True, None, validation_info 