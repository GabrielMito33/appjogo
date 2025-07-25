#!/usr/bin/env python3
"""
🔥 SISTEMA DE SINAIS AVANÇADO V2.0
Sistema completo com controle de gales, estatísticas e múltiplas funcionalidades
"""

import time
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import os

# === CONFIGURAÇÕES REAIS ===
BOT_TOKEN = "8106969377:AAHp4PRKZN-RHb1GxR3C3l7PzikFHEcRsck"
CHAT_ID = "-1002852101467"
BLAZE_API_URL = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# === CONFIGURAÇÕES AVANÇADAS ===
ESTRATEGIAS = [
    {
        "id": 1,
        "name": "🔴 Sequência Vermelhos",
        "conditions": ["V", "V"],
        "bet_direction": "P",
        "priority": 1,
        "active": True,
        "min_confidence": 80
    },
    {
        "id": 2,
        "name": "⚫ Sequência Pretos", 
        "conditions": ["P", "P"],
        "bet_direction": "V",
        "priority": 1,
        "active": True,
        "min_confidence": 80
    },
    {
        "id": 3,
        "name": "🎯 Padrão Alternado",
        "conditions": ["V", "P", "V"],
        "bet_direction": "P",
        "priority": 2,
        "active": True,
        "min_confidence": 70
    },
    {
        "id": 4,
        "name": "💎 Triple Pattern",
        "conditions": ["V", "V", "P"],
        "bet_direction": "V",
        "priority": 3,
        "active": True,
        "min_confidence": 75
    },
    {
        "id": 5,
        "name": "🌟 Mega Sequencia",
        "conditions": ["P", "P", "P"],
        "bet_direction": "V",
        "priority": 1,
        "active": True,
        "min_confidence": 90
    }
]

# Configurações do sistema
CONFIG = {
    "max_gales": 2,
    "protection": True,
    "interval_seconds": 3,
    "enable_alerts": True,
    "enable_statistics": True,
    "auto_restart": True,
    "send_daily_report": True,
    "confidence_threshold": 70
}

# === ESTADO AVANÇADO DO SISTEMA ===
class SystemState:
    def __init__(self):
        self.ativo = True
        self.ultimo_resultado = None
        self.historico_resultados = []
        self.gales_ativos = {}  # {signal_id: gale_info}
        
        # Estatísticas
        self.stats = {
            "sinais_enviados": 0,
            "wins": 0,
            "losses": 0,
            "brancos": 0,
            "gales_1": 0,
            "gales_2": 0,
            "tempo_inicio": datetime.now(),
            "ultimo_sinal": None,
            "estrategias_stats": {str(e["id"]): {"sinais": 0, "wins": 0, "losses": 0} for e in ESTRATEGIAS}
        }
        
        # Controles
        self.pause_until = None
        self.maintenance_mode = False

state = SystemState()

