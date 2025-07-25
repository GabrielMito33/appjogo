#!/usr/bin/env python3
"""
🎯 SISTEMA DE SINAIS COM ESTRATÉGIAS PERSONALIZÁVEIS DO USUÁRIO
Versão que carrega estratégias do arquivo CSV definido pelo usuário
Compatible com ScriptSolo.py original
"""

import time
import requests
import json
import csv
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# === CONFIGURAÇÕES ===
BOT_TOKEN = "8106969377:AAHp4PRKZN-RHb1GxR3C3l7PzikFHEcRsck"
CHAT_ID = "-1002852101467"
BLAZE_API_URL = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Configurações do sistema
CONFIG = {
    "protection": True,
    "max_gales": 2,
    "interval_seconds": 5,
    "estrategias_file": "estrategias_usuario.csv",
    "enable_alerts": True
}

# Estado do sistema
class SystemState:
    def __init__(self):
        self.ativo = True
        self.ultimo_resultado = None
        self.historico_resultados = []
        self.gales_ativos = {}
        self.analisar = True
        
        # Estatísticas
        self.stats = {
            "sinais_enviados": 0,
            "wins": 0,
            "losses": 0,
            "brancos": 0,
            "estrategias_testadas": 0
        }

state = SystemState()

def log(message, level="INFO"):
    """Log simples"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def convert_number_to_color(number: int) -> str:
    """Converte número para cor (igual ao ScriptSolo.py)"""
    if 1 <= number <= 7:
        return "V"  # Vermelho
    elif 8 <= number <= 14:
        return "P"  # Preto
    else:
        return "B"  # Branco

def carregar_estrategias_csv() -> List[Dict]:
    """
    Carrega estratégias do arquivo CSV (formato ScriptSolo.py)
    Cada linha: "condicao1-condicao2-...=aposta"
    """
    estrategias_file = Path(CONFIG["estrategias_file"])
    
    if not estrategias_file.exists():
        log(f"❌ Arquivo de estratégias não encontrado: {estrategias_file}", "ERROR")
        return []
    
    estrategias = []
    
    try:
        with open(estrategias_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for i, row in enumerate(reader):
                if not row or not row[0].strip():
                    continue
                
                estrategia_str = row[0].strip()
                
                # Parser da estratégia
                if "=" not in estrategia_str:
                    log(f"⚠️ Linha {i+1}: Formato inválido '{estrategia_str}'", "WARNING")
                    continue
                
                try:
                    condicoes_str, aposta_str = estrategia_str.split("=", 1)
                    condicoes = [c.strip() for c in condicoes_str.split("-")]
                    aposta = aposta_str.strip()
                    
                    # Validar
                    if aposta not in ["V", "P", "B"]:
                        log(f"⚠️ Linha {i+1}: Aposta inválida '{aposta}'", "WARNING")
                        continue
                    
                    estrategias.append({
                        "id": i + 1,
                        "conditions": condicoes,
                        "bet_direction": aposta,
                        "original": estrategia_str,
                        "active": True
                    })
                    
                except Exception as e:
                    log(f"❌ Erro na linha {i+1} '{estrategia_str}': {e}", "ERROR")
        
        log(f"✅ Carregadas {len(estrategias)} estratégias do arquivo CSV")
        return estrategias
        
    except Exception as e:
        log(f"❌ Erro ao carregar estratégias: {e}", "ERROR")
        return []

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
        log(f"Erro ao enviar Telegram: {e}", "ERROR")
        return False

def verificar_estrategia(estrategia: Dict, results: List[int]) -> bool:
    """
    Verifica se uma estratégia faz match com os resultados
    LÓGICA IDÊNTICA AO ScriptSolo.py original
    """
    conditions = estrategia["conditions"]
    
    # Verificar se temos dados suficientes
    if len(conditions) > len(results):
        return False
    
    # Converter números para cores
    colors = [convert_number_to_color(num) for num in results]
    
    log(f"Testando estratégia: {estrategia['original']}", "DEBUG")
    log(f"Números: {results[:len(conditions)]}", "DEBUG")
    log(f"Cores: {colors[:len(conditions)]}", "DEBUG")
    
    # LÓGICA CORRIGIDA FINAL (igual ao ScriptSolo.py):
    # A primeira condição corresponde ao resultado mais antigo
    # A última condição corresponde ao resultado mais recente
    
    for i, condition in enumerate(conditions):
        # A condição i corresponde à posição (len(conditions)-1-i) no histórico
        posicao_historico = len(conditions) - 1 - i
        
        numero_nesta_posicao = str(results[posicao_historico])
        cor_nesta_posicao = colors[posicao_historico]
        
        log(f"  Condição {i+1}: '{condition}' | Posição {posicao_historico} | Número: {numero_nesta_posicao} | Cor: {cor_nesta_posicao}", "DEBUG")
        
        # Verificar se a condição é atendida
        if condition == "X":  # Wildcard
            log(f"    ✓ Wildcard aceito", "DEBUG")
            continue
        elif condition == numero_nesta_posicao:  # Match por número
            log(f"    ✓ Número match: {condition} == {numero_nesta_posicao}", "DEBUG")
            continue
        elif condition == cor_nesta_posicao:  # Match por cor
            log(f"    ✓ Cor match: {condition} == {cor_nesta_posicao}", "DEBUG")
            continue
        else:
            log(f"    ❌ Sem match: {condition} != {numero_nesta_posicao} e != {cor_nesta_posicao}", "DEBUG")
            return False
    
    return True

def verificar_alerta(estrategia: Dict, results: List[int]) -> bool:
    """
    Verifica se deve emitir alerta (condições parciais)
    Remove a última condição e verifica match
    """
    conditions = estrategia["conditions"]
    
    # Precisa ter pelo menos 2 condições para alerta
    if len(conditions) <= 1:
        return False
    
    # Verificar alerta (condições parciais - remover última condição)
    conditions_alert = conditions[:-1]
    
    # Criar estratégia temporária para alerta
    estrategia_alerta = {
        "conditions": conditions_alert,
        "original": " → ".join(conditions_alert) + " (ALERTA)"
    }
    
    return verificar_estrategia(estrategia_alerta, results)

def get_color_emoji(color: str) -> str:
    """Converte cor para emoji"""
    mapping = {"V": "🔴", "P": "⚫", "B": "⚪"}
    return mapping.get(color, "❓")

def get_color_name(color: str) -> str:
    """Converte cor para nome"""
    mapping = {"V": "VERMELHO", "P": "PRETO", "B": "BRANCO"}
    return mapping.get(color, "DESCONHECIDO")

def send_signal(estrategia: Dict, results: List[int]):
    """Envia sinal baseado na estratégia do usuário"""
    bet_direction = estrategia["bet_direction"]
    color_emoji = get_color_emoji(bet_direction)
    color_name = get_color_name(bet_direction)
    
    signal_message = f"""🎯 **SINAL DETECTADO** 🔥

