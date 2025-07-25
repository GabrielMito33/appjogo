#!/usr/bin/env python3
"""
🎯 EXEMPLO PRÁTICO: CRIAR SEU BOT PERSONALIZADO
Script demonstrando como criar um bot com suas estratégias
"""

import json
from pathlib import Path

def criar_meu_bot_exemplo():
    """Exemplo de como criar um bot personalizado"""
    
    print("🤖 CRIANDO BOT PERSONALIZADO - EXEMPLO")
    print("=" * 45)
    
    # Configuração do seu bot
    meu_bot = {
        "id": "meu_bot_especial",
        "name": "Meu Bot Especial",
        "token": "SEU_TOKEN_AQUI",  # ← Substitua pelo seu token
        "chat_id": "SEU_CHAT_ID",   # ← Substitua pelo seu chat ID
        "active": True,
        "estrategias_file": "meu_bot_especial_estrategias.csv",
        "config": {
            "max_gales": 2,
            "protection": True,
            "interval_seconds": 3,
            "enable_alerts": True,
            "confidence_threshold": 80,  # 80% de confiança
            "max_daily_signals": 15     # Máximo 15 sinais por dia
        },
        "mensagens": {
            "sinal_template": """🔥 **MEU BOT ESPECIAL** 🔥

🎯 **Estratégia**: {estrategia}
🎰 **APOSTAR**: {cor_emoji} **{cor_nome}**
🛡️ **PROTEÇÃO**: ⚪ BRANCO
🔄 **Gales**: {max_gales}x

📊 **Análise**:
• Números: {numeros}
• Cores: {cores_emoji}

⏰ {timestamp}

🚀 **VAMOS LUCRAR JUNTOS!**""",
            
            "alerta_template": """⚠️ **ATENÇÃO - MEU BOT** ⚠️

📈 **{estrategia}** se formando
🎯 Prepare-se para o próximo sinal!

⏰ {timestamp}""",
            
            "stats_template": """📊 **RELATÓRIO DO MEU BOT**

🎯 Sinais hoje: {sinais}
✅ Acertos: {wins}
❌ Erros: {losses}  
⚪ Brancos: {brancos}
📈 Taxa de sucesso: {taxa}%

⏰ {timestamp}""",
            
            "inicio_template": """🚀 **MEU BOT ESPECIAL ONLINE**

📋 {total_estrategias} estratégias carregadas
🎯 Sistema operacional
💪 Pronto para lucrar!

⏰ {timestamp}""",
            
            "fim_template": """🛑 **MEU BOT ESPECIAL OFFLINE**

📊 Sinais enviados hoje: {sinais}
💰 Obrigado por usar meu bot!

⏰ {timestamp}"""
        }
    }
    
    # Minhas estratégias personalizadas
    minhas_estrategias = [
        "V-V=P",         # Minha estratégia favorita
        "P-P=V",         # Estratégia clássica
        "V-V-P=V",       # Padrão de 3
        "1-1=P",         # Números específicos
        "8-8=V",         # Números da sorte
        "X-V-V=P",       # Com wildcard
        "V-X-P=V",       # Padrão especial
    ]
    
    # Salvar configuração
    config_file = Path("config_bots.json")
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {"bots": [], "global_config": {}}
    
    # Adicionar meu bot
    config["bots"].append(meu_bot)
    
    # Salvar configuração atualizada
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # Criar arquivo de estratégias
    estrategias_file = Path("meu_bot_especial_estrategias.csv")
    with open(estrategias_file, 'w', encoding='utf-8') as f:
        for estrategia in minhas_estrategias:
            f.write(f"{estrategia}\n")
    
    print("✅ MEU BOT CRIADO COM SUCESSO!")
    print(f"📁 Configuração salva em: {config_file}")
    print(f"📋 Estratégias salvas em: {estrategias_file}")
    print()
    print("🚀 PRÓXIMOS PASSOS:")
    print("1. Edite o token e chat_id no config_bots.json")
    print("2. Personalize suas estratégias no CSV")
    print("3. Execute: python gerenciador_multi_bots.py")
    print()
    print("🎯 SEU BOT ESTÁ PRONTO!")

if __name__ == "__main__":
    criar_meu_bot_exemplo() 