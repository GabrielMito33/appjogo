#!/usr/bin/env python3
"""
🔧 OTIMIZADOR DO SISTEMA DE SINAIS
Analisa dados reais e otimiza configurações automaticamente
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class SistemaOtimizador:
    def __init__(self):
        self.db_path = Path("data/sistema_signals.db")
        self.config_file = Path("configuracoes_otimizadas.json")
        
    def analisar_performance(self) -> Dict:
        """Analisa performance do sistema baseado nos dados salvos"""
        if not self.db_path.exists():
            return {"erro": "Banco de dados não encontrado"}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Análise geral
            cursor.execute("SELECT COUNT(*) FROM signals")
            total_sinais = cursor.fetchone()[0]
            
            if total_sinais == 0:
                return {"erro": "Nenhum sinal encontrado para análise"}
            
            # Sinais por estratégia
            cursor.execute("""
                SELECT strategy_name, COUNT(*) as count, 
                       AVG(confidence) as avg_confidence
                FROM signals 
                GROUP BY strategy_name
            """)
            estrategias_stats = cursor.fetchall()
            
            # Últimos sinais
            cursor.execute("""
                SELECT strategy_name, confidence, timestamp, blaze_results
                FROM signals 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            ultimos_sinais = cursor.fetchall()
            
            # Análise temporal
            cursor.execute("""
                SELECT timestamp FROM signals 
                ORDER BY timestamp
            """)
            timestamps = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Calcular frequência
            if len(timestamps) > 1:
                primeiro = datetime.fromisoformat(timestamps[0])
                ultimo = datetime.fromisoformat(timestamps[-1])
                duracao_minutos = (ultimo - primeiro).total_seconds() / 60
                frequencia_por_minuto = total_sinais / max(duracao_minutos, 1)
            else:
                frequencia_por_minuto = 0
            
            return {
                "total_sinais": total_sinais,
                "estrategias": estrategias_stats,
                "ultimos_sinais": ultimos_sinais,
                "frequencia_por_minuto": round(frequencia_por_minuto, 2),
                "periodo_analise": f"{timestamps[0]} até {timestamps[-1]}" if timestamps else "N/A"
            }
            
        except Exception as e:
            return {"erro": f"Erro na análise: {e}"}
    
    def detectar_problemas(self, analise: Dict) -> List[str]:
        """Detecta problemas na configuração atual"""
        problemas = []
        
        if "erro" in analise:
            return [analise["erro"]]
        
        # Problema 1: Muitos sinais por minuto
        if analise["frequencia_por_minuto"] > 1.0:
            problemas.append(f"🚨 SPAM DE SINAIS: {analise['frequencia_por_minuto']} sinais/minuto (recomendado: <0.5)")
        
        # Problema 2: Apenas uma estratégia ativa
        if len(analise["estrategias"]) == 1:
            problemas.append("⚠️ ESTRATÉGIA ÚNICA: Apenas 1 estratégia detectando padrões")
        
        # Problema 3: Confiança muito baixa
        for estrategia in analise["estrategias"]:
            if estrategia[2] < 80:  # avg_confidence
                problemas.append(f"📉 CONFIANÇA BAIXA: {estrategia[0]} com {estrategia[2]:.1f}% (recomendado: >80%)")
        
        # Problema 4: Muitos sinais de uma estratégia
        for estrategia in analise["estrategias"]:
            if estrategia[1] > 10:  # count
                problemas.append(f"🔄 SPAM ESTRATÉGIA: {estrategia[0]} com {estrategia[1]} sinais (recomendado: <10/dia)")
        
        return problemas
    
    def gerar_configuracao_otimizada(self, analise: Dict, problemas: List[str]) -> Dict:
        """Gera configuração otimizada baseada na análise"""
        config_otimizada = {
            "timestamp": datetime.now().isoformat(),
            "analise_base": analise,
            "problemas_detectados": problemas,
            "configuracoes_otimizadas": {}
        }
        
        # Configurações base
        config = {
            "interval_seconds": 3,
            "confidence_threshold": 75,
            "max_concurrent_gales": 3,
            "max_daily_signals_per_strategy": 10
        }
        
        # Otimizações baseadas nos problemas
        if any("SPAM DE SINAIS" in p for p in problemas):
            config["interval_seconds"] = 10  # Mais lento
            config["confidence_threshold"] = 85  # Mais rigoroso
            config["max_daily_signals_per_strategy"] = 5  # Menos sinais
            config_otimizada["mudancas"] = ["Reduzido spam aumentando intervalo e confiança"]
        
        if any("CONFIANÇA BAIXA" in p for p in problemas):
            config["confidence_threshold"] = max(85, config["confidence_threshold"])
            config_otimizada["mudancas"] = config_otimizada.get("mudancas", []) + ["Aumentada confiança mínima"]
        
        if any("ESTRATÉGIA ÚNICA" in p for p in problemas):
            config["estrategias_sugestoes"] = [
                "Ativar mais estratégias para diversificar",
                "Verificar se outras estratégias estão configuradas corretamente",
                "Ajustar condições das estratégias menos ativas"
            ]
        
        config_otimizada["configuracoes_otimizadas"] = config
        
        return config_otimizada
    
    def aplicar_otimizacoes(self, config_otimizada: Dict) -> str:
        """Gera código Python com as otimizações"""
        config = config_otimizada["configuracoes_otimizadas"]
        
        codigo_otimizado = f'''# CONFIGURAÇÕES OTIMIZADAS - {datetime.now().strftime("%d/%m/%Y %H:%M")}
# Baseado na análise de {config_otimizada["analise_base"]["total_sinais"]} sinais

PRODUCTION_CONFIG = {{
    "max_gales": 2,
    "protection": True,
    "interval_seconds": {config["interval_seconds"]},  # Otimizado: antes era 3
    "confidence_threshold": {config["confidence_threshold"]},  # Otimizado: antes era 75
    "max_concurrent_gales": {config["max_concurrent_gales"]},
    "max_daily_signals_per_strategy": {config["max_daily_signals_per_strategy"]},  # Otimizado: antes era 10
    "api_timeout": 15,
    "max_retries": 3,
    "backup_interval": 3600,
    "stats_interval": 1800,
    "health_check_interval": 300,
    "log_level": "INFO"
}}

# ESTRATÉGIAS OTIMIZADAS
ESTRATEGIAS_PRODUCAO = [
    {{
        "id": 1,
        "name": "🔴 Double Red Alert",
        "conditions": ["V", "V"],
        "bet_direction": "P",
        "priority": 1,
        "active": True,
        "min_confidence": {config["confidence_threshold"]},  # Otimizado
        "max_daily_signals": {config["max_daily_signals_per_strategy"]}  # Otimizado
    }},
    {{
        "id": 2,
        "name": "⚫ Double Black Alert",
        "conditions": ["P", "P"],
        "bet_direction": "V",
        "priority": 1,
        "active": True,  # ATIVADA para diversificar
        "min_confidence": {config["confidence_threshold"]},
        "max_daily_signals": {config["max_daily_signals_per_strategy"]}
    }},
    {{
        "id": 3,
        "name": "🎯 Triple Pattern",
        "conditions": ["V", "V", "P"],
        "bet_direction": "V",
        "priority": 2,
        "active": True,  # ATIVADA para diversificar
        "min_confidence": {config["confidence_threshold"] - 5},
        "max_daily_signals": 3  # Menos sinais para padrões mais complexos
    }}
]

# PROBLEMAS CORRIGIDOS:
{chr(10).join([f"# - {p}" for p in config_otimizada["problemas_detectados"]])}

# MUDANÇAS APLICADAS:
{chr(10).join([f"# - {m}" for m in config_otimizada.get("mudancas", [])])}
'''
        
        return codigo_otimizado

def main():
    print("🔧 OTIMIZADOR DO SISTEMA DE SINAIS")
    print("=" * 40)
    
    otimizador = SistemaOtimizador()
    
    print("📊 Analisando performance atual...")
    analise = otimizador.analisar_performance()
    
    if "erro" in analise:
        print(f"❌ {analise['erro']}")
        return
    
    print(f"\n📈 RESULTADO DA ANÁLISE:")
    print(f"Total de sinais: {analise['total_sinais']}")
    print(f"Frequência: {analise['frequencia_por_minuto']} sinais/minuto")
    print(f"Período: {analise['periodo_analise']}")
    
    print(f"\n🎯 ESTRATÉGIAS ATIVAS:")
    for estrategia in analise["estrategias"]:
        print(f"  • {estrategia[0]}: {estrategia[1]} sinais (confiança média: {estrategia[2]:.1f}%)")
    
    print(f"\n🔍 Detectando problemas...")
    problemas = otimizador.detectar_problemas(analise)
    
    if not problemas:
        print("✅ Nenhum problema detectado! Sistema bem otimizado.")
        return
    
    print(f"\n⚠️ PROBLEMAS ENCONTRADOS:")
    for problema in problemas:
        print(f"  {problema}")
    
    print(f"\n🔧 Gerando configuração otimizada...")
    config_otimizada = otimizador.gerar_configuracao_otimizada(analise, problemas)
    
    # Salvar configuração
    with open("configuracoes_otimizadas.json", "w") as f:
        json.dump(config_otimizada, f, indent=2, default=str)
    
    # Gerar código otimizado
    codigo = otimizador.aplicar_otimizacoes(config_otimizada)
    
    with open("sistema_otimizado.py", "w", encoding="utf-8") as f:
        f.write(codigo)
    
    print(f"✅ OTIMIZAÇÃO CONCLUÍDA!")
    print(f"📁 Arquivos gerados:")
    print(f"  • configuracoes_otimizadas.json - Análise completa")
    print(f"  • sistema_otimizado.py - Configurações otimizadas")
    
    print(f"\n🚀 PRÓXIMOS PASSOS:")
    print(f"1. Revisar configurações em 'sistema_otimizado.py'")
    print(f"2. Aplicar mudanças no 'sistema_producao_24h.py'")
    print(f"3. Testar por pelo menos 1 hora")
    print(f"4. Executar otimizador novamente para validar")

if __name__ == "__main__":
    main() 