📋 **Estratégia**: {estrategia['original']}
🎰 **Apostar em**: {color_emoji} **{color_name}**
💰 **Proteção**: ⚪ **BRANCO**
♻️ **Gales**: Até {CONFIG['max_gales']}

📊 **Análise**:
• Últimos: {results[:5]}
• Cores: {' '.join([get_color_emoji(convert_number_to_color(r)) for r in results[:5]])}

⏰ **{datetime.now().strftime('%H:%M:%S')}**

🍀 **BOA SORTE!** 🚀"""

    if send_telegram_message(signal_message):
        state.stats["sinais_enviados"] += 1
        log(f"✅ SINAL ENVIADO: {estrategia['original']} -> {color_name}")
    else:
        log(f"❌ Falha ao enviar sinal: {estrategia['original']}")

def send_alert(estrategia: Dict):
    """Envia alerta de estratégia próxima"""
    alert_message = f"""⚠️ **FIQUE ATENTO!** ⚠️

📋 **Estratégia**: {estrategia['original']}
🎯 **Próximo resultado pode ativar sinal**

⏰ **{datetime.now().strftime('%H:%M:%S')}**"""

    if send_telegram_message(alert_message):
        log(f"⚠️ ALERTA ENVIADO: {estrategia['original']}")

def processar_estrategias_usuario(results: List[int], estrategias: List[Dict]):
    """
    Processa estratégias definidas pelo usuário
    LÓGICA IGUAL AO ScriptSolo.py original
    """
    if len(results) < 2:
        return
    
    log(f"Processando {len(estrategias)} estratégias do usuário...")
    
    state.stats["estrategias_testadas"] = len(estrategias)
    
    # Verificar cada estratégia
    for estrategia in estrategias:
        if not estrategia.get("active", True):
            continue
        
        # Verificar sinal completo
        if verificar_estrategia(estrategia, results):
            log(f"🎯 MATCH ENCONTRADO! Estratégia: {estrategia['original']}")
            send_signal(estrategia, results)
            return  # Parar após primeiro match (igual ao original)
        
        # Verificar alerta
        if CONFIG["enable_alerts"] and verificar_alerta(estrategia, results):
            log(f"⚠️ ALERTA: {estrategia['original']}")
            send_alert(estrategia)
            return  # Parar após primeiro alerta

def mostrar_estatisticas():
    """Mostra estatísticas atuais"""
    stats_message = f"""📊 **ESTATÍSTICAS DO SISTEMA**

