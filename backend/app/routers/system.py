"""
System Router - Endpoints para monitoramento e teste do sistema
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database import get_db
from app.models.user import User
from app.core.security import get_current_active_user
from app.services.blaze_monitor import get_blaze_monitor
from app.services.telegram_service import get_telegram_manager
from app.services.strategy_engine import get_strategy_engine
from app.services.signal_orchestrator import get_signal_orchestrator
from app.core.validators import validate_complete_room, TelegramValidator, StrategyValidator

router = APIRouter()

@router.get("/status")
async def system_status():
    """Status geral do sistema"""
    blaze_monitor = get_blaze_monitor()
    telegram_manager = get_telegram_manager()
    
    return {
        "system": "online",
        "timestamp": "2024-01-15T10:00:00Z",
        "components": {
            "blaze_monitor": blaze_monitor.get_status(),
            "telegram_manager": telegram_manager.get_stats(),
            "database": "connected"
        }
    }

@router.post("/test/blaze")
async def test_blaze_connection():
    """Testa conexão com a API da Blaze"""
    blaze_monitor = get_blaze_monitor()
    
    try:
        results = blaze_monitor.fetch_latest_results_sync()
        if results:
            return {
                "status": "success",
                "message": "Conexão com Blaze funcionando",
                "results_count": len(results),
                "latest_results": results[:5]
            }
        else:
            return {
                "status": "error",
                "message": "Não foi possível obter resultados da Blaze"
            }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Erro na conexão: {str(e)}"
        }

@router.post("/test/telegram")
async def test_telegram_token(
    token: str,
    chat_id: str = None,
    current_user: User = Depends(get_current_active_user)
):
    """Testa token e acesso do bot Telegram"""
    
    # Validar token
    token_valid, token_error, bot_info = await TelegramValidator.validate_bot_token_api(token)
    
    result = {
        "token_valid": token_valid,
        "bot_info": bot_info,
        "chat_access": None
    }
    
    if not token_valid:
        result["error"] = token_error
    
    # Se forneceu chat_id, testar acesso também
    if token_valid and chat_id:
        chat_valid, chat_error, chat_info = await TelegramValidator.validate_chat_access(token, chat_id)
        result["chat_access"] = {
            "valid": chat_valid,
            "chat_info": chat_info,
            "error": chat_error
        }
    
    return result

@router.post("/test/strategy")
async def test_strategy(
    conditions: List[str],
    bet_direction: str,
    test_results: List[int] = [1, 8, 0, 5, 12],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Testa uma estratégia com resultados simulados"""
    
    # Validar estratégia
    strategy_valid, strategy_error = StrategyValidator.validate_strategy_logic(conditions, bet_direction)
    
    if not strategy_valid:
        return {
            "status": "error",
            "message": strategy_error
        }
    
    # Criar estratégia temporária para teste
    from app.models.strategy import Strategy, BetDirection
    
    strategy = Strategy(
        id=999,
        user_id=current_user.id,
        name="Teste",
        conditions=conditions,
        bet_direction=BetDirection(bet_direction)
    )
    
    # Testar com engine
    engine = get_strategy_engine(db)
    
    # Testar match
    match = engine.check_strategy_match(strategy, test_results)
    
    # Testar alerta  
    alert = engine.check_strategy_alert(strategy, test_results)
    
    # Converter números para cores para referência
    colors = engine.convert_numbers_to_colors(test_results)
    
    return {
        "status": "success",
        "strategy": {
            "conditions": conditions,
            "bet_direction": bet_direction
        },
        "test_results": {
            "numbers": test_results,
            "colors": colors
        },
        "analysis": {
            "match": match,
            "alert": alert,
            "bet_color_emoji": engine.get_bet_color_emoji(BetDirection(bet_direction))
        }
    }

