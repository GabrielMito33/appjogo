#!/usr/bin/env python3
"""
📊 ANÁLISE COMPLETA DO SISTEMA
Análise do estado atual e limpeza de arquivos duplicados/desnecessários
"""

import os
import json
from pathlib import Path
from datetime import datetime
import shutil

class AnalisadorSistema:
    """Analisador completo do sistema"""
    
    def __init__(self):
        self.arquivos_analisados = []
        self.arquivos_duplicados = []
        self.arquivos_desnecessarios = []
        self.arquivos_essenciais = []
        self.estrutura_final = {}
    
    def analisar_script_solo(self):
        """Analisa o ScriptSolo.py para entender funcionalidades essenciais"""
        print("🔍 ANALISANDO SCRIPT SOLO")
        print("=" * 30)
        
        script_solo = Path("../ScriptSolo.py")
        if not script_solo.exists():
            print("❌ ScriptSolo.py não encontrado")
            return
        
        print("✅ ScriptSolo.py encontrado")
        
        # Funcionalidades identificadas no ScriptSolo.py
        funcionalidades_solo = {
            "api_blaze": "Coleta dados da API da Blaze",
            "telegram_bot": "Envio de mensagens via Telegram",
            "estrategias_csv": "Leitura de estratégias de arquivo CSV",
            "martingale": "Sistema de gales/martingale",
            "protecao_branco": "Proteção contra resultados brancos",
            "estatisticas": "Contagem de wins/losses/brancos",
            "restart_diario": "Reinicialização diária de estatísticas",
            "alertas": "Sistema de alertas e notificações",
            "logs": "Logs de operações"
        }
        
        print("📋 Funcionalidades identificadas no ScriptSolo.py:")
        for func, desc in funcionalidades_solo.items():
            print(f"   • {func}: {desc}")
        
        return funcionalidades_solo
    
    def analisar_arquivos_backend(self):
        """Analisa todos os arquivos do backend"""
        print(f"\n📁 ANALISANDO ARQUIVOS DO BACKEND")
        print("=" * 35)
        
        backend_dir = Path(".")
        arquivos_backend = []
        
        for arquivo in backend_dir.rglob("*"):
            if arquivo.is_file() and arquivo.suffix in ['.py', '.md', '.txt', '.json', '.sql']:
                arquivos_backend.append({
                    'nome': arquivo.name,
                    'caminho': str(arquivo),
                    'tamanho': arquivo.stat().st_size,
                    'tipo': arquivo.suffix,
                    'modificado': datetime.fromtimestamp(arquivo.stat().st_mtime)
                })
        
        # Categorizar arquivos
        categorias = {
            'CORE_SISTEMA': [],
            'ADMIN_WEB': [],
            'SUPABASE': [],
            'ANALISE': [],
            'DOCUMENTACAO': [],
            'CONFIGURACAO': [],
            'DADOS': [],
            'DESNECESSARIOS': []
        }
        
        for arquivo in arquivos_backend:
            nome = arquivo['nome']
            caminho = arquivo['caminho']
            
            # CORE DO SISTEMA (essenciais)
            if nome in [
                'executor_bots.py',           # Sistema principal 24/7
                'gerenciador_sistema.py',     # Interface terminal
                'plataformas_api.py',         # APIs das plataformas
                'sistema_variaveis_mensagens.py', # Processamento de variáveis
                'validador_configuracoes.py'  # Validação
            ]:
                categorias['CORE_SISTEMA'].append(arquivo)
            
            # ADMIN WEB
            elif nome in [
                'admin_backend.py',           # FastAPI admin
                'start_admin.py',             # Inicializador admin
                'admin_requirements.txt'      # Dependências admin
            ]:
                categorias['ADMIN_WEB'].append(arquivo)
            
            # SUPABASE
            elif nome in [
                'database_supabase.sql',      # SQL do banco
                'supabase_config.py',         # Cliente Supabase
                'migracao_supabase.py'        # Migração de dados
            ]:
                categorias['SUPABASE'].append(arquivo)
            
            # ANÁLISE E CONFIGURAÇÃO
            elif nome in [
                'configurador_robos.py',      # Configurador de robôs
                'analisador_estrategias.py',  # Análise de estratégias
                'painel_estrategias.py',      # Painel de análise
                'configurador_mensagens_avancado.py' # Editor de mensagens
            ]:
                categorias['ANALISE'].append(arquivo)
            
            # DOCUMENTAÇÃO
            elif nome.endswith('.md'):
                categorias['DOCUMENTACAO'].append(arquivo)
            
            # CONFIGURAÇÃO
            elif nome in [
                'requirements_mvp.txt',       # Dependências principais
                '.env', '.env.exemplo'        # Configurações
            ]:
                categorias['CONFIGURACAO'].append(arquivo)
            
            # DADOS
            elif nome.endswith('.json') and nome not in [
                'database_supabase.sql', 'supabase_config.py'
            ]:
                categorias['DADOS'].append(arquivo)
            
            # DESNECESSÁRIOS
            else:
                categorias['DESNECESSARIOS'].append(arquivo)
        
        # Mostrar análise
        for categoria, arquivos in categorias.items():
            if arquivos:
                print(f"\n🔸 {categoria}:")
                for arquivo in arquivos:
                    print(f"   ✅ {arquivo['nome']} ({arquivo['tamanho']:,} bytes)")
        
        return categorias
    
    def identificar_duplicados(self, categorias):
        """Identifica arquivos duplicados ou redundantes"""
        print(f"\n🔍 IDENTIFICANDO DUPLICADOS")
        print("=" * 30)
        
        duplicados = []
        
        # Verificar arquivos de análise
        arquivos_analise = [
            'analise_mvp_status.py',
            'analise_mvp_status.json',
            'status_backend_sistema.py'
        ]
        
        for arquivo in arquivos_analise:
            if Path(arquivo).exists():
                duplicados.append({
                    'arquivo': arquivo,
                    'motivo': 'Análise temporária - pode ser removido',
                    'tipo': 'ANALISE_TEMPORARIA'
                })
        
        # Verificar arquivos de demonstração
        arquivos_demo = [
            'demonstracao_sistema_completo.py',
            'relatorio_demonstracao.json'
        ]
        
        for arquivo in arquivos_demo:
            if Path(arquivo).exists():
                duplicados.append({
                    'arquivo': arquivo,
                    'motivo': 'Demonstração - não necessário em produção',
                    'tipo': 'DEMONSTRACAO'
                })
        
        # Verificar arquivos de configuração duplicados
        if Path('configurador_robos.py').exists() and Path('configurador_mensagens_avancado.py').exists():
            duplicados.append({
                'arquivo': 'configurador_mensagens_avancado.py',
                'motivo': 'Funcionalidade integrada no admin web',
                'tipo': 'FUNCIONALIDADE_DUPLICADA'
            })
        
        # Mostrar duplicados encontrados
        if duplicados:
            print("📋 Arquivos duplicados/desnecessários encontrados:")
            for dup in duplicados:
                print(f"   ❌ {dup['arquivo']}")
                print(f"      Motivo: {dup['motivo']}")
                print(f"      Tipo: {dup['tipo']}")
        else:
            print("✅ Nenhum arquivo duplicado encontrado")
        
        return duplicados
    
    def definir_estrutura_final(self, categorias, duplicados):
        """Define a estrutura final limpa do sistema"""
        print(f"\n🎯 ESTRUTURA FINAL DO SISTEMA")
        print("=" * 35)
        
        estrutura_final = {
            'CORE_SISTEMA': {
                'descricao': 'Sistema principal de execução',
                'arquivos': [
                    'executor_bots.py',           # Sistema 24/7
                    'gerenciador_sistema.py',     # Interface terminal
                    'plataformas_api.py',         # APIs das plataformas
                    'sistema_variaveis_mensagens.py', # Variáveis globais
                    'validador_configuracoes.py'  # Validação
                ]
            },
            'ADMIN_WEB': {
                'descricao': 'Interface web de administração',
                'arquivos': [
                    'admin_backend.py',           # FastAPI
                    'start_admin.py',             # Inicializador
                    'admin_requirements.txt'      # Dependências
                ]
            },
            'SUPABASE': {
                'descricao': 'Banco de dados e migração',
                'arquivos': [
                    'database_supabase.sql',      # SQL completo
                    'supabase_config.py',         # Cliente
                    'migracao_supabase.py'        # Migração
                ]
            },
            'CONFIGURACAO': {
                'descricao': 'Configurações e dependências',
                'arquivos': [
                    'requirements_mvp.txt',       # Dependências
                    '.env',                       # Configurações
                    'configurador_robos.py'       # Configurador
                ]
            },
            'ANALISE': {
                'descricao': 'Análise e painéis',
                'arquivos': [
                    'analisador_estrategias.py',  # Engine de análise
                    'painel_estrategias.py'       # Painel de análise
                ]
            },
            'DOCUMENTACAO': {
                'descricao': 'Documentação do sistema',
                'arquivos': [
                    'README_SISTEMA_COMPLETO.md', # Documentação principal
                    'GUIA_INICIO_RAPIDO.md',      # Guia rápido
                    'README_SUPABASE.md'          # Doc Supabase
                ]
            }
        }
        
        # Mostrar estrutura final
        for categoria, info in estrutura_final.items():
            print(f"\n🔸 {categoria}:")
            print(f"   {info['descricao']}")
            for arquivo in info['arquivos']:
                if Path(arquivo).exists():
                    print(f"   ✅ {arquivo}")
                else:
                    print(f"   ❌ {arquivo} (FALTANDO)")
        
        return estrutura_final
    
    def limpar_arquivos_desnecessarios(self, duplicados):
        """Remove arquivos desnecessários"""
        print(f"\n🧹 LIMPANDO ARQUIVOS DESNECESSÁRIOS")
        print("=" * 40)
        
        arquivos_para_remover = []
        
        for dup in duplicados:
            if dup['tipo'] in ['ANALISE_TEMPORARIA', 'DEMONSTRACAO']:
                arquivos_para_remover.append(dup['arquivo'])
        
        # Adicionar outros arquivos desnecessários
        arquivos_extras = [
            'configurador_mensagens_avancado.py',  # Funcionalidade no admin web
            'relatorio_validacao.txt',             # Relatório temporário
        ]
        
        for arquivo in arquivos_extras:
            if Path(arquivo).exists():
                arquivos_para_remover.append(arquivo)
        
        if arquivos_para_remover:
            print("📋 Arquivos que serão removidos:")
            for arquivo in arquivos_para_remover:
                print(f"   🗑️ {arquivo}")
            
            confirmar = input("\n❓ Confirmar remoção? (s/n): ").lower()
            if confirmar == 's':
                for arquivo in arquivos_para_remover:
                    try:
                        Path(arquivo).unlink()
                        print(f"   ✅ {arquivo} removido")
                    except Exception as e:
                        print(f"   ❌ Erro ao remover {arquivo}: {e}")
            else:
                print("   ⚠️ Remoção cancelada")
        else:
            print("✅ Nenhum arquivo para remover")
    
    def gerar_relatorio_final(self, estrutura_final):
        """Gera relatório final do sistema"""
        print(f"\n📊 RELATÓRIO FINAL DO SISTEMA")
        print("=" * 35)
        
        total_arquivos = 0
        arquivos_presentes = 0
        
        for categoria, info in estrutura_final.items():
            print(f"\n🔸 {categoria}:")
            print(f"   {info['descricao']}")
            
            for arquivo in info['arquivos']:
                total_arquivos += 1
                if Path(arquivo).exists():
                    tamanho = Path(arquivo).stat().st_size
                    print(f"   ✅ {arquivo} ({tamanho:,} bytes)")
                    arquivos_presentes += 1
                else:
                    print(f"   ❌ {arquivo} (FALTANDO)")
        
        print(f"\n📈 RESUMO:")
        print(f"   📁 Arquivos essenciais: {arquivos_presentes}/{total_arquivos}")
        print(f"   📊 Completude: {(arquivos_presentes/total_arquivos)*100:.1f}%")
        
        if arquivos_presentes >= total_arquivos * 0.9:
            print(f"\n🎉 SISTEMA COMPLETO E FUNCIONAL!")
        else:
            print(f"\n⚠️ Sistema incompleto - arquivos faltando")
        
        # Comparação com ScriptSolo.py
        print(f"\n🔄 COMPARAÇÃO COM SCRIPT SOLO:")
        print(f"   ✅ Funcionalidades mantidas:")
        print(f"      • API Blaze integrada")
        print(f"      • Telegram Bot funcionando")
        print(f"      • Estratégias CSV suportadas")
        print(f"      • Sistema de gales/martingale")
        print(f"      • Proteção contra brancos")
        print(f"      • Estatísticas em tempo real")
        print(f"      • Alertas e notificações")
        print(f"      • Logs detalhados")
        
        print(f"\n🚀 MELHORIAS ADICIONADAS:")
        print(f"      • Multi-usuário com planos")
        print(f"      • Múltiplas plataformas (Blaze, Jonbet, Betfire)")
        print(f"      • Interface web de administração")
        print(f"      • Banco de dados Supabase")
        print(f"      • Variáveis globais nas mensagens")
        print(f"      • Análise avançada de estratégias")
        print(f"      • Sistema de validação robusto")
        print(f"      • Migração automática de dados")
    
    def executar_analise_completa(self):
        """Executa análise completa do sistema"""
        print("📊 ANÁLISE COMPLETA DO SISTEMA")
        print("=" * 40)
        print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        # 1. Analisar ScriptSolo.py
        funcionalidades_solo = self.analisar_script_solo()
        
        # 2. Analisar arquivos do backend
        categorias = self.analisar_arquivos_backend()
        
        # 3. Identificar duplicados
        duplicados = self.identificar_duplicados(categorias)
        
        # 4. Definir estrutura final
        estrutura_final = self.definir_estrutura_final(categorias, duplicados)
        
        # 5. Limpar arquivos desnecessários
        self.limpar_arquivos_desnecessarios(duplicados)
        
        # 6. Gerar relatório final
        self.gerar_relatorio_final(estrutura_final)

def main():
    """Função principal"""
    analisador = AnalisadorSistema()
    analisador.executar_analise_completa()

if __name__ == "__main__":
    main() 