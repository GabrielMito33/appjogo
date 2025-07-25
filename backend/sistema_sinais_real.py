#!/usr/bin/env python3
"""
🔥 SISTEMA DE SINAIS EM TEMPO REAL
Sistema completo baseado no ScriptSolo.py mas para múltiplas estratégias
Roda continuamente monitorando a Blaze e enviando sinais via Telegram
"""

import time
import requests
import json
from datetime import datetime
from typing import List, Dict, Any
import threading

# === CONFIGURAÇÕES REAIS ===
BOT_TOKEN = "8106969377:AAHp4PRKZN-RHb1GxR3C3l7PzikFHEcRsck"
CHAT_ID = "-1002852101467"
BLAZE_API_URL = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# === ESTRATÉGIAS CONFIGURÁVEIS ===
ESTRATEGIAS = [
    {
        "name": "🔴 Sequência Vermelhos",
        "conditions": ["V", "V"],
        "bet_direction": "P",
        "priority": 1
    },
    {
        "name": "⚫ Sequência Pretos", 
        "conditions": ["P", "P"],
        "bet_direction": "V",
        "priority": 1
    },
    {
        "name": "🎯 Padrão Alternado",
        "conditions": ["V", "P", "V"],
        "bet_direction": "P",
        "priority": 2
    },
    {
        "name": "💎 Triple Pattern",
        "conditions": ["V", "V", "P"],
        "bet_direction": "V",
        "priority": 3
    },
    {
        "name": "🚀 Gale Helper",
        "conditions": ["X", "P"],  # Wildcard + Preto
        "bet_direction": "V",
        "priority": 4
    }
]

# === CONFIGURAÇÕES DO SISTEMA ===
MAX_GALES = 2
PROTECTION = True
INTERVAL_SECONDS = 2
ENABLE_ALERTS = True

# === ESTADO GLOBAL ===
sistema_ativo = True
ultimo_resultado = None
historico_resultados = []
sinais_enviados = 0
wins = 0
losses = 0
brancos = 0

def log(message):
    """Log com timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

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

def fetch_blaze_results() -> List[int]:
    """Busca resultados da Blaze"""
    try:
        response = requests.get(BLAZE_API_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [item['roll'] for item in data]
        return []
    except Exception as e:
        log(f"❌ Erro ao buscar Blaze: {e}")
        return []

def check_strategy_match(strategy: Dict, results: List[int]) -> bool:
    """Verifica se estratégia faz match"""
    conditions = strategy["conditions"]
    if len(conditions) > len(results):
        return False
    
    # Converter números para cores
    colors = [convert_number_to_color(num) for num in results[:len(conditions)]]
    
    # Verificar match das condições
    for i, condition in enumerate(conditions):
        posicao = len(conditions) - 1 - i
        numero_atual = str(results[posicao])
        cor_atual = colors[posicao]
        
        if condition == "X":  # Wildcard
            continue
        elif condition == numero_atual or condition == cor_atual:
            continue
        else:
            return False
    
    return True

def send_telegram_message(message: str) -> bool:
    """Envia mensagem para o Telegram"""
    try:
        response = requests.post(
            f"{TELEGRAM_API_BASE}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        log(f"❌ Erro ao enviar Telegram: {e}")
        return False

def send_signal(strategy: Dict, results: List[int]):
    """Envia sinal baseado na estratégia"""
    global sinais_enviados
    
    bet_direction = strategy["bet_direction"]
    color_emoji = get_color_emoji(bet_direction)
    color_name = get_color_name(bet_direction)
    
    # Construir mensagem de sinal
    signal_message = f"""🎲 **SINAL DETECTADO** 🔥

🎯 **Estratégia**: {strategy['name']}
🎰 **Entrada para**: {color_emoji} **{color_name}**
💰 **Proteção no**: ⚪ **BRANCO**
♻️ **Gales**: Até {MAX_GALES}

📊 **Análise**:
• Últimos: {results[:5]}
• Cores: {' '.join([get_color_emoji(convert_number_to_color(r)) for r in results[:5]])}
• Prioridade: {strategy['priority']}

⏰ **{datetime.now().strftime('%H:%M:%S')}** | 🤖 **Sistema Auto**

💡 **Boa sorte! 🍀**"""

    if send_telegram_message(signal_message):
        sinais_enviados += 1
        log(f"🎯 SINAL ENVIADO: {strategy['name']} -> {color_name}")
    else:
        log(f"❌ Falha ao enviar sinal: {strategy['name']}")

def send_alert(strategy: Dict):
    """Envia alerta de estratégia próxima"""
    if not ENABLE_ALERTS:
        return
        
    alert_message = f"""⚠️ **FIQUE ATENTO** ⚠️

🔍 **Estratégia**: {strategy['name']}
📈 **Status**: Próxima de ativar
⏳ **Aguardando**: Próximo resultado

🎯 **Prepare-se para possível entrada!**

