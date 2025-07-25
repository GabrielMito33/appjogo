#!/usr/bin/env python3
"""
🤖 BOT AVANÇADO COM VARIÁVEIS GLOBAIS
Versão do sistema de bots que usa todas as variáveis personalizadas
Integra com o sistema de processamento de variáveis avançadas
"""

import json
import threading
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from sistema_variaveis_mensagens import ProcessadorVariaveisGlobais

class BotAvancadoComVariaveis:
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
        
        # Sistema de variáveis globais
        self.processador_variaveis = ProcessadorVariaveisGlobais()
        self.processador_variaveis.stats['max_gales'] = self.bot_config.get('max_gales', 2)
        
        # Estado do bot
        self.running = False
        self.thread = None
        self.estrategias = []
        self.ultimo_resultado = None
        self.historico_resultados = []
        self.gales_ativos = {}
        
        # Controle de data para reset diário
        self.data_atual = datetime.now().date()
        
        # API Telegram
        self.telegram_api = f"https://api.telegram.org/bot{self.token}"
    
    def verificar_mudanca_dia(self):
        """Verifica se mudou o dia e reseta estatísticas se necessário"""
        hoje = datetime.now().date()
        if hoje != self.data_atual:
            self.log("🌅 Novo dia detectado - resetando estatísticas diárias")
            self.processador_variaveis.resetar_estatisticas_diarias()
            self.data_atual = hoje
    
    def log(self, message: str, level: str = "INFO"):
        """Log específico do bot"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {level}: {message}")
    
    def carregar_estrategias(self) -> bool:
        """Carrega estratégias específicas do bot"""
        estrategias_path = Path(self.estrategias_file)
        
        if not estrategias_path.exists():
            self.log(f"❌ Arquivo de estratégias não encontrado: {estrategias_path}", "ERROR")
            return False
        
        self.estrategias = []
        
        try:
            with open(estrategias_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if "=" not in line:
                        continue
                    
                    condicoes_str, aposta_str = line.split("=", 1)
                    condicoes = [c.strip() for c in condicoes_str.split("-")]
                    aposta = aposta_str.strip()
                    
                    if aposta in ["V", "P", "B"]:
                        self.estrategias.append({
                            "id": i + 1,
                            "conditions": condicoes,
                            "bet_direction": aposta,
                            "original": line,
                            "active": True,
                            "name": f"Estratégia {i+1}"
                        })
            
            self.log(f"✅ Carregadas {len(self.estrategias)} estratégias")
            return len(self.estrategias) > 0
            
        except Exception as e:
            self.log(f"❌ Erro ao carregar estratégias: {e}", "ERROR")
            return False
    
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
    
    def processar_template_avancado(self, template_key: str, **kwargs) -> str:
        """Processa template usando variáveis globais avançadas"""
        template = self.mensagens.get(template_key, "")
        if not template:
            return f"Template '{template_key}' não encontrado para {self.name}"
        
        # Parâmetros adicionais específicos do bot
        params_bot = {
            'bot_name': self.name,
            'total_estrategias': len(self.estrategias),
            **kwargs
        }
        
        return self.processador_variaveis.processar_todas_variaveis(template, **params_bot)
    
    def send_signal(self, estrategia: Dict, results: List[int]):
        """Envia sinal com mensagem avançada processada"""
        bet_direction = estrategia["bet_direction"]
        cor_emoji = self.get_color_emoji(bet_direction)
        cor_nome = self.get_color_name(bet_direction)
        
        # Atualizar nome da estratégia atual no processador
        self.processador_variaveis.stats['nome_estrategia'] = estrategia['original']
        
        # Formatar dados para o template
        numeros = ', '.join(map(str, results[:5]))
        cores_emoji = ' '.join([self.get_color_emoji(self.convert_number_to_color(r)) for r in results[:5]])
        
        # Processar template de sinal
        message = self.processar_template_avancado(
            'sinal_template',
            cor_emoji=cor_emoji,
            cor_nome=cor_nome,
            estrategia=estrategia['original'],
            numeros=numeros,
            cores_emoji=cores_emoji,
            confianca=85  # Pode ser calculado dinamicamente
        )
        
        if self.send_telegram_message(message):
            # Registrar sinal enviado (por enquanto como pendente)
            self.log(f"✅ SINAL ENVIADO: {estrategia['original']} -> {cor_nome}")
            
            # Armazenar para tracking de gales
            self.gales_ativos[estrategia['original']] = {
                'estrategia': estrategia,
                'cor_apostada': bet_direction,
                'gale_atual': 0,
                'timestamp': datetime.now()
            }
        else:
            self.log(f"❌ Falha ao enviar sinal: {estrategia['original']}")
    
    def send_alert(self, estrategia: Dict):
        """Envia alerta com mensagem avançada processada"""
        # Atualizar nome da estratégia no processador
        self.processador_variaveis.stats['nome_estrategia'] = estrategia['original']
        
        message = self.processar_template_avancado(
            'alerta_template',
            estrategia=estrategia['original']
        )
        
        if self.send_telegram_message(message):
            self.log(f"⚠️ ALERTA ENVIADO: {estrategia['original']}")
    
    def processar_resultado_gales(self, novo_resultado: int):
        """Processa resultado para verificar gales ativos"""
        cor_resultado = self.convert_number_to_color(novo_resultado)
        
        gales_finalizados = []
        
        for estrategia_original, info_gale in self.gales_ativos.items():
            cor_apostada = info_gale['cor_apostada']
            gale_atual = info_gale['gale_atual']
            estrategia = info_gale['estrategia']
            
            # Verificar se foi WIN
            if cor_resultado == cor_apostada or cor_resultado == "B":  # B = proteção
                resultado_tipo = "WIN" if cor_resultado == cor_apostada else "BRANCO"
                
                # Atualizar estatísticas
                self.processador_variaveis.atualizar_estatisticas(
                    resultado_tipo, 
                    gale_atual, 
                    estrategia['original']
                )
                
                # Enviar mensagem de resultado WIN
                self.send_win_message(estrategia, gale_atual, resultado_tipo)
                
                gales_finalizados.append(estrategia_original)
                
            else:
                # Foi RED, verificar se deve fazer gale
                max_gales = self.bot_config.get('max_gales', 2)
                
                if gale_atual < max_gales:
                    # Fazer próximo gale
                    info_gale['gale_atual'] += 1
                    self.processador_variaveis.stats['gale_atual'] = info_gale['gale_atual']
                    
                    self.log(f"🎲 Fazendo G{info_gale['gale_atual']} para {estrategia_original}")
                    
                    # Enviar mensagem de gale
                    self.send_gale_message(estrategia, info_gale['gale_atual'])
                    
                else:
                    # Esgotaram-se os gales - LOSS
                    self.processador_variaveis.atualizar_estatisticas(
                        "LOSS", 
                        gale_atual, 
                        estrategia['original']
                    )
                    
                    # Enviar mensagem de LOSS
                    self.send_loss_message(estrategia, gale_atual)
                    
                    gales_finalizados.append(estrategia_original)
        
        # Remover gales finalizados
        for estrategia_original in gales_finalizados:
            del self.gales_ativos[estrategia_original]
    
    def send_win_message(self, estrategia: Dict, gale_usado: int, tipo_resultado: str):
        """Envia mensagem de WIN com variáveis avançadas"""
        # Verificar se existe template específico para WIN
        template_key = 'win_template' if 'win_template' in self.mensagens else 'stats_template'
        
        if template_key not in self.mensagens:
            # Template padrão se não existir
            message = f"✅ **GREEN** - {estrategia['original']} {'de primeira' if gale_usado == 0 else f'com G{gale_usado}'}!"
        else:
            message = self.processar_template_avancado(template_key)
        
        self.send_telegram_message(message)
    
    def send_loss_message(self, estrategia: Dict, gales_usados: int):
        """Envia mensagem de LOSS com variáveis avançadas"""
        template_key = 'loss_template' if 'loss_template' in self.mensagens else 'stats_template'
        
        if template_key not in self.mensagens:
            message = f"❌ **RED** - {estrategia['original']} após {gales_usados} gales"
        else:
            message = self.processar_template_avancado(template_key)
        
        self.send_telegram_message(message)
    
    def send_gale_message(self, estrategia: Dict, gale_numero: int):
        """Envia mensagem de GALE"""
        cor_emoji = self.get_color_emoji(estrategia['bet_direction'])
        cor_nome = self.get_color_name(estrategia['bet_direction'])
        
        message = f"🎲 **GALE {gale_numero}** - {cor_emoji} {cor_nome}"
        self.send_telegram_message(message)
    
    def send_stats(self):
        """Envia estatísticas com variáveis avançadas"""
        message = self.processar_template_avancado('stats_template')
        self.send_telegram_message(message)
    
    def processar_estrategias(self, results: List[int]):
        """Processa estratégias específicas do bot"""
        if len(results) < 2:
            return
        
        for estrategia in self.estrategias:
            if not estrategia.get("active", True):
                continue
            
            # Pular se já tem gale ativo desta estratégia
            if estrategia['original'] in self.gales_ativos:
                continue
            
            # Verificar sinal completo
            if self.verificar_estrategia(estrategia, results):
                self.log(f"🎯 MATCH: {estrategia['original']}")
                self.send_signal(estrategia, results)
                return  # Parar após primeiro match
    
    def run_bot(self):
        """Loop principal do bot com variáveis avançadas"""
        self.log("🚀 Bot iniciado com sistema de variáveis avançadas")
        
        # Mensagem de início
        message = self.processar_template_avancado('inicio_template')
        self.send_telegram_message(message)
        
        while self.running:
            try:
                # Verificar mudança de dia
                self.verificar_mudanca_dia()
                
                # Buscar resultados
                results = self.fetch_blaze_results()
                
                if results and results[0] != self.ultimo_resultado:
                    novo_resultado = results[0]
                    
                    # Processar gales ativos primeiro
                    if self.gales_ativos:
                        self.processar_resultado_gales(novo_resultado)
                    
                    # Atualizar estado
                    self.ultimo_resultado = novo_resultado
                    self.historico_resultados = results
                    
                    cor = self.convert_number_to_color(novo_resultado)
                    emoji = self.get_color_emoji(cor)
                    self.log(f"Novo resultado: {novo_resultado} ({emoji})")
                    
                    # Processar estratégias para novos sinais
                    if not self.gales_ativos:  # Só enviar novo sinal se não tem gales ativos
                        self.processar_estrategias(results)
                
                time.sleep(self.bot_config["interval_seconds"])
                
            except Exception as e:
                self.log(f"Erro no loop: {e}", "ERROR")
                time.sleep(10)
        
        # Mensagem de finalização
        message = self.processar_template_avancado('fim_template')
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
    
    def obter_estatisticas_avancadas(self) -> Dict[str, Any]:
        """Retorna estatísticas avançadas do bot"""
        return self.processador_variaveis.obter_resumo_estatisticas()

def main():
    """Teste do bot avançado"""
    print("🤖 TESTE DO BOT AVANÇADO COM VARIÁVEIS GLOBAIS")
    print("=" * 55)
    
    # Configuração de teste
    config_teste = {
        "id": "bot_teste",
        "name": "Bot Teste Avançado",
        "token": "8106969377:AAHp4PRKZN-RHb1GxR3C3l7PzikFHEcRsck",
        "chat_id": "-1002852101467",
        "active": True,
        "estrategias_file": "bot1_estrategias.csv",
        "config": {
            "max_gales": 2,
            "protection": True,
            "interval_seconds": 5,
            "enable_alerts": True
        },
        "mensagens": {
            "sinal_template": """🎯 [N]SINAL DETECTADO[/N] 🔥