def log(message, level="INFO"):
    """Log avançado com timestamp e níveis"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    icon = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "📝")
    print(f"[{timestamp}] {icon} {message}")
    
    # Salvar em arquivo (opcional)
    try:
        with open("sistema_logs.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {level}: {message}\n")
    except:
        pass

def convert_number_to_color(number: int) -> str:
    """Converte número para cor"""
    if 1 <= number <= 7:
        return "V"
    elif 8 <= number <= 14:
        return "P"
    else:
        return "B"

def get_color_emoji(color: str) -> str:
    """Converte cor para emoji"""
    mapping = {"V": "🔴", "P": "⚫", "B": "⚪"}
    return mapping.get(color, "❓")

def get_color_name(color: str) -> str:
    """Converte cor para nome"""
    mapping = {"V": "VERMELHO", "P": "PRETO", "B": "BRANCO"}
    return mapping.get(color, "DESCONHECIDO")

def calculate_confidence(strategy: Dict, results: List[int]) -> int:
    """Calcula confiança da estratégia baseado no histórico"""
    # Análise simples baseada na frequência de padrões
    base_confidence = strategy.get("min_confidence", 70)
    
    # Adicionar lógica para aumentar/diminuir confiança
    # baseado no histórico de wins/losses da estratégia
    strategy_id = str(strategy["id"])
    stats = state.stats["estrategias_stats"].get(strategy_id, {"sinais": 0, "wins": 0})
    
    if stats["sinais"] > 0:
        win_rate = stats["wins"] / stats["sinais"]
        confidence_modifier = (win_rate - 0.5) * 20  # -10 a +10
        return min(100, max(30, base_confidence + confidence_modifier))
    
    return base_confidence

def fetch_blaze_results() -> List[int]:
    """Busca resultados da Blaze"""
    try:
        response = requests.get(BLAZE_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [item['roll'] for item in data]
        return []
    except Exception as e:
        log(f"Erro ao buscar Blaze: {e}", "ERROR")
        return []

def send_telegram_message(message: str, parse_mode: str = "Markdown") -> bool:
    """Envia mensagem para o Telegram"""
    try:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": parse_mode
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"Erro ao enviar Telegram: {e}", "ERROR")
        return False

def send_sticker(sticker_id: str) -> bool:
    """Envia sticker para o Telegram"""
    try:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/sendSticker",
            json={
                "chat_id": CHAT_ID,
                "sticker": sticker_id
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"Erro ao enviar sticker: {e}", "ERROR")
        return False

def check_strategy_match(strategy: Dict, results: List[int]) -> bool:
    """Verifica se estratégia faz match"""
    if not strategy.get("active", True):
        return False
        
    conditions = strategy["conditions"]
    if len(conditions) > len(results):
        return False
    
    colors = [convert_number_to_color(num) for num in results[:len(conditions)]]
    
    for i, condition in enumerate(conditions):
        posicao = len(conditions) - 1 - i
        numero_atual = str(results[posicao])
        cor_atual = colors[posicao]
        
        if condition == "X":
            continue
        elif condition == numero_atual or condition == cor_atual:
            continue
        else:
            return False
    
    return True

def send_signal(strategy: Dict, results: List[int]):
    """Envia sinal avançado com controle de gales"""
    confidence = calculate_confidence(strategy, results)
    
    if confidence < CONFIG["confidence_threshold"]:
        log(f"Sinal {strategy['name']} descartado - baixa confiança: {confidence}%", "WARNING")
        return
    
    bet_direction = strategy["bet_direction"]
    color_emoji = get_color_emoji(bet_direction)
    color_name = get_color_name(bet_direction)
    
    # ID único para o sinal
    signal_id = f"{strategy['id']}_{int(time.time())}"
    
    # Sticker de entrada (opcional)
    entry_stickers = {
        "V": "CAACAgEAAxkBAAMPZrqPFR0VdwEGmMIhUvD-ftVCU9IAAm8CAAIhWPBGBpXDpqXsW8Q1BA",
        "P": "CAACAgEAAxkBAAMTZrqPNtuE01MlUnK6yF68sSO6lc0AAsQCAAIEQehG-NlOMcjRGTM1BA"
    }
    
    # Construir mensagem de sinal
    signal_message = f"""🎲 **SINAL DETECTADO** 🔥

🎯 **Estratégia**: {strategy['name']}
🎰 **Entrada para**: {color_emoji} **{color_name}**
💰 **Proteção no**: ⚪ **BRANCO**
♻️ **Gales**: Até {CONFIG['max_gales']}

📊 **Análise**:
• Últimos: {results[:5]}
• Cores: {' '.join([get_color_emoji(convert_number_to_color(r)) for r in results[:5]])}
• Confiança: {confidence}%
• Prioridade: {strategy['priority']}

⏰ **{datetime.now().strftime('%H:%M:%S')}** | 🤖 **Sistema Auto**

