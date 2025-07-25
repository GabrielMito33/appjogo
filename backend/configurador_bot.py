#!/usr/bin/env python3
"""
⚙️ CONFIGURADOR DE BOTS
Interface amigável para criar e configurar novos bots
Cada bot tem suas estratégias, mensagens e configurações próprias
"""

import json
import csv
from pathlib import Path
from typing import Dict, Any

class ConfiguradorBot:
    def __init__(self):
        self.config_file = Path("config_bots.json")
        self.templates_mensagens = {
            "padrao": {
                "sinal_template": "🎯 **SINAL {bot_name}** 🔥\n\n📋 **Estratégia**: {estrategia}\n🎰 **Apostar em**: {cor_emoji} **{cor_nome}**\n💰 **Proteção**: ⚪ **BRANCO**\n♻️ **Gales**: Até {max_gales}\n\n📊 **Análise**:\n• Últimos: {numeros}\n• Cores: {cores_emoji}\n\n⏰ **{timestamp}**\n\n🍀 **BOA SORTE!** 🚀",
                "alerta_template": "⚠️ **FIQUE ATENTO - {bot_name}!** ⚠️\n\n📋 **Estratégia**: {estrategia}\n🎯 **Próximo resultado pode ativar sinal**\n\n⏰ **{timestamp}**",
                "stats_template": "📊 **ESTATÍSTICAS - {bot_name}**\n\n🎯 **Sinais enviados**: {sinais}\n✅ **Wins**: {wins}\n❌ **Losses**: {losses}\n⚪ **Brancos**: {brancos}\n📈 **Taxa**: {taxa}%\n\n⏰ **{timestamp}**",
                "inicio_template": "🎯 **{bot_name} ATIVADO**\n\n📋 **Estratégias**: {total_estrategias}\n⏰ **Início**: {timestamp}\n🚀 **Aguardando sinais...**",
                "fim_template": "🛑 **{bot_name} FINALIZADO**\n\n📊 **Resumo**: {sinais} sinais enviados\n⏰ **Finalizado**: {timestamp}"
            },
            "vip": {
                "sinal_template": "💎 **SINAL VIP - {bot_name}** 💎\n\n🎯 **{estrategia}**\n🔥 **APOSTA**: {cor_emoji} {cor_nome}\n🛡️ **PROTEÇÃO**: ⚪ BRANCO\n\n📈 **Confiança**: {confianca}%\n⚡ **Gales**: {max_gales}x\n\n🕐 {timestamp}\n\n💰 **VIP EXCLUSIVE!**",
                "alerta_template": "🚨 **ALERTA VIP - {bot_name}** 🚨\n\n⚠️ **{estrategia}** próxima de ativar\n\n🕐 {timestamp}",
                "stats_template": "💎 **RELATÓRIO VIP - {bot_name}**\n\n📊 Sinais: {sinais} | Wins: {wins}\n📈 Performance: {taxa}%\n\n🕐 {timestamp}",
                "inicio_template": "💎 **{bot_name} VIP INICIADO**\n\n🎯 {total_estrategias} estratégias premium\n🚀 Sistema ativo!\n\n🕐 {timestamp}",
                "fim_template": "💎 **{bot_name} VIP FINALIZADO**\n\n📊 Total: {sinais} sinais\n🕐 {timestamp}"
            },
            "premium": {
                "sinal_template": "⭐ **PREMIUM {bot_name}** ⭐\n\n🎲 **Estratégia**: {estrategia}\n🎯 **ENTRADA**: {cor_emoji} {cor_nome}\n🔒 **STOP**: ⚪ BRANCO\n🔄 **Martingale**: {max_gales}x\n\n📊 **Dados**: {numeros}\n🎨 **Cores**: {cores_emoji}\n\n⏰ {timestamp}\n\n🚀 **VAMOS LUCRAR!**",
                "alerta_template": "🔔 **ATENÇÃO PREMIUM - {bot_name}** 🔔\n\n📈 **{estrategia}** se formando\n⚡ Prepare-se para entrada!\n\n⏰ {timestamp}",
                "stats_template": "⭐ **RELATÓRIO PREMIUM - {bot_name}**\n\n🎯 Sinais: {sinais}\n✅ Acertos: {wins}\n❌ Erros: {losses}\n⚪ Brancos: {brancos}\n📈 Eficiência: {taxa}%\n\n⏰ {timestamp}",
                "inicio_template": "⭐ **{bot_name} PREMIUM ONLINE**\n\n📋 {total_estrategias} estratégias carregadas\n🎯 Sistema em operação\n\n⏰ {timestamp}",
                "fim_template": "⭐ **{bot_name} PREMIUM OFFLINE**\n\n📊 Sinais enviados: {sinais}\n⏰ {timestamp}"
            }
        }
    
    def carregar_config_atual(self) -> Dict:
        """Carrega configuração atual ou cria uma nova"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "bots": [],
                "global_config": {
                    "blaze_api_url": "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1",
                    "backup_interval": 3600,
                    "log_level": "INFO",
                    "max_concurrent_bots": 5
                }
            }
    
    def salvar_config(self, config: Dict):
        """Salva configuração no arquivo"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuração salva em {self.config_file}")
    
    def criar_arquivo_estrategias(self, bot_id: str, estrategias_exemplo: bool = True):
        """Cria arquivo de estratégias para o bot"""
        estrategias_file = f"{bot_id}_estrategias.csv"
        
        if estrategias_exemplo:
            exemplos = [
                "V-V=P",
                "P-P=V", 
                "V-V-P=V",
                "P-P-P=V",
                "X-V-V=P",
                "X-P-P=V"
            ]
        else:
            exemplos = []
        
        with open(estrategias_file, 'w', encoding='utf-8') as f:
            for exemplo in exemplos:
                f.write(f"{exemplo}\n")
        
        print(f"✅ Arquivo de estratégias criado: {estrategias_file}")
        return estrategias_file
    
    def criar_novo_bot(self):
        """Interface para criar novo bot"""
        print("\n🤖 CRIANDO NOVO BOT")
        print("=" * 30)
        
        # Dados básicos
        bot_id = input("ID do bot (ex: bot3): ").strip()
        if not bot_id:
            print("❌ ID não pode estar vazio")
            return None
        
        nome = input("Nome do bot (ex: Bot Especial): ").strip()
        if not nome:
            nome = f"Bot {bot_id.upper()}"
        
        token = input("Token do bot Telegram: ").strip()
        if not token:
            print("❌ Token é obrigatório")
            return None
        
        chat_id = input("Chat ID (com - se for grupo): ").strip()
        if not chat_id:
            print("❌ Chat ID é obrigatório")
            return None
        
        # Configurações
        print(f"\n⚙️ CONFIGURAÇÕES DO BOT:")
        
        try:
            max_gales = int(input("Máximo de gales (padrão 2): ") or "2")
            interval_seconds = int(input("Intervalo em segundos (padrão 3): ") or "3")
            confidence_threshold = int(input("Confiança mínima % (padrão 75): ") or "75")
            max_daily_signals = int(input("Máximo sinais por dia (padrão 20): ") or "20")
        except ValueError:
            print("❌ Valores inválidos, usando padrões")
            max_gales = 2
            interval_seconds = 3
            confidence_threshold = 75
            max_daily_signals = 20
        
        protection = input("Proteção no branco? (S/n): ").strip().lower() != 'n'
        enable_alerts = input("Habilitar alertas? (S/n): ").strip().lower() != 'n'
        
        # Template de mensagens
        print(f"\n📝 ESCOLHA O TEMPLATE DE MENSAGENS:")
        print("1. 🎯 Padrão")
        print("2. 💎 VIP")
        print("3. ⭐ Premium")
        
        template_choice = input("Escolha (1-3): ").strip()
        
        if template_choice == "2":
            template = "vip"
        elif template_choice == "3":
            template = "premium"
        else:
            template = "padrao"
        
        # Criar arquivo de estratégias
        print(f"\n📋 ESTRATÉGIAS:")
        criar_exemplos = input("Criar exemplos de estratégias? (S/n): ").strip().lower() != 'n'
        estrategias_file = self.criar_arquivo_estrategias(bot_id, criar_exemplos)
        
        # Montar configuração do bot
        bot_config = {
            "id": bot_id,
            "name": nome,
            "token": token,
            "chat_id": chat_id,
            "active": True,
            "estrategias_file": estrategias_file,
            "config": {
                "max_gales": max_gales,
                "protection": protection,
                "interval_seconds": interval_seconds,
                "enable_alerts": enable_alerts,
                "confidence_threshold": confidence_threshold,
                "max_daily_signals": max_daily_signals
            },
            "mensagens": self.templates_mensagens[template].copy()
        }
        
        print(f"\n✅ BOT CONFIGURADO:")
        print(f"  ID: {bot_id}")
        print(f"  Nome: {nome}")
        print(f"  Template: {template}")
        print(f"  Estratégias: {estrategias_file}")
        print(f"  Gales: {max_gales}")
        print(f"  Intervalo: {interval_seconds}s")
        
        return bot_config
    
    def editar_mensagens_bot(self, bot_config: Dict):
        """Edita mensagens de um bot"""
        print(f"\n📝 EDITANDO MENSAGENS DO BOT: {bot_config['name']}")
        print("=" * 50)
        
        mensagens = bot_config.get("mensagens", {})
        templates = ["sinal_template", "alerta_template", "stats_template", "inicio_template", "fim_template"]
        nomes = ["Sinal", "Alerta", "Estatísticas", "Início", "Fim"]
        
        for i, (template_key, nome) in enumerate(zip(templates, nomes)):
            print(f"\n{i+1}. {nome}")
            print(f"Atual: {mensagens.get(template_key, 'Não definido')[:100]}...")
            
            if input(f"Editar template de {nome}? (s/N): ").strip().lower() == 's':
                print(f"\nTemplate atual de {nome}:")
                print("-" * 30)
                print(mensagens.get(template_key, ""))
                print("-" * 30)
                
                print(f"\nVariáveis disponíveis:")
                if template_key == "sinal_template":
                    print("  {bot_name}, {estrategia}, {cor_emoji}, {cor_nome}")
                    print("  {max_gales}, {numeros}, {cores_emoji}, {timestamp}")
                elif template_key == "alerta_template":
                    print("  {bot_name}, {estrategia}, {timestamp}")
                elif template_key == "stats_template":
                    print("  {bot_name}, {sinais}, {wins}, {losses}, {brancos}, {taxa}, {timestamp}")
                elif template_key in ["inicio_template", "fim_template"]:
                    print("  {bot_name}, {total_estrategias}, {sinais}, {timestamp}")
                
                print(f"\nDigite o novo template de {nome}:")
                print("(Enter em linha vazia para finalizar)")
                
                lines = []
                while True:
                    line = input()
                    if line == "" and lines:
                        break
                    lines.append(line)
                
                if lines:
                    mensagens[template_key] = "\n".join(lines)
                    print(f"✅ Template de {nome} atualizado")
        
        bot_config["mensagens"] = mensagens
    
    def listar_bots_config(self, config: Dict):
        """Lista bots da configuração"""
        bots = config.get("bots", [])
        
        if not bots:
            print("📭 Nenhum bot configurado")
            return
        
        print(f"\n🤖 BOTS CONFIGURADOS ({len(bots)}):")
        print("=" * 60)
        
        for i, bot in enumerate(bots, 1):
            status = "✅ ATIVO" if bot.get("active", True) else "❌ INATIVO"
            
            print(f"{i}. {bot['name']} ({bot['id']})")
            print(f"   Status: {status}")
            print(f"   Token: {bot['token'][:20]}...")
            print(f"   Chat: {bot['chat_id']}")
            print(f"   Estratégias: {bot['estrategias_file']}")
            print(f"   Gales: {bot['config']['max_gales']} | Intervalo: {bot['config']['interval_seconds']}s")
            print()
    
    def remover_bot(self, config: Dict):
        """Remove um bot da configuração"""
        bots = config.get("bots", [])
        
        if not bots:
            print("📭 Nenhum bot para remover")
            return
        
        self.listar_bots_config(config)
        
        try:
            index = int(input("Número do bot para remover: ")) - 1
            if 0 <= index < len(bots):
                bot_removido = bots.pop(index)
                print(f"✅ Bot '{bot_removido['name']}' removido")
            else:
                print("❌ Número inválido")
        except ValueError:
            print("❌ Número inválido")