📋 **Estratégia**: [NOME_ESTRATEGIA]
🎰 **Apostar**: {cor_emoji} **{cor_nome}**
🛡️ **Proteção**: ⚪ BRANCO
🔄 **Gales**: Até [MAX_GALES]x

📊 **Hoje**: [WINS]W | [LOSSES]L | [PERCENTUAL_ASSERTIVIDADE]%
🔥 **Sequência**: [GANHOS_CONSECUTIVOS] seguidos

📅 [DATA_HOJE] | ⏰ [HORA_AGORA]""",
            
            "stats_template": """📊 [N]ESTATÍSTICAS[/N] - [DATA_HOJE]

🎯 **Performance**:
• ✅ Wins: [WINS] | ❌ Losses: [LOSSES]
• 📈 Assertividade: [PERCENTUAL_ASSERTIVIDADE]%
• 🔥 Sequência: [GANHOS_CONSECUTIVOS]

🎲 **Detalhamento**:
• 🎯 Sem Gale: [SG]
• 🎲 G1: [G1] | G2: [G2]

⏰ [HORA_AGORA]""",
            
            "inicio_template": """🚀 [N]{bot_name} ONLINE[/N]

📋 {total_estrategias} estratégias carregadas
🎯 Gales: até [MAX_GALES]x
📅 [DATA_HOJE] | ⏰ [HORA_AGORA]