🍀 **BOA SORTE!** 🚀"""

    # Enviar sticker primeiro
    if bet_direction in entry_stickers:
        send_sticker(entry_stickers[bet_direction])
        time.sleep(0.5)
    
    if send_telegram_message(signal_message):
        # Registrar estado do gale
        state.gales_ativos[signal_id] = {
            "strategy_id": strategy["id"],
            "strategy_name": strategy["name"],
            "bet_direction": bet_direction,
            "confidence": confidence,
            "timestamp": datetime.now(),
            "gale_count": 0,
            "status": "active"
        }
        
        # Atualizar estatísticas
        state.stats["sinais_enviados"] += 1
        state.stats["ultimo_sinal"] = datetime.now()
        strategy_id = str(strategy["id"])
        state.stats["estrategias_stats"][strategy_id]["sinais"] += 1
        
        log(f"SINAL ENVIADO: {strategy['name']} -> {color_name} (Confiança: {confidence}%)", "SUCCESS")
    else:
        log(f"Falha ao enviar sinal: {strategy['name']}", "ERROR")

def check_gale_results(new_result: int):
    """Verifica resultados dos gales ativos"""
    result_color = convert_number_to_color(new_result)
    
    completed_gales = []
    
    for signal_id, gale_info in state.gales_ativos.items():
        if gale_info["status"] != "active":
            continue
            
        bet_direction = gale_info["bet_direction"]
        
        # Verificar se ganhou
        won = False
        if result_color == bet_direction:
            won = True
        elif result_color == "B" and CONFIG["protection"]:
            won = True  # Proteção no branco
        
        if won:
            # WIN!
            result_type = "white" if result_color == "B" else "win"
            send_result_message(gale_info, result_type, new_result)
            
            # Atualizar estatísticas
            if result_type == "win":
                state.stats["wins"] += 1
            else:
                state.stats["brancos"] += 1
                
            strategy_id = str(gale_info["strategy_id"])
            state.stats["estrategias_stats"][strategy_id]["wins"] += 1
            
            completed_gales.append(signal_id)
            gale_info["status"] = "completed_win"
            
        else:
            # LOSS - verificar gale
            gale_count = gale_info["gale_count"]
            
            if gale_count < CONFIG["max_gales"]:
                # Ir para próximo gale
                gale_info["gale_count"] += 1
                send_gale_message(gale_info, gale_count + 1)
                
                # Atualizar estatísticas de gale
                if gale_count == 0:
                    state.stats["gales_1"] += 1
                elif gale_count == 1:
                    state.stats["gales_2"] += 1
                    
            else:
                # LOSS final
                send_result_message(gale_info, "loss", new_result)
                state.stats["losses"] += 1
                
                strategy_id = str(gale_info["strategy_id"])
                state.stats["estrategias_stats"][strategy_id]["losses"] += 1
                
                completed_gales.append(signal_id)
                gale_info["status"] = "completed_loss"
    
    # Remover gales completados
    for signal_id in completed_gales:
        if signal_id in state.gales_ativos:
            del state.gales_ativos[signal_id]

def send_result_message(gale_info: Dict, result_type: str, winning_number: int):
    """Envia mensagem de resultado"""
    stickers = {
        "win": "CAACAgEAAxkBAAMPZrqPFR0VdwEGmMIhUvD-ftVCU9IAAm8CAAIhWPBGBpXDpqXsW8Q1BA",
        "loss": "CAACAgEAAxkBAAMTZrqPNtuE01MlUnK6yF68sSO6lc0AAsQCAAIEQehG-NlOMcjRGTM1BA",
        "white": "CAACAgEAAxkBAAMRZrqPJkaflJxOqn_wTYTupKMtpDkAAjYCAAJMK-lGHp_XWq_MVE01BA"
    }
    
    messages = {
        "win": f"✅ **WIN!** 🎉\n\n🎯 Estratégia: {gale_info['strategy_name']}\n🎲 Resultado: {winning_number} {get_color_emoji(convert_number_to_color(winning_number))}\n💰 **PARABÉNS!**",
        "loss": f"❌ **LOSS** 😔\n\n🎯 Estratégia: {gale_info['strategy_name']}\n🎲 Resultado: {winning_number} {get_color_emoji(convert_number_to_color(winning_number))}\n🚀 **Próxima será GREEN!**",
        "white": f"⚪ **BRANCO - PROTEÇÃO!** 🛡️\n\n🎯 Estratégia: {gale_info['strategy_name']}\n🎲 Resultado: {winning_number} {get_color_emoji(convert_number_to_color(winning_number))}\n✅ **Protegido!**"
    }
    
    # Enviar sticker
    if result_type in stickers:
        send_sticker(stickers[result_type])
        time.sleep(0.5)
    
    # Enviar mensagem
    send_telegram_message(messages[result_type])

def send_gale_message(gale_info: Dict, gale_number: int):
    """Envia mensagem de gale"""
    gale_message = f"""⚠️ **VAMOS PARA O {gale_number}º GALE** ⚠️

