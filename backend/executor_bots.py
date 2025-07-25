#!/usr/bin/env python3
"""
🚀 EXECUTOR PRINCIPAL DOS BOTS
Sistema de execução contínua que conecta toda a infraestrutura:
Coleta → Análise → Detecção → Envio para Telegram
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import signal
import sys

# Imports dos nossos módulos
from plataformas_api import GerenciadorPlataformas
from analisador_estrategias import AnalisadorEstrategias
from sistema_variaveis_mensagens import ProcessadorVariaveisGlobais

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('executor_bots.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ControladorGales:
    """Controla o sistema de gales para cada estratégia"""
    
    def __init__(self):
        self.gales_ativos = {}  # {estrategia_id: {'gale_atual': 0, 'timestamp': datetime, ...}}
        self.resultados_aguardando = {}  # Aguardando resultados de sinais enviados
        
    def iniciar_gale(self, robo_id: str, estrategia_nome: str, max_gales: int):
        """Inicia uma sequência de gales"""
        gale_id = f"{robo_id}_{estrategia_nome}_{int(time.time())}"
        
        self.gales_ativos[gale_id] = {
            'robo_id': robo_id,
            'estrategia': estrategia_nome,
            'gale_atual': 0,
            'max_gales': max_gales,
            'timestamp_inicio': datetime.now(),
            'timestamp_ultimo': datetime.now(),
            'resultado_esperado': None,
            'status': 'ativo'
        }
        
        logger.info(f"🎲 Gale iniciado: {gale_id}")
        return gale_id
    
    def verificar_resultado(self, gale_id: str, resultado_numero: int, resultado_cor: str) -> str:
        """Verifica resultado e determina próxima ação"""
        if gale_id not in self.gales_ativos:
            return "gale_nao_encontrado"
        
        gale = self.gales_ativos[gale_id]
        resultado_esperado = gale.get('resultado_esperado')
        
        # Verificar se bateu
        if resultado_cor == resultado_esperado or resultado_cor == 'B':  # B = proteção
            # WIN!
            resultado_final = "win" if resultado_cor == resultado_esperado else "protecao"
            self.finalizar_gale(gale_id, resultado_final)
            logger.info(f"✅ {resultado_final.upper()}: {gale_id} - G{gale['gale_atual']}")
            return resultado_final
        
        else:
            # LOSS neste gale
            gale['gale_atual'] += 1
            gale['timestamp_ultimo'] = datetime.now()
            
            if gale['gale_atual'] >= gale['max_gales']:
                # Máximo de gales atingido - LOSS FINAL
                self.finalizar_gale(gale_id, "loss")
                logger.info(f"❌ LOSS FINAL: {gale_id} - G{gale['gale_atual']}")
                return "loss"
            else:
                # Continuar para próximo gale
                logger.info(f"🔄 Próximo gale: {gale_id} - G{gale['gale_atual'] + 1}")
                return f"proximo_gale_G{gale['gale_atual'] + 1}"
    
    def finalizar_gale(self, gale_id: str, resultado: str):
        """Finaliza uma sequência de gales"""
        if gale_id in self.gales_ativos:
            gale = self.gales_ativos[gale_id]
            gale['status'] = 'finalizado'
            gale['resultado_final'] = resultado
            gale['timestamp_fim'] = datetime.now()
            
            # Mover para histórico (opcional - implementar depois)
            del self.gales_ativos[gale_id]
    
    def definir_resultado_esperado(self, gale_id: str, cor_esperada: str):
        """Define qual resultado estamos esperando"""
        if gale_id in self.gales_ativos:
            self.gales_ativos[gale_id]['resultado_esperado'] = cor_esperada

class TelegramSender:
    """Envia mensagens para o Telegram"""
    
    def __init__(self):
        self.rate_limits = {}  # Controle de rate limit por bot
        
    async def enviar_mensagem(self, token: str, chat_id: str, mensagem: str) -> bool:
        """Envia mensagem para o Telegram"""
        try:
            import aiohttp
            
            # Verificar rate limit
            if not self._verificar_rate_limit(token):
                logger.warning(f"Rate limit atingido para token {token[:20]}...")
                return False
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    'chat_id': chat_id,
                    'text': mensagem,
                    'parse_mode': 'Markdown'
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"✅ Mensagem enviada para {chat_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Erro Telegram {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def _verificar_rate_limit(self, token: str) -> bool:
        """Verifica se pode enviar mensagem (rate limit)"""
        agora = time.time()
        
        if token not in self.rate_limits:
            self.rate_limits[token] = []
        
        # Limpar mensagens antigas (últimos 60 segundos)
        self.rate_limits[token] = [
            t for t in self.rate_limits[token] 
            if agora - t < 60
        ]
        
        # Telegram permite ~20 mensagens por minuto
        if len(self.rate_limits[token]) >= 18:
            return False
        
        self.rate_limits[token].append(agora)
        return True

class ExecutorBots:
    """Executor principal que coordena todos os bots"""
    
    def __init__(self):
        self.gerenciador_plataformas = GerenciadorPlataformas()
        self.analisador = AnalisadorEstrategias()
        self.controlador_gales = ControladorGales()
        self.telegram = TelegramSender()
        self.processadores_mensagens = {}  # Um por robô
        
        self.robos_ativos = []
        self.executando = False
        self.intervalo_verificacao = 3  # segundos
        
        self.ultima_verificacao = {}  # Por plataforma
        self.dados_cache = {}  # Cache dos últimos dados
        
        # Estatísticas
        self.stats = {
            'sinais_enviados': 0,
            'wins': 0,
            'losses': 0,
            'inicio_execucao': None
        }
        
    def carregar_robos(self):
        """Carrega robôs configurados"""
        try:
            config_file = Path("robos_configurados.json")
            if not config_file.exists():
                logger.error("❌ Arquivo robos_configurados.json não encontrado")
                return []
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            robos = config.get('robos', [])
            robos_ativos = [r for r in robos if r.get('status') == 'ativo']
            
            logger.info(f"📋 {len(robos_ativos)} robôs ativos carregados")
            
            # Criar processadores de mensagens para cada robô
            for robo in robos_ativos:
                robo_id = robo['id']
                self.processadores_mensagens[robo_id] = ProcessadorVariaveisGlobais()
            
            return robos_ativos
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar robôs: {e}")
            return []
    
    async def verificar_plataforma(self, plataforma_id: str) -> List[Dict]:
        """Verifica uma plataforma e retorna novos resultados"""
        try:
            # Buscar dados atuais
            dados_atuais = self.gerenciador_plataformas.buscar_dados_plataforma(plataforma_id)
            
            if not dados_atuais:
                return []
            
            # Verificar se há dados novos
            dados_anteriores = self.dados_cache.get(plataforma_id, [])
            
            if not dados_anteriores:
                # Primeira vez - salvar no cache
                self.dados_cache[plataforma_id] = dados_atuais
                logger.info(f"🎰 {plataforma_id}: {len(dados_atuais)} resultados iniciais")
                return []
            
            # Comparar e encontrar novos
            novos_resultados = []
            
            for resultado in dados_atuais:
                resultado_id = resultado.get('id')
                
                # Verificar se já existia
                ja_existe = any(r.get('id') == resultado_id for r in dados_anteriores)
                
                if not ja_existe:
                    novos_resultados.append(resultado)
            
            if novos_resultados:
                logger.info(f"🆕 {plataforma_id}: {len(novos_resultados)} novos resultados")
                
                # Atualizar cache
                self.dados_cache[plataforma_id] = dados_atuais
                
                # Salvar dados históricos
                self.gerenciador_plataformas.salvar_dados_historicos({
                    plataforma_id: dados_atuais
                })
            
            return novos_resultados
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar {plataforma_id}: {e}")
            return []
    
    def verificar_estrategias_robo(self, robo: Dict, novos_resultados: List[Dict]) -> List[Dict]:
        """Verifica estratégias de um robô contra novos resultados"""
        if not novos_resultados:
            return []
        
        plataforma_id = robo['plataforma']['id']
        dados_historicos = self.dados_cache.get(plataforma_id, [])
        
        if len(dados_historicos) < 10:  # Precisa de histórico mínimo
            return []
        
        sinais_detectados = []
        
        for estrategia in robo.get('estrategias', []):
            # Usar o analisador para verificar se a estratégia bate
            try:
                # Simular análise da estratégia com dados atuais
                pattern = estrategia['pattern']
                bet_direction = estrategia['bet']
                
                # Verificar se o padrão se forma nos últimos resultados
                if self._verificar_match_pattern(pattern, dados_historicos[-10:]):
                    # Sinal detectado!
                    sinal = {
                        'robo_id': robo['id'],
                        'robo_nome': robo['nome'],
                        'estrategia': estrategia,
                        'cor_apostada': bet_direction,
                        'timestamp': datetime.now().isoformat(),
                        'dados_contexto': dados_historicos[-5:],  # Últimos 5 para contexto
                        'confianca': self._calcular_confianca(estrategia, dados_historicos)
                    }
                    
                    sinais_detectados.append(sinal)
                    logger.info(f"🎯 SINAL: {robo['nome']} - {estrategia['name']}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao verificar estratégia {estrategia.get('name', '?')}: {e}")
        
        return sinais_detectados
    
    def _verificar_match_pattern(self, pattern: str, dados_historicos: List[Dict]) -> bool:
        """Verifica se um padrão faz match com o histórico"""
        try:
            condicoes = pattern.split('-')
            
            if len(condicoes) > len(dados_historicos):
                return False
            
            # Verificar as últimas N posições (onde N = len(condicoes))
            resultados_relevantes = dados_historicos[-len(condicoes):]
            
            for i, condicao in enumerate(condicoes):
                resultado = resultados_relevantes[i]
                numero = resultado['numero']
                cor = resultado['cor']
                
                # Verificar match
                if condicao == "X":  # Wildcard
                    continue
                elif condicao == str(numero):  # Match por número
                    continue
                elif condicao == cor:  # Match por cor
                    continue
                else:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar pattern {pattern}: {e}")
            return False
    
    def _calcular_confianca(self, estrategia: Dict, dados_historicos: List[Dict]) -> float:
        """Calcula confiança da estratégia baseada no histórico"""
        try:
            # Análise rápida dos últimos 100 resultados
            analise = self.analisador.analisar_estrategia_historica(
                estrategia, dados_historicos, janela_analise=min(100, len(dados_historicos))
            )
            
            return analise.get('taxa_sucesso', 50.0)
            
        except Exception:
            return 60.0  # Confiança padrão
    
    async def processar_sinal(self, sinal: Dict) -> bool:
        """Processa um sinal detectado"""
        try:
            robo_id = sinal['robo_id']
            
            # Buscar configuração do robô
            robo = next((r for r in self.robos_ativos if r['id'] == robo_id), None)
            if not robo:
                logger.error(f"❌ Robô {robo_id} não encontrado")
                return False
            
            # Verificar confiança mínima
            confianca_minima = robo['configuracoes'].get('confianca_minima', 75)
            if sinal['confianca'] < confianca_minima:
                logger.info(f"⚠️ Sinal rejeitado - confiança {sinal['confianca']:.1f}% < {confianca_minima}%")
                return False
            
            # Verificar limite diário de sinais
            max_sinais_dia = robo['configuracoes'].get('max_sinais_dia', 20)
            # TODO: Implementar contagem diária
            
            # Gerar mensagem
            mensagem = self._gerar_mensagem_sinal(robo, sinal)
            
            # Enviar para Telegram
            token = robo['telegram']['token']
            chat_id = robo['telegram']['chat_id']
            
            sucesso = await self.telegram.enviar_mensagem(token, chat_id, mensagem)
            
            if sucesso:
                # Iniciar controle de gales
                max_gales = robo['configuracoes'].get('max_gales', 2)
                gale_id = self.controlador_gales.iniciar_gale(
                    robo_id, sinal['estrategia']['name'], max_gales
                )
                
                self.controlador_gales.definir_resultado_esperado(
                    gale_id, sinal['cor_apostada']
                )
                
                # Atualizar estatísticas
                self.stats['sinais_enviados'] += 1
                
                # Atualizar processador de mensagens
                if robo_id in self.processadores_mensagens:
                    processador = self.processadores_mensagens[robo_id]
                    processador.stats['nome_estrategia'] = sinal['estrategia']['name']
                
                logger.info(f"📤 Sinal enviado: {robo['nome']} - {sinal['estrategia']['name']}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar sinal: {e}")
            return False
    
    def _gerar_mensagem_sinal(self, robo: Dict, sinal: Dict) -> str:
        """Gera mensagem do sinal usando o sistema de variáveis"""
        try:
            robo_id = robo['id']
            
            # Usar template personalizado do robô ou padrão
            template = robo.get('mensagens', {}).get('sinal_template', self._get_template_padrao())
            
            # Preparar variáveis para o template
            estrategia = sinal['estrategia']
            cor_apostada = sinal['cor_apostada']
            
            # Emoji da cor
            cor_emoji = "🔴" if cor_apostada == "V" else "⚫" if cor_apostada == "P" else "⚪"
            cor_nome = "VERMELHO" if cor_apostada == "V" else "PRETO" if cor_apostada == "P" else "BRANCO"
            
            # Contexto dos últimos números
            contexto = sinal.get('dados_contexto', [])
            numeros = ", ".join([str(r['numero']) for r in contexto[-5:]])
            cores_emoji = " ".join([
                "🔴" if r['cor'] == "V" else "⚫" if r['cor'] == "P" else "⚪" 
                for r in contexto[-5:]
            ])
            
            # Usar processador de variáveis globais
            if robo_id in self.processadores_mensagens:
                processador = self.processadores_mensagens[robo_id]
                
                mensagem = processador.processar_todas_variaveis(
                    template,
                    bot_name=robo['nome'],
                    estrategia=estrategia['name'],
                    cor_emoji=cor_emoji,
                    cor_nome=cor_nome,
                    max_gales=str(robo['configuracoes'].get('max_gales', 2)),
                    numeros=numeros,
                    cores_emoji=cores_emoji,
                    confianca=f"{sinal['confianca']:.0f}",
                    timestamp=datetime.now().strftime("%H:%M:%S")
                )
            else:
                # Fallback simples
                mensagem = f"🎯 **SINAL {robo['nome']}**\n\n"
                mensagem += f"📋 **Estratégia**: {estrategia['name']}\n"
                mensagem += f"🎰 **Apostar em**: {cor_emoji} **{cor_nome}**\n"
                mensagem += f"💰 **Proteção**: ⚪ **BRANCO**\n"
                mensagem += f"📊 **Confiança**: {sinal['confianca']:.0f}%\n"
                mensagem += f"⏰ **{datetime.now().strftime('%H:%M:%S')}**"
            
            return mensagem
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar mensagem: {e}")
            return "🎯 Sinal detectado (erro na formatação)"
    
    def _get_template_padrao(self) -> str:
        """Template padrão para sinais"""
        return """🎯 **SINAL {bot_name}** 🔥