💪 [N]VAMOS LUCRAR![/N]""",
            
            "fim_template": """🛑 [N]{bot_name} OFFLINE[/N]

📊 **Resumo**: [WINS]W | [LOSSES]L
📈 **Assertividade**: [PERCENTUAL_ASSERTIVIDADE]%

⏰ Finalizado às [HORA_AGORA]"""
        }
    }
    
    # Criar e testar bot
    bot = BotAvancadoComVariaveis(config_teste)
    
    # Simular algumas estatísticas
    bot.processador_variaveis.atualizar_estatisticas('WIN', 0, 'V-V=P')
    bot.processador_variaveis.atualizar_estatisticas('WIN', 1, 'P-P=V')
    bot.processador_variaveis.atualizar_estatisticas('LOSS', 2, 'V-V-P=V')
    
    # Testar processamento de templates
    print("\n🔍 TESTE DE TEMPLATES:")
    print("-" * 30)
    
    # Template de início
    msg_inicio = bot.processar_template_avancado('inicio_template')
    print("📨 Mensagem de início:")
    print(msg_inicio)
    print()
    
    # Template de estatísticas
    msg_stats = bot.processar_template_avancado('stats_template')
    print("📨 Mensagem de estatísticas:")
    print(msg_stats)
    print()
    
    # Estatísticas avançadas
    stats = bot.obter_estatisticas_avancadas()
    print("📊 Estatísticas avançadas:")
    for key, value in stats.items():
        print(f"  • {key}: {value}")

if __name__ == "__main__":
    main() 