🎯 **Sinais enviados**: {state.stats['sinais_enviados']}
✅ **Wins**: {state.stats['wins']}
❌ **Losses**: {state.stats['losses']}
⚪ **Brancos**: {state.stats['brancos']}
📋 **Estratégias testadas**: {state.stats['estrategias_testadas']}

⏰ **{datetime.now().strftime('%H:%M:%S')}**"""

    send_telegram_message(stats_message)
    print(stats_message)

def monitor_blaze():
    """Monitor principal da Blaze"""
    log("🚀 Iniciando sistema com estratégias personalizáveis do usuário...")
    
    # Carregar estratégias do usuário
    estrategias = carregar_estrategias_csv()
    
    if not estrategias:
        log("❌ Nenhuma estratégia válida encontrada. Sistema não pode continuar.", "ERROR")
        return
    
    log(f"📋 Estratégias carregadas:")
    for estrategia in estrategias:
        status = "✅" if estrategia["active"] else "❌"
        log(f"  {status} {estrategia['original']}")
    
    # Mensagem de início
    start_message = f"""🎯 **SISTEMA ATIVADO COM ESTRATÉGIAS PERSONALIZÁVEIS**

📁 **Arquivo**: {CONFIG['estrategias_file']}
📋 **Estratégias carregadas**: {len(estrategias)}
⏰ **Início**: {datetime.now().strftime('%H:%M:%S')}
⚡ **Intervalo**: {CONFIG['interval_seconds']}s

🚀 **Aguardando sinais das suas estratégias...**"""
    
    send_telegram_message(start_message)
    
    while state.ativo:
        try:
            # Buscar novos resultados
            results = fetch_blaze_results()
            
            if results and results[0] != state.ultimo_resultado:
                state.ultimo_resultado = results[0]
                state.historico_resultados = results
                
                log(f"Novo resultado: {state.ultimo_resultado} ({get_color_emoji(convert_number_to_color(state.ultimo_resultado))})")
                
                # Processar estratégias do usuário
                processar_estrategias_usuario(results, estrategias)
            
            time.sleep(CONFIG["interval_seconds"])
            
        except KeyboardInterrupt:
            log("Sistema interrompido pelo usuário")
            state.ativo = False
        except Exception as e:
            log(f"Erro no monitor: {e}", "ERROR")
            time.sleep(10)

def main():
    """Função principal"""
    print("=" * 60)
    print("🎯 SISTEMA DE SINAIS COM ESTRATÉGIAS PERSONALIZÁVEIS")
    print("=" * 60)
    print(f"📁 Arquivo de estratégias: {CONFIG['estrategias_file']}")
    print(f"💬 Canal: {CHAT_ID}")
    print(f"⚡ Intervalo: {CONFIG['interval_seconds']}s")
    print("=" * 60)
    print("\nComandos:")
    print("  'stats' - Enviar estatísticas")
    print("  'quit'  - Parar sistema")
    print("\n🚀 Iniciando em 3 segundos...")
    
    time.sleep(3)
    
    try:
        monitor_blaze()
    except KeyboardInterrupt:
        log("Sistema finalizado")
    finally:
        mostrar_estatisticas()
        
        end_message = f"""🛑 **SISTEMA FINALIZADO**

📊 **Resumo da sessão**:
• Sinais enviados: {state.stats['sinais_enviados']}
• Estratégias testadas: {state.stats['estrategias_testadas']}

⏰ **Finalizado**: {datetime.now().strftime('%H:%M:%S')}"""
        
        send_telegram_message(end_message)
        print("\n✅ Sistema finalizado com sucesso!")

if __name__ == "__main__":
    main() 