🎯 **Estratégia**: {gale_info['strategy_name']}
🎰 **Manter entrada**: {get_color_emoji(gale_info['bet_direction'])} **{get_color_name(gale_info['bet_direction'])}**
💰 **Proteção**: ⚪ **BRANCO**

🚀 **Confiança mantida!** 💪

⏰ **{datetime.now().strftime('%H:%M:%S')}**"""

    send_telegram_message(gale_message)
    log(f"GALE {gale_number}: {gale_info['strategy_name']}", "WARNING")

def send_statistics():
    """Envia estatísticas completas"""
    tempo_ativo = datetime.now() - state.stats["tempo_inicio"]
    horas = int(tempo_ativo.total_seconds() // 3600)
    minutos = int((tempo_ativo.total_seconds() % 3600) // 60)
    
    total_results = state.stats["wins"] + state.stats["losses"] + state.stats["brancos"]
    win_rate = (state.stats["wins"] + state.stats["brancos"]) / max(total_results, 1) * 100
    
    stats_message = f"""📊 **ESTATÍSTICAS COMPLETAS**

⏰ **Tempo Ativo**: {horas}h {minutos}m
🎯 **Sinais Enviados**: {state.stats['sinais_enviados']}
✅ **Wins**: {state.stats['wins']}
❌ **Losses**: {state.stats['losses']}
⚪ **Brancos**: {state.stats['brancos']}
📈 **Taxa de Sucesso**: {win_rate:.1f}%

🎰 **Gales**:
• 1º Gale: {state.stats['gales_1']}
• 2º Gale: {state.stats['gales_2']}

🔥 **Estratégias Ativas**: {len([e for e in ESTRATEGIAS if e.get('active', True)])}
⚡ **Gales Ativos**: {len(state.gales_ativos)}

🤖 **Sistema funcionando perfeitamente!**"""

    send_telegram_message(stats_message)
    log("Estatísticas enviadas", "SUCCESS")

def process_strategies(results: List[int]):
    """Processa todas as estratégias"""
    if len(results) < 2:
        return
    
    log(f"Processando: {results[:5]} -> {[get_color_emoji(convert_number_to_color(r)) for r in results[:5]]}")
    
    # Verificar resultados de gales primeiro
    check_gale_results(results[0])
    
    # Verificar sinais (apenas se não há muitos gales ativos)
    if len(state.gales_ativos) < 3:  # Limite de gales simultâneos
        for strategy in sorted(ESTRATEGIAS, key=lambda x: x["priority"]):
            if check_strategy_match(strategy, results):
                send_signal(strategy, results)
                return  # Apenas um sinal por vez

def monitor_blaze():
    """Monitor principal da Blaze"""
    log("Iniciando monitor da Blaze...", "SUCCESS")
    
    # Mensagem de início
    start_message = f"""🔥 **SISTEMA AVANÇADO ATIVADO** 🔥

⏰ **Início**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
🎯 **Estratégias**: {len(ESTRATEGIAS)} configuradas
⚡ **Intervalo**: {CONFIG['interval_seconds']}s
🛡️ **Proteção**: {'✅ Ativada' if CONFIG['protection'] else '❌ Desativada'}
📊 **Confiança Mín**: {CONFIG['confidence_threshold']}%

🚀 **Sistema V2.0 pronto para detectar sinais!**

