#!/usr/bin/env python3
"""
🤖 CONFIGURADOR DE ROBÔS POR PLATAFORMA
Interface para configurar robôs específicos para cada casa de apostas
Nome, Plataforma, Token, Canal, Estratégias
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from plataformas_api import GerenciadorPlataformas

class ConfiguradorRobos:
    def __init__(self):
        self.config_file = Path("robos_configurados.json")
        self.gerenciador_plataformas = GerenciadorPlataformas()
        
    def carregar_configuracao(self) -> Dict[str, Any]:
        """Carrega configuração existente ou cria nova"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Erro ao carregar configuração: {e}")
        
        return {
            "robos": [],
            "configuracao_global": {
                "versao": "1.0",
                "criado_em": "2025-01-25",
                "total_robos": 0
            }
        }
    
    def salvar_configuracao(self, config: Dict[str, Any]):
        """Salva configuração no arquivo"""
        config["configuracao_global"]["total_robos"] = len(config.get("robos", []))
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuração salva em {self.config_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
    
    def criar_novo_robo(self) -> Dict[str, Any]:
        """Interface para criar novo robô"""
        print("\n🤖 CRIANDO NOVO ROBÔ")
        print("=" * 30)
        
        # Nome do robô
        nome_robo = input("📝 Nome do Robô: ").strip()
        if not nome_robo:
            print("❌ Nome é obrigatório")
            return None
        
        # Escolher plataforma
        plataformas = self.gerenciador_plataformas.listar_plataformas_disponiveis()
        
        print(f"\n🎰 PLATAFORMAS DISPONÍVEIS:")
        plataformas_lista = list(plataformas.keys())
        
        for i, (key, info) in enumerate(plataformas.items(), 1):
            status_emoji = "✅" if info['status'] == 'ativo' else "🚧"
            print(f"{i}. {status_emoji} {info['nome']} {info['jogo']} - {info['url']}")
        
        try:
            escolha_plat = int(input(f"\nEscolha a plataforma (1-{len(plataformas)}): ")) - 1
            if not 0 <= escolha_plat < len(plataformas_lista):
                print("❌ Plataforma inválida")
                return None
            
            plataforma_id = plataformas_lista[escolha_plat]
            plataforma_info = plataformas[plataforma_id]
            
        except ValueError:
            print("❌ Número inválido")
            return None
        
        # Token do bot
        print(f"\n🤖 CONFIGURAÇÃO DO BOT TELEGRAM:")
        print("💡 Crie seu bot com @BotFather no Telegram")
        token_bot = input("🔑 Token do Bot: ").strip()
        if not token_bot:
            print("❌ Token é obrigatório")
            return None
        
        # ID do canal
        print(f"\n💬 CANAL/GRUPO TELEGRAM:")
        print("💡 Para grupos: use o ID com '-' (ex: -1001234567890)")
        print("💡 Para canais: use o @ ou ID (ex: @meucanal)")
        chat_id = input("📱 ID do Canal/Grupo: ").strip()
        if not chat_id:
            print("❌ ID do canal é obrigatório")
            return None
        
        # Configurações avançadas
        print(f"\n⚙️ CONFIGURAÇÕES DO ROBÔ:")
        
        try:
            max_gales = int(input("🎲 Máximo de gales (padrão 2): ") or "2")
            intervalo = int(input("⏱️ Intervalo entre verificações em segundos (padrão 3): ") or "3")
            confianca_min = int(input("📊 Confiança mínima % (padrão 75): ") or "75")
            max_sinais_dia = int(input("🎯 Máximo de sinais por dia (padrão 20): ") or "20")
        except ValueError:
            print("⚠️ Valores inválidos, usando padrões")
            max_gales = 2
            intervalo = 3
            confianca_min = 75
            max_sinais_dia = 20
        
        # Configurações de proteção
        protecao_branco = input("🛡️ Proteção no branco? (S/n): ").strip().lower() != 'n'
        alertas_ativos = input("⚠️ Enviar alertas de estratégias? (S/n): ").strip().lower() != 'n'
        
        # Escolher estratégias
        print(f"\n📋 ESTRATÉGIAS:")
        print("💡 Você pode configurar estratégias específicas depois")
        usar_estrategias_padrao = input("Usar estratégias padrão para começar? (S/n): ").strip().lower() != 'n'
        
        estrategias_padrao = []
        if usar_estrategias_padrao:
            estrategias_padrao = [
                {"pattern": "V-V", "bet": "P", "name": "Dois Vermelhos"},
                {"pattern": "P-P", "bet": "V", "name": "Dois Pretos"},
                {"pattern": "V-V-P", "bet": "V", "name": "Sequência VVP"},
                {"pattern": "P-P-V", "bet": "P", "name": "Sequência PPV"}
            ]
        
        # Gerar ID único
        config_atual = self.carregar_configuracao()
        robo_id = f"robo_{len(config_atual.get('robos', []))+ 1}_{plataforma_id}"
        
        # Montar configuração do robô
        robo_config = {
            "id": robo_id,
            "nome": nome_robo,
            "plataforma": {
                "id": plataforma_id,
                "nome": plataforma_info["nome"],
                "jogo": plataforma_info["jogo"],
                "url": plataforma_info["url"]
            },
            "telegram": {
                "token": token_bot,
                "chat_id": chat_id
            },
            "configuracoes": {
                "max_gales": max_gales,
                "intervalo_segundos": intervalo,
                "confianca_minima": confianca_min,
                "max_sinais_dia": max_sinais_dia,
                "protecao_branco": protecao_branco,
                "alertas_ativos": alertas_ativos
            },
            "estrategias": estrategias_padrao,
            "status": "ativo",
            "criado_em": "2025-01-25",
            "estatisticas": {
                "sinais_enviados": 0,
                "wins": 0,
                "losses": 0,
                "ultima_atividade": None
            }
        }
        
        # Mostrar resumo
        print(f"\n✅ ROBÔ CONFIGURADO:")
        print(f"  📝 Nome: {nome_robo}")
        print(f"  🎰 Plataforma: {plataforma_info['nome']} {plataforma_info['jogo']}")
        print(f"  🤖 Token: {token_bot[:20]}...")
        print(f"  💬 Canal: {chat_id}")
        print(f"  🎲 Gales: {max_gales} | ⏱️ Intervalo: {intervalo}s")
        print(f"  📊 Confiança: {confianca_min}% | 🎯 Sinais/dia: {max_sinais_dia}")
        print(f"  📋 Estratégias: {len(estrategias_padrao)}")
        
        return robo_config
    
    def listar_robos(self, config: Dict[str, Any]):
        """Lista robôs configurados"""
        robos = config.get("robos", [])
        
        if not robos:
            print("📭 Nenhum robô configurado")
            return
        
        print(f"\n🤖 ROBÔS CONFIGURADOS ({len(robos)}):")
        print("=" * 60)
        
        for i, robo in enumerate(robos, 1):
            status_emoji = "✅" if robo["status"] == "ativo" else "❌"
            plataforma = robo["plataforma"]
            
            print(f"{i}. {robo['nome']} ({robo['id']})")
            print(f"   Status: {status_emoji} {robo['status'].upper()}")
            print(f"   Plataforma: {plataforma['nome']} {plataforma['jogo']}")
            print(f"   Telegram: {robo['telegram']['chat_id']}")
            print(f"   Configurações: {robo['configuracoes']['max_gales']} gales, {robo['configuracoes']['intervalo_segundos']}s")
            print(f"   Estratégias: {len(robo['estrategias'])}")
            
            # Estatísticas se houver
            stats = robo.get("estatisticas", {})
            if stats.get("sinais_enviados", 0) > 0:
                print(f"   Stats: {stats['sinais_enviados']} sinais, {stats['wins']}W/{stats['losses']}L")
            
            print()
    
    def editar_robo(self, config: Dict[str, Any]):
        """Edita um robô existente"""
        robos = config.get("robos", [])
        
        if not robos:
            print("📭 Nenhum robô para editar")
            return
        
        self.listar_robos(config)
        
        try:
            escolha = int(input("Número do robô para editar: ")) - 1
            if not 0 <= escolha < len(robos):
                print("❌ Robô inválido")
                return
        except ValueError:
            print("❌ Número inválido")
            return
        
        robo = robos[escolha]
        
        print(f"\n✏️ EDITANDO ROBÔ: {robo['nome']}")
        print("=" * 40)
        
        while True:
            print(f"\n📋 OPÇÕES DE EDIÇÃO:")
            print("1. 📝 Alterar nome")
            print("2. 🔑 Alterar token Telegram")
            print("3. 💬 Alterar canal/grupo")
            print("4. ⚙️ Configurações avançadas")
            print("5. 📋 Gerenciar estratégias")
            print("6. 🔄 Alterar status (ativo/inativo)")
            print("7. 💾 Salvar e voltar")
            
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1":
                novo_nome = input(f"Novo nome (atual: {robo['nome']}): ").strip()
                if novo_nome:
                    robo['nome'] = novo_nome
                    print("✅ Nome atualizado")
            
            elif opcao == "2":
                novo_token = input("Novo token: ").strip()
                if novo_token:
                    robo['telegram']['token'] = novo_token
                    print("✅ Token atualizado")
            
            elif opcao == "3":
                novo_chat = input(f"Novo canal/grupo (atual: {robo['telegram']['chat_id']}): ").strip()
                if novo_chat:
                    robo['telegram']['chat_id'] = novo_chat
                    print("✅ Canal atualizado")
            
            elif opcao == "4":
                self.editar_configuracoes_avancadas(robo)
            
            elif opcao == "5":
                self.gerenciar_estrategias_robo(robo)
            
            elif opcao == "6":
                status_atual = robo['status']
                novo_status = "inativo" if status_atual == "ativo" else "ativo"
                robo['status'] = novo_status
                print(f"✅ Status alterado para: {novo_status}")
            
            elif opcao == "7":
                break
            
            else:
                print("❌ Opção inválida")
    
    def editar_configuracoes_avancadas(self, robo: Dict[str, Any]):
        """Edita configurações avançadas do robô"""
        config = robo['configuracoes']
        
        print(f"\n⚙️ CONFIGURAÇÕES AVANÇADAS:")
        print(f"Atual: {config['max_gales']} gales, {config['intervalo_segundos']}s, {config['confianca_minima']}%")
        
        try:
            novo_gales = input(f"Máximo de gales (atual: {config['max_gales']}): ").strip()
            if novo_gales:
                config['max_gales'] = int(novo_gales)
            
            novo_intervalo = input(f"Intervalo em segundos (atual: {config['intervalo_segundos']}): ").strip()
            if novo_intervalo:
                config['intervalo_segundos'] = int(novo_intervalo)
            
            nova_confianca = input(f"Confiança mínima % (atual: {config['confianca_minima']}): ").strip()
            if nova_confianca:
                config['confianca_minima'] = int(nova_confianca)
            
            novo_max_sinais = input(f"Máx sinais/dia (atual: {config['max_sinais_dia']}): ").strip()
            if novo_max_sinais:
                config['max_sinais_dia'] = int(novo_max_sinais)
            
            print("✅ Configurações atualizadas")
            
        except ValueError:
            print("❌ Valores inválidos")
    
    def gerenciar_estrategias_robo(self, robo: Dict[str, Any]):
        """Gerencia estratégias do robô"""
        estrategias = robo.get('estrategias', [])
        
        while True:
            print(f"\n📋 ESTRATÉGIAS DO ROBÔ ({len(estrategias)}):")
            
            for i, est in enumerate(estrategias, 1):
                print(f"{i}. {est['name']}: {est['pattern']} → {est['bet']}")
            
            print(f"\n📋 OPÇÕES:")
            print("1. ➕ Adicionar estratégia")
            print("2. ❌ Remover estratégia")
            print("3. ✏️ Editar estratégia")
            print("4. 🔙 Voltar")
            
            opcao = input("\nEscolha: ").strip()
            
            if opcao == "1":
                # Adicionar estratégia
                pattern = input("Padrão (ex: V-V-P): ").strip().upper()
                bet = input("Apostar em (V/P/B): ").strip().upper()
                name = input("Nome da estratégia: ").strip()
                
                if pattern and bet in ['V', 'P', 'B'] and name:
                    estrategias.append({
                        "pattern": pattern,
                        "bet": bet,
                        "name": name
                    })
                    print("✅ Estratégia adicionada")
                else:
                    print("❌ Dados inválidos")
            
            elif opcao == "2":
                # Remover estratégia
                try:
                    idx = int(input("Número da estratégia para remover: ")) - 1
                    if 0 <= idx < len(estrategias):
                        removida = estrategias.pop(idx)
                        print(f"✅ Estratégia '{removida['name']}' removida")
                    else:
                        print("❌ Número inválido")
                except ValueError:
                    print("❌ Número inválido")
            
            elif opcao == "3":
                # Editar estratégia
                try:
                    idx = int(input("Número da estratégia para editar: ")) - 1
                    if 0 <= idx < len(estrategias):
                        est = estrategias[idx]
                        
                        novo_pattern = input(f"Novo padrão (atual: {est['pattern']}): ").strip().upper()
                        if novo_pattern:
                            est['pattern'] = novo_pattern
                        
                        novo_bet = input(f"Nova aposta (atual: {est['bet']}): ").strip().upper()
                        if novo_bet in ['V', 'P', 'B']:
                            est['bet'] = novo_bet
                        
                        novo_name = input(f"Novo nome (atual: {est['name']}): ").strip()
                        if novo_name:
                            est['name'] = novo_name
                        
                        print("✅ Estratégia atualizada")
                    else:
                        print("❌ Número inválido")
                except ValueError:
                    print("❌ Número inválido")
            
            elif opcao == "4":
                break
            
            else:
                print("❌ Opção inválida")
        
        robo['estrategias'] = estrategias
    
    def remover_robo(self, config: Dict[str, Any]):
        """Remove um robô"""
        robos = config.get("robos", [])
        
        if not robos:
            print("📭 Nenhum robô para remover")
            return
        
        self.listar_robos(config)
        
        try:
            escolha = int(input("Número do robô para remover: ")) - 1
            if 0 <= escolha < len(robos):
                robo_removido = robos.pop(escolha)
                print(f"✅ Robô '{robo_removido['nome']}' removido")
            else:
                print("❌ Número inválido")
        except ValueError:
            print("❌ Número inválido")
    
    def testar_conectividade_robos(self, config: Dict[str, Any]):
        """Testa conectividade dos robôs com suas plataformas"""
        robos = config.get("robos", [])
        
        if not robos:
            print("📭 Nenhum robô para testar")
            return
        
        print(f"\n🔍 TESTANDO CONECTIVIDADE DOS ROBÔS:")
        print("-" * 45)
        
        for robo in robos:
            plataforma_id = robo['plataforma']['id']
            nome_robo = robo['nome']
            
            try:
                dados = self.gerenciador_plataformas.buscar_dados_plataforma(plataforma_id)
                
                if dados:
                    print(f"✅ {nome_robo}: Conectado à {robo['plataforma']['nome']}")
                    print(f"   └─ {len(dados)} resultados obtidos")
                else:
                    print(f"❌ {nome_robo}: Sem dados da {robo['plataforma']['nome']}")
                
            except Exception as e:
                print(f"❌ {nome_robo}: Erro - {e}")

def main():
    """Interface principal do configurador"""
    print("🤖 CONFIGURADOR DE ROBÔS POR PLATAFORMA")
    print("=" * 45)
    
    configurador = ConfiguradorRobos()
    
    while True:
        print(f"\n📋 MENU PRINCIPAL:")
        print("1. 🤖 Criar novo robô")
        print("2. 📝 Listar robôs configurados")
        print("3. ✏️ Editar robô existente")
        print("4. ❌ Remover robô")
        print("5. 🔍 Testar conectividade")
        print("6. 📊 Ver plataformas disponíveis")
        print("7. 💾 Salvar e sair")
        print("8. 🚪 Sair sem salvar")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        config = configurador.carregar_configuracao()
        
        if escolha == "1":
            novo_robo = configurador.criar_novo_robo()
            if novo_robo:
                config["robos"].append(novo_robo)
                print("✅ Robô adicionado à configuração")
        
        elif escolha == "2":
            configurador.listar_robos(config)
        
        elif escolha == "3":
            configurador.editar_robo(config)
        
        elif escolha == "4":
            configurador.remover_robo(config)
        
        elif escolha == "5":
            configurador.testar_conectividade_robos(config)
        
        elif escolha == "6":
            plataformas = configurador.gerenciador_plataformas.listar_plataformas_disponiveis()
            print(f"\n🎰 PLATAFORMAS DISPONÍVEIS:")
            for key, info in plataformas.items():
                status_emoji = "✅" if info['status'] == 'ativo' else "🚧"
                print(f"  {status_emoji} {info['nome']} {info['jogo']} - {info['url']}")
        
        elif escolha == "7":
            configurador.salvar_configuracao(config)
            print("👋 Configuração salva! Use o painel para analisar estratégias.")
            break
        
        elif escolha == "8":
            print("👋 Saindo sem salvar")
            break
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main() 