def main():
    print("⚙️ CONFIGURADOR DE BOTS")
    print("=" * 30)
    
    configurador = ConfiguradorBot()
    
    while True:
        print(f"\n📋 OPÇÕES:")
        print("1. 🤖 Criar novo bot")
        print("2. 📝 Listar bots configurados")
        print("3. ✏️ Editar mensagens de um bot")
        print("4. 🗑️ Remover bot")
        print("5. 💾 Salvar e sair")
        print("6. 🚪 Sair sem salvar")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        config = configurador.carregar_config_atual()
        
        if escolha == "1":
            novo_bot = configurador.criar_novo_bot()
            if novo_bot:
                config["bots"].append(novo_bot)
                print("✅ Novo bot adicionado à configuração")
        
        elif escolha == "2":
            configurador.listar_bots_config(config)
        
        elif escolha == "3":
            bots = config.get("bots", [])
            if not bots:
                print("📭 Nenhum bot configurado")
                continue
            
            configurador.listar_bots_config(config)
            
            try:
                index = int(input("Número do bot para editar mensagens: ")) - 1
                if 0 <= index < len(bots):
                    configurador.editar_mensagens_bot(bots[index])
                    print("✅ Mensagens atualizadas")
                else:
                    print("❌ Número inválido")
            except ValueError:
                print("❌ Número inválido")
        
        elif escolha == "4":
            configurador.remover_bot(config)
        
        elif escolha == "5":
            configurador.salvar_config(config)
            print("👋 Configuração salva! Use 'python gerenciador_multi_bots.py' para executar")
            break
        
        elif escolha == "6":
            print("👋 Saindo sem salvar")
            break
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main() 