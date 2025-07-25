#!/usr/bin/env python3
"""
🔐 VALIDADOR DE CONFIGURAÇÕES
Sistema para validar tokens, canais e configurações dos robôs
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any
import aiohttp
import logging

logger = logging.getLogger(__name__)

class ValidadorConfiguracoes:
    def __init__(self):
        self.resultados_validacao = {}
        
    async def validar_token_telegram(self, token: str) -> Tuple[bool, str, Dict]:
        """Valida token do Telegram Bot"""
        try:
            # Verificar formato do token
            if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
                return False, "Formato de token inválido", {}
            
            # Testar API do Telegram
            url = f"https://api.telegram.org/bot{token}/getMe"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok'):
                            bot_info = data.get('result', {})
                            return True, "Token válido", {
                                'bot_id': bot_info.get('id'),
                                'bot_name': bot_info.get('first_name'),
                                'username': bot_info.get('username'),
                                'can_join_groups': bot_info.get('can_join_groups'),
                                'can_read_all_group_messages': bot_info.get('can_read_all_group_messages')
                            }
                        else:
                            return False, "Token rejeitado pela API", {}
                    else:
                        return False, f"Erro HTTP {response.status}", {}
                        
        except Exception as e:
            return False, f"Erro na validação: {str(e)}", {}
    
    async def validar_chat_id(self, token: str, chat_id: str) -> Tuple[bool, str, Dict]:
        """Valida se o bot consegue enviar mensagens para o chat"""
        try:
            # Verificar formato do chat_id
            if chat_id.startswith('@'):
                # Username do canal
                if not re.match(r'^@[A-Za-z0-9_]+$', chat_id):
                    return False, "Formato de username inválido", {}
            else:
                # ID numérico
                try:
                    int(chat_id)
                except ValueError:
                    return False, "Chat ID deve ser numérico ou @username", {}
            
            # Testar envio de mensagem
            url = f"https://api.telegram.org/bot{token}/getChat"
            
            async with aiohttp.ClientSession() as session:
                payload = {'chat_id': chat_id}
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok'):
                            chat_info = data.get('result', {})
                            return True, "Chat ID válido", {
                                'chat_id': chat_info.get('id'),
                                'title': chat_info.get('title'),
                                'type': chat_info.get('type'),
                                'description': chat_info.get('description')
                            }
                        else:
                            return False, "Chat não encontrado ou bot não tem acesso", {}
                    else:
                        return False, f"Erro HTTP {response.status}", {}
                        
        except Exception as e:
            return False, f"Erro na validação: {str(e)}", {}
    
    async def testar_envio_mensagem(self, token: str, chat_id: str) -> Tuple[bool, str]:
        """Testa envio real de mensagem"""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            
            mensagem_teste = "🔧 **TESTE DE CONFIGURAÇÃO**\n\nSeu bot está funcionando corretamente!\n⏰ " + \
                           f"{asyncio.get_event_loop().time()}"
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    'chat_id': chat_id,
                    'text': mensagem_teste,
                    'parse_mode': 'Markdown'
                }
                
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('ok'):
                            return True, "Mensagem enviada com sucesso"
                        else:
                            return False, f"Erro na API: {data.get('description', 'Desconhecido')}"
                    else:
                        error_text = await response.text()
                        return False, f"Erro HTTP {response.status}: {error_text}"
                        
        except Exception as e:
            return False, f"Erro ao enviar: {str(e)}"
    
    def validar_configuracoes_robo(self, robo: Dict) -> Dict[str, Any]:
        """Valida configurações de um robô"""
        validacao = {
            'robo_id': robo.get('id'),
            'nome': robo.get('nome'),
            'valido': True,
            'erros': [],
            'avisos': [],
            'detalhes': {}
        }
        
        # Validar campos obrigatórios
        campos_obrigatorios = {
            'id': 'ID do robô',
            'nome': 'Nome do robô',
            'plataforma': 'Configuração da plataforma',
            'telegram': 'Configuração do Telegram',
            'configuracoes': 'Configurações operacionais',
            'estrategias': 'Lista de estratégias'
        }
        
        for campo, descricao in campos_obrigatorios.items():
            if not robo.get(campo):
                validacao['erros'].append(f"Campo obrigatório ausente: {descricao}")
                validacao['valido'] = False
        
        # Validar plataforma
        if robo.get('plataforma'):
            plataforma = robo['plataforma']
            if not plataforma.get('id'):
                validacao['erros'].append("ID da plataforma não especificado")
                validacao['valido'] = False
            else:
                plataformas_suportadas = ['blaze', 'jonbet', 'betfire']
                if plataforma['id'] not in plataformas_suportadas:
                    validacao['avisos'].append(f"Plataforma '{plataforma['id']}' pode não estar totalmente suportada")
        
        # Validar configurações do Telegram
        if robo.get('telegram'):
            telegram = robo['telegram']
            
            if not telegram.get('token'):
                validacao['erros'].append("Token do Telegram não especificado")
                validacao['valido'] = False
            
            if not telegram.get('chat_id'):
                validacao['erros'].append("Chat ID não especificado")
                validacao['valido'] = False
        
        # Validar configurações operacionais
        if robo.get('configuracoes'):
            config = robo['configuracoes']
            
            # Validar max_gales
            max_gales = config.get('max_gales', 2)
            if not isinstance(max_gales, int) or max_gales < 0 or max_gales > 10:
                validacao['erros'].append("max_gales deve ser um número entre 0 e 10")
                validacao['valido'] = False
            
            # Validar intervalo
            intervalo = config.get('intervalo_segundos', 3)
            if not isinstance(intervalo, int) or intervalo < 1 or intervalo > 60:
                validacao['erros'].append("intervalo_segundos deve ser entre 1 e 60")
                validacao['valido'] = False
            
            # Validar confiança
            confianca = config.get('confianca_minima', 75)
            if not isinstance(confianca, (int, float)) or confianca < 0 or confianca > 100:
                validacao['erros'].append("confianca_minima deve ser entre 0 e 100")
                validacao['valido'] = False
            
            # Validar max_sinais_dia
            max_sinais = config.get('max_sinais_dia', 20)
            if not isinstance(max_sinais, int) or max_sinais < 1 or max_sinais > 100:
                validacao['erros'].append("max_sinais_dia deve ser entre 1 e 100")
                validacao['valido'] = False
        
        # Validar estratégias
        if robo.get('estrategias'):
            estrategias = robo['estrategias']
            
            if not isinstance(estrategias, list) or len(estrategias) == 0:
                validacao['erros'].append("Deve ter pelo menos uma estratégia")
                validacao['valido'] = False
            else:
                for i, estrategia in enumerate(estrategias):
                    if not isinstance(estrategia, dict):
                        validacao['erros'].append(f"Estratégia {i+1} deve ser um objeto")
                        continue
                    
                    # Validar campos da estratégia
                    if not estrategia.get('pattern'):
                        validacao['erros'].append(f"Estratégia {i+1}: pattern não especificado")
                        validacao['valido'] = False
                    
                    if not estrategia.get('bet'):
                        validacao['erros'].append(f"Estratégia {i+1}: bet não especificado")
                        validacao['valido'] = False
                    elif estrategia['bet'] not in ['V', 'P', 'B']:
                        validacao['erros'].append(f"Estratégia {i+1}: bet deve ser V, P ou B")
                        validacao['valido'] = False
                    
                    if not estrategia.get('name'):
                        validacao['avisos'].append(f"Estratégia {i+1}: nome não especificado")
                    
                    # Validar formato do pattern
                    if estrategia.get('pattern'):
                        pattern = estrategia['pattern']
                        if not re.match(r'^[VPBXvpbx0-9-]+$', pattern):
                            validacao['erros'].append(f"Estratégia {i+1}: pattern '{pattern}' contém caracteres inválidos")
                            validacao['valido'] = False
        
        return validacao
    
    async def validar_robo_completo(self, robo: Dict) -> Dict[str, Any]:
        """Validação completa de um robô (incluindo testes de conectividade)"""
        validacao = self.validar_configuracoes_robo(robo)
        
        if not validacao['valido']:
            return validacao
        
        # Testes de conectividade
        telegram = robo.get('telegram', {})
        token = telegram.get('token')
        chat_id = telegram.get('chat_id')
        
        if token:
            # Validar token
            print(f"🔍 Validando token do {robo['nome']}...")
            token_valido, token_msg, token_info = await self.validar_token_telegram(token)
            
            validacao['detalhes']['token'] = {
                'valido': token_valido,
                'mensagem': token_msg,
                'info': token_info
            }
            
            if not token_valido:
                validacao['erros'].append(f"Token inválido: {token_msg}")
                validacao['valido'] = False
            else:
                print(f"  ✅ Token válido - Bot: {token_info.get('bot_name', '?')}")
                
                # Validar chat_id se token é válido
                if chat_id:
                    print(f"🔍 Validando chat ID...")
                    chat_valido, chat_msg, chat_info = await self.validar_chat_id(token, chat_id)
                    
                    validacao['detalhes']['chat'] = {
                        'valido': chat_valido,
                        'mensagem': chat_msg,
                        'info': chat_info
                    }
                    
                    if not chat_valido:
                        validacao['erros'].append(f"Chat ID inválido: {chat_msg}")
                        validacao['valido'] = False
                    else:
                        print(f"  ✅ Chat válido - {chat_info.get('title', chat_id)}")
                        
                        # Teste de envio
                        print(f"📤 Testando envio de mensagem...")
                        envio_ok, envio_msg = await self.testar_envio_mensagem(token, chat_id)
                        
                        validacao['detalhes']['envio'] = {
                            'sucesso': envio_ok,
                            'mensagem': envio_msg
                        }
                        
                        if not envio_ok:
                            validacao['avisos'].append(f"Erro no teste de envio: {envio_msg}")
                        else:
                            print(f"  ✅ Mensagem de teste enviada com sucesso")
        
        return validacao
    
    async def validar_arquivo_robos(self, arquivo: str = "robos_configurados.json") -> Dict[str, Any]:
        """Valida arquivo completo de robôs"""
        resultado = {
            'arquivo': arquivo,
            'valido': True,
            'robos_validos': 0,
            'robos_com_erro': 0,
            'robos_com_aviso': 0,
            'validacoes': []
        }
        
        try:
            config_file = Path(arquivo)
            if not config_file.exists():
                resultado['valido'] = False
                resultado['erro'] = f"Arquivo {arquivo} não encontrado"
                return resultado
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            robos = config.get('robos', [])
            
            if not robos:
                resultado['valido'] = False
                resultado['erro'] = "Nenhum robô encontrado no arquivo"
                return resultado
            
            print(f"🔍 Validando {len(robos)} robôs...")
            
            for robo in robos:
                print(f"\n📋 Validando: {robo.get('nome', 'Sem nome')}")
                
                validacao = await self.validar_robo_completo(robo)
                resultado['validacoes'].append(validacao)
                
                if validacao['valido']:
                    resultado['robos_validos'] += 1
                    if validacao['avisos']:
                        resultado['robos_com_aviso'] += 1
                    print(f"  ✅ Robô válido")
                else:
                    resultado['robos_com_erro'] += 1
                    resultado['valido'] = False
                    print(f"  ❌ Robô com erros:")
                    for erro in validacao['erros']:
                        print(f"    • {erro}")
                
                if validacao['avisos']:
                    print(f"  ⚠️ Avisos:")
                    for aviso in validacao['avisos']:
                        print(f"    • {aviso}")
            
        except Exception as e:
            resultado['valido'] = False
            resultado['erro'] = f"Erro ao processar arquivo: {str(e)}"
        
        return resultado
    
    def gerar_relatorio_validacao(self, resultado: Dict) -> str:
        """Gera relatório textual da validação"""
        relatorio = ["🔐 RELATÓRIO DE VALIDAÇÃO DE CONFIGURAÇÕES"]
        relatorio.append("=" * 50)
        
        if not resultado['valido']:
            relatorio.append(f"❌ VALIDAÇÃO FALHOU")
            if 'erro' in resultado:
                relatorio.append(f"Erro: {resultado['erro']}")
            relatorio.append("")
        
        # Resumo
        relatorio.append("📊 RESUMO:")
        relatorio.append(f"  ✅ Robôs válidos: {resultado['robos_validos']}")
        relatorio.append(f"  ❌ Robôs com erro: {resultado['robos_com_erro']}")
        relatorio.append(f"  ⚠️ Robôs com aviso: {resultado['robos_com_aviso']}")
        relatorio.append("")
        
        # Detalhes por robô
        if resultado.get('validacoes'):
            relatorio.append("📋 DETALHES POR ROBÔ:")
            relatorio.append("-" * 30)
            
            for validacao in resultado['validacoes']:
                status = "✅" if validacao['valido'] else "❌"
                relatorio.append(f"{status} {validacao['nome']} ({validacao['robo_id']})")
                
                if validacao['erros']:
                    relatorio.append("  Erros:")
                    for erro in validacao['erros']:
                        relatorio.append(f"    • {erro}")
                
                if validacao['avisos']:
                    relatorio.append("  Avisos:")
                    for aviso in validacao['avisos']:
                        relatorio.append(f"    • {aviso}")
                
                # Detalhes de conectividade
                if validacao.get('detalhes'):
                    detalhes = validacao['detalhes']
                    
                    if 'token' in detalhes:
                        token = detalhes['token']
                        if token['valido'] and token.get('info'):
                            info = token['info']
                            relatorio.append(f"  Bot: {info.get('bot_name')} (@{info.get('username')})")
                    
                    if 'chat' in detalhes:
                        chat = detalhes['chat']
                        if chat['valido'] and chat.get('info'):
                            info = chat['info']
                            relatorio.append(f"  Chat: {info.get('title', info.get('chat_id'))}")
                    
                    if 'envio' in detalhes:
                        envio = detalhes['envio']
                        status_envio = "✅" if envio['sucesso'] else "❌"
                        relatorio.append(f"  Teste envio: {status_envio} {envio['mensagem']}")
                
                relatorio.append("")
        
        return "\n".join(relatorio)

async def main():
    """Função principal para validação"""
    print("🔐 VALIDADOR DE CONFIGURAÇÕES")
    print("=" * 35)
    
    validador = ValidadorConfiguracoes()
    
    # Validar arquivo de robôs
    resultado = await validador.validar_arquivo_robos()
    
    # Gerar e exibir relatório
    relatorio = validador.gerar_relatorio_validacao(resultado)
    print(relatorio)
    
    # Salvar relatório
    relatorio_file = Path("relatorio_validacao.txt")
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        f.write(relatorio)
    
    print(f"\n💾 Relatório salvo em: {relatorio_file}")
    
    if resultado['valido']:
        print("🎉 Todas as configurações estão válidas!")
        return True
    else:
        print("⚠️ Existem problemas nas configurações que precisam ser corrigidos.")
        return False

if __name__ == "__main__":
    asyncio.run(main()) 