📋 **Estratégia**: {estrategia}
🎰 **Apostar em**: {cor_emoji} **{cor_nome}**
💰 **Proteção**: ⚪ **BRANCO**
♻️ **Gales**: Até {max_gales}

📊 **Análise**:
• Últimos: {numeros}
• Cores: {cores_emoji}
• Confiança: {confianca}%

⏰ **{timestamp}**

🍀 **BOA SORTE!** 🚀"""
    
    async def loop_principal(self):
        """Loop principal de execução"""
        logger.info("🚀 Iniciando loop principal dos bots")
        self.stats['inicio_execucao'] = datetime.now()
        
        while self.executando:
            try:
                # Verificar cada plataforma usada pelos robôs ativos
                plataformas_usadas = list(set(r['plataforma']['id'] for r in self.robos_ativos))
                
                for plataforma_id in plataformas_usadas:
                    # Verificar novos resultados
                    novos_resultados = await self.verificar_plataforma(plataforma_id)
                    
                    if novos_resultados:
                        # Verificar estratégias de cada robô desta plataforma
                        for robo in self.robos_ativos:
                            if robo['plataforma']['id'] == plataforma_id:
                                sinais = self.verificar_estrategias_robo(robo, novos_resultados)
                                
                                # Processar sinais detectados
                                for sinal in sinais:
                                    await self.processar_sinal(sinal)
                                    
                                    # Intervalo entre sinais
                                    await asyncio.sleep(1)
                
                # Aguardar próxima verificação
                await asyncio.sleep(self.intervalo_verificacao)
                
            except Exception as e:
                logger.error(f"❌ Erro no loop principal: {e}")
                await asyncio.sleep(5)  # Pausa em caso de erro
    
    async def iniciar(self):
        """Inicia o executor"""
        logger.info("🎬 INICIANDO EXECUTOR DE BOTS")
        
        # Carregar robôs
        self.robos_ativos = self.carregar_robos()
        
        if not self.robos_ativos:
            logger.error("❌ Nenhum robô ativo encontrado")
            return False
        
        # Verificar conectividade das plataformas
        plataformas_usadas = list(set(r['plataforma']['id'] for r in self.robos_ativos))
        logger.info(f"🎰 Verificando {len(plataformas_usadas)} plataformas...")
        
        conectividade = self.gerenciador_plataformas.testar_conectividade()
        plataformas_online = [p for p in plataformas_usadas if conectividade.get(p, False)]
        
        if not plataformas_online:
            logger.error("❌ Nenhuma plataforma online")
            return False
        
        logger.info(f"✅ {len(plataformas_online)} plataformas online")
        
        # Inicializar cache de dados
        logger.info("📊 Inicializando cache de dados...")
        for plataforma_id in plataformas_online:
            dados_iniciais = self.gerenciador_plataformas.buscar_dados_plataforma(plataforma_id)
            if dados_iniciais:
                self.dados_cache[plataforma_id] = dados_iniciais
                logger.info(f"  📥 {plataforma_id}: {len(dados_iniciais)} resultados")
        
        # Iniciar execução
        self.executando = True
        
        logger.info("🎯 EXECUTOR INICIADO - Monitorando sinais...")
        logger.info(f"   🤖 Robôs ativos: {len(self.robos_ativos)}")
        logger.info(f"   🎰 Plataformas: {', '.join(plataformas_online)}")
        logger.info(f"   ⏱️ Intervalo: {self.intervalo_verificacao}s")
        
        # Executar loop principal
        await self.loop_principal()
        
        return True
    
    def parar(self):
        """Para a execução"""
        logger.info("🛑 Parando executor...")
        self.executando = False
    
    def get_estatisticas(self) -> Dict:
        """Retorna estatísticas de execução"""
        tempo_execucao = None
        if self.stats['inicio_execucao']:
            tempo_execucao = (datetime.now() - self.stats['inicio_execucao']).total_seconds()
        
        return {
            'sinais_enviados': self.stats['sinais_enviados'],
            'wins': self.stats['wins'],
            'losses': self.stats['losses'],
            'tempo_execucao_segundos': tempo_execucao,
            'robos_ativos': len(self.robos_ativos),
            'gales_ativos': len(self.controlador_gales.gales_ativos)
        }

# Variável global para o executor
executor_global = None

def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global executor_global
    print("\n🛑 Interrompido pelo usuário")
    if executor_global:
        executor_global.parar()
    sys.exit(0)

async def main():
    """Função principal"""
    global executor_global
    
    # Configurar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 EXECUTOR DE BOTS - SISTEMA MULTI-PLATAFORMA")
    print("=" * 55)
    print("Pressione Ctrl+C para parar")
    print()
    
    executor_global = ExecutorBots()
    
    try:
        await executor_global.iniciar()
    except KeyboardInterrupt:
        print("\n🛑 Executor interrompido")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
    finally:
        if executor_global:
            executor_global.parar()
            
            # Mostrar estatísticas finais
            stats = executor_global.get_estatisticas()
            print(f"\n📊 ESTATÍSTICAS FINAIS:")
            print(f"  📤 Sinais enviados: {stats['sinais_enviados']}")
            print(f"  ✅ Wins: {stats['wins']}")
            print(f"  ❌ Losses: {stats['losses']}")
            if stats['tempo_execucao_segundos']:
                print(f"  ⏱️ Tempo execução: {stats['tempo_execucao_segundos']:.0f}s")

if __name__ == "__main__":
    asyncio.run(main()) 