💡 *Aguarde os próximos resultados...*"""
    
    send_telegram_message(start_message)
    
    last_stats_time = datetime.now()
    
    while state.ativo:
        try:
            # Verificar modo manutenção
            if state.maintenance_mode:
                time.sleep(10)
                continue
                
            # Verificar pausa
            if state.pause_until and datetime.now() < state.pause_until:
                time.sleep(5)
                continue
            
            # Buscar novos resultados
            results = fetch_blaze_results()
            
            if results and results[0] != state.ultimo_resultado:
                state.ultimo_resultado = results[0]
                state.historico_resultados = results
                
                log(f"Novo resultado: {state.ultimo_resultado} ({get_color_emoji(convert_number_to_color(state.ultimo_resultado))})")
                
                # Processar estratégias
                process_strategies(results)
            
            # Enviar estatísticas a cada 30 minutos
            if CONFIG["enable_statistics"] and (datetime.now() - last_stats_time).seconds > 1800:
                send_statistics()
                last_stats_time = datetime.now()
            
            time.sleep(CONFIG["interval_seconds"])
            
        except KeyboardInterrupt:
            log("Sistema interrompido pelo usuário", "WARNING")
            state.ativo = False
        except Exception as e:
            log(f"Erro no monitor: {e}", "ERROR")
            time.sleep(10)  # Pausa maior em caso de erro

def handle_commands():
    """Thread para comandos do usuário"""
    commands_help = """
Comandos disponíveis:
  stats       - Enviar estatísticas
  status      - Status do sistema
  pause 5     - Pausar por 5 minutos
  resume      - Retomar sistema
  strategy 1  - Toggle estratégia 1
  quit        - Parar sistema
  help        - Esta ajuda
"""
    
    print(commands_help)
    
    while state.ativo:
        try:
            cmd = input().strip().lower()
            
            if cmd in ['quit', 'exit', 'stop']:
                log("Parando sistema...", "WARNING")
                state.ativo = False
                break
            elif cmd == 'stats':
                send_statistics()
            elif cmd == 'status':
                log(f"Sinais: {state.stats['sinais_enviados']} | Gales ativos: {len(state.gales_ativos)} | Win rate: {((state.stats['wins'] + state.stats['brancos']) / max(state.stats['sinais_enviados'], 1) * 100):.1f}%")
            elif cmd.startswith('pause'):
                parts = cmd.split()
                minutes = int(parts[1]) if len(parts) > 1 else 5
                state.pause_until = datetime.now() + timedelta(minutes=minutes)
                log(f"Sistema pausado por {minutes} minutos")
            elif cmd == 'resume':
                state.pause_until = None
                log("Sistema retomado")
            elif cmd.startswith('strategy'):
                parts = cmd.split()
                if len(parts) > 1:
                    strategy_id = int(parts[1])
                    for strategy in ESTRATEGIAS:
                        if strategy["id"] == strategy_id:
                            strategy["active"] = not strategy.get("active", True)
                            log(f"Estratégia {strategy['name']}: {'Ativada' if strategy['active'] else 'Desativada'}")
                            break
            elif cmd == 'help':
                print(commands_help)
                
        except Exception as e:
            log(f"Erro no comando: {e}", "ERROR")

def main():
    """Função principal"""
    print("="*60)
    print("🔥 SISTEMA DE SINAIS AVANÇADO V2.0")
    print("="*60)
    print(f"🤖 Bot: @blisscriador_bot")
    print(f"💬 Canal: {CHAT_ID}")
    print(f"🎯 Estratégias: {len(ESTRATEGIAS)}")
    print(f"⚡ Intervalo: {CONFIG['interval_seconds']}s")
    print(f"📊 Confiança mín: {CONFIG['confidence_threshold']}%")
    print("="*60)
    print("\n🚀 Iniciando em 3 segundos...")
    
    time.sleep(3)
    
    # Iniciar thread de comandos
    cmd_thread = threading.Thread(target=handle_commands, daemon=True)
    cmd_thread.start()
    
    try:
        monitor_blaze()
    except KeyboardInterrupt:
        log("Sistema finalizado", "SUCCESS")
    finally:
        # Mensagem de finalização
        tempo_total = datetime.now() - state.stats["tempo_inicio"]
        end_message = f"""🛑 **SISTEMA FINALIZADO**

⏰ **Finalizado**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
⏱️ **Tempo Total**: {int(tempo_total.total_seconds() // 3600)}h {int((tempo_total.total_seconds() % 3600) // 60)}m
🎯 **Total de Sinais**: {state.stats['sinais_enviados']}
✅ **Wins**: {state.stats['wins']}
❌ **Losses**: {state.stats['losses']}

🤖 **Sistema V2.0 offline**"""
        
        send_telegram_message(end_message)
        print("\n✅ Sistema avançado finalizado com sucesso!")

if __name__ == "__main__":
    main() 