@router.post("/test/room")
async def test_room_complete(
    name: str,
    bot_token: str,
    chat_id: str,
    max_gales: int = 2,
    protection: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """Teste completo de configuração de sala"""
    
    # Validação completa
    is_valid, error_message, validation_info = await validate_complete_room(
        name, bot_token, chat_id, max_gales, protection
    )
    
    if not is_valid:
        return {
            "status": "error",
            "message": error_message
        }
    
    # Teste de envio de mensagem
    telegram_manager = get_telegram_manager()
    test_message = f"🧪 Teste de configuração da sala '{name}'"
    
    message_sent = await telegram_manager.send_message(
        token=bot_token,
        chat_id=chat_id,
        message=test_message
    )
    
    return {
        "status": "success",
        "message": "Configuração da sala válida",
        "validation_info": validation_info,
        "test_message_sent": message_sent
    }

@router.get("/stats")
async def system_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Estatísticas do sistema para o usuário atual"""
    
    from app.models.signal_room import SignalRoom
    from app.models.strategy import Strategy
    
    # Estatísticas do usuário
    user_rooms = db.query(SignalRoom).filter(SignalRoom.user_id == current_user.id).all()
    user_strategies = db.query(Strategy).filter(Strategy.user_id == current_user.id).all()
    
    total_signals = sum(room.total_signals for room in user_rooms)
    total_wins = sum(room.wins for room in user_rooms)
    total_losses = sum(room.losses for room in user_rooms)
    total_brancos = sum(room.brancos for room in user_rooms)
    
    # Calcular assertividade geral
    total_results = total_wins + total_losses + total_brancos
    overall_assertiveness = 0
    if total_results > 0:
        overall_assertiveness = ((total_wins + total_brancos) / total_results) * 100
    
    return {
        "user_stats": {
            "total_rooms": len(user_rooms),
            "active_rooms": len([r for r in user_rooms if r.is_active]),
            "total_strategies": len(user_strategies),
            "active_strategies": len([s for s in user_strategies if s.is_active])
        },
        "signal_stats": {
            "total_signals": total_signals,
            "wins": total_wins,
            "losses": total_losses,
            "brancos": total_brancos,
            "overall_assertiveness": f"{overall_assertiveness:.2f}%"
        },
        "room_details": [
            {
                "id": room.id,
                "name": room.name,
                "is_active": room.is_active,
                "total_signals": room.total_signals,
                "wins": room.wins,
                "losses": room.losses,
                "brancos": room.brancos,
                "assertiveness": f"{((room.wins + room.brancos) / max(room.total_signals, 1)) * 100:.2f}%"
            }
            for room in user_rooms
        ]
    }

@router.post("/simulate/signal")
async def simulate_signal_processing(
    room_id: int,
    simulated_results: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Simula processamento de sinais para uma sala"""
    
    from app.models.signal_room import SignalRoom
    
    # Buscar sala do usuário
    room = db.query(SignalRoom).filter(
        SignalRoom.id == room_id,
        SignalRoom.user_id == current_user.id
    ).first()
    
    if not room:
        raise HTTPException(status_code=404, detail="Sala não encontrada")
    
    # Simular processamento
    orchestrator = get_signal_orchestrator(db)
    strategy_engine = get_strategy_engine(db)
    
    # Processar estratégias da sala
    results = strategy_engine.process_room_strategies(room, simulated_results)
    
    return {
        "status": "success",
        "room": {
            "id": room.id,
            "name": room.name
        },
        "simulated_results": {
            "numbers": simulated_results,
            "colors": strategy_engine.convert_numbers_to_colors(simulated_results)
        },
        "processing_results": {
            "signals_found": len(results["signals"]),
            "alerts_found": len(results["alerts"]),
            "signals": [
                {
                    "strategy_id": s.id,
                    "strategy_name": s.name,
                    "conditions": s.conditions,
                    "bet_direction": s.bet_direction.value
                }
                for s in results["signals"]
            ],
            "alerts": [
                {
                    "strategy_id": s.id,
                    "strategy_name": s.name,
                    "conditions": s.conditions,
                    "next_condition": s.conditions[-1] if s.conditions else None
                }
                for s in results["alerts"]
            ]
        }
    } 