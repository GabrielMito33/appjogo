#!/usr/bin/env python3
"""
🚀 SCRIPT PARA INICIAR ADMIN BACKEND
Inicia o painel de administração do sistema
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências do admin...")
    
    dependencias = [
        'fastapi',
        'uvicorn',
        'python-multipart',
        'pyjwt',
        'psutil'
    ]
    
    faltando = []
    
    for dep in dependencias:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  ✅ {dep}")
        except ImportError:
            print(f"  ❌ {dep}")
            faltando.append(dep)
    
    if faltando:
        print(f"\n⚠️ Dependências faltando: {', '.join(faltando)}")
        print("Instalando automaticamente...")
        
        try:
            for dep in faltando:
                print(f"📦 Instalando {dep}...")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            
            print("✅ Todas as dependências foram instaladas!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao instalar dependências: {e}")
            print("Execute manualmente: pip install fastapi uvicorn python-multipart pyjwt psutil")
            return False
    
    print("✅ Todas as dependências estão instaladas")
    return True

def verificar_arquivos():
    """Verifica se os arquivos necessários existem"""
    print("\n📁 Verificando arquivos do sistema...")
    
    arquivos_necessarios = [
        'admin_backend.py',
        'plataformas_api.py',
        'analisador_estrategias.py',
        'validador_configuracoes.py'
    ]
    
    faltando = []
    
    for arquivo in arquivos_necessarios:
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

def mostrar_info_inicial():
    """Mostra informações iniciais"""
    print("\n👑 ADMIN BACKEND - SISTEMA MULTI-PLATAFORMA")
    print("=" * 55)
    print("🎯 Painel de administração para gerenciar robôs")
    print("🌐 Interface web completa com autenticação")
    print("📊 Dashboard em tempo real")
    print("🤖 Gerenciamento de robôs")
    print("🔐 Validação de configurações")
    print("📝 Visualização de logs")
    print()

def mostrar_credenciais():
    """Mostra credenciais de acesso"""
    print("🔐 CREDENCIAIS DE ACESSO:")
    print("-" * 25)
    print("👤 Super Admin:")
    print("   Username: admin")
    print("   Password: admin123")
    print()
    print("👤 Manager:")
    print("   Username: manager") 
    print("   Password: manager123")
    print()

def iniciar_admin():
    """Inicia o admin backend"""
    print("🚀 INICIANDO ADMIN BACKEND...")
    print("-" * 30)
    
    try:
        # Executar admin backend
        os.chdir(Path(__file__).parent)
        
        print("🌐 Servidor iniciando...")
        print("📍 URL: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("🛑 Pressione Ctrl+C para parar")
        print()
        
        # Aguardar um pouco para o usuário ler
        time.sleep(2)
        
        # Executar
        subprocess.run([
            sys.executable, 
            "admin_backend.py"
        ])
        
    except KeyboardInterrupt:
        print("\n\n🛑 Admin backend interrompido pelo usuário")
    except FileNotFoundError:
        print("❌ Erro: admin_backend.py não encontrado")
        print("Certifique-se de estar no diretório correto")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

def main():
    """Função principal"""
    mostrar_info_inicial()
    
    # Verificações
    if not verificar_dependencias():
        input("\nPressione Enter para continuar mesmo assim...")
    
    if not verificar_arquivos():
        print("❌ Não é possível continuar sem os arquivos necessários")
        input("Pressione Enter para sair...")
        return
    
    # Mostrar credenciais
    mostrar_credenciais()
    
    # Confirmar início
    resposta = input("Deseja iniciar o admin backend? (S/n): ").strip().lower()
    
    if resposta == 'n':
        print("👋 Operação cancelada")
        return
    
    # Iniciar
    iniciar_admin()

if __name__ == "__main__":
    main() 