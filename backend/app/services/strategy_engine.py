"""
Strategy Engine - Sistema que executa estratégias e identifica sinais
Baseado na lógica do ScriptSolo.py original, mas escalável para múltiplas salas
"""

from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
import structlog

from app.models.strategy import Strategy, BetDirection
from app.models.signal_room import SignalRoom
from app.models.room_strategy import RoomStrategy

logger = structlog.get_logger(__name__)

class StrategyEngine:
    """Engine principal para execução de estratégias"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def check_strategy_match(self, strategy: Strategy, results: List[int]) -> bool:
        """
        Verifica se uma estratégia faz match com os resultados da Blaze
        
        Args:
            strategy: Estratégia a ser verificada
            results: Lista de números da Blaze (mais recente primeiro)
            
        Returns:
            True se a estratégia faz match
        """
        conditions = strategy.conditions
        
        # Verificar se temos dados suficientes
        if len(conditions) > len(results):
            logger.debug(
                "Dados insuficientes para estratégia",
                strategy_id=strategy.id,
                conditions_needed=len(conditions),
                results_available=len(results)
            )
            return False
        
        # Converter números para cores
        colors = self.convert_numbers_to_colors(results[:len(conditions)])
        
        # Verificar match das condições (ordem temporal correta)
        for i, condition in enumerate(conditions):
            # A condição i corresponde à posição (len(conditions)-1-i) no histórico
            # Exemplo: conditions = ["1", "P"] 
            # conditions[0]="1" verifica posicao_historico=1 (mais antigo)
            # conditions[1]="P" verifica posicao_historico=0 (mais recente)
            posicao_historico = len(conditions) - 1 - i
            
            numero_nesta_posicao = str(results[posicao_historico])
            cor_nesta_posicao = colors[posicao_historico]
            
            logger.debug(
                "Verificando condição",
                strategy_id=strategy.id,
                condition_index=i,
                condition=condition,
                position=posicao_historico,
                number=numero_nesta_posicao,
                color=cor_nesta_posicao
            )
            
            # Verificar se a condição é atendida
            if condition == "X":  # Wildcard - qualquer valor
                continue
            elif condition == numero_nesta_posicao:  # Match por número específico
                continue
            elif condition == cor_nesta_posicao:  # Match por cor
                continue
            else:
                logger.debug(
                    "Condição não atendida",
                    strategy_id=strategy.id,
                    condition=condition,
                    number=numero_nesta_posicao,
                    color=cor_nesta_posicao
                )
                return False
        
        logger.info(
            "Estratégia match encontrada!",
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            conditions=conditions,
            bet_direction=strategy.bet_direction
        )
        return True
    
    def check_strategy_alert(self, strategy: Strategy, results: List[int]) -> bool:
        """
        Verifica se uma estratégia está próxima de dar sinal (alerta)
        Remove a última condição e verifica match
        
        Args:
            strategy: Estratégia a ser verificada
            results: Lista de números da Blaze
            
        Returns:
            True se deve emitir alerta
        """
        conditions = strategy.conditions
        
        # Precisa ter pelo menos 2 condições para alerta
        if len(conditions) <= 1:
            return False
        
        # Verificar alerta (condições parciais - remover última condição)
        conditions_alert = conditions[:-1]
        
        if len(conditions_alert) > len(results):
            return False
        
        # Converter números para cores
        colors = self.convert_numbers_to_colors(results[:len(conditions_alert)])
        
        # Verificar match das condições de alerta
        for i, condition in enumerate(conditions_alert):
            posicao_historico = len(conditions_alert) - 1 - i
            
            numero_nesta_posicao = str(results[posicao_historico])
            cor_nesta_posicao = colors[posicao_historico]
            
            if condition == "X":
                continue
            elif condition == numero_nesta_posicao or condition == cor_nesta_posicao:
                continue
            else:
                return False
        
        logger.info(
            "Alerta de estratégia!",
            strategy_id=strategy.id,
            strategy_name=strategy.name,
            conditions_alert=conditions_alert,
            next_condition=conditions[-1]
        )
        return True
    
    def convert_numbers_to_colors(self, numbers: List[int]) -> List[str]:
        """
        Converte números da Blaze para cores (V/P/B)
        Baseado nas regras: 1-7=Vermelho, 8-14=Preto, 0=Branco
        
        Args:
            numbers: Lista de números da Blaze
            
        Returns:
            Lista de cores correspondentes
        """
        colors = []
        for num in numbers:
            if 1 <= num <= 7:
                colors.append("V")  # Vermelho
            elif 8 <= num <= 14:
                colors.append("P")  # Preto
            else:  # 0 ou outros valores
                colors.append("B")  # Branco
        return colors
    
    def get_bet_color_emoji(self, bet_direction: BetDirection) -> str:
        """Converte direção da aposta para emoji"""
        mapping = {
            BetDirection.RED: "🔴",     # V -> 🔴
            BetDirection.BLACK: "⚫️",   # P -> ⚫️
            BetDirection.WHITE: "⚪️"    # B -> ⚪️
        }
        return mapping.get(bet_direction, "❓")
    
    def process_room_strategies(self, room: SignalRoom, results: List[int]) -> Dict[str, List[Strategy]]:
        """
        Processa todas as estratégias de uma sala e retorna sinais/alertas
        
        Args:
            room: Sala de sinais
            results: Resultados da Blaze
            
        Returns:
            Dict com listas de estratégias para 'signals' e 'alerts'
        """
        response = {
            "signals": [],
            "alerts": []
        }
        
        # Buscar estratégias ativas da sala ordenadas por prioridade
        room_strategies = self.db.query(RoomStrategy).filter(
            RoomStrategy.room_id == room.id,
            RoomStrategy.is_active == True
        ).join(Strategy).filter(
            Strategy.is_active == True
        ).order_by(RoomStrategy.priority).all()
        
        logger.info(
            "Processando estratégias da sala",
            room_id=room.id,
            room_name=room.name,
            strategies_count=len(room_strategies),
            results_count=len(results)
        )
        
        for room_strategy in room_strategies:
            strategy = room_strategy.strategy
            
            # Verificar sinal
            if self.check_strategy_match(strategy, results):
                response["signals"].append(strategy)
                logger.info(
                    "Sinal identificado",
                    room_id=room.id,
                    strategy_id=strategy.id,
                    strategy_name=strategy.name
                )
            
            # Verificar alerta (apenas se não há sinal)
            elif self.check_strategy_alert(strategy, results):
                response["alerts"].append(strategy)
                logger.info(
                    "Alerta identificado",
                    room_id=room.id,
                    strategy_id=strategy.id,
                    strategy_name=strategy.name
                )
        
        return response
    
    def validate_strategy_conditions(self, conditions: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Valida se as condições de uma estratégia são válidas
        
        Args:
            conditions: Lista de condições
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not conditions or len(conditions) == 0:
            return False, "Estratégia deve ter pelo menos uma condição"
        
        if len(conditions) > 10:
            return False, "Estratégia não pode ter mais de 10 condições"
        
        valid_values = {"V", "P", "B", "X"} | {str(i) for i in range(15)}
        
        for i, condition in enumerate(conditions):
            if condition not in valid_values:
                return False, f"Condição {i+1} inválida: '{condition}'. Valores válidos: V, P, B, X, 0-14"
        
        return True, None

# Instância singleton para uso global (pode ser injetada via DI depois)
def get_strategy_engine(db: Session) -> StrategyEngine:
    """Factory function para criar instância do engine"""
    return StrategyEngine(db) 