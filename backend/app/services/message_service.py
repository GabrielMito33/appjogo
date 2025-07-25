"""
Message Service - Sistema de templates de mensagens personalizáveis
Processa templates com variáveis dinâmicas e stickers
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import structlog
from datetime import datetime

from app.models.signal_room import SignalRoom
from app.models.strategy import Strategy, BetDirection
from app.models.message_template import MessageTemplate, MessageType
from app.models.user import User

logger = structlog.get_logger(__name__)

class MessageTemplateService:
    """Serviço para processamento de templates de mensagens"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def render_signal_template(self, 
                             room: SignalRoom, 
                             strategy: Strategy,
                             custom_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Renderiza template de mensagem de sinal
        
        Args:
            room: Sala de sinais
            strategy: Estratégia que gerou o sinal
            custom_vars: Variáveis customizadas adicionais
            
        Returns:
            Dict com message, sticker_id e variables
        """
        # Buscar template específico da sala ou template padrão do usuário
        template = self._get_template(room.id, room.user_id, MessageType.SIGNAL)
        
        # Preparar variáveis para substituição
        variables = self._prepare_signal_variables(room, strategy, custom_vars)
        
        # Renderizar template
        message = self._render_template(template.template, variables)
        
        logger.info(
            "Template de sinal renderizado",
            room_id=room.id,
            strategy_id=strategy.id,
            template_id=template.id,
            message_length=len(message)
        )
        
        return {
            "message": message,
            "sticker_id": template.sticker_id,
            "variables": variables,
            "template_id": template.id
        }
    
    def render_alert_template(self, 
                            room: SignalRoom, 
                            strategy: Strategy,
                            next_condition: str) -> Dict[str, Any]:
        """
        Renderiza template de mensagem de alerta
        
        Args:
            room: Sala de sinais
            strategy: Estratégia próxima de dar sinal
            next_condition: Próxima condição esperada
            
        Returns:
            Dict com message, sticker_id e variables
        """
        template = self._get_template(room.id, room.user_id, MessageType.ALERT)
        
        variables = self._prepare_alert_variables(room, strategy, next_condition)
        message = self._render_template(template.template, variables)
        
        logger.info(
            "Template de alerta renderizado",
            room_id=room.id,
            strategy_id=strategy.id,
            next_condition=next_condition
        )
        
        return {
            "message": message,
            "sticker_id": template.sticker_id,
            "variables": variables,
            "template_id": template.id
        }
    
    def render_gale_template(self, 
                           room: SignalRoom, 
                           gale_number: int) -> Dict[str, Any]:
        """
        Renderiza template de mensagem de gale
        
        Args:
            room: Sala de sinais
            gale_number: Número do gale (1, 2, etc.)
            
        Returns:
            Dict com message, sticker_id e variables
        """
        template = self._get_template(room.id, room.user_id, MessageType.GALE)
        
        variables = self._prepare_gale_variables(room, gale_number)
        message = self._render_template(template.template, variables)
        
        logger.info(
            "Template de gale renderizado",
            room_id=room.id,
            gale_number=gale_number
        )
        
        return {
            "message": message,
            "sticker_id": template.sticker_id,
            "variables": variables,
            "template_id": template.id
        }
    
    def render_result_template(self, 
                             room: SignalRoom, 
                             result_type: str,
                             winning_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Renderiza template de resultado (win/loss/white)
        
        Args:
            room: Sala de sinais
            result_type: 'win', 'loss', ou 'white'
            winning_number: Número que saiu na Blaze
            
        Returns:
            Dict com message, sticker_id e variables
        """
        message_type = {
            'win': MessageType.WIN,
            'loss': MessageType.LOSS,
            'white': MessageType.WHITE
        }.get(result_type, MessageType.WIN)
        
        template = self._get_template(room.id, room.user_id, message_type)
        
        variables = self._prepare_result_variables(room, result_type, winning_number)
        message = self._render_template(template.template, variables)
        
        logger.info(
            "Template de resultado renderizado",
            room_id=room.id,
            result_type=result_type,
            winning_number=winning_number
        )
        
        return {
            "message": message,
            "sticker_id": template.sticker_id,
            "variables": variables,
            "template_id": template.id
        }
    
    def render_statistics_template(self, room: SignalRoom) -> Dict[str, Any]:
        """
        Renderiza template de estatísticas/placar
        
        Args:
            room: Sala de sinais
            
        Returns:
            Dict com message, sticker_id e variables
        """
        template = self._get_template(room.id, room.user_id, MessageType.RESULTS)
        
        variables = self._prepare_statistics_variables(room)
        message = self._render_template(template.template, variables)
        
        logger.info(
            "Template de estatísticas renderizado",
            room_id=room.id,
            wins=room.wins,
            losses=room.losses
        )
        
        return {
            "message": message,
            "sticker_id": template.sticker_id,
            "variables": variables,
            "template_id": template.id
        }
    
    def _get_template(self, room_id: int, user_id: int, message_type: MessageType) -> MessageTemplate:
        """Busca template específico ou retorna template padrão"""
        
        # Tentar buscar template específico da sala
        template = self.db.query(MessageTemplate).filter(
            MessageTemplate.room_id == room_id,
            MessageTemplate.type == message_type,
            MessageTemplate.is_active == True
        ).first()
        
        # Se não encontrar, buscar template global do usuário
        if not template:
            template = self.db.query(MessageTemplate).filter(
                MessageTemplate.user_id == user_id,
                MessageTemplate.room_id == None,  # Template global
                MessageTemplate.type == message_type,
                MessageTemplate.is_active == True
            ).first()
        
        # Se ainda não encontrar, criar template padrão
        if not template:
            template = self._create_default_template(user_id, message_type)
            
        return template
    
    def _create_default_template(self, user_id: int, message_type: MessageType) -> MessageTemplate:
        """Cria template padrão baseado no tipo"""
        
        default_templates = {
            MessageType.SIGNAL: {
                "template": """🎲 - Modo: Double Blaze
🎰 - Entrada será para: {bet_color}
💰 - Com proteção no: ⚪️
♻️ - Utilize até o Gale: {max_gales}""",
                "sticker_id": None
            },
            MessageType.ALERT: {
                "template": "⚠️ ANALISANDO, FIQUE ATENTO!!!",
                "sticker_id": None
            },
            MessageType.GALE: {
                "template": "⚠️ Vamos para o {gale_number}ª GALE",
                "sticker_id": None
            },
            MessageType.WIN: {
                "template": "✅ WIN! Parabéns!",
                "sticker_id": "CAACAgEAAxkBAAMPZrqPFR0VdwEGmMIhUvD-ftVCU9IAAm8CAAIhWPBGBpXDpqXsW8Q1BA"
            },
            MessageType.LOSS: {
                "template": "❌ LOSS! Próxima será GREEN!",
                "sticker_id": "CAACAgEAAxkBAAMTZrqPNtuE01MlUnK6yF68sSO6lc0AAsQCAAIEQehG-NlOMcjRGTM1BA"
            },
            MessageType.WHITE: {
                "template": "⚪️ BRANCO! Proteção ativada!",
                "sticker_id": "CAACAgEAAxkBAAMRZrqPJkaflJxOqn_wTYTupKMtpDkAAjYCAAJMK-lGHp_XWq_MVE01BA"
            },
            MessageType.RESULTS: {
                "template": """
► PLACAR = ✅{wins} | ⚪️{brancos} | 🚫{losses} 
► Consecutivas = {consecutive_wins}
► Assertividade = {assertiveness}""",
                "sticker_id": None
            }
        }
        
        default = default_templates.get(message_type)
        if not default:
            default = {"template": "Mensagem padrão", "sticker_id": None}
        
        # Criar template no banco
        template = MessageTemplate(
            user_id=user_id,
            room_id=None,  # Template global
            type=message_type,
            name=f"Template Padrão - {message_type.value}",
            template=default["template"],
            sticker_id=default["sticker_id"],
            is_active=True,
            is_default=True
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        logger.info(
            "Template padrão criado",
            user_id=user_id,
            message_type=message_type,
            template_id=template.id
        )
        
        return template
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Renderiza template substituindo variáveis"""
        try:
            return template.format(**variables)
        except KeyError as e:
            logger.warning(
                "Variável não encontrada no template",
                missing_variable=str(e),
                available_variables=list(variables.keys())
            )
            # Retornar template sem substituição em caso de erro
            return template
        except Exception as e:
            logger.error("Erro ao renderizar template", error=str(e))
            return template
    
    def _prepare_signal_variables(self, 
                                room: SignalRoom, 
                                strategy: Strategy,
                                custom_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepara variáveis para template de sinal"""
        
        bet_color_emoji = self._get_bet_color_emoji(strategy.bet_direction)
        bet_color_name = self._get_bet_color_name(strategy.bet_direction)
        
        variables = {
            # Informações da sala
            "room_name": room.name,
            "max_gales": room.max_gales,
            "protection": "SIM" if room.protection else "NÃO",
            
            # Informações da estratégia
            "strategy_name": strategy.name,
            "bet_direction": strategy.bet_direction.value,
            "bet_color": bet_color_emoji,
            "bet_color_name": bet_color_name,
            "conditions": " - ".join(strategy.conditions),
            
            # Estatísticas
            "total_signals": room.total_signals,
            "wins": room.wins,
            "losses": room.losses,
            "brancos": room.brancos,
            "assertiveness": self._calculate_assertiveness(room),
            
            # Data/hora
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "datetime": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        # Adicionar variáveis customizadas
        if custom_vars:
            variables.update(custom_vars)
            
        return variables
    
    def _prepare_alert_variables(self, 
                               room: SignalRoom, 
                               strategy: Strategy,
                               next_condition: str) -> Dict[str, Any]:
        """Prepara variáveis para template de alerta"""
        return {
            "room_name": room.name,
            "strategy_name": strategy.name,
            "next_condition": next_condition,
            "conditions_so_far": " - ".join(strategy.conditions[:-1]),
            "time": datetime.now().strftime("%H:%M:%S")
        }
    
    def _prepare_gale_variables(self, room: SignalRoom, gale_number: int) -> Dict[str, Any]:
        """Prepara variáveis para template de gale"""
        return {
            "room_name": room.name,
            "gale_number": gale_number,
            "max_gales": room.max_gales,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    
    def _prepare_result_variables(self, 
                                room: SignalRoom, 
                                result_type: str,
                                winning_number: Optional[int] = None) -> Dict[str, Any]:
        """Prepara variáveis para template de resultado"""
        
        winning_color = ""
        if winning_number is not None:
            if 1 <= winning_number <= 7:
                winning_color = "🔴 Vermelho"
            elif 8 <= winning_number <= 14:
                winning_color = "⚫️ Preto"
            else:
                winning_color = "⚪️ Branco"
        
        return {
            "room_name": room.name,
            "result_type": result_type.upper(),
            "winning_number": winning_number,
            "winning_color": winning_color,
            "time": datetime.now().strftime("%H:%M:%S")
        }
    
    def _prepare_statistics_variables(self, room: SignalRoom) -> Dict[str, Any]:
        """Prepara variáveis para template de estatísticas"""
        
        # Calcular consecutivas (mock - implementar lógica real depois)
        consecutive_wins = 0  # TODO: Implementar cálculo real
        
        return {
            "room_name": room.name,
            "wins": room.wins,
            "losses": room.losses,
            "brancos": room.brancos,
            "total_signals": room.total_signals,
            "consecutive_wins": consecutive_wins,
            "assertiveness": self._calculate_assertiveness(room),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "time": datetime.now().strftime("%H:%M:%S")
        }
    
    def _get_bet_color_emoji(self, bet_direction: BetDirection) -> str:
        """Converte direção da aposta para emoji"""
        mapping = {
            BetDirection.RED: "🔴",
            BetDirection.BLACK: "⚫️", 
            BetDirection.WHITE: "⚪️"
        }
        return mapping.get(bet_direction, "❓")
    
    def _get_bet_color_name(self, bet_direction: BetDirection) -> str:
        """Converte direção da aposta para nome"""
        mapping = {
            BetDirection.RED: "Vermelho",
            BetDirection.BLACK: "Preto",
            BetDirection.WHITE: "Branco"
        }
        return mapping.get(bet_direction, "Desconhecido")
    
    def _calculate_assertiveness(self, room: SignalRoom) -> str:
        """Calcula assertividade da sala"""
        total = room.wins + room.losses + room.brancos
        if total == 0:
            return "0.00%"
        
        success = room.wins + room.brancos  # Wins + brancos (proteção)
        assertiveness = (success / total) * 100
        return f"{assertiveness:.2f}%"

# Factory function
def get_message_service(db: Session) -> MessageTemplateService:
    """Factory function para criar instância do serviço"""
    return MessageTemplateService(db) 