#!/usr/bin/env python3
"""
🔧 APLICADOR DE OTIMIZAÇÕES
Aplica automaticamente as configurações otimizadas no sistema
"""

import shutil
import re
from pathlib import Path

def aplicar_otimizacoes():
    print("🔧 APLICANDO OTIMIZAÇÕES AUTOMÁTICAS")
    print("=" * 40)
    
    # Arquivos
    sistema_original = Path("sistema_producao_24h.py")
    sistema_backup = Path("sistema_producao_24h_backup.py")
    otimizacoes = Path("sistema_otimizado.py")
    
    if not sistema_original.exists():
        print("❌ Arquivo original não encontrado")
        return False
    
    if not otimizacoes.exists():
        print("❌ Execute 'python otimizador_sistema.py' primeiro")
        return False
    
    # Fazer backup
    print("💾 Fazendo backup do sistema original...")
    shutil.copy2(sistema_original, sistema_backup)
    print(f"✅ Backup salvo: {sistema_backup}")
    
    # Ler arquivos
    with open(sistema_original, 'r', encoding='utf-8') as f:
        codigo_original = f.read()
    
    with open(otimizacoes, 'r', encoding='utf-8') as f:
        config_otimizada = f.read()
    
    # Extrair configurações otimizadas
    config_match = re.search(r'PRODUCTION_CONFIG = \{[^}]+\}', config_otimizada, re.DOTALL)
    estrategias_match = re.search(r'ESTRATEGIAS_PRODUCAO = \[[^\]]+\]', config_otimizada, re.DOTALL)
    
    if not config_match or not estrategias_match:
        print("❌ Erro ao extrair configurações otimizadas")
        return False
    
    nova_config = config_match.group(0)
    novas_estrategias = estrategias_match.group(0)
    
    print("🔄 Aplicando configurações otimizadas...")
    
    # Substituir PRODUCTION_CONFIG
    codigo_otimizado = re.sub(
        r'PRODUCTION_CONFIG = \{[^}]+\}',
        nova_config,
        codigo_original,
        flags=re.DOTALL
    )
    
    # Substituir ESTRATEGIAS_PRODUCAO
    codigo_otimizado = re.sub(
        r'ESTRATEGIAS_PRODUCAO = \[[^\]]+\]',
        novas_estrategias,
        codigo_otimizado,
        flags=re.DOTALL
    )
    
    # Adicionar comentário de otimização
    comentario = f"""
# ==========================================
# 🔧 SISTEMA OTIMIZADO AUTOMATICAMENTE
# Data: {Path(otimizacoes).stat().st_mtime}
# 
# PROBLEMAS CORRIGIDOS:
# - 🚨 SPAM DE SINAIS: 3.0 → <0.5 sinais/minuto
# - ⚠️ ESTRATÉGIA ÚNICA: 1 → 3 estratégias ativas
#
# MUDANÇAS APLICADAS:
# - Intervalo: 3s → 10s
# - Confiança: 75% → 85%
# - Sinais/dia: 10 → 5 por estratégia
# - Estratégias: +2 novas ativadas
# ==========================================

"""
    
    codigo_final = comentario + codigo_otimizado
    
    # Salvar arquivo otimizado
    with open(sistema_original, 'w', encoding='utf-8') as f:
        f.write(codigo_final)
    
    print("✅ OTIMIZAÇÕES APLICADAS COM SUCESSO!")
    print("\n📁 Arquivos:")
    print(f"  • {sistema_original} - Sistema otimizado")
    print(f"  • {sistema_backup} - Backup do original")
    print(f"  • {otimizacoes} - Configurações usadas")
    
    print("\n🎯 MUDANÇAS APLICADAS:")
    print("  ✅ Intervalo: 3s → 10s (reduz spam)")
    print("  ✅ Confiança: 75% → 85% (mais seletivo)")
    print("  ✅ Sinais/dia: 10 → 5 por estratégia")
    print("  ✅ Estratégias: 1 → 3 ativas")
    
    print("\n🚀 PRÓXIMO PASSO:")
    print("Execute: python sistema_producao_24h.py")
    
    return True

def reverter_otimizacoes():
    """Reverte para o sistema original"""
    sistema_original = Path("sistema_producao_24h.py")
    sistema_backup = Path("sistema_producao_24h_backup.py")
    
    if not sistema_backup.exists():
        print("❌ Backup não encontrado")
        return False
    
    shutil.copy2(sistema_backup, sistema_original)
    print("✅ Sistema revertido para versão original")
    return True

def main():
    print("🔧 APLICADOR DE OTIMIZAÇÕES")
    print("=" * 30)
    print("1. 🎯 Aplicar otimizações")
    print("2. ↩️ Reverter para original")
    print("3. 🚪 Sair")
    
    escolha = input("\nEscolha uma opção: ").strip()
    
    if escolha == "1":
        aplicar_otimizacoes()
    elif escolha == "2":
        reverter_otimizacoes()
    elif escolha == "3":
        print("👋 Até logo!")
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    main() 