#!/bin/bash
# Script para iniciar sistema de produção 24/7

echo "🔥 INICIANDO SISTEMA DE PRODUÇÃO 24/7"
echo "======================================"

# Criar diretórios necessários
mkdir -p logs backup data

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado"
    exit 1
fi

# Instalar dependências se necessário
echo "📦 Verificando dependências..."
pip3 install requests sqlite3-worker > /dev/null 2>&1

# Fazer backup se existir dados anteriores
if [ -f "data/sistema_signals.db" ]; then
    echo "💾 Fazendo backup dos dados existentes..."
    cp data/sistema_signals.db backup/backup_$(date +%Y%m%d_%H%M%S).db
fi

# Iniciar sistema
echo "🚀 Iniciando sistema de produção..."
echo "📁 Logs em: logs/"
echo "💾 Backup em: backup/"
echo "🗄️ Banco em: data/"
echo ""
echo "Comandos disponíveis durante execução:"
echo "  stats    - Relatório completo"
echo "  status   - Status rápido"
echo "  backup   - Backup manual"
echo "  pause 10 - Pausar por 10 min"
echo "  quit     - Parar sistema"
echo ""
echo "🎯 Sistema iniciando em 3 segundos..."
sleep 3

# Executar sistema
python3 sistema_producao_24h.py

echo ""
echo "✅ Sistema finalizado!" 