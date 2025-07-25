"""
Signal Orchestrator - Orquestrador principal do sistema de sinais
Integra todos os serviços (Strategy Engine, Blaze Monitor, Telegram, Templates)
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import structlog
from datetime import datetime

from app.models.signal_room import SignalRoom
from app.models.strategy import Strategy
from app.models.result_history import ResultHistory, ResultType, BetColor
from app.services.strategy_engine import StrategyEngine, get_strategy_engine
from app.services.blaze_monitor import BlazeMonitor, get_blaze_monitor
from app.services.telegram_service import TelegramBotManager, get_telegram_manager
from app.services.message_service import MessageTemplateService, get_message_service
from app.database import get_db

logger = structlog.get_logger(__name__)

class SignalOrchestrator:
    """Orquestrador principal para processamento de sinais"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.strategy_engine = get_strategy_engine(db_session)
        self.blaze_monitor = get_blaze_monitor()
        self.telegram_manager = get_telegram_manager()
        self.message_service = get_message_service(db_session)
        
        # Estado interno
        self.active_rooms: List[SignalRoom] = []
        self.pending_signals: Dict[int, Dict] = {}  # room_id -> signal_data
        self.gale_states: Dict[int, Dict] = {}      # room_id -> gale_state
        
        logger.info("SignalOrchestrator inicializado")
    
    async def process_blaze_results(self, results: List[int]) -> Dict[str, Any]:
        """
        Processa novos resultados da Blaze para todas as salas ativas
        
        Args:
            results: Lista de números da Blaze (mais recente primeiro)
            
        Returns:
            Dict com estatísticas do processamento
        """
        start_time = datetime.now()
        
        logger.info(
            "Processando novos resultados da Blaze",
            results_count=len(results),
            latest_result=results[0] if results else None
        )
        
        # Buscar salas ativas
        self.active_rooms = self._get_active_rooms()
        
        stats = {
            "rooms_processed": 0,
            "signals_sent": 0,
            "alerts_sent": 0,
            "errors": 0,
            "gales_processed": 0
        }
        
        # Processar cada sala
        for room in self.active_rooms:
            try:
                room_stats = await self._process_room_results(room, results)
                
                # Agregar estatísticas
                stats["rooms_processed"] += 1
                stats["signals_sent"] += room_stats.get("signals_sent", 0)
                stats["alerts_sent"] += room_stats.get("alerts_sent", 0)
                stats["gales_processed"] += room_stats.get("gales_processed", 0)
                
            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    "Erro ao processar sala",
                    room_id=room.id,
                    room_name=room.name,
                    error=str(e)
                )
        
        # Verificar resultados de gales pendentes
        await self._check_pending_gales(results[0] if results else None)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            "Processamento de resultados concluído",
            processing_time=processing_time,
            stats=stats
        )
        
        return stats
    
    async def _process_room_results(self, room: SignalRoom, results: List[int]) -> Dict[str, Any]:
        """Processa resultados para uma sala específica"""
        
        logger.debug(
            "Processando sala",
            room_id=room.id,
            room_name=room.name,
            strategies_count=len(room.strategies)
        )
        
        room_stats = {
            "signals_sent": 0,
            "alerts_sent": 0,
            "gales_processed": 0
        }
        
        # Verificar se há gale ativo para esta sala
        if room.id in self.gale_states:
            gale_result = await self._process_gale_result(room, results[0])
            if gale_result:
                room_stats["gales_processed"] = 1
                return room_stats
        
        # Processar estratégias da sala
        strategy_results = self.strategy_engine.process_room_strategies(room, results)
        
        # Processar sinais encontrados
        for strategy in strategy_results["signals"]:
            success = await self._send_signal(room, strategy)
            if success:
                room_stats["signals_sent"] += 1
        
        # Processar alertas encontrados
        for strategy in strategy_results["alerts"]:
            success = await self._send_alert(room, strategy)
            if success:
                room_stats["alerts_sent"] += 1
        
        return room_stats
    
    async def _send_signal(self, room: SignalRoom, strategy: Strategy) -> bool:
        """Envia sinal para uma sala"""
        
        logger.info(
            "Enviando sinal",
            room_id=room.id,
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            bet_direction=strategy.bet_direction
        )
        
        try:
            # Renderizar template de mensagem
            template_data = self.message_service.render_signal_template(room, strategy)
            
            # Enviar sticker primeiro (se configurado)
            if template_data["sticker_id"]:
                sticker_sent = await self.telegram_manager.send_sticker(
                    token=room.bot_token,
                    chat_id=room.chat_id,
                    sticker_id=template_data["sticker_id"]
                )
                if not sticker_sent:
                    logger.warning("Falha ao enviar sticker", room_id=room.id)
            
            # Enviar mensagem
            message_sent = await self.telegram_manager.send_message(
                token=room.bot_token,
                chat_id=room.chat_id,
                message=template_data["message"]
            )
            
            if message_sent:
                # Registrar sinal no histórico
                await self._save_signal_history(room.id, strategy.id, "signal")
                
                # Atualizar estatísticas da sala
                room.total_signals += 1
                self.db.commit()
                
                # Registrar estado para monitorar gales
                self.pending_signals[room.id] = {
                    "strategy": strategy,
                    "timestamp": datetime.now(),
                    "bet_direction": strategy.bet_direction,
                    "gale_count": 0
                }
                
                logger.info("Sinal enviado com sucesso", room_id=room.id, strategy_id=strategy.id)
                return True
            else:
                logger.error("Falha ao enviar mensagem de sinal", room_id=room.id)
                return False
                
        except Exception as e:
            logger.error(
                "Erro ao enviar sinal",
                room_id=room.id,
                strategy_id=strategy.id,
                error=str(e)
            )
            return False
    
    async def _send_alert(self, room: SignalRoom, strategy: Strategy) -> bool:
        """Envia alerta para uma sala"""
        
        logger.info(
            "Enviando alerta",
            room_id=room.id,
            strategy_id=strategy.id,
            strategy_name=strategy.name
        )
        
        try:
            # Próxima condição esperada
            next_condition = strategy.conditions[-1]
            
            # Renderizar template de alerta
            template_data = self.message_service.render_alert_template(
                room, strategy, next_condition
            )
            
            # Enviar mensagem
            message_sent = await self.telegram_manager.send_message(
                token=room.bot_token,
                chat_id=room.chat_id,
                message=template_data["message"]
            )
            
            if message_sent:
                logger.info("Alerta enviado com sucesso", room_id=room.id, strategy_id=strategy.id)
                return True
            else:
                logger.error("Falha ao enviar alerta", room_id=room.id)
                return False
                
        except Exception as e:
            logger.error(
                "Erro ao enviar alerta",
                room_id=room.id,
                strategy_id=strategy.id,
                error=str(e)
            )
            return False
    
    async def _process_gale_result(self, room: SignalRoom, result: int) -> bool:
        """Processa resultado quando há gale ativo"""
        
        if room.id not in self.gale_states:
            return False
        
        gale_state = self.gale_states[room.id]
        bet_direction = gale_state["bet_direction"]
        gale_count = gale_state["gale_count"]
        
        # Converter resultado para cor
        result_color = self._number_to_color(result)
        
        # Verificar se ganhou
        won = self._check_win_condition(bet_direction, result_color, room.protection)
        
        logger.info(
            "Processando resultado de gale",
            room_id=room.id,
            result=result,
            result_color=result_color,
            bet_direction=bet_direction,
            gale_count=gale_count,
            won=won
        )
        
        if won:
            # WIN ou BRANCO (proteção)
            result_type = "white" if result_color == "B" else "win"
            await self._send_result_message(room, result_type, result)
            
            # Atualizar estatísticas
            if result_type == "win":
                room.wins += 1
            else:
                room.brancos += 1
            
            # Limpar estado de gale
            del self.gale_states[room.id]
            
        else:
            # LOSS - verificar se deve ir para próximo gale
            if gale_count < room.max_gales:
                # Ir para próximo gale
                self.gale_states[room.id]["gale_count"] += 1
                await self._send_gale_message(room, gale_count + 1)
            else:
                # LOSS final
                await self._send_result_message(room, "loss", result)
                room.losses += 1
                del self.gale_states[room.id]
        
        self.db.commit()
        return True
    
    async def _check_pending_gales(self, latest_result: Optional[int]):
        """Verifica sinais pendentes que podem ter resultado"""
        
        if latest_result is None:
            return
        
        # Implementar lógica para verificar se algum sinal pendente teve resultado
        # Isso requer lógica mais complexa de timing e controle de estado
        pass
    
    async def _send_result_message(self, room: SignalRoom, result_type: str, winning_number: int):
        """Envia mensagem de resultado (win/loss/white)"""
        
        template_data = self.message_service.render_result_template(
            room, result_type, winning_number
        )
        
        # Enviar sticker primeiro
        if template_data["sticker_id"]:
            await self.telegram_manager.send_sticker(
                token=room.bot_token,
                chat_id=room.chat_id,
                sticker_id=template_data["sticker_id"]
            )
        
        # Enviar mensagem
        await self.telegram_manager.send_message(
            token=room.bot_token,
            chat_id=room.chat_id,
            message=template_data["message"]
        )
        
        logger.info(
            "Mensagem de resultado enviada",
            room_id=room.id,
            result_type=result_type,
            winning_number=winning_number
        )
    
    async def _send_gale_message(self, room: SignalRoom, gale_number: int):
        """Envia mensagem de gale"""
        
        template_data = self.message_service.render_gale_template(room, gale_number)
        
        await self.telegram_manager.send_message(
            token=room.bot_token,
            chat_id=room.chat_id,
            message=template_data["message"]
        )
        
        logger.info(
            "Mensagem de gale enviada",
            room_id=room.id,
            gale_number=gale_number
        )
    
    def _get_active_rooms(self) -> List[SignalRoom]:
        """Busca salas ativas no banco"""
        return self.db.query(SignalRoom).filter(
            SignalRoom.is_active == True
        ).all()
    
    def _number_to_color(self, number: int) -> str:
        """Converte número da Blaze para cor"""
        if 1 <= number <= 7:
            return "V"  # Vermelho
        elif 8 <= number <= 14:
            return "P"  # Preto
        else:
            return "B"  # Branco
    
    def _check_win_condition(self, bet_direction, result_color: str, protection: bool) -> bool:
        """Verifica se ganhou baseado na direção da aposta e resultado"""
        
        # Se saiu branco e tem proteção, conta como win
        if result_color == "B" and protection:
            return True
        
        # Verificar match direto
        if bet_direction.value == result_color:
            return True
        
        return False
    
    async def _save_signal_history(self, room_id: int, strategy_id: int, action: str):
        """Salva histórico de ações"""
        
        # Implementar salvamento no banco
        history = ResultHistory(
            room_id=room_id,
            strategy_id=strategy_id,
            result_type=ResultType.WIN,  # Será atualizado quando souber o resultado
            bet_color=BetColor.RED,      # Será atualizado
            timestamp=datetime.now()
        )
        
        # self.db.add(history)
        # self.db.commit()
        
        logger.debug(
            "Histórico salvo",
            room_id=room_id,
            strategy_id=strategy_id,
            action=action
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do orquestrador"""
        return {
            "active_rooms": len(self.active_rooms),
            "pending_signals": len(self.pending_signals),
            "active_gales": len(self.gale_states),
            "blaze_monitor_status": self.blaze_monitor.get_status(),
            "telegram_stats": self.telegram_manager.get_stats()
        }

# Factory function
def get_signal_orchestrator(db: Session) -> SignalOrchestrator:
    """Factory function para criar instância do orquestrador"""
    return SignalOrchestrator(db) 