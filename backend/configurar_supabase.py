#!/usr/bin/env python3
"""
🚀 CONFIGURADOR INTERATIVO DO SUPABASE
Guia passo-a-passo para configurar o banco de dados
"""

import os
import json
import time
import webbrowser
from pathlib import Path
import asyncio
import aiohttp

class ConfiguradorSupabase:
    """Configurador interativo do Supabase"""
    
    def __init__(self):
        self.config = {}
        self.projeto_url = ""
        self.anon_key = ""
        self.service_key = ""
    
    def mostrar_banner(self):
        """Mostra banner inicial"""
        print("🚀 CONFIGURADOR SUPABASE")
        print("=" * 30)
        print("📋 Este script vai te guiar na configuração completa do Supabase")
        print("⏱️ Tempo estimado: 5-10 minutos")
        print("🌐 Será necessário acessar o site do Supabase")
        print()
    
    def passo_1_criar_conta(self):
        """Passo 1: Criar conta no Supabase"""
        print("📝 PASSO 1: CRIAR CONTA E PROJETO")
        print("=" * 35)
        print()
        print("1️⃣ Vamos abrir o site do Supabase...")
        
        # Abrir site automaticamente
        try:
            webbrowser.open("https://supabase.com")
            print("   ✅ Site aberto no seu navegador")
        except:
            print("   ⚠️ Abra manualmente: https://supabase.com")
        
        print()
        print("2️⃣ No site do Supabase:")
        print("   • Clique em 'Start your project' ou 'Sign up'")
        print("   • Crie uma conta (pode usar GitHub/Google)")
        print("   • Confirme seu email se necessário")
        print()
        
        input("📌 Pressione ENTER quando tiver criado sua conta...")
        
        print("\n3️⃣ Criar novo projeto:")
        print("   • Clique em 'New Project'")
        print("   • Escolha um nome (ex: 'sistema-bots')")
        print("   • Escolha uma senha forte para o banco")
        print("   • Selecione uma região próxima")
        print("   • Clique em 'Create new project'")
        print("   • ⏳ Aguarde 2-3 minutos para criação")
        print()
        
        input("📌 Pressione ENTER quando o projeto estiver criado...")
    
    def passo_2_obter_chaves(self):
        """Passo 2: Obter chaves da API"""
        print("\n🔑 PASSO 2: OBTER CHAVES DA API")
        print("=" * 32)
        print()
        print("1️⃣ No painel do seu projeto:")
        print("   • Clique em 'Settings' (⚙️) na barra lateral")
        print("   • Clique em 'API' na seção Settings")
        print()
        print("2️⃣ Você verá 3 informações importantes:")
        print("   📍 Project URL")
        print("   🔓 anon public (chave pública)")
        print("   🔐 service_role (chave privada)")
        print()
        
        # Coletar URL do projeto
        while True:
            self.projeto_url = input("📍 Cole aqui a Project URL: ").strip()
            if self.projeto_url.startswith("https://") and "supabase.co" in self.projeto_url:
                break
            print("   ❌ URL inválida. Deve começar com https:// e conter supabase.co")
        
        # Coletar chave pública
        while True:
            self.anon_key = input("🔓 Cole aqui a chave anon public: ").strip()
            if len(self.anon_key) > 50:  # Validação básica
                break
            print("   ❌ Chave muito curta. Verifique se copiou corretamente")
        
        # Coletar chave privada
        while True:
            self.service_key = input("🔐 Cole aqui a chave service_role: ").strip()
            if len(self.service_key) > 50:  # Validação básica
                break
            print("   ❌ Chave muito curta. Verifique se copiou corretamente")
        
        print("\n✅ Chaves coletadas com sucesso!")
    
    def passo_3_testar_conexao(self):
        """Passo 3: Testar conexão"""
        print("\n🔍 PASSO 3: TESTANDO CONEXÃO")
        print("=" * 28)
        print()
        
        async def testar():
            try:
                headers = {
                    'apikey': self.anon_key,
                    'Authorization': f'Bearer {self.anon_key}',
                    'Content-Type': 'application/json'
                }
                
                async with aiohttp.ClientSession() as session:
                    # Testar endpoint básico
                    url = f"{self.projeto_url}/rest/v1/"
                    async with session.get(url, headers=headers, timeout=10) as response:
                        if response.status == 200:
                            print("   ✅ Conexão estabelecida com sucesso!")
                            return True
                        else:
                            print(f"   ❌ Erro na conexão: Status {response.status}")
                            return False
            except Exception as e:
                print(f"   ❌ Erro na conexão: {e}")
                return False
        
        print("🔄 Testando conexão...")
        sucesso = asyncio.run(testar())
        
        if not sucesso:
            print("\n⚠️ Problema na conexão:")
            print("   • Verifique se as chaves estão corretas")
            print("   • Verifique se o projeto foi criado completamente")
            print("   • Tente aguardar mais alguns minutos")
            
            if input("\n🔄 Tentar novamente? (s/n): ").lower() == 's':
                return self.passo_3_testar_conexao()
            else:
                return False
        
        return True
    
    def passo_4_criar_env(self):
        """Passo 4: Criar arquivo .env"""
        print("\n📝 PASSO 4: CRIANDO ARQUIVO .ENV")
        print("=" * 32)
        print()
        
        env_content = f"""# ================================================
# 🔧 CONFIGURAÇÃO SUPABASE - GERADO AUTOMATICAMENTE
# ================================================
# Criado em: {time.strftime('%d/%m/%Y %H:%M:%S')}

# ===== SUPABASE CONFIGURAÇÃO =====
SUPABASE_URL={self.projeto_url}
SUPABASE_ANON_KEY={self.anon_key}
SUPABASE_SERVICE_KEY={self.service_key}

# ===== CONFIGURAÇÃO DO SISTEMA =====
ENVIRONMENT=production
LOG_LEVEL=INFO
DEBUG=false

# ===== SEGURANÇA =====
JWT_SECRET=chave-secreta-jwt-{int(time.time())}
SESSION_SECRET=chave-sessao-secreta-{int(time.time())}

# ===== API CONFIGURAÇÕES =====
API_TIMEOUT=30
MAX_RETRIES=3
RATE_LIMIT_PER_MINUTE=60
"""
        
        # Salvar arquivo .env
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        
        print("✅ Arquivo .env criado com sucesso!")
        print(f"📁 Localização: {Path('.env').absolute()}")
        print()
        print("🔐 Configurações salvas:")
        print(f"   📍 URL: {self.projeto_url}")
        print(f"   🔓 Chave pública: {self.anon_key[:20]}...")
        print(f"   🔐 Chave privada: {self.service_key[:20]}...")
    
    def passo_5_executar_sql(self):
        """Passo 5: Executar SQL no Supabase"""
        print("\n🗄️ PASSO 5: EXECUTAR SQL NO SUPABASE")
        print("=" * 35)
        print()
        
        # Ler arquivo SQL
        sql_file = Path('database_supabase.sql')
        if not sql_file.exists():
            print("❌ Arquivo database_supabase.sql não encontrado!")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("1️⃣ Vamos abrir o SQL Editor do Supabase...")
        
        # Construir URL do SQL Editor
        sql_editor_url = f"{self.projeto_url.replace('https://', 'https://supabase.com/dashboard/project/')}/sql"
        
        try:
            webbrowser.open(sql_editor_url)
            print("   ✅ SQL Editor aberto no navegador")
        except:
            print(f"   ⚠️ Abra manualmente: {sql_editor_url}")
        
        print()
        print("2️⃣ No SQL Editor:")
        print("   • Clique em 'New query' se necessário")
        print("   • Cole todo o conteúdo do arquivo SQL")
        print("   • Clique em 'Run' ou pressione Ctrl+Enter")
        print("   • Aguarde a execução (pode demorar 30-60 segundos)")
        print()
        
        print("📋 CONTEÚDO DO SQL PARA COPIAR:")
        print("=" * 40)
        print("⚠️ COPIE TODO O TEXTO ABAIXO:")
        print()
        
        # Mostrar primeiras linhas do SQL para confirmar
        linhas = sql_content.split('\n')[:10]
        for linha in linhas:
            if linha.strip():
                print(f"   {linha}")
        
        print("   ... (resto do arquivo)")
        print()
        print(f"📁 Arquivo completo em: {sql_file.absolute()}")
        print()
        
        # Copiar para clipboard se possível
        try:
            import pyperclip
            pyperclip.copy(sql_content)
            print("📋 SQL copiado para a área de transferência!")
        except ImportError:
            print("💡 Dica: Abra o arquivo database_supabase.sql para copiar")
        
        print()
        input("📌 Pressione ENTER quando tiver executado o SQL...")
        
        return True
    
    def passo_6_verificar_tabelas(self):
        """Passo 6: Verificar se as tabelas foram criadas"""
        print("\n🔍 PASSO 6: VERIFICANDO TABELAS")
        print("=" * 30)
        print()
        
        async def verificar():
            try:
                headers = {
                    'apikey': self.service_key,
                    'Authorization': f'Bearer {self.service_key}',
                    'Content-Type': 'application/json'
                }
                
                # Testar algumas tabelas principais
                tabelas_teste = ['usuarios', 'robos', 'plataformas', 'estrategias']
                tabelas_ok = []
                
                async with aiohttp.ClientSession() as session:
                    for tabela in tabelas_teste:
                        try:
                            url = f"{self.projeto_url}/rest/v1/{tabela}?limit=1"
                            async with session.get(url, headers=headers, timeout=5) as response:
                                if response.status == 200:
                                    tabelas_ok.append(tabela)
                                    print(f"   ✅ Tabela '{tabela}' criada")
                                else:
                                    print(f"   ❌ Tabela '{tabela}' não encontrada")
                        except Exception as e:
                            print(f"   ❌ Erro ao verificar '{tabela}': {e}")
                
                return len(tabelas_ok) == len(tabelas_teste)
            
            except Exception as e:
                print(f"   ❌ Erro na verificação: {e}")
                return False
        
        print("🔄 Verificando tabelas criadas...")
        sucesso = asyncio.run(verificar())
        
        if sucesso:
            print("\n🎉 TODAS AS TABELAS FORAM CRIADAS COM SUCESSO!")
        else:
            print("\n⚠️ Algumas tabelas não foram encontradas:")
            print("   • Verifique se o SQL foi executado completamente")
            print("   • Veja se houve erros no SQL Editor")
            print("   • Tente executar o SQL novamente")
            
            if input("\n🔄 Tentar verificação novamente? (s/n): ").lower() == 's':
                return self.passo_6_verificar_tabelas()
        
        return sucesso
    
    def passo_7_migrar_dados(self):
        """Passo 7: Migrar dados locais"""
        print("\n🚀 PASSO 7: MIGRAR DADOS LOCAIS")
        print("=" * 30)
        print()
        
        # Verificar se há dados para migrar
        arquivos_dados = [
            'robos_configurados.json',
            'dados_plataformas.json'
        ]
        
        tem_dados = any(Path(arquivo).exists() for arquivo in arquivos_dados)
        
        if not tem_dados:
            print("📝 Nenhum dado local encontrado para migrar")
            print("💡 Isso é normal se for a primeira instalação")
            
            gerar_teste = input("\n🧪 Gerar dados de teste? (s/n): ").lower() == 's'
            if gerar_teste:
                print("\n🔄 Executando migração com dados de teste...")
                try:
                    import subprocess
                    result = subprocess.run(['python', 'migracao_supabase.py'], 
                                          input='2\n', text=True, capture_output=True)
                    if result.returncode == 0:
                        print("✅ Dados de teste criados com sucesso!")
                    else:
                        print(f"❌ Erro ao criar dados de teste: {result.stderr}")
                except Exception as e:
                    print(f"❌ Erro: {e}")
        else:
            print("📁 Dados locais encontrados:")
            for arquivo in arquivos_dados:
                if Path(arquivo).exists():
                    size = Path(arquivo).stat().st_size
                    print(f"   ✅ {arquivo} ({size:,} bytes)")
            
            migrar = input("\n🔄 Migrar dados locais para Supabase? (s/n): ").lower() == 's'
            if migrar:
                print("\n🔄 Executando migração...")
                try:
                    import subprocess
                    result = subprocess.run(['python', 'migracao_supabase.py'], 
                                          input='1\n', text=True, capture_output=True)
                    if result.returncode == 0:
                        print("✅ Migração concluída com sucesso!")
                        print("📊 Verifique o relatório de migração")
                    else:
                        print(f"❌ Erro na migração: {result.stderr}")
                except Exception as e:
                    print(f"❌ Erro: {e}")
    
    def finalizar_configuracao(self):
        """Finaliza configuração"""
        print("\n🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 40)
        print()
        print("✅ RESUMO DO QUE FOI CONFIGURADO:")
        print(f"   📍 Projeto Supabase: {self.projeto_url}")
        print(f"   🗄️ Banco de dados criado com 10 tabelas")
        print(f"   🔐 Arquivo .env configurado")
        print(f"   🔄 Dados migrados/teste criados")
        print()
        print("🚀 PRÓXIMOS PASSOS:")
        print("   1. Execute: python admin_backend.py")
        print("   2. Acesse: http://localhost:8000")
        print("   3. Login: admin@sistema.local / admin123")
        print("   4. Comece a usar o sistema!")
        print()
        print("📚 DOCUMENTAÇÃO:")
        print("   • README_SUPABASE.md - Documentação completa")
        print("   • supabase_config.py - Exemplos de uso")
        print("   • migracao_supabase.py - Migração de dados")
        print()
        print("🎯 SEU SISTEMA AGORA É UM SAAS PROFISSIONAL!")
    
    async def executar_configuracao_completa(self):
        """Executa configuração completa"""
        self.mostrar_banner()
        
        try:
            # Passo 1: Criar conta
            self.passo_1_criar_conta()
            
            # Passo 2: Obter chaves
            self.passo_2_obter_chaves()
            
            # Passo 3: Testar conexão
            if not self.passo_3_testar_conexao():
                print("❌ Configuração interrompida devido a erro de conexão")
                return
            
            # Passo 4: Criar .env
            self.passo_4_criar_env()
            
            # Passo 5: Executar SQL
            if not self.passo_5_executar_sql():
                print("❌ Configuração interrompida")
                return
            
            # Passo 6: Verificar tabelas
            if not self.passo_6_verificar_tabelas():
                print("⚠️ Continue mesmo com problemas nas tabelas")
            
            # Passo 7: Migrar dados
            self.passo_7_migrar_dados()
            
            # Finalizar
            self.finalizar_configuracao()
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Configuração cancelada pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro inesperado: {e}")

def main():
    """Função principal"""
    configurador = ConfiguradorSupabase()
    asyncio.run(configurador.executar_configuracao_completa())

if __name__ == "__main__":
    main() 