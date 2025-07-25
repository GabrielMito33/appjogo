#!/usr/bin/env python3
"""
🤖 GERENCIADOR DE MÚLTIPLOS BOTS
Sistema completo para gerenciar vários bots simultaneamente
Cada bot tem suas próprias estratégias, mensagens e configurações
"""

import json
import csv
import threading
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class BotStats:
    sinais_enviados: int = 0
    wins: int = 0
    losses: int = 0
    brancos: int = 0
    uptime_inicio: Optional[datetime] = None
    ultimo_sinal: Optional[datetime] = None

class BotInstance:
    def __init__(self, config: Dict):
        self.config = config
        self.id = config["id"]
        self.name = config["name"]
        self.token = config["token"]
        self.chat_id = config["chat_id"]
        self.active = config["active"]
        self.estrategias_file = config["estrategias_file"]
        self.mensagens = config["mensagens"]
        self.bot_config = config["config"]
        
        # Estado do bot
        self.running = False
        self.thread = None
        self.stats = BotStats()
        self.estrategias = []
        self.ultimo_resultado = None
        self.historico_resultados = []
        
        # API Telegram
        self.telegram_api = f"https://api.telegram.org/bot{self.token}"
        
    def carregar_estrategias(self) -> bool:
        """Carrega estratégias específicas do bot"""
        estrategias_path = Path(self.estrategias_file)
        
        if not estrategias_path.exists():
            self.log(f"❌ Arquivo de estratégias não encontrado: {estrategias_path}", "ERROR")
            return False
        
        self.estrategias = []
        
        try:
            with open(estrategias_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                for i, row in enumerate(reader):
                    if not row or not row[0].strip():
                        continue
                    
                    estrategia_str = row[0].strip()
                    
                    if "=" not in estrategia_str:
                        continue
                    
                    condicoes_str, aposta_str = estrategia_str.split("=", 1)
                    condicoes = [c.strip() for c in condicoes_str.split("-")]
                    aposta = aposta_str.strip()
                    
                    if aposta in ["V", "P", "B"]:
                        self.estrategias.append({
                            "id": i + 1,
                            "conditions": condicoes,
                            "bet_direction": aposta,
                            "original": estrategia_str,
                            "active": True
                        })
            
            self.log(f"✅ Carregadas {len(self.estrategias)} estratégias")
            return len(self.estrategias) > 0
            
        except Exception as e:
            self.log(f"❌ Erro ao carregar estratégias: {e}", "ERROR")
            return False
    
    def log(self, message: str, level: str = "INFO"):
        """Log específico do bot"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {level}: {message}")
    
    def convert_number_to_color(self, number: int) -> str:
        """Converte número para cor"""
        if 1 <= number <= 7:
            return "V"
        elif 8 <= number <= 14:
            return "P"
        else:
            return "B"
    
    def get_color_emoji(self, color: str) -> str:
        """Converte cor para emoji"""
        mapping = {"V": "🔴", "P": "⚫", "B": "⚪"}
        return mapping.get(color, "❓")
    
    def get_color_name(self, color: str) -> str:
        """Converte cor para nome"""
        mapping = {"V": "VERMELHO", "P": "PRETO", "B": "BRANCO"}
        return mapping.get(color, "DESCONHECIDO")
    
    def fetch_blaze_results(self) -> List[int]:
        """Busca resultados da Blaze"""
        try:
            response = requests.get(
                "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return [item['roll'] for item in data]
            return []
        except Exception as e:
            self.log(f"Erro ao buscar Blaze: {e}", "ERROR")
            return []
    
    def send_telegram_message(self, message: str) -> bool:
        """Envia mensagem personalizada do bot"""
        try:
            response = requests.post(
                f"{self.telegram_api}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                },
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.log(f"Erro ao enviar Telegram: {e}", "ERROR")
            return False
    
    def verificar_estrategia(self, estrategia: Dict, results: List[int]) -> bool:
        """Verifica se estratégia faz match"""
        conditions = estrategia["conditions"]
        
        if len(conditions) > len(results):
            return False
        
        colors = [self.convert_number_to_color(num) for num in results]
        
        for i, condition in enumerate(conditions):
            posicao_historico = len(conditions) - 1 - i
            numero_nesta_posicao = str(results[posicao_historico])
            cor_nesta_posicao = colors[posicao_historico]
            
            if condition == "X":
                continue
            elif condition == numero_nesta_posicao or condition == cor_nesta_posicao:
                continue
            else:
                return False
        
        return True
    
    def formatar_mensagem(self, template: str, **kwargs) -> str:
        """Formata mensagem com template personalizado do bot"""
        return template.format(
            bot_name=self.name,
            timestamp=datetime.now().strftime('%H:%M:%S'),
            **kwargs
        )
    
    def send_signal(self, estrategia: Dict, results: List[int]):
        """Envia sinal com mensagem personalizada do bot"""
        bet_direction = estrategia["bet_direction"]
        cor_emoji = self.get_color_emoji(bet_direction)
        cor_nome = self.get_color_name(bet_direction)
        
        # Formatar dados para o template
        numeros = str(results[:5])[1:-1]  # Remove [ ]
        cores_emoji = ' '.join([self.get_color_emoji(self.convert_number_to_color(r)) for r in results[:5]])
        
        message = self.formatar_mensagem(
            self.mensagens["sinal_template"],
            estrategia=estrategia["original"],
            cor_emoji=cor_emoji,
            cor_nome=cor_nome,
            max_gales=self.bot_config["max_gales"],
            numeros=numeros,
            cores_emoji=cores_emoji,
            confianca=85  # Pode ser calculado dinamicamente
        )
        
        if self.send_telegram_message(message):
            self.stats.sinais_enviados += 1
            self.stats.ultimo_sinal = datetime.now()
            self.log(f"✅ SINAL ENVIADO: {estrategia['original']} -> {cor_nome}")
        else:
            self.log(f"❌ Falha ao enviar sinal: {estrategia['original']}")
    
    def send_alert(self, estrategia: Dict):
        """Envia alerta com mensagem personalizada do bot"""
        message = self.formatar_mensagem(
            self.mensagens["alerta_template"],
            estrategia=estrategia["original"]
        )
        
        if self.send_telegram_message(message):
            self.log(f"⚠️ ALERTA ENVIADO: {estrategia['original']}")
    
    def send_stats(self):
        """Envia estatísticas do bot"""
        total = self.stats.sinais_enviados
        taxa = ((self.stats.wins + self.stats.brancos) / total * 100) if total > 0 else 0
        
        message = self.formatar_mensagem(
            self.mensagens["stats_template"],
            sinais=self.stats.sinais_enviados,
            wins=self.stats.wins,
            losses=self.stats.losses,
            brancos=self.stats.brancos,
            taxa=f"{taxa:.1f}"
        )
        
        self.send_telegram_message(message)
    
    def processar_estrategias(self, results: List[int]):
        """Processa estratégias específicas do bot"""
        if len(results) < 2:
            return
        
        for estrategia in self.estrategias:
            if not estrategia.get("active", True):
                continue
            
            # Verificar sinal completo
            if self.verificar_estrategia(estrategia, results):
                self.log(f"🎯 MATCH: {estrategia['original']}")
                self.send_signal(estrategia, results)
                return
            
            # Verificar alerta (se habilitado)
            if self.bot_config.get("enable_alerts", False):
                # Lógica de alerta aqui
                pass
    
    def run_bot(self):
        """Loop principal do bot"""
        self.log("🚀 Bot iniciado")
        self.stats.uptime_inicio = datetime.now()
        
        # Mensagem de início
        message = self.formatar_mensagem(
            self.mensagens["inicio_template"],
            total_estrategias=len(self.estrategias)
        )
        self.send_telegram_message(message)
        
        while self.running:
            try:
                # Buscar resultados
                results = self.fetch_blaze_results()
                
                if results and results[0] != self.ultimo_resultado:
                    self.ultimo_resultado = results[0]
                    self.historico_resultados = results
                    
                    cor = self.convert_number_to_color(self.ultimo_resultado)
                    emoji = self.get_color_emoji(cor)
                    self.log(f"Novo resultado: {self.ultimo_resultado} ({emoji})")
                    
                    # Processar estratégias
                    self.processar_estrategias(results)
                
                time.sleep(self.bot_config["interval_seconds"])
                
            except Exception as e:
                self.log(f"Erro no loop: {e}", "ERROR")
                time.sleep(10)
        
        # Mensagem de finalização
        message = self.formatar_mensagem(
            self.mensagens["fim_template"],
            sinais=self.stats.sinais_enviados
        )
        self.send_telegram_message(message)
        
        self.log("🛑 Bot finalizado")
    
    def start(self) -> bool:
        """Inicia o bot"""
        if self.running:
            self.log("Bot já está rodando", "WARNING")
            return False
        
        if not self.carregar_estrategias():
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self.run_bot, daemon=True)
        self.thread.start()
        
        return True
    
    def stop(self):
        """Para o bot"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

class MultiBotsManager:
    def __init__(self, config_file: str = "config_bots.json"):
        self.config_file = Path(config_file)
        self.bots: Dict[str, BotInstance] = {}
        self.global_config = {}
        
    def carregar_configuracao(self) -> bool:
        """Carrega configuração dos bots"""
        if not self.config_file.exists():
            print(f"❌ Arquivo de configuração não encontrado: {self.config_file}")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.global_config = config_data.get("global_config", {})
            
            # Criar instâncias dos bots
            for bot_config in config_data.get("bots", []):
                bot = BotInstance(bot_config)
                self.bots[bot.id] = bot
            
            print(f"✅ Carregados {len(self.bots)} bots da configuração")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return False
    
    def listar_bots(self):
        """Lista todos os bots configurados"""
        print(f"\n🤖 BOTS CONFIGURADOS ({len(self.bots)}):")
        print("=" * 80)
        
        for bot_id, bot in self.bots.items():
            status = "✅ ATIVO" if bot.active else "❌ INATIVO"
            running = "🟢 RODANDO" if bot.running else "🔴 PARADO"
            
            print(f"ID: {bot_id}")
            print(f"Nome: {bot.name}")
            print(f"Status: {status} | Estado: {running}")
            print(f"Token: {bot.token[:20]}...")
            print(f"Chat ID: {bot.chat_id}")
            print(f"Estratégias: {bot.estrategias_file}")
            print(f"Intervalo: {bot.bot_config['interval_seconds']}s")
            
            if bot.stats.sinais_enviados > 0:
                print(f"Sinais enviados: {bot.stats.sinais_enviados}")
            
            print("-" * 40)
    
    def iniciar_bot(self, bot_id: str) -> bool:
        """Inicia um bot específico"""
        if bot_id not in self.bots:
            print(f"❌ Bot '{bot_id}' não encontrado")
            return False
        
        bot = self.bots[bot_id]
        
        if not bot.active:
            print(f"❌ Bot '{bot_id}' está marcado como inativo")
            return False
        
        return bot.start()
    
    def parar_bot(self, bot_id: str):
        """Para um bot específico"""
        if bot_id not in self.bots:
            print(f"❌ Bot '{bot_id}' não encontrado")
            return
        
        self.bots[bot_id].stop()
    
    def iniciar_todos_bots(self):
        """Inicia todos os bots ativos"""
        iniciados = 0
        
        for bot_id, bot in self.bots.items():
            if bot.active and not bot.running:
                if self.iniciar_bot(bot_id):
                    iniciados += 1
                    print(f"✅ Bot '{bot_id}' iniciado")
                else:
                    print(f"❌ Falha ao iniciar bot '{bot_id}'")
        
        print(f"\n🚀 {iniciados} bots iniciados")
    
    def parar_todos_bots(self):
        """Para todos os bots"""
        parados = 0
        
        for bot_id, bot in self.bots.items():
            if bot.running:
                self.parar_bot(bot_id)
                parados += 1
                print(f"🛑 Bot '{bot_id}' parado")
        
        print(f"\n✅ {parados} bots parados")
    
    def estatisticas_gerais(self):
        """Mostra estatísticas de todos os bots"""
        print(f"\n📊 ESTATÍSTICAS GERAIS:")
        print("=" * 50)
        
        total_sinais = sum(bot.stats.sinais_enviados for bot in self.bots.values())
        bots_ativos = sum(1 for bot in self.bots.values() if bot.running)
        
        print(f"🤖 Total de bots: {len(self.bots)}")
        print(f"🟢 Bots rodando: {bots_ativos}")
        print(f"🎯 Total de sinais: {total_sinais}")
        
        print(f"\n📋 DETALHES POR BOT:")
        for bot_id, bot in self.bots.items():
            if bot.stats.sinais_enviados > 0:
                uptime = ""
                if bot.stats.uptime_inicio:
                    delta = datetime.now() - bot.stats.uptime_inicio
                    uptime = f"({delta.seconds//3600}h {(delta.seconds//60)%60}m)"
                
                print(f"  {bot.name}: {bot.stats.sinais_enviados} sinais {uptime}")

def main():
    print("🤖 GERENCIADOR DE MÚLTIPLOS BOTS")
    print("=" * 40)
    
    manager = MultiBotsManager()
    
    if not manager.carregar_configuracao():
        print("❌ Não foi possível carregar a configuração")
        return
    
    while True:
        print(f"\n📋 OPÇÕES:")
        print("1. 📝 Listar bots")
        print("2. 🚀 Iniciar bot específico")
        print("3. 🛑 Parar bot específico")
        print("4. 🟢 Iniciar todos os bots ativos")
        print("5. 🔴 Parar todos os bots")
        print("6. 📊 Estatísticas gerais")
        print("7. ⚙️ Recarregar configuração")
        print("8. 🚪 Sair")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "1":
            manager.listar_bots()
        
        elif escolha == "2":
            bot_id = input("ID do bot para iniciar: ").strip()
            if manager.iniciar_bot(bot_id):
                print(f"✅ Bot '{bot_id}' iniciado com sucesso")
            else:
                print(f"❌ Falha ao iniciar bot '{bot_id}'")
        
        elif escolha == "3":
            bot_id = input("ID do bot para parar: ").strip()
            manager.parar_bot(bot_id)
            print(f"🛑 Bot '{bot_id}' parado")
        
        elif escolha == "4":
            manager.iniciar_todos_bots()
        
        elif escolha == "5":
            manager.parar_todos_bots()
        
        elif escolha == "6":
            manager.estatisticas_gerais()
        
        elif escolha == "7":
            manager.parar_todos_bots()
            if manager.carregar_configuracao():
                print("✅ Configuração recarregada")
            else:
                print("❌ Erro ao recarregar configuração")
        
        elif escolha == "8":
            manager.parar_todos_bots()
            print("👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main() 