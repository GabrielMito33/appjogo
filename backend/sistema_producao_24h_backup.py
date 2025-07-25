#!/usr/bin/env python3
"""
🔥 SISTEMA DE SINAIS PRODUÇÃO 24/7 V3.0
Sistema robusto para operação contínua com logs completos, backup e recovery automático
"""

import time
import requests
import json
import os
import logging
import sqlite3
import traceback
import threading
import signal
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
from logging.handlers import RotatingFileHandler

# === CONFIGURAÇÕES DE PRODUÇÃO ===
BOT_TOKEN = "8106969377:AAHp4PRKZN-RHb1GxR3C3l7PzikFHEcRsck"
CHAT_ID = "-1002852101467"
ADMIN_CHAT_ID = CHAT_ID  # Para alertas de sistema
BLAZE_API_URL = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Configurações robustas
PRODUCTION_CONFIG = {
    "max_gales": 2,
    "protection": True,
    "interval_seconds": 3,
    "enable_alerts": True,
    "confidence_threshold": 75,
    "max_concurrent_gales": 3,
    "api_timeout": 15,
    "max_retries": 3,
    "backup_interval": 3600,  # 1 hora
    "stats_interval": 1800,   # 30 minutos
    "health_check_interval": 300,  # 5 minutos
    "log_level": "INFO",
    "auto_restart_errors": 5,
    "maintenance_hour": 4,  # 4h da manhã para manutenção
}

# Estratégias otimizadas para produção
ESTRATEGIAS_PRODUCAO = [
    {
        "id": 1,
        "name": "🔴 Double Red Alert",
        "conditions": ["V", "V"],
        "bet_direction": "P",
        "priority": 1,
        "active": True,
        "min_confidence": 85,
        "max_daily_signals": 10
    },
    {
        "id": 2,
        "name": "⚫ Double Black Alert", 
        "conditions": ["P", "P"],
        "bet_direction": "V",
        "priority": 1,
        "active": True,
        "min_confidence": 85,
        "max_daily_signals": 10
    },
    {
        "id": 3,
        "name": "🎯 Triple Sequence",
        "conditions": ["V", "V", "P"],
        "bet_direction": "V",
        "priority": 2,
        "active": True,
        "min_confidence": 80,
        "max_daily_signals": 5
    },
    {
        "id": 4,
        "name": "💎 Mega Pattern",
        "conditions": ["P", "P", "P"],
        "bet_direction": "V",
        "priority": 1,
        "active": True,
        "min_confidence": 90,
        "max_daily_signals": 3
    },
    {
        "id": 5,
        "name": "⚡ Lightning Strike",
        "conditions": ["V", "P", "V", "P"],
        "bet_direction": "V",
        "priority": 3,
        "active": True,
        "min_confidence": 75,
        "max_daily_signals": 8
    }
]

