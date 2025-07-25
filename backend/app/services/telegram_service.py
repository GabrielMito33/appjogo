"""
Telegram Service - Gerenciador de múltiplos bots Telegram
Sistema para enviar mensagens, stickers e gerenciar bots de diferentes salas
"""

import asyncio
from typing import Dict, Optional, List
import structlog
from telegram import Bot
from telegram.error import TelegramError, RetryAfter, TimeLimitExceeded
import re

logger = structlog.get_logger(__name__)

class TelegramBotManager:
    """Gerenciador principal de bots Telegram"""
    
    def __init__(self):
        self.bots: Dict[str, Bot] = {}  # Cache de bots por token
        self.rate_limits: Dict[str, float] = {}  # Rate limiting por bot
        self.failed_tokens: set = set()  # Tokens que falharam
        
    def get_bot(self, token: str) -> Optional[Bot]:
        """
        Retorna instância do bot (com cache)
        
        Args:
            token: Token do bot Telegram
            
        Returns:
            Instância do Bot ou None se inválido
        """
        # Verificar se token já falhou antes
        if token in self.failed_tokens:
            logger.warning("Token já marcado como inválido", token_prefix=token[:10])
            return None
        
        # Retornar do cache se existir
        if token in self.bots:
            return self.bots[token]
        
        # Validar formato do token
        if not self.validate_bot_token_format(token):
            logger.error("Formato de token inválido", token_prefix=token[:10])
            self.failed_tokens.add(token)
            return None
        
        try:
            # Criar nova instância
            bot = Bot(token=token)
            self.bots[token] = bot
            
            logger.info("Bot criado com sucesso", token_prefix=token[:10])
            return bot
            
        except Exception as e:
            logger.error("Erro ao criar bot", error=str(e), token_prefix=token[:10])
            self.failed_tokens.add(token)
            return None
    
    async def validate_bot_token(self, token: str) -> bool:
        """
        Valida se o token do bot é válido fazendo uma chamada à API
        
        Args:
            token: Token do bot
            
        Returns:
            True se válido
        """
        try:
            bot = self.get_bot(token)
            if bot is None:
                return False
            
            # Tentar fazer uma chamada simples
            me = await bot.get_me()
            logger.info(
                "Token validado com sucesso",
                bot_username=me.username,
                bot_name=me.first_name
            )
            return True
            
        except TelegramError as e:
            logger.error("Token inválido", error=str(e), token_prefix=token[:10])
            self.failed_tokens.add(token)
            return False
        except Exception as e:
            logger.error("Erro na validação do token", error=str(e), token_prefix=token[:10])
            return False
    
    async def send_message(self, 
                          token: str, 
                          chat_id: str, 
                          message: str,
                          parse_mode: str = "Markdown",
                          disable_web_page_preview: bool = True) -> bool:
        """
        Envia mensagem via bot
        
        Args:
            token: Token do bot
            chat_id: ID do chat/grupo
            message: Mensagem a ser enviada
            parse_mode: Modo de parse (Markdown, HTML)
            disable_web_page_preview: Desabilitar preview de links
            
        Returns:
            True se enviado com sucesso
        """
        bot = self.get_bot(token)
        if bot is None:
            return False
        
        try:
            # Verificar rate limiting
            if not self._check_rate_limit(token):
                logger.warning("Rate limit atingido", token_prefix=token[:10])
                await asyncio.sleep(1)
            
            # Enviar mensagem
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            
            logger.info(
                "Mensagem enviada com sucesso",
                chat_id=chat_id,
                message_length=len(message),
                token_prefix=token[:10]
            )
            
            self._update_rate_limit(token)
            return True
            
        except RetryAfter as e:
            logger.warning(
                "Rate limit do Telegram",
                retry_after=e.retry_after,
                token_prefix=token[:10]
            )
            # Aguardar e tentar novamente
            await asyncio.sleep(e.retry_after + 1)
            return await self.send_message(token, chat_id, message, parse_mode)
            
        except TelegramError as e:
            logger.error(
                "Erro do Telegram ao enviar mensagem",
                error=str(e),
                chat_id=chat_id,
                token_prefix=token[:10]
            )
            return False
            
        except Exception as e:
            logger.error(
                "Erro inesperado ao enviar mensagem",
                error=str(e),
                chat_id=chat_id,
                token_prefix=token[:10]
            )
            return False
    
    async def send_sticker(self, 
                          token: str, 
                          chat_id: str, 
                          sticker_id: str) -> bool:
        """
        Envia sticker via bot
        
        Args:
            token: Token do bot
            chat_id: ID do chat/grupo
            sticker_id: ID do sticker
            
        Returns:
            True se enviado com sucesso
        """
        bot = self.get_bot(token)
        if bot is None:
            return False
        
        try:
            await bot.send_sticker(
                chat_id=chat_id,
                sticker=sticker_id
            )
            
            logger.info(
                "Sticker enviado com sucesso",
                chat_id=chat_id,
                sticker_id=sticker_id,
                token_prefix=token[:10]
            )
            
            self._update_rate_limit(token)
            return True
            
        except TelegramError as e:
            logger.error(
                "Erro do Telegram ao enviar sticker",
                error=str(e),
                chat_id=chat_id,
                sticker_id=sticker_id,
                token_prefix=token[:10]
            )
            return False
            
        except Exception as e:
            logger.error(
                "Erro inesperado ao enviar sticker",
                error=str(e),
                chat_id=chat_id,
                sticker_id=sticker_id,
                token_prefix=token[:10]
            )
            return False
    
    async def delete_message(self, 
                           token: str, 
                           chat_id: str, 
                           message_id: int) -> bool:
        """
        Deleta mensagem
        
        Args:
            token: Token do bot
            chat_id: ID do chat
            message_id: ID da mensagem
            
        Returns:
            True se deletado com sucesso
        """
        bot = self.get_bot(token)
        if bot is None:
            return False
        
        try:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
            
            logger.info(
                "Mensagem deletada com sucesso",
                chat_id=chat_id,
                message_id=message_id,
                token_prefix=token[:10]
            )
            return True
            
        except TelegramError as e:
            logger.error(
                "Erro ao deletar mensagem",
                error=str(e),
                chat_id=chat_id,
                message_id=message_id,
                token_prefix=token[:10]
            )
            return False
    
    async def get_chat_info(self, token: str, chat_id: str) -> Optional[Dict]:
        """
        Obtém informações do chat
        
        Args:
            token: Token do bot
            chat_id: ID do chat
            
        Returns:
            Dict com informações do chat ou None
        """
        bot = self.get_bot(token)
        if bot is None:
            return None
        
        try:
            chat = await bot.get_chat(chat_id=chat_id)
            
            info = {
                "id": chat.id,
                "title": chat.title,
                "type": chat.type,
                "description": chat.description,
                "member_count": getattr(chat, 'member_count', None)
            }
            
            logger.info("Informações do chat obtidas", chat_info=info)
            return info
            
        except TelegramError as e:
            logger.error(
                "Erro ao obter informações do chat",
                error=str(e),
                chat_id=chat_id,
                token_prefix=token[:10]
            )
            return None
    
    def validate_bot_token_format(self, token: str) -> bool:
        """
        Valida formato do token (sem fazer chamada à API)
        
        Args:
            token: Token a ser validado
            
        Returns:
            True se formato válido
        """
        # Formato: 123456789:ABCDEF1234567890abcdef1234567890abcdef
        pattern = r'^\d{8,10}:[a-zA-Z0-9_-]{35}$'
        return bool(re.match(pattern, token))
    
    def validate_chat_id_format(self, chat_id: str) -> bool:
        """
        Valida formato do chat_id
        
        Args:
            chat_id: Chat ID a ser validado
            
        Returns:
            True se formato válido
        """
        # Formato: -1001234567890 (grupos) ou 123456789 (privado)
        pattern = r'^-?\d+$'
        return bool(re.match(pattern, chat_id))
    
    def _check_rate_limit(self, token: str) -> bool:
        """Verifica se pode enviar mensagem (rate limiting)"""
        import time
        now = time.time()
        last_sent = self.rate_limits.get(token, 0)
        
        # Limite: 1 mensagem por segundo
        if now - last_sent < 1.0:
            return False
        return True
    
    def _update_rate_limit(self, token: str):
        """Atualiza timestamp do último envio"""
        import time
        self.rate_limits[token] = time.time()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do manager"""
        return {
            "active_bots": len(self.bots),
            "failed_tokens": len(self.failed_tokens),
            "total_tokens_seen": len(self.bots) + len(self.failed_tokens)
        }
    
    def clear_failed_tokens(self):
        """Limpa cache de tokens que falharam (para retry)"""
        self.failed_tokens.clear()
        logger.info("Cache de tokens falhos limpo")

# Singleton instance
_telegram_manager_instance = None

def get_telegram_manager() -> TelegramBotManager:
    """Factory function para obter instância singleton"""
    global _telegram_manager_instance
    if _telegram_manager_instance is None:
        _telegram_manager_instance = TelegramBotManager()
    return _telegram_manager_instance 