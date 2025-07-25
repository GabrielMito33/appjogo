#!/usr/bin/env python3
"""
🎮 GERENCIADOR DO SISTEMA COMPLETO
Interface principal para controlar todo o sistema MVP
"""

import asyncio
import subprocess
import sys
from pathlib import Path
import json
import time

class GerenciadorSistema:
    def __init__(self):
        self.sistema_rodando = False
        
    def verificar_dependencias(self):
        """Verifica se as dependências estão instaladas"""
        print("🔍 Verificando dependências...")
        
        dependencias_criticas = [
            'aiohttp', 'requests', 'pathlib', 'json', 'datetime'
        ]
        
        faltando = []
        
        for dep in dependencias_criticas:
            try:
                __import__(dep)
                print(f"  ✅ {dep}")
            except ImportError:
                print(f"  ❌ {dep}")
                faltando.append(dep)
        
        if faltando:
            print(f"\n⚠️ Dependências faltando: {', '.join(faltando)}")
            print("Execute: pip install -r requirements_mvp.txt")
            return False
        
        print("✅ Todas as dependências estão instaladas")
        return True
    
    def verificar_arquivos_sistema(self):
        """Verifica se todos os arquivos necessários existem"""
        print("\n📁 Verificando arquivos do sistema...")
        
        arquivos_criticos = [
            'plataformas_api.py',
            'configurador_robos.py', 
            'analisador_estrategias.py',
            'executor_bots.py',
            'validador_configuracoes.py',
            'sistema_variaveis_mensagens.py'
        ]
        
        faltando = []
        
        for arquivo in arquivos_criticos:
            if Path(arquivo).exists():
                print(f"  ✅ {arquivo}")
            else:
                print(f"  ❌ {arquivo}")
                faltando.append(arquivo)
        
        if faltando:
            print(f"\n⚠️ Arquivos faltando: {', '.join(faltando)}")
            return False
        
        print("✅ Todos os arquivos necessários estão presentes")
        return True
    
    def verificar_configuracoes(self):
        """Verifica se há robôs configurados"""
        print("\n🤖 Verificando configurações de robôs...")
        
        config_file = Path("robos_configurados.json")
        
        if not config_file.exists():
            print("  ❌ Arquivo robos_configurados.json não encontrado")
            print("  💡 Execute: python configurador_robos.py")
            return False
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            robos = config.get('robos', [])
            robos_ativos = [r for r in robos if r.get('status') == 'ativo']
            
            print(f"  📋 {len(robos)} robôs configurados")
            print(f"  ✅ {len(robos_ativos)} robôs ativos")
            
            if len(robos_ativos) == 0:
                print("  ⚠️ Nenhum robô ativo. Configure pelo menos um robô.")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ❌ Erro ao ler configurações: {e}")
            return False
    
    async def validar_sistema_completo(self):
        """Validação completa do sistema"""
        print("\n🔐 Validando configurações completas...")
        
        try:
            from validador_configuracoes import ValidadorConfiguracoes
            
            validador = ValidadorConfiguracoes()
            resultado = await validador.validar_arquivo_robos()
            
            if resultado['valido']:
                print(f"  ✅ {resultado['robos_validos']} robôs válidos")
                if resultado['robos_com_aviso'] > 0:
                    print(f"  ⚠️ {resultado['robos_com_aviso']} robôs com avisos")
                return True
            else:
                print(f"  ❌ {resultado['robos_com_erro']} robôs com erros")
                print("  💡 Execute: python validador_configuracoes.py")
                return False
                
        except Exception as e:
            print(f"  ❌ Erro na validação: {e}")
            return False
    
    def mostrar_menu_principal(self):
        """Mostra menu principal do sistema"""
        print("\n🎮 GERENCIADOR DO SISTEMA MULTI-PLATAFORMA")
        print("=" * 50)
        print("1. 🔧 Instalar dependências")
        print("2. 🤖 Configurar robôs")
        print("3. 🔐 Validar configurações")
        print("4. 📊 Coletar dados das plataformas")
        print("5. 🎯 Analisar estratégias")
        print("6. 🚀 Iniciar sistema completo")
        print("7. 📋 Status do sistema")
        print("8. 🧪 Demonstração completa")
        print("9. 📖 Ajuda e documentação")
        print("10. 🚪 Sair")
    
    def instalar_dependencias(self):
        """Instala dependências do sistema"""
        print("\n🔧 Instalando dependências...")
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r', 'requirements_mvp.txt'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Dependências instaladas com sucesso")
                return True
            else:
                print(f"❌ Erro na instalação: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao instalar: {e}")
            return False
    
    def executar_configurador_robos(self):
        """Executa o configurador de robôs"""
        print("\n🤖 Iniciando configurador de robôs...")
        
        try:
            subprocess.run([sys.executable, 'configurador_robos.py'])
        except Exception as e:
            print(f"❌ Erro ao executar configurador: {e}")
    
    async def executar_validador(self):
        """Executa validação das configurações"""
        print("\n🔐 Iniciando validação...")
        
        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, 'validador_configuracoes.py'
            )
            await proc.wait()
        except Exception as e:
            print(f"❌ Erro ao executar validador: {e}")
    
    def coletar_dados_plataformas(self):
        """Coleta dados das plataformas"""
        print("\n📊 Coletando dados das plataformas...")
        
        try:
            subprocess.run([sys.executable, 'plataformas_api.py'])
        except Exception as e:
            print(f"❌ Erro ao coletar dados: {e}")
    
    def executar_analise_estrategias(self):
        """Executa análise de estratégias"""
        print("\n🎯 Iniciando análise de estratégias...")
        
        try:
            subprocess.run([sys.executable, 'painel_estrategias.py'])
        except Exception as e:
            print(f"❌ Erro ao executar análise: {e}")
    
    async def iniciar_sistema_completo(self):
        """Inicia o sistema completo em produção"""
        print("\n🚀 INICIANDO SISTEMA COMPLETO")
        print("=" * 35)
        
        # Verificações finais
        if not self.verificar_dependencias():
            return False
        
        if not self.verificar_arquivos_sistema():
            return False
        
        if not self.verificar_configuracoes():
            return False
        
        if not await self.validar_sistema_completo():
            confirmar = input("\n⚠️ Há problemas nas configurações. Continuar mesmo assim? (s/N): ")
            if confirmar.lower() != 's':
                return False
        
        print("\n✅ Todas as verificações passaram!")
        print("🚀 Iniciando executor principal...")
        
        try:
            # Executar o sistema principal
            proc = await asyncio.create_subprocess_exec(
                sys.executable, 'executor_bots.py'
            )
            
            self.sistema_rodando = True
            return_code = await proc.wait()
            self.sistema_rodando = False
            
            if return_code == 0:
                print("✅ Sistema finalizado normalmente")
            else:
                print(f"⚠️ Sistema finalizado com código: {return_code}")
                
        except Exception as e:
            print(f"❌ Erro ao executar sistema: {e}")
            self.sistema_rodando = False
            return False
    
    async def mostrar_status_sistema(self):
        """Mostra status atual do sistema"""
        print("\n📋 STATUS DO SISTEMA")
        print("=" * 25)
        
        # Verificar dependências
        deps_ok = self.verificar_dependencias()
        
        # Verificar arquivos
        arquivos_ok = self.verificar_arquivos_sistema()
        
        # Verificar configurações
        config_ok = self.verificar_configuracoes()
        
        # Status geral
        print(f"\n🎯 STATUS GERAL:")
        print(f"  Dependências: {'✅' if deps_ok else '❌'}")
        print(f"  Arquivos: {'✅' if arquivos_ok else '❌'}")
        print(f"  Configurações: {'✅' if config_ok else '❌'}")
        print(f"  Sistema rodando: {'✅' if self.sistema_rodando else '❌'}")
        
        # Verificar dados coletados
        dados_file = Path("dados_plataformas.json")
        if dados_file.exists():
            try:
                with open(dados_file, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                
                total_dados = sum(len(resultados) for resultados in dados.get('plataformas', {}).values())
                print(f"  Dados coletados: ✅ {total_dados} resultados")
                
            except:
                print(f"  Dados coletados: ⚠️ Arquivo corrompido")
        else:
            print(f"  Dados coletados: ❌ Não coletados")
        
        # Recomendações
        if not all([deps_ok, arquivos_ok, config_ok]):
            print(f"\n💡 PRÓXIMAS AÇÕES:")
            if not deps_ok:
                print("  1. Instalar dependências")
            if not config_ok:
                print("  2. Configurar robôs")
            if not arquivos_ok:
                print("  3. Verificar instalação do sistema")
        else:
            print(f"\n🎉 Sistema pronto para execução!")
    
    def executar_demonstracao(self):
        """Executa demonstração completa"""
        print("\n🧪 Iniciando demonstração completa...")
        
        try:
            subprocess.run([sys.executable, 'demonstracao_sistema_completo.py'])
        except Exception as e:
            print(f"❌ Erro ao executar demonstração: {e}")
    
    def mostrar_ajuda(self):
        """Mostra ajuda e documentação"""
        print("\n📖 AJUDA E DOCUMENTAÇÃO")
        print("=" * 30)
        
        print("🎯 FLUXO RECOMENDADO PARA INICIAR:")
        print("  1. Instalar dependências (opção 1)")
        print("  2. Configurar seus robôs (opção 2)")
        print("  3. Validar configurações (opção 3)")
        print("  4. Coletar dados das plataformas (opção 4)")
        print("  5. Iniciar sistema completo (opção 6)")
        
        print(f"\n📁 ARQUIVOS IMPORTANTES:")
        print("  • robos_configurados.json - Configuração dos robôs")
        print("  • dados_plataformas.json - Dados coletados das APIs")
        print("  • executor_bots.log - Logs do sistema em execução")
        print("  • relatorio_validacao.txt - Relatório de validação")
        
        print(f"\n🚀 COMANDOS DIRETOS:")
        print("  python configurador_robos.py - Configurar robôs")
        print("  python validador_configuracoes.py - Validar setup")
        print("  python executor_bots.py - Executar sistema")
        print("  python painel_estrategias.py - Analisar estratégias")
        
        print(f"\n📋 DOCUMENTAÇÃO COMPLETA:")
        print("  • README_SISTEMA_COMPLETO.md")
        print("  • analise_mvp_status.json")
        
        input("\nPressione Enter para continuar...")
    
    async def executar(self):
        """Loop principal do gerenciador"""
        print("🎮 GERENCIADOR DO SISTEMA MULTI-PLATAFORMA")
        print("Sistema completo para robôs de sinais")
        print()
        
        while True:
            try:
                self.mostrar_menu_principal()
                opcao = input("\nEscolha uma opção: ").strip()
                
                if opcao == "1":
                    self.instalar_dependencias()
                
                elif opcao == "2":
                    self.executar_configurador_robos()
                
                elif opcao == "3":
                    await self.executar_validador()
                
                elif opcao == "4":
                    self.coletar_dados_plataformas()
                
                elif opcao == "5":
                    self.executar_analise_estrategias()
                
                elif opcao == "6":
                    await self.iniciar_sistema_completo()
                
                elif opcao == "7":
                    await self.mostrar_status_sistema()
                
                elif opcao == "8":
                    self.executar_demonstracao()
                
                elif opcao == "9":
                    self.mostrar_ajuda()
                
                elif opcao == "10":
                    print("👋 Obrigado por usar o sistema!")
                    break
                
                else:
                    print("❌ Opção inválida")
                
                if opcao != "6":  # Não pausar após executar sistema completo
                    input("\nPressione Enter para continuar...")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Sistema interrompido pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                input("Pressione Enter para continuar...")

async def main():
    """Função principal"""
    gerenciador = GerenciadorSistema()
    await gerenciador.executar()

if __name__ == "__main__":
    asyncio.run(main()) 