⏰ **{datetime.now().strftime('%H:%M:%S')}**"""

    if send_telegram_message(alert_message):
        log(f"⚠️ ALERTA ENVIADO: {strategy['name']}")

def check_strategy_alert(strategy: Dict, results: List[int]) -> bool:
    """Verifica se deve enviar alerta"""
    conditions = strategy["conditions"]
    if len(conditions) <= 1:
        return False
    
    # Verificar condições parciais (sem a última)
    alert_conditions = conditions[:-1]
    
    if len(alert_conditions) > len(results):
        return False
    
    colors = [convert_number_to_color(num) for num in results[:len(alert_conditions)]]
    
    for i, condition in enumerate(alert_conditions):
        posicao = len(alert_conditions) - 1 - i
        numero_atual = str(results[posicao])
        cor_atual = colors[posicao]
        
        if condition == "X":
            continue
        elif condition == numero_atual or condition == cor_atual:
            continue
        else:
            return False
    
    return True

def process_strategies(results: List[int]):
    """Processa todas as estratégias"""
    if len(results) < 2:
        return
    
    log(f"🎲 Processando: {results[:5]} -> {[get_color_emoji(convert_number_to_color(r)) for r in results[:5]]}")
    
    # Verificar sinais
    for strategy in ESTRATEGIAS:
        if check_strategy_match(strategy, results):
            send_signal(strategy, results)
            return  # Enviar apenas um sinal por vez
    
    # Verificar alertas (se não houve sinais)
    for strategy in ESTRATEGIAS:
        if check_strategy_alert(strategy, results):
            send_alert(strategy)
            time.sleep(1)  # Pequena pausa entre alertas

def send_statistics():
    """Envia estatísticas do sistema"""
    total_sinais = sinais_enviados
    tempo_ativo = datetime.now().strftime('%H:%M:%S')
    
    stats_message = f"""📊 **ESTATÍSTICAS DO SISTEMA**

🎯 **Sinais Enviados**: {total_sinais}
⏰ **Tempo Ativo**: Desde {tempo_ativo}
🔥 **Estratégias**: {len(ESTRATEGIAS)} ativas
📡 **Status**: 🟢 Online

💎 **Estratégias Monitoradas**:
"""
    
    for i, strategy in enumerate(ESTRATEGIAS, 1):
        stats_message += f"{i}. {strategy['name']}\n"
    
    stats_message += f"\n🤖 **Sistema funcionando perfeitamente!**"
    
    send_telegram_message(stats_message)
    log("📊 Estatísticas enviadas")

def monitor_blaze():
    """Monitor principal da Blaze"""
    global ultimo_resultado, historico_resultados, sistema_ativo
    
    log("🚀 Iniciando monitor da Blaze...")
    
    # Enviar mensagem de início
    start_message = f"""🔥 **SISTEMA DE SINAIS ATIVADO** 🔥

⏰ **Início**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
🎯 **Estratégias**: {len(ESTRATEGIAS)} configuradas
⚡ **Intervalo**: {INTERVAL_SECONDS} segundos
🛡️ **Proteção**: {'✅ Ativada' if PROTECTION else '❌ Desativada'}

🚀 **Sistema pronto para detectar sinais!**

💡 *Aguarde os próximos resultados...*"""
    
    send_telegram_message(start_message)
    
    while sistema_ativo:
        try:
            # Buscar novos resultados
            results = fetch_blaze_results()
            
            if results and results[0] != ultimo_resultado:
                ultimo_resultado = results[0]
                historico_resultados = results
                
                log(f"🆕 Novo resultado: {ultimo_resultado} ({get_color_emoji(convert_number_to_color(ultimo_resultado))})")
                
                # Processar estratégias
                process_strategies(results)
            
            time.sleep(INTERVAL_SECONDS)
            
        except KeyboardInterrupt:
            log("🛑 Sistema interrompido pelo usuário")
            sistema_ativo = False
        except Exception as e:
            log(f"❌ Erro no monitor: {e}")
            time.sleep(5)

def input_commands():
    """Thread para comandos do usuário"""
    global sistema_ativo
    
    while sistema_ativo:
        try:
            cmd = input().strip().lower()
            
            if cmd in ['quit', 'exit', 'stop']:
                log("🛑 Parando sistema...")
                sistema_ativo = False
                break
            elif cmd == 'stats':
                send_statistics()
            elif cmd == 'status':
                log(f"📊 Sinais enviados: {sinais_enviados} | Resultados: {len(historico_resultados)}")
            elif cmd == 'help':
                print("\nComandos disponíveis:")
                print("  stats  - Enviar estatísticas")
                print("  status - Status do sistema")
                print("  quit   - Parar sistema")
        except:
            pass

def main():
    """Função principal"""
    print("="*60)
    print("🔥 SISTEMA DE SINAIS EM TEMPO REAL")
    print("="*60)
    print(f"🤖 Bot: @blisscriador_bot")
    print(f"💬 Canal: {CHAT_ID}")
    print(f"🎯 Estratégias: {len(ESTRATEGIAS)}")
    print(f"⚡ Intervalo: {INTERVAL_SECONDS}s")
    print("="*60)
    print("\nComandos:")
    print("  'stats' - Enviar estatísticas")
    print("  'quit'  - Parar sistema")
    print("\n🚀 Iniciando em 3 segundos...")
    
    time.sleep(3)
    
    # Iniciar thread de comandos
    cmd_thread = threading.Thread(target=input_commands, daemon=True)
    cmd_thread.start()
    
    # Iniciar monitor principal
    try:
        monitor_blaze()
    except KeyboardInterrupt:
        log("🛑 Sistema finalizado")
    finally:
        # Mensagem de finalização
        end_message = f"""🛑 **SISTEMA FINALIZADO**

⏰ **Finalizado**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
🎯 **Total de Sinais**: {sinais_enviados}
⏱️ **Tempo de Operação**: Sessão encerrada

🤖 **Sistema offline**"""
        
        send_telegram_message(end_message)
        print("\n✅ Sistema finalizado com sucesso!")

if __name__ == "__main__":
    main() 