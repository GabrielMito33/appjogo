#!/usr/bin/env python3
"""
🚀 MIGRAÇÃO PARA SUPABASE
Script para migrar dados locais (JSON/SQLite) para Supabase
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import bcrypt

from supabase_config import DatabaseManager, carregar_configuracao_env

class MigradorSupabase:
    """Migrador de dados para Supabase"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.dados_migrados = {
            'usuarios': 0,
            'robos': 0,
            'estrategias': 0,
            'resultados': 0,
            'erros': []
        }
    
    async def init(self):
        """Inicializa conexões"""
        await self.db.init()
    
    async def close(self):
        """Fecha conexões"""
        await self.db.close()
    
    def carregar_dados_locais(self) -> Dict:
        """Carrega dados dos arquivos JSON locais"""
        dados = {
            'robos_config': None,
            'dados_plataformas': None,
            'relatorio_demo': None
        }
        
        # Carregar robos_configurados.json
        if Path('robos_configurados.json').exists():
            with open('robos_configurados.json', 'r', encoding='utf-8') as f:
                dados['robos_config'] = json.load(f)
        
        # Carregar dados_plataformas.json
        if Path('dados_plataformas.json').exists():
            with open('dados_plataformas.json', 'r', encoding='utf-8') as f:
                dados['dados_plataformas'] = json.load(f)
        
        # Carregar relatorio_demonstracao.json
        if Path('relatorio_demonstracao.json').exists():
            with open('relatorio_demonstracao.json', 'r', encoding='utf-8') as f:
                dados['relatorio_demo'] = json.load(f)
        
        return dados
    
    def gerar_senha_hash(self, senha: str) -> str:
        """Gera hash da senha usando bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')
    
    async def criar_usuario_padrao(self) -> str:
        """Cria usuário padrão do sistema"""
        print("👤 Criando usuário padrão...")
        
        # Verificar se já existe
        usuario_existente = await self.db.buscar_usuario_por_email('admin@sistema.local')
        if usuario_existente:
            print("   ✅ Usuário padrão já existe")
            return usuario_existente['id']
        
        # Criar novo usuário
        senha_hash = self.gerar_senha_hash('admin123')
        user_id = await self.db.criar_usuario(
            email='admin@sistema.local',
            nome='Administrador Local',
            senha_hash=senha_hash,
            plano='admin'
        )
        
        if user_id:
            print(f"   ✅ Usuário criado: {user_id}")
            self.dados_migrados['usuarios'] += 1
            return user_id
        else:
            erro = "Erro ao criar usuário padrão"
            print(f"   ❌ {erro}")
            self.dados_migrados['erros'].append(erro)
            return None
    
    async def migrar_robos(self, dados: Dict, usuario_id: str):
        """Migra robôs dos dados locais"""
        if not dados.get('robos_config'):
            print("⚠️ Nenhum dado de robôs encontrado")
            return
        
        print("🤖 Migrando robôs...")
        
        robos = dados['robos_config'].get('robos', [])
        
        for robo_data in robos:
            try:
                print(f"   🔄 Migrando: {robo_data['nome']}")
                
                # Criar robô
                robo_id = await self.db.criar_robo(
                    usuario_id=usuario_id,
                    plataforma_id=robo_data['plataforma']['id'],
                    nome=robo_data['nome'],
                    telegram_bot_token=robo_data['telegram']['token'],
                    telegram_chat_id=robo_data['telegram']['chat_id']
                )
                
                if robo_id:
                    print(f"     ✅ Robô criado: {robo_id}")
                    self.dados_migrados['robos'] += 1
                    
                    # Migrar estratégias do robô
                    await self.migrar_estrategias_robo(robo_data, robo_id)
                    
                    # Atualizar configurações e status
                    await self.db.client.update(
                        'robos',
                        {
                            'status': robo_data.get('status', 'inativo'),
                            'configuracoes': robo_data.get('configuracoes', {}),
                            'estatisticas': robo_data.get('estatisticas', {})
                        },
                        {'id': robo_id}
                    )
                else:
                    erro = f"Erro ao criar robô: {robo_data['nome']}"
                    print(f"     ❌ {erro}")
                    self.dados_migrados['erros'].append(erro)
            
            except Exception as e:
                erro = f"Erro ao migrar robô {robo_data.get('nome', 'desconhecido')}: {e}"
                print(f"     ❌ {erro}")
                self.dados_migrados['erros'].append(erro)
    
    async def migrar_estrategias_robo(self, robo_data: Dict, robo_id: str):
        """Migra estratégias de um robô"""
        estrategias = robo_data.get('estrategias', [])
        
        for estrategia in estrategias:
            try:
                estrategia_id = await self.db.criar_estrategia(
                    robo_id=robo_id,
                    nome=estrategia.get('name', 'Estratégia'),
                    pattern=estrategia.get('pattern', ''),
                    bet=estrategia.get('bet', ''),
                    confianca=estrategia.get('confianca', 50)
                )
                
                if estrategia_id:
                    print(f"       ✅ Estratégia: {estrategia['name']}")
                    self.dados_migrados['estrategias'] += 1
                else:
                    erro = f"Erro ao criar estratégia: {estrategia.get('name')}"
                    print(f"       ❌ {erro}")
                    self.dados_migrados['erros'].append(erro)
            
            except Exception as e:
                erro = f"Erro ao migrar estratégia {estrategia.get('name', 'desconhecida')}: {e}"
                print(f"       ❌ {erro}")
                self.dados_migrados['erros'].append(erro)
    
    async def migrar_resultados_plataformas(self, dados: Dict):
        """Migra resultados das plataformas"""
        if not dados.get('dados_plataformas'):
            print("⚠️ Nenhum dado de plataformas encontrado")
            return
        
        print("📊 Migrando resultados das plataformas...")
        
        plataformas_data = dados['dados_plataformas'].get('plataformas', {})
        
        for plataforma_id, resultados in plataformas_data.items():
            print(f"   🎰 Migrando {plataforma_id}: {len(resultados)} resultados")
            
            for resultado in resultados:
                try:
                    # Converter timestamp
                    timestamp_str = resultado.get('created_at', resultado.get('timestamp'))
                    if timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = datetime.now()
                    
                    # Determinar cor baseada no número
                    numero = resultado.get('numero', resultado.get('roll', 0))
                    if numero == 0:
                        cor = 'branco'
                    elif numero <= 7:
                        cor = 'vermelho'
                    else:
                        cor = 'preto'
                    
                    await self.db.salvar_resultado_plataforma(
                        plataforma_id=plataforma_id,
                        resultado=str(numero),
                        numero=numero,
                        cor=cor,
                        timestamp_plataforma=timestamp,
                        dados_completos=resultado
                    )
                    
                    self.dados_migrados['resultados'] += 1
                
                except Exception as e:
                    erro = f"Erro ao migrar resultado de {plataforma_id}: {e}"
                    self.dados_migrados['erros'].append(erro)
            
            print(f"     ✅ {plataforma_id} migrada")
    
    async def verificar_migracao(self):
        """Verifica dados migrados"""
        print("\n🔍 VERIFICANDO MIGRAÇÃO...")
        
        # Contar usuários
        usuarios = await self.db.client.select('usuarios', use_service_key=True)
        print(f"   👤 Usuários: {len(usuarios)}")
        
        # Contar robôs
        robos = await self.db.client.select('robos', use_service_key=True)
        print(f"   🤖 Robôs: {len(robos)}")
        
        # Contar estratégias
        estrategias = await self.db.client.select('estrategias', use_service_key=True)
        print(f"   🎯 Estratégias: {len(estrategias)}")
        
        # Contar resultados
        resultados = await self.db.client.select('resultados_plataformas', use_service_key=True)
        print(f"   📊 Resultados: {len(resultados)}")
        
        # Contar plataformas
        plataformas = await self.db.client.select('plataformas', use_service_key=True)
        print(f"   🏢 Plataformas: {len(plataformas)}")
    
    async def executar_migracao_completa(self):
        """Executa migração completa"""
        print("🚀 INICIANDO MIGRAÇÃO PARA SUPABASE")
        print("=" * 40)
        
        try:
            # Carregar dados locais
            print("📁 Carregando dados locais...")
            dados = self.carregar_dados_locais()
            
            # Criar usuário padrão
            usuario_id = await self.criar_usuario_padrao()
            if not usuario_id:
                print("❌ Não foi possível criar usuário padrão")
                return
            
            # Migrar robôs e estratégias
            await self.migrar_robos(dados, usuario_id)
            
            # Migrar resultados das plataformas
            await self.migrar_resultados_plataformas(dados)
            
            # Verificar migração
            await self.verificar_migracao()
            
            # Relatório final
            print("\n📋 RELATÓRIO DE MIGRAÇÃO")
            print("=" * 25)
            print(f"✅ Usuários migrados: {self.dados_migrados['usuarios']}")
            print(f"✅ Robôs migrados: {self.dados_migrados['robos']}")
            print(f"✅ Estratégias migradas: {self.dados_migrados['estrategias']}")
            print(f"✅ Resultados migrados: {self.dados_migrados['resultados']}")
            
            if self.dados_migrados['erros']:
                print(f"\n⚠️ Erros encontrados: {len(self.dados_migrados['erros'])}")
                for erro in self.dados_migrados['erros'][:5]:  # Mostrar apenas os primeiros 5
                    print(f"   • {erro}")
                if len(self.dados_migrados['erros']) > 5:
                    print(f"   • ... e mais {len(self.dados_migrados['erros']) - 5} erros")
            else:
                print("\n🎉 MIGRAÇÃO CONCLUÍDA SEM ERROS!")
        
        except Exception as e:
            print(f"❌ Erro crítico na migração: {e}")
    
    async def gerar_dados_teste(self):
        """Gera dados de teste no Supabase"""
        print("🧪 GERANDO DADOS DE TESTE...")
        
        # Criar usuário de teste
        user_id = await self.db.criar_usuario(
            email='teste@sistema.local',
            nome='Usuário Teste',
            senha_hash=self.gerar_senha_hash('teste123'),
            plano='premium'
        )
        
        if user_id:
            print(f"   ✅ Usuário teste criado: {user_id}")
            
            # Criar robô de teste
            robo_id = await self.db.criar_robo(
                usuario_id=user_id,
                plataforma_id='blaze',
                nome='Robô Teste Blaze',
                telegram_bot_token='123456789:TEST_TOKEN',
                telegram_chat_id='-100123456789'
            )
            
            if robo_id:
                print(f"   ✅ Robô teste criado: {robo_id}")
                
                # Criar estratégias de teste
                estrategias_teste = [
                    {'nome': 'Dois Vermelhos', 'pattern': 'V-V', 'bet': 'P'},
                    {'nome': 'Dois Pretos', 'pattern': 'P-P', 'bet': 'V'},
                    {'nome': 'Alternado', 'pattern': 'V-P', 'bet': 'V'}
                ]
                
                for est in estrategias_teste:
                    est_id = await self.db.criar_estrategia(
                        robo_id=robo_id,
                        nome=est['nome'],
                        pattern=est['pattern'],
                        bet=est['bet'],
                        confianca=75
                    )
                    if est_id:
                        print(f"     ✅ Estratégia: {est['nome']}")
                
                # Gerar alguns sinais de teste
                await self.db.registrar_sinal(
                    robo_id=robo_id,
                    estrategia_id=est_id,  # Usar última estratégia criada
                    plataforma_id='blaze',
                    sinal='V',
                    confianca=80
                )
                print("     ✅ Sinal de teste criado")
        
        print("🎉 Dados de teste gerados!")

async def main():
    """Função principal"""
    print("🔧 MIGRADOR SUPABASE")
    print("=" * 20)
    
    # Carregar configurações
    carregar_configuracao_env()
    
    # Verificar se .env existe
    if not Path('.env').exists():
        print("❌ Arquivo .env não encontrado!")
        print("📝 Copie o arquivo .env.exemplo para .env e configure suas chaves do Supabase")
        return
    
    migrador = MigradorSupabase()
    
    try:
        await migrador.init()
        
        print("\n1️⃣ Migração completa (dados locais → Supabase)")
        print("2️⃣ Gerar dados de teste")
        print("3️⃣ Verificar migração")
        
        opcao = input("\nEscolha uma opção (1-3): ").strip()
        
        if opcao == '1':
            await migrador.executar_migracao_completa()
        elif opcao == '2':
            await migrador.gerar_dados_teste()
        elif opcao == '3':
            await migrador.verificar_migracao()
        else:
            print("❌ Opção inválida")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        await migrador.close()

if __name__ == "__main__":
    asyncio.run(main()) 