#!/usr/bin/env python3
"""
📊 ANÁLISE RÁPIDA DO SISTEMA
Análise rápida dos dados coletados na execução
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def analisar_dados():
    db_path = Path("data/sistema_signals.db")
    
    if not db_path.exists():
        print("❌ Banco de dados não encontrado")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 ANÁLISE RÁPIDA DOS DADOS COLETADOS")
        print("=" * 45)
        
        # Total de sinais
        cursor.execute("SELECT COUNT(*) FROM signals")
        total = cursor.fetchone()[0]
        print(f"🎯 Total de sinais enviados: {total}")
        
        if total == 0:
            print("📭 Nenhum sinal encontrado")
            return
        
        # Sinais por estratégia
        cursor.execute("""
            SELECT strategy_name, COUNT(*) as count, 
                   AVG(confidence) as avg_confidence,
                   MIN(confidence) as min_conf,
                   MAX(confidence) as max_conf
            FROM signals 
            GROUP BY strategy_name
        """)
        
        print(f"\n📈 PERFORMANCE POR ESTRATÉGIA:")
        print("-" * 45)
        
        estrategias = cursor.fetchall()
        for est in estrategias:
            print(f"🎯 {est[0]}")
            print(f"   Sinais: {est[1]}")
            print(f"   Confiança: {est[2]:.1f}% (min: {est[3]}%, max: {est[4]}%)")
            print()
        
        # Análise temporal
        cursor.execute("""
            SELECT timestamp, strategy_name, confidence, blaze_results
            FROM signals 
            ORDER BY timestamp
        """)
        
        sinais = cursor.fetchall()
        
        if len(sinais) >= 2:
            primeiro = datetime.fromisoformat(sinais[0][0])
            ultimo = datetime.fromisoformat(sinais[-1][0])
            duracao = ultimo - primeiro
            
            print(f"⏰ ANÁLISE TEMPORAL:")
            print(f"   Primeiro sinal: {primeiro.strftime('%H:%M:%S')}")
            print(f"   Último sinal: {ultimo.strftime('%H:%M:%S')}")
            print(f"   Duração total: {duracao}")
            print(f"   Frequência: {total/duracao.total_seconds()*60:.2f} sinais/minuto")
            
            if total/duracao.total_seconds()*60 > 1.0:
                print("   ⚠️ ATENÇÃO: Frequência muito alta!")
        
        print(f"\n🔍 ÚLTIMOS 5 SINAIS:")
        print("-" * 45)
        
        for sinal in sinais[-5:]:
            timestamp = datetime.fromisoformat(sinal[0])
            resultados = json.loads(sinal[3])[:3] if sinal[3] else []
            print(f"⏰ {timestamp.strftime('%H:%M:%S')} | {sinal[1]} | {sinal[2]}% | {resultados}")
        
        # Análise dos resultados da Blaze
        print(f"\n🎲 ANÁLISE DOS RESULTADOS BLAZE:")
        print("-" * 45)
        
        todos_resultados = []
        for sinal in sinais:
            if sinal[3]:
                resultados = json.loads(sinal[3])
                todos_resultados.extend(resultados[:5])
        
        if todos_resultados:
            vermelhos = len([r for r in todos_resultados if 1 <= r <= 7])
            pretos = len([r for r in todos_resultados if 8 <= r <= 14]) 
            brancos = len([r for r in todos_resultados if r == 0])
            
            total_nums = len(todos_resultados)
            
            print(f"🔴 Vermelhos: {vermelhos} ({vermelhos/total_nums*100:.1f}%)")
            print(f"⚫ Pretos: {pretos} ({pretos/total_nums*100:.1f}%)")
            print(f"⚪ Brancos: {brancos} ({brancos/total_nums*100:.1f}%)")
            print(f"📊 Total analisado: {total_nums} resultados")
        
        conn.close()
        
        print(f"\n🎯 RECOMENDAÇÕES:")
        print("-" * 45)
        
        if total/duracao.total_seconds()*60 > 1.0:
            print("🔧 Reduzir frequência de sinais (intervalo maior)")
        
        if len(estrategias) == 1:
            print("🔧 Ativar mais estratégias para diversificar")
        
        for est in estrategias:
            if est[2] < 80:  # confiança média
                print(f"🔧 Aumentar confiança mínima para {est[0]}")
            
            if est[1] > 10:  # muitos sinais
                print(f"🔧 Limitar sinais diários para {est[0]}")
        
        print(f"\n✅ Execute 'python otimizador_sistema.py' para otimização automática")
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")

if __name__ == "__main__":
    analisar_dados() 