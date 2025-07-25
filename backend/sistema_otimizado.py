# CONFIGURAÇÕES OTIMIZADAS - 25/07/2025 11:22
# Baseado na análise de 3 sinais

PRODUCTION_CONFIG = {
    "max_gales": 2,
    "protection": True,
    "interval_seconds": 10,  # Otimizado: antes era 3
    "confidence_threshold": 85,  # Otimizado: antes era 75
    "max_concurrent_gales": 3,
    "max_daily_signals_per_strategy": 5,  # Otimizado: antes era 10
    "api_timeout": 15,
    "max_retries": 3,
    "backup_interval": 3600,
    "stats_interval": 1800,
    "health_check_interval": 300,
    "log_level": "INFO"
}

# ESTRATÉGIAS OTIMIZADAS
ESTRATEGIAS_PRODUCAO = [
    {
        "id": 1,
        "name": "🔴 Double Red Alert",
        "conditions": ["V", "V"],
        "bet_direction": "P",
        "priority": 1,
        "active": True,
        "min_confidence": 85,  # Otimizado
        "max_daily_signals": 5  # Otimizado
    },
    {
        "id": 2,
        "name": "⚫ Double Black Alert",
        "conditions": ["P", "P"],
        "bet_direction": "V",
        "priority": 1,
        "active": True,  # ATIVADA para diversificar
        "min_confidence": 85,
        "max_daily_signals": 5
    },
    {
        "id": 3,
        "name": "🎯 Triple Pattern",
        "conditions": ["V", "V", "P"],
        "bet_direction": "V",
        "priority": 2,
        "active": True,  # ATIVADA para diversificar
        "min_confidence": 80,
        "max_daily_signals": 3  # Menos sinais para padrões mais complexos
    }
]

# PROBLEMAS CORRIGIDOS:
# - 🚨 SPAM DE SINAIS: 3.0 sinais/minuto (recomendado: <0.5)
# - ⚠️ ESTRATÉGIA ÚNICA: Apenas 1 estratégia detectando padrões

# MUDANÇAS APLICADAS:
# - Reduzido spam aumentando intervalo e confiança