# === SISTEMA DE LOGS COMPLETO ===
def setup_logging():
    """Configurar sistema de logs completo"""
    # Criar diretórios
    Path("logs").mkdir(exist_ok=True)
    Path("backup").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger('SistemaSignals')
    logger.setLevel(getattr(logging, PRODUCTION_CONFIG["log_level"]))
    
    # Formatador
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo principal (rotativo)
    main_handler = RotatingFileHandler(
        'logs/sistema_principal.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    main_handler.setFormatter(formatter)
    logger.addHandler(main_handler)
    
    # Handler para arquivo diário
    today = datetime.now().strftime('%Y-%m-%d')
    daily_handler = logging.FileHandler(f'logs/sinais_{today}.log', encoding='utf-8')
    daily_handler.setFormatter(formatter)
    logger.addHandler(daily_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Logger específico para erros
    error_logger = logging.getLogger('Errors')
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10
    )
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    
    return logger

logger = setup_logging()

# === BANCO DE DADOS PARA PERSISTÊNCIA ===
class DatabaseManager:
    def __init__(self):
        self.db_path = "data/sistema_signals.db"
        self.init_database()
    
    def init_database(self):
        """Inicializar banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de sinais
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_id INTEGER,
                    strategy_name TEXT,
                    bet_direction TEXT,
                    confidence INTEGER,
                    timestamp DATETIME,
                    result TEXT,
                    profit_loss REAL,
                    gale_count INTEGER,
                    blaze_results TEXT
                )
            ''')
            
            # Tabela de estatísticas diárias
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    signals_sent INTEGER,
                    wins INTEGER,
                    losses INTEGER,
                    brancos INTEGER,
                    total_profit REAL,
                    best_strategy TEXT,
                    uptime_seconds INTEGER
                )
            ''')
            
            # Tabela de logs de sistema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    level TEXT,
                    component TEXT,
                    message TEXT,
                    extra_data TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco: {e}")
    
    def save_signal(self, signal_data: Dict):
        """Salvar sinal no banco"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO signals 
                (strategy_id, strategy_name, bet_direction, confidence, timestamp, blaze_results)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                signal_data['strategy_id'],
                signal_data['strategy_name'],
                signal_data['bet_direction'],
                signal_data['confidence'],
                signal_data['timestamp'],
                json.dumps(signal_data['blaze_results'])
            ))
            
            conn.commit()
            signal_id = cursor.lastrowid
            conn.close()
            return signal_id
            
        except Exception as e:
            logger.error(f"Erro ao salvar sinal: {e}")
            return None
    
    def update_signal_result(self, signal_id: int, result: str, gale_count: int = 0):
        """Atualizar resultado do sinal"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE signals 
                SET result = ?, gale_count = ?
                WHERE id = ?
            ''', (result, gale_count, signal_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar resultado: {e}")
    
    def get_daily_stats(self, date: str = None) -> Dict:
        """Obter estatísticas do dia"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM daily_stats WHERE date = ?
            ''', (date,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "date": result[0],
                    "signals_sent": result[1],
                    "wins": result[2],
                    "losses": result[3],
                    "brancos": result[4],
                    "total_profit": result[5],
                    "best_strategy": result[6],
                    "uptime_seconds": result[7]
                }
            return {}
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

db = DatabaseManager()

# === SISTEMA DE ESTADO ROBUSTO ===
class ProductionSystemState:
    def __init__(self):
        self.ativo = True
        self.maintenance_mode = False
        self.pause_until = None
        
        # Controle de conexão
        self.last_blaze_success = None
        self.last_telegram_success = None
        self.consecutive_errors = 0
        
        # Dados em tempo real
        self.ultimo_resultado = None
        self.historico_resultados = []
        self.gales_ativos = {}
        
        # Estatísticas em memória
        self.session_stats = {
            "inicio": datetime.now(),
            "sinais_enviados": 0,
            "wins": 0,
            "losses": 0,
            "brancos": 0,
            "gales_1": 0,
            "gales_2": 0,
            "ultimo_sinal": None,
            "ultimo_backup": None,
            "errors_count": 0,
            "api_calls": 0,
            "telegram_messages": 0
        }
        
        # Controle por estratégia
        self.strategy_daily_count = {str(s["id"]): 0 for s in ESTRATEGIAS_PRODUCAO}
        
        # Threading locks
        self.state_lock = threading.Lock()
        
        logger.info("Estado do sistema inicializado")

state = ProductionSystemState()

# === FUNÇÕES AUXILIARES ROBUSTAS ===
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

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator para retry automático"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Falha após {max_retries} tentativas em {func.__name__}: {e}")
                        raise
                    logger.warning(f"Tentativa {attempt + 1} falhou em {func.__name__}: {e}")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

@retry_on_failure(max_retries=PRODUCTION_CONFIG["max_retries"])
def fetch_blaze_results() -> List[int]:
    """Busca resultados da Blaze com retry"""
    response = requests.get(
        BLAZE_API_URL, 
        timeout=PRODUCTION_CONFIG["api_timeout"]
    )
    
    if response.status_code == 200:
        data = response.json()
        results = [item['roll'] for item in data]
        
        state.last_blaze_success = datetime.now()
        state.session_stats["api_calls"] += 1
        
        logger.debug(f"Blaze API: Obtidos {len(results)} resultados")
        return results
    else:
        raise Exception(f"Blaze API retornou status {response.status_code}")

@retry_on_failure(max_retries=PRODUCTION_CONFIG["max_retries"])
def send_telegram_message(message: str, chat_id: str = None, parse_mode: str = "Markdown") -> bool:
    """Envia mensagem para o Telegram com retry"""
    if not chat_id:
        chat_id = CHAT_ID
    
    response = requests.post(
        f"{TELEGRAM_API_BASE}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        },
        timeout=PRODUCTION_CONFIG["api_timeout"]
    )
    
    if response.status_code == 200:
        state.last_telegram_success = datetime.now()
        state.session_stats["telegram_messages"] += 1
        logger.debug("Mensagem Telegram enviada com sucesso")
        return True
    else:
        raise Exception(f"Telegram API retornou status {response.status_code}")

def send_admin_alert(message: str, level: str = "WARNING"):
    """Envia alerta para admin"""
    try:
        alert_message = f"🚨 **ALERTA DO SISTEMA** 🚨\n\n**Nível**: {level}\n**Horário**: {datetime.now().strftime('%H:%M:%S')}\n**Mensagem**: {message}"
        send_telegram_message(alert_message, ADMIN_CHAT_ID)
        logger.warning(f"Alerta admin enviado: {message}")
    except Exception as e:
        logger.error(f"Erro ao enviar alerta admin: {e}")

def calculate_advanced_confidence(strategy: Dict, results: List[int]) -> int:
    """Calcula confiança avançada baseada em múltiplos fatores"""
    base_confidence = strategy.get("min_confidence", 70)
    
    # Fator 1: Histórico da estratégia
    strategy_id = str(strategy["id"])
    today_count = state.strategy_daily_count.get(strategy_id, 0)
    max_daily = strategy.get("max_daily_signals", 10)
    
    if today_count >= max_daily:
        return 0  # Estratégia já usada demais hoje
    
    # Fator 2: Horário (melhor performance em certos horários)
    hour = datetime.now().hour
    if 6 <= hour <= 22:  # Horário comercial
        time_bonus = 5
    else:
        time_bonus = -10
    
    # Fator 3: Padrão nos resultados recentes
    colors = [convert_number_to_color(r) for r in results[:10]]
    color_diversity = len(set(colors)) / len(colors) if colors else 0
    diversity_bonus = int(color_diversity * 10)
    
    # Fator 4: Intervalo desde último sinal
    if state.session_stats["ultimo_sinal"]:
        minutes_since = (datetime.now() - state.session_stats["ultimo_sinal"]).total_seconds() / 60
        if minutes_since < 5:
            interval_penalty = -15  # Evitar spam
        else:
            interval_penalty = 0
    else:
        interval_penalty = 0
    
    final_confidence = base_confidence + time_bonus + diversity_bonus + interval_penalty
    final_confidence = max(0, min(100, final_confidence))
    
    logger.debug(f"Confiança calculada para {strategy['name']}: {final_confidence}% (base: {base_confidence}, time: {time_bonus}, diversity: {diversity_bonus}, interval: {interval_penalty})")
    
    return final_confidence

def check_strategy_match(strategy: Dict, results: List[int]) -> bool:
    """Verifica se estratégia faz match"""
    if not strategy.get("active", True):
        return False
    
    # Verificar limite diário
    strategy_id = str(strategy["id"])
    if state.strategy_daily_count.get(strategy_id, 0) >= strategy.get("max_daily_signals", 10):
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

def send_production_signal(strategy: Dict, results: List[int]):
    """Envia sinal em ambiente de produção"""
    confidence = calculate_advanced_confidence(strategy, results)
    
    if confidence < PRODUCTION_CONFIG["confidence_threshold"]:
        logger.info(f"Sinal {strategy['name']} descartado - baixa confiança: {confidence}%")
        return
    
    with state.state_lock:
        bet_direction = strategy["bet_direction"]
        color_emoji = get_color_emoji(bet_direction)
        color_name = get_color_name(bet_direction)
        
        # ID único para o sinal
        signal_id = f"{strategy['id']}_{int(time.time())}"
        
        # Construir mensagem otimizada
        signal_message = f"""🎲 **SINAL DETECTADO** 🔥

🎯 **Estratégia**: {strategy['name']}
🎰 **Entrada para**: {color_emoji} **{color_name}**
💰 **Proteção no**: ⚪ **BRANCO**
♻️ **Gales**: Até {PRODUCTION_CONFIG['max_gales']}

📊 **Análise Técnica**:
• Últimos: {results[:5]}
• Cores: {' '.join([get_color_emoji(convert_number_to_color(r)) for r in results[:5]])}
• Confiança: {confidence}% ⚡
• Prioridade: {strategy['priority']}

⏰ **{datetime.now().strftime('%H:%M:%S')}** | 🤖 **V3.0 Auto**

🍀 **BOA SORTE!** 🚀"""

        try:
            if send_telegram_message(signal_message):
                # Salvar no banco
                signal_data = {
                    "strategy_id": strategy["id"],
                    "strategy_name": strategy["name"],
                    "bet_direction": bet_direction,
                    "confidence": confidence,
                    "timestamp": datetime.now(),
                    "blaze_results": results[:10]
                }
                
                db_signal_id = db.save_signal(signal_data)
                
                # Registrar estado do gale
                state.gales_ativos[signal_id] = {
                    "db_id": db_signal_id,
                    "strategy_id": strategy["id"],
                    "strategy_name": strategy["name"],
                    "bet_direction": bet_direction,
                    "confidence": confidence,
                    "timestamp": datetime.now(),
                    "gale_count": 0,
                    "status": "active"
                }
                
                # Atualizar estatísticas
                state.session_stats["sinais_enviados"] += 1
                state.session_stats["ultimo_sinal"] = datetime.now()
                state.strategy_daily_count[str(strategy["id"])] += 1
                
                logger.info(f"✅ SINAL ENVIADO: {strategy['name']} -> {color_name} (Confiança: {confidence}%)")
                
                # Log detalhado
                logger.info(f"Signal Details - ID: {signal_id}, Strategy: {strategy['id']}, Results: {results[:5]}, Confidence: {confidence}%")
                
            else:
                logger.error(f"❌ Falha ao enviar sinal: {strategy['name']}")
                state.session_stats["errors_count"] += 1
                
        except Exception as e:
            logger.error(f"Erro crítico ao enviar sinal: {e}")
            logger.error(traceback.format_exc())
            send_admin_alert(f"Erro crítico ao enviar sinal: {e}")

def check_gale_results_production(new_result: int):
    """Verifica resultados dos gales em produção"""
    result_color = convert_number_to_color(new_result)
    completed_gales = []
    
    with state.state_lock:
        for signal_id, gale_info in state.gales_ativos.items():
            if gale_info["status"] != "active":
                continue
                
            bet_direction = gale_info["bet_direction"]
            
            # Verificar resultado
            won = False
            result_type = "loss"
            
            if result_color == bet_direction:
                won = True
                result_type = "win"
            elif result_color == "B" and PRODUCTION_CONFIG["protection"]:
                won = True
                result_type = "white"
            
            if won:
                # WIN ou BRANCO
                send_result_message_production(gale_info, result_type, new_result)
                
                # Atualizar banco
                if gale_info.get("db_id"):
                    db.update_signal_result(gale_info["db_id"], result_type, gale_info["gale_count"])
                
                # Estatísticas
                if result_type == "win":
                    state.session_stats["wins"] += 1
                else:
                    state.session_stats["brancos"] += 1
                
                completed_gales.append(signal_id)
                gale_info["status"] = "completed_win"
                
                logger.info(f"✅ {result_type.upper()}: {gale_info['strategy_name']} - Gale {gale_info['gale_count']}")
                
            else:
                # LOSS - verificar gale
                gale_count = gale_info["gale_count"]
                
                if gale_count < PRODUCTION_CONFIG["max_gales"]:
                    # Próximo gale
                    gale_info["gale_count"] += 1
                    send_gale_message_production(gale_info, gale_count + 1)
                    
                    # Estatísticas de gale
                    if gale_count == 0:
                        state.session_stats["gales_1"] += 1
                    elif gale_count == 1:
                        state.session_stats["gales_2"] += 1
                        
                    logger.info(f"⚠️ GALE {gale_count + 1}: {gale_info['strategy_name']}")
                    
                else:
                    # LOSS final
                    send_result_message_production(gale_info, "loss", new_result)
                    
                    # Atualizar banco
                    if gale_info.get("db_id"):
                        db.update_signal_result(gale_info["db_id"], "loss", gale_info["gale_count"])
                    
                    state.session_stats["losses"] += 1
                    completed_gales.append(signal_id)
                    gale_info["status"] = "completed_loss"
                    
                    logger.info(f"❌ LOSS FINAL: {gale_info['strategy_name']} - Gale {gale_info['gale_count']}")
        
        # Remover gales completados
        for signal_id in completed_gales:
            if signal_id in state.gales_ativos:
                del state.gales_ativos[signal_id]

def send_result_message_production(gale_info: Dict, result_type: str, winning_number: int):
    """Envia mensagem de resultado em produção"""
    messages = {
        "win": f"✅ **WIN!** 🎉\n\n🎯 {gale_info['strategy_name']}\n🎲 {winning_number} {get_color_emoji(convert_number_to_color(winning_number))}\n💰 **PARABÉNS!** 🚀",
        "loss": f"❌ **LOSS** 😔\n\n🎯 {gale_info['strategy_name']}\n🎲 {winning_number} {get_color_emoji(convert_number_to_color(winning_number))}\n🚀 **Próxima será GREEN!** 💪",
        "white": f"⚪ **BRANCO - PROTEÇÃO!** 🛡️\n\n🎯 {gale_info['strategy_name']}\n🎲 {winning_number}\n✅ **Protegido com sucesso!** 🎯"
    }
    
    try:
        send_telegram_message(messages[result_type])
        logger.info(f"Resultado enviado: {result_type.upper()} para {gale_info['strategy_name']}")
    except Exception as e:
        logger.error(f"Erro ao enviar resultado: {e}")

def send_gale_message_production(gale_info: Dict, gale_number: int):
    """Envia mensagem de gale em produção"""
    gale_message = f"""⚠️ **VAMOS PARA O {gale_number}º GALE** ⚠️

🎯 **Estratégia**: {gale_info['strategy_name']}
🎰 **Manter**: {get_color_emoji(gale_info['bet_direction'])} **{get_color_name(gale_info['bet_direction'])}**
💰 **Proteção**: ⚪ **BRANCO**

💪 **Confiança mantida!** 🔥

⏰ **{datetime.now().strftime('%H:%M:%S')}**"""

    try:
        send_telegram_message(gale_message)
        logger.info(f"Gale {gale_number} enviado para {gale_info['strategy_name']}")
    except Exception as e:
        logger.error(f"Erro ao enviar gale: {e}")

def process_strategies_production(results: List[int]):
    """Processa estratégias em ambiente de produção"""
    if len(results) < 2:
        return
    
    logger.debug(f"Processando resultados: {results[:5]}")
    
    # Verificar resultados de gales primeiro
    check_gale_results_production(results[0])
    
    # Verificar novos sinais (limite de gales simultâneos)
    active_gales = len([g for g in state.gales_ativos.values() if g["status"] == "active"])
    
    if active_gales < PRODUCTION_CONFIG["max_concurrent_gales"]:
        # Processar estratégias por prioridade
        sorted_strategies = sorted(ESTRATEGIAS_PRODUCAO, key=lambda x: x["priority"])
        
        for strategy in sorted_strategies:
            if check_strategy_match(strategy, results):
                send_production_signal(strategy, results)
                break  # Apenas um sinal por ciclo

def backup_system_data():
    """Backup completo dos dados do sistema"""
    try:
        backup_dir = Path("backup") / datetime.now().strftime('%Y-%m-%d')
        backup_dir.mkdir(exist_ok=True)
        
        # Backup do banco de dados
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Copiar banco SQLite
        os.system(f'cp data/sistema_signals.db "backup/{timestamp}_database.db"')
        
        # Backup das configurações
        backup_data = {
            "timestamp": timestamp,
            "config": PRODUCTION_CONFIG,
            "strategies": ESTRATEGIAS_PRODUCAO,
            "session_stats": state.session_stats,
            "strategy_daily_count": state.strategy_daily_count
        }
        
        with open(f"backup/{timestamp}_config.json", "w") as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        state.session_stats["ultimo_backup"] = datetime.now()
        logger.info(f"Backup realizado: {timestamp}")
        
    except Exception as e:
        logger.error(f"Erro no backup: {e}")
        send_admin_alert(f"Falha no backup: {e}")

def send_production_statistics():
    """Envia estatísticas completas de produção"""
    try:
        tempo_ativo = datetime.now() - state.session_stats["inicio"]
        horas = int(tempo_ativo.total_seconds() // 3600)
        minutos = int((tempo_ativo.total_seconds() % 3600) // 60)
        
        total_results = state.session_stats["wins"] + state.session_stats["losses"] + state.session_stats["brancos"]
        win_rate = (state.session_stats["wins"] + state.session_stats["brancos"]) / max(total_results, 1) * 100
        
        # Estatísticas por estratégia
        strategy_stats = []
        for strategy in ESTRATEGIAS_PRODUCAO:
            count = state.strategy_daily_count.get(str(strategy["id"]), 0)
            strategy_stats.append(f"• {strategy['name']}: {count} sinais")
        
        stats_message = f"""📊 **RELATÓRIO DE PRODUÇÃO** 📊

⏰ **Tempo Ativo**: {horas}h {minutos}m
🎯 **Sinais Enviados**: {state.session_stats['sinais_enviados']}
✅ **Wins**: {state.session_stats['wins']}
❌ **Losses**: {state.session_stats['losses']}
⚪ **Brancos**: {state.session_stats['brancos']}
📈 **Taxa de Sucesso**: {win_rate:.1f}%

🎰 **Controle de Gales**:
• 1º Gale: {state.session_stats['gales_1']}
• 2º Gale: {state.session_stats['gales_2']}
• Gales Ativos: {len(state.gales_ativos)}

📡 **Performance do Sistema**:
• API Calls: {state.session_stats['api_calls']}
• Mensagens: {state.session_stats['telegram_messages']}
• Erros: {state.session_stats['errors_count']}
• Último Backup: {state.session_stats['ultimo_backup'].strftime('%H:%M') if state.session_stats['ultimo_backup'] else 'Nunca'}

🎯 **Estratégias Hoje**:
{chr(10).join(strategy_stats)}

🤖 **Sistema V3.0 operando em produção!** ⚡"""

        send_telegram_message(stats_message)
        logger.info("📊 Relatório de produção enviado")
        
    except Exception as e:
        logger.error(f"Erro ao enviar estatísticas: {e}")

def health_check():
    """Verificação de saúde do sistema"""
    issues = []
    
    # Verificar conectividade com Blaze
    if state.last_blaze_success:
        time_since = (datetime.now() - state.last_blaze_success).total_seconds()
        if time_since > 300:  # 5 minutos
            issues.append("API Blaze sem resposta há mais de 5 minutos")
    
    # Verificar conectividade com Telegram
    if state.last_telegram_success:
        time_since = (datetime.now() - state.last_telegram_success).total_seconds()
        if time_since > 300:
            issues.append("API Telegram sem resposta há mais de 5 minutos")
    
    # Verificar erros consecutivos
    if state.consecutive_errors > PRODUCTION_CONFIG["auto_restart_errors"]:
        issues.append(f"Muitos erros consecutivos: {state.consecutive_errors}")
    
    # Verificar uso de memória (simplificado)
    if len(state.historico_resultados) > 1000:
        state.historico_resultados = state.historico_resultados[:500]
        logger.info("Histórico de resultados limpo")
    
    # Reportar problemas
    if issues:
        for issue in issues:
            logger.warning(f"Health Check: {issue}")
            send_admin_alert(issue, "WARNING")
    else:
        logger.debug("Health check: Sistema operando normalmente")

def monitor_blaze_production():
    """Monitor principal para produção 24/7"""
    logger.info("🚀 Iniciando monitor de produção 24/7...")
    
    # Mensagem de início
    start_message = f"""🔥 **SISTEMA V3.0 PRODUÇÃO ATIVADO** 🔥

⏰ **Início**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
🎯 **Estratégias**: {len(ESTRATEGIAS_PRODUCAO)} configuradas
⚡ **Intervalo**: {PRODUCTION_CONFIG['interval_seconds']}s
🛡️ **Proteção**: ✅ Ativada
📊 **Confiança Mín**: {PRODUCTION_CONFIG['confidence_threshold']}%
🔄 **Backup**: A cada {PRODUCTION_CONFIG['backup_interval']//60} min
📈 **Relatórios**: A cada {PRODUCTION_CONFIG['stats_interval']//60} min

🚀 **Sistema robusto pronto para operar 24/7!**

💡 *Monitoramento automático ativo...*"""
    
    send_telegram_message(start_message)
    
    # Timers para tarefas periódicas
    last_backup = datetime.now()
    last_stats = datetime.now()
    last_health_check = datetime.now()
    
    while state.ativo:
        try:
            # Verificar modo manutenção
            if state.maintenance_mode:
                logger.info("Sistema em modo manutenção, pausando...")
                time.sleep(60)
                continue
            
            # Verificar pausa
            if state.pause_until and datetime.now() < state.pause_until:
                time.sleep(10)
                continue
            
            # Buscar novos resultados
            try:
                results = fetch_blaze_results()
                state.consecutive_errors = 0  # Reset contador de erros
                
                if results and results[0] != state.ultimo_resultado:
                    state.ultimo_resultado = results[0]
                    state.historico_resultados = results
                    
                    logger.info(f"🆕 Novo resultado: {state.ultimo_resultado} ({get_color_emoji(convert_number_to_color(state.ultimo_resultado))})")
                    
                    # Processar estratégias
                    process_strategies_production(results)
                
            except Exception as e:
                state.consecutive_errors += 1
                logger.error(f"Erro ao buscar/processar resultados: {e}")
                
                if state.consecutive_errors >= PRODUCTION_CONFIG["auto_restart_errors"]:
                    send_admin_alert(f"Sistema com {state.consecutive_errors} erros consecutivos. Reiniciando...")
                    # Aqui você pode implementar restart automático
            
            # Tarefas periódicas
            now = datetime.now()
            
            # Backup automático
            if (now - last_backup).seconds >= PRODUCTION_CONFIG["backup_interval"]:
                backup_system_data()
                last_backup = now
            
            # Estatísticas automáticas
            if (now - last_stats).seconds >= PRODUCTION_CONFIG["stats_interval"]:
                send_production_statistics()
                last_stats = now
            
            # Health check
            if (now - last_health_check).seconds >= PRODUCTION_CONFIG["health_check_interval"]:
                health_check()
                last_health_check = now
            
            # Manutenção automática (4h da manhã)
            if now.hour == PRODUCTION_CONFIG["maintenance_hour"] and now.minute == 0:
                logger.info("Iniciando manutenção automática...")
                backup_system_data()
                # Reset contadores diários
                state.strategy_daily_count = {str(s["id"]): 0 for s in ESTRATEGIAS_PRODUCAO}
                
            time.sleep(PRODUCTION_CONFIG["interval_seconds"])
            
        except KeyboardInterrupt:
            logger.info("🛑 Sistema interrompido pelo usuário")
            state.ativo = False
        except Exception as e:
            logger.error(f"Erro crítico no monitor: {e}")
            logger.error(traceback.format_exc())
            send_admin_alert(f"Erro crítico no monitor: {e}")
            time.sleep(30)  # Pausa maior para erros críticos

def handle_production_commands():
    """Thread para comandos em produção"""
    commands_help = """
🔧 COMANDOS DE PRODUÇÃO:
  stats          - Relatório completo
  status         - Status rápido
  backup         - Backup manual
  health         - Health check
  pause 10       - Pausar por 10 min
  resume         - Retomar
  maintenance    - Modo manutenção
  strategy 1     - Toggle estratégia
  restart        - Reiniciar sistema
  quit           - Parar sistema
"""
    
    print(commands_help)
    
    while state.ativo:
        try:
            cmd = input().strip().lower()
            
            if cmd in ['quit', 'exit', 'stop']:
                logger.info("🛑 Comando de parada recebido")
                state.ativo = False
                break
            elif cmd == 'stats':
                send_production_statistics()
            elif cmd == 'status':
                active_gales = len([g for g in state.gales_ativos.values() if g["status"] == "active"])
                logger.info(f"📊 Status: {state.session_stats['sinais_enviados']} sinais | {active_gales} gales ativos | {state.consecutive_errors} erros consecutivos")
            elif cmd == 'backup':
                backup_system_data()
            elif cmd == 'health':
                health_check()
            elif cmd.startswith('pause'):
                parts = cmd.split()
                minutes = int(parts[1]) if len(parts) > 1 else 10
                state.pause_until = datetime.now() + timedelta(minutes=minutes)
                logger.info(f"Sistema pausado por {minutes} minutos")
                send_admin_alert(f"Sistema pausado manualmente por {minutes} minutos")
            elif cmd == 'resume':
                state.pause_until = None
                logger.info("Sistema retomado")
                send_admin_alert("Sistema retomado manualmente")
            elif cmd == 'maintenance':
                state.maintenance_mode = not state.maintenance_mode
                status = "ativado" if state.maintenance_mode else "desativado"
                logger.info(f"Modo manutenção {status}")
                send_admin_alert(f"Modo manutenção {status}")
            elif cmd.startswith('strategy'):
                parts = cmd.split()
                if len(parts) > 1:
                    strategy_id = int(parts[1])
                    for strategy in ESTRATEGIAS_PRODUCAO:
                        if strategy["id"] == strategy_id:
                            strategy["active"] = not strategy.get("active", True)
                            status = "ativada" if strategy["active"] else "desativada"
                            logger.info(f"Estratégia {strategy['name']}: {status}")
                            break
            elif cmd == 'restart':
                logger.info("🔄 Reiniciando sistema...")
                send_admin_alert("Sistema sendo reiniciado manualmente")
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
        except Exception as e:
            logger.error(f"Erro no comando: {e}")

def signal_handler(signum, frame):
    """Handler para sinais do sistema (SIGTERM, SIGINT)"""
    logger.info(f"Sinal {signum} recebido. Finalizando sistema...")
    state.ativo = False

def main():
    """Função principal para produção"""
    # Configurar handlers de sinal
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*80)
    print("🔥 SISTEMA DE SINAIS PRODUÇÃO 24/7 V3.0")
    print("="*80)
    print(f"🤖 Bot: @blisscriador_bot")
    print(f"💬 Canal: {CHAT_ID}")
    print(f"🎯 Estratégias: {len(ESTRATEGIAS_PRODUCAO)}")
    print(f"⚡ Intervalo: {PRODUCTION_CONFIG['interval_seconds']}s")
    print(f"📊 Confiança: {PRODUCTION_CONFIG['confidence_threshold']}%")
    print(f"🔄 Backup: {PRODUCTION_CONFIG['backup_interval']//60}min")
    print(f"📈 Stats: {PRODUCTION_CONFIG['stats_interval']//60}min")
    print("="*80)
    
    logger.info("🚀 Iniciando sistema de produção...")
    
    # Backup inicial
    backup_system_data()
    
    # Iniciar thread de comandos
    cmd_thread = threading.Thread(target=handle_production_commands, daemon=True)
    cmd_thread.start()
    
    try:
        monitor_blaze_production()
    except Exception as e:
        logger.error(f"Erro crítico na execução: {e}")
        logger.error(traceback.format_exc())
        send_admin_alert(f"Sistema finalizado por erro crítico: {e}")
    finally:
        # Backup final e mensagem de encerramento
        logger.info("Realizando backup final...")
        backup_system_data()
        
        tempo_total = datetime.now() - state.session_stats["inicio"]
        end_message = f"""🛑 **SISTEMA V3.0 FINALIZADO**

⏰ **Finalizado**: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
⏱️ **Tempo Total**: {int(tempo_total.total_seconds() // 3600)}h {int((tempo_total.total_seconds() % 3600) // 60)}m
🎯 **Total de Sinais**: {state.session_stats['sinais_enviados']}
✅ **Wins**: {state.session_stats['wins']}
❌ **Losses**: {state.session_stats['losses']}
⚪ **Brancos**: {state.session_stats['brancos']}

📊 **Performance**:
• Taxa de Sucesso: {((state.session_stats['wins'] + state.session_stats['brancos']) / max(state.session_stats['sinais_enviados'], 1) * 100):.1f}%
• API Calls: {state.session_stats['api_calls']}
• Mensagens: {state.session_stats['telegram_messages']}

🤖 **Sistema V3.0 offline - Dados salvos** 💾"""
        
        send_telegram_message(end_message)
        logger.info("✅ Sistema finalizado com sucesso")
        print("\n✅ Sistema de produção finalizado!")

if __name__ == "__main__":
    main() 