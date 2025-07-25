#!/usr/bin/env python3
"""
📊 Monitor de Logs em Tempo Real
Monitora e analisa logs do sistema de produção
"""

import os
import time
import json
from datetime import datetime
from pathlib import Path

def get_latest_log_file():
    """Obtém o arquivo de log mais recente"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return None
    
    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        return None
    
    # Retorna o mais recente
    return max(log_files, key=os.path.getmtime)

def analyze_logs():
    """Analisa logs e mostra estatísticas"""
    log_file = get_latest_log_file()
    if not log_file:
        print("❌ Nenhum arquivo de log encontrado")
        return
    
    print(f"📊 Analisando: {log_file}")
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Estatísticas
        total_lines = len(lines)
        info_count = len([l for l in lines if "INFO" in l])
        error_count = len([l for l in lines if "ERROR" in l])
        warning_count = len([l for l in lines if "WARNING" in l])
        
        # Últimas linhas importantes
        recent_errors = [l.strip() for l in lines[-50:] if "ERROR" in l]
        recent_signals = [l.strip() for l in lines[-20:] if "SINAL ENVIADO" in l]
        
        print(f"""
📈 ESTATÍSTICAS DOS LOGS:
========================
📝 Total de linhas: {total_lines}
ℹ️  Info: {info_count}
⚠️  Warnings: {warning_count}
❌ Errors: {error_count}

🎯 ÚLTIMOS SINAIS:
""")
        
        for signal in recent_signals[-5:]:
            timestamp = signal.split('|')[0].strip()
            message = signal.split('SINAL ENVIADO:')[1].strip() if 'SINAL ENVIADO:' in signal else signal
            print(f"  {timestamp} | {message}")
        
        if recent_errors:
            print(f"\n❌ ÚLTIMOS ERROS:")
            for error in recent_errors[-3:]:
                print(f"  {error}")
        
        print(f"\n⏰ Última atualização: {datetime.now().strftime('%H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Erro ao analisar logs: {e}")

def monitor_real_time():
    """Monitor em tempo real"""
    print("🔍 MONITOR DE LOGS EM TEMPO REAL")
    print("================================")
    print("Pressione Ctrl+C para sair\n")
    
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            
            print("🔍 MONITOR DE LOGS EM TEMPO REAL")
            print("================================")
            
            analyze_logs()
            
            print("\n🔄 Atualizando em 10 segundos...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\n👋 Monitor finalizado!")

def tail_logs():
    """Mostra últimas linhas do log"""
    log_file = get_latest_log_file()
    if not log_file:
        print("❌ Nenhum arquivo de log encontrado")
        return
    
    print(f"📜 ÚLTIMAS 20 LINHAS - {log_file}")
    print("=" * 60)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines[-20:]:
            # Colorir por tipo
            if "ERROR" in line:
                print(f"❌ {line.strip()}")
            elif "WARNING" in line:
                print(f"⚠️  {line.strip()}")
            elif "SINAL ENVIADO" in line:
                print(f"🎯 {line.strip()}")
            elif "INFO" in line:
                print(f"ℹ️  {line.strip()}")
            else:
                print(f"📝 {line.strip()}")
                
    except Exception as e:
        print(f"❌ Erro ao ler logs: {e}")

def main():
    """Menu principal"""
    while True:
        print("\n📊 MONITOR DE LOGS")
        print("==================")
        print("1. 📈 Análise completa")
        print("2. 🔍 Monitor em tempo real")
        print("3. 📜 Últimas linhas")
        print("4. 🚪 Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            analyze_logs()
        elif choice == "2":
            monitor_real_time()
        elif choice == "3":
            tail_logs()
        elif choice == "4":
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main() 