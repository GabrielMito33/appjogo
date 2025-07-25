#!/usr/bin/env python3
"""
🔗 CONFIGURAÇÃO SUPABASE - INTEGRAÇÃO PYTHON
Sistema de conexão e operações com banco Supabase
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import asyncio
import aiohttp
from pathlib import Path

class SupabaseConfig:
    """Configuração central do Supabase"""
    
    def __init__(self):
        # URLs e chaves do Supabase (configurar no .env)
        self.url = os.getenv('SUPABASE_URL', 'https://seu-projeto.supabase.co')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY', 'sua-chave-anonima')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY', 'sua-chave-service')
        
        # Headers padrão
        self.headers = {
            'apikey': self.anon_key,
            'Authorization': f'Bearer {self.anon_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        # Headers para service role (operações admin)
        self.service_headers = {
            'apikey': self.service_key,
            'Authorization': f'Bearer {self.service_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def get_rest_url(self, table: str) -> str:
        """Gera URL da REST API para uma tabela"""
        return f"{self.url}/rest/v1/{table}"
    
    def get_auth_url(self) -> str:
        """Gera URL da API de autenticação"""
        return f"{self.url}/auth/v1"

class SupabaseClient:
    """Cliente para operações com Supabase"""
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.session = None
        self.user_token = None
    
    async def init_session(self):
        """Inicializa sessão HTTP"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Fecha sessão HTTP"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def set_user_token(self, token: str):
        """Define token do usuário autenticado"""
        self.user_token = token
    
    def get_headers(self, use_service_key: bool = False, user_token: str = None) -> Dict[str, str]:
        """Retorna headers apropriados"""
        if use_service_key:
            return self.config.service_headers.copy()
        
        headers = self.config.headers.copy()
        if user_token or self.user_token:
            token = user_token or self.user_token
            headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    async def auth_login(self, email: str, password: str) -> Optional[Dict]:
        """Faz login no sistema"""
        await self.init_session()
        
        url = f"{self.config.get_auth_url()}/token?grant_type=password"
        data = {
            'email': email,
            'password': password
        }
        
        try:
            async with self.session.post(url, json=data, headers=self.get_headers()) as response:
                if response.status == 200:
                    result = await response.json()
                    self.set_user_token(result.get('access_token'))
                    return result
                return None
        except Exception as e:
            print(f"Erro no login: {e}")
            return None
    
    async def select(self, table: str, select: str = "*", filters: Dict = None, 
                    use_service_key: bool = False) -> List[Dict]:
        """Seleciona dados de uma tabela"""
        await self.init_session()
        
        url = self.config.get_rest_url(table)
        params = {'select': select}
        
        # Adicionar filtros
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    params[key] = f'eq.{value}'
                else:
                    params[key] = f'eq.{value}'
        
        try:
            async with self.session.get(
                url, 
                params=params, 
                headers=self.get_headers(use_service_key)
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as e:
            print(f"Erro no select: {e}")
            return []
    
    async def insert(self, table: str, data: Dict, use_service_key: bool = False) -> Optional[Dict]:
        """Insere dados em uma tabela"""
        await self.init_session()
        
        url = self.config.get_rest_url(table)
        
        try:
            async with self.session.post(
                url, 
                json=data, 
                headers=self.get_headers(use_service_key)
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    return result[0] if result else None
                return None
        except Exception as e:
            print(f"Erro no insert: {e}")
            return None
    
    async def update(self, table: str, data: Dict, filters: Dict, 
                    use_service_key: bool = False) -> Optional[List[Dict]]:
        """Atualiza dados em uma tabela"""
        await self.init_session()
        
        url = self.config.get_rest_url(table)
        params = {}
        
        # Adicionar filtros
        if filters:
            for key, value in filters.items():
                params[key] = f'eq.{value}'
        
        try:
            async with self.session.patch(
                url, 
                json=data, 
                params=params,
                headers=self.get_headers(use_service_key)
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Erro no update: {e}")
            return None
    
    async def delete(self, table: str, filters: Dict, use_service_key: bool = False) -> bool:
        """Deleta dados de uma tabela"""
        await self.init_session()
        
        url = self.config.get_rest_url(table)
        params = {}
        
        # Adicionar filtros
        if filters:
            for key, value in filters.items():
                params[key] = f'eq.{value}'
        
        try:
            async with self.session.delete(
                url, 
                params=params,
                headers=self.get_headers(use_service_key)
            ) as response:
                return response.status == 204
        except Exception as e:
            print(f"Erro no delete: {e}")
            return False

class DatabaseManager:
    """Gerenciador de operações do banco de dados"""
    
    def __init__(self):
        self.config = SupabaseConfig()
        self.client = SupabaseClient(self.config)
    
    async def init(self):
        """Inicializa conexão"""
        await self.client.init_session()
    
    async def close(self):
        """Fecha conexão"""
        await self.client.close_session()
    
    # ===== OPERAÇÕES DE USUÁRIOS =====
    
    async def criar_usuario(self, email: str, nome: str, senha_hash: str, 
                          plano: str = 'free') -> Optional[str]:
        """Cria um novo usuário"""
        data = {
            'email': email,
            'nome': nome,
            'senha_hash': senha_hash,
            'plano': plano,
            'max_robos': 1 if plano == 'free' else (5 if plano == 'premium' else 20),
            'max_sinais_dia': 50 if plano == 'free' else (200 if plano == 'premium' else 1000)
        }
        
        result = await self.client.insert('usuarios', data, use_service_key=True)
        return result['id'] if result else None
    
    async def buscar_usuario_por_email(self, email: str) -> Optional[Dict]:
        """Busca usuário por email"""
        users = await self.client.select(
            'usuarios', 
            filters={'email': email},
            use_service_key=True
        )
        return users[0] if users else None
    
    async def atualizar_ultimo_login(self, user_id: str):
        """Atualiza último login do usuário"""
        await self.client.update(
            'usuarios',
            {'ultimo_login': datetime.now().isoformat()},
            {'id': user_id},
            use_service_key=True
        )
    
    # ===== OPERAÇÕES DE ROBÔS =====
    
    async def criar_robo(self, usuario_id: str, plataforma_id: str, nome: str,
                        telegram_bot_token: str, telegram_chat_id: str) -> Optional[str]:
        """Cria um novo robô"""
        data = {
            'usuario_id': usuario_id,
            'plataforma_id': plataforma_id,
            'nome': nome,
            'telegram_bot_token': telegram_bot_token,
            'telegram_chat_id': telegram_chat_id,
            'status': 'inativo'
        }
        
        result = await self.client.insert('robos', data)
        return result['id'] if result else None
    
    async def listar_robos_usuario(self, usuario_id: str) -> List[Dict]:
        """Lista robôs de um usuário"""
        return await self.client.select(
            'robos',
            select='*, plataformas(nome, jogo)',
            filters={'usuario_id': usuario_id}
        )
    
    async def buscar_robo(self, robo_id: str) -> Optional[Dict]:
        """Busca um robô específico"""
        robos = await self.client.select(
            'robos',
            select='*, usuarios(nome), plataformas(nome, jogo)',
            filters={'id': robo_id}
        )
        return robos[0] if robos else None
    
    async def atualizar_status_robo(self, robo_id: str, status: str):
        """Atualiza status do robô"""
        await self.client.update(
            'robos',
            {'status': status},
            {'id': robo_id}
        )
    
    async def atualizar_estatisticas_robo(self, robo_id: str, estatisticas: Dict):
        """Atualiza estatísticas do robô"""
        await self.client.update(
            'robos',
            {'estatisticas': estatisticas},
            {'id': robo_id}
        )
    
    # ===== OPERAÇÕES DE ESTRATÉGIAS =====
    
    async def criar_estrategia(self, robo_id: str, nome: str, pattern: str, 
                             bet: str, confianca: int = 50) -> Optional[str]:
        """Cria uma nova estratégia"""
        data = {
            'robo_id': robo_id,
            'nome': nome,
            'pattern': pattern,
            'bet': bet,
            'confianca': confianca
        }
        
        result = await self.client.insert('estrategias', data)
        return result['id'] if result else None
    
    async def listar_estrategias_robo(self, robo_id: str) -> List[Dict]:
        """Lista estratégias de um robô"""
        return await self.client.select(
            'estrategias',
            filters={'robo_id': robo_id, 'ativa': True}
        )
    
    # ===== OPERAÇÕES DE SINAIS =====
    
    async def registrar_sinal(self, robo_id: str, estrategia_id: str, 
                            plataforma_id: str, sinal: str, confianca: int) -> Optional[str]:
        """Registra um novo sinal"""
        data = {
            'robo_id': robo_id,
            'estrategia_id': estrategia_id,
            'plataforma_id': plataforma_id,
            'sinal': sinal,
            'confianca': confianca,
            'status': 'pendente'
        }
        
        result = await self.client.insert('sinais', data)
        return result['id'] if result else None
    
    async def atualizar_resultado_sinal(self, sinal_id: str, resultado: str, 
                                       gales_utilizados: int = 0):
        """Atualiza resultado de um sinal"""
        status = 'win' if resultado in ['win', 'green'] else 'loss'
        
        await self.client.update(
            'sinais',
            {
                'resultado': resultado,
                'status': status,
                'gales_utilizados': gales_utilizados,
                'timestamp_resultado': datetime.now().isoformat()
            },
            {'id': sinal_id}
        )
    
    async def listar_sinais_robo_hoje(self, robo_id: str) -> List[Dict]:
        """Lista sinais do robô do dia atual"""
        hoje = datetime.now().date().isoformat()
        return await self.client.select(
            'sinais',
            filters={'robo_id': robo_id}
        )
    
    # ===== OPERAÇÕES DE RESULTADOS DAS PLATAFORMAS =====
    
    async def salvar_resultado_plataforma(self, plataforma_id: str, resultado: str,
                                        numero: int, cor: str, timestamp_plataforma: datetime,
                                        dados_completos: Dict = None) -> Optional[str]:
        """Salva resultado de uma plataforma"""
        data = {
            'plataforma_id': plataforma_id,
            'resultado': resultado,
            'numero': numero,
            'cor': cor,
            'timestamp_plataforma': timestamp_plataforma.isoformat(),
            'dados_completos': dados_completos or {}
        }
        
        result = await self.client.insert('resultados_plataformas', data)
        return result['id'] if result else None
    
    async def buscar_resultados_recentes(self, plataforma_id: str, limite: int = 50) -> List[Dict]:
        """Busca resultados recentes de uma plataforma"""
        return await self.client.select(
            'resultados_plataformas',
            filters={'plataforma_id': plataforma_id}
        )
    
    # ===== OPERAÇÕES DE LOGS =====
    
    async def registrar_log(self, nivel: str, categoria: str, mensagem: str,
                          usuario_id: str = None, robo_id: str = None, 
                          detalhes: Dict = None):
        """Registra um log do sistema"""
        data = {
            'nivel': nivel,
            'categoria': categoria,
            'mensagem': mensagem,
            'detalhes': detalhes or {}
        }
        
        if usuario_id:
            data['usuario_id'] = usuario_id
        if robo_id:
            data['robo_id'] = robo_id
        
        await self.client.insert('logs_sistema', data, use_service_key=True)
    
    # ===== OPERAÇÕES DE PLATAFORMAS =====
    
    async def listar_plataformas(self) -> List[Dict]:
        """Lista todas as plataformas disponíveis"""
        return await self.client.select('plataformas')
    
    async def buscar_plataforma(self, plataforma_id: str) -> Optional[Dict]:
        """Busca uma plataforma específica"""
        plataformas = await self.client.select(
            'plataformas',
            filters={'id': plataforma_id}
        )
        return plataformas[0] if plataformas else None

# ===== FUNÇÕES UTILITÁRIAS =====

def carregar_configuracao_env():
    """Carrega configuração do arquivo .env"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def criar_arquivo_env_exemplo():
    """Cria arquivo .env de exemplo"""
    env_exemplo = """# Configuração Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-chave-anonima-aqui
SUPABASE_SERVICE_KEY=sua-chave-service-aqui

# Configuração do Sistema
ENVIRONMENT=development
LOG_LEVEL=INFO
"""
    
    with open('.env.exemplo', 'w') as f:
        f.write(env_exemplo)
    
    print("📝 Arquivo .env.exemplo criado!")
    print("📋 Configure suas chaves do Supabase e renomeie para .env")

# ===== EXEMPLO DE USO =====

async def exemplo_uso():
    """Exemplo de como usar o DatabaseManager"""
    
    # Carregar configurações
    carregar_configuracao_env()
    
    # Inicializar manager
    db = DatabaseManager()
    await db.init()
    
    try:
        # Listar plataformas
        plataformas = await db.listar_plataformas()
        print(f"📊 Plataformas disponíveis: {len(plataformas)}")
        
        # Buscar usuário
        usuario = await db.buscar_usuario_por_email('admin@sistema.com')
        if usuario:
            print(f"👤 Usuário encontrado: {usuario['nome']}")
            
            # Listar robôs do usuário
            robos = await db.listar_robos_usuario(usuario['id'])
            print(f"🤖 Robôs do usuário: {len(robos)}")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    finally:
        await db.close()

if __name__ == "__main__":
    # Criar arquivo de exemplo se não existir .env
    if not Path('.env').exists():
        criar_arquivo_env_exemplo()
    
    # Executar exemplo
    asyncio.run(exemplo_uso()) 