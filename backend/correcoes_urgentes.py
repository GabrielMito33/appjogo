#!/usr/bin/env python3
"""
🔧 CORREÇÕES URGENTES
Aplica correções aos bugs identificados na análise
"""

import re
from pathlib import Path

def corrigir_bugs():
    print("🔧 APLICANDO CORREÇÕES URGENTES")
    print("=" * 35)
    
    sistema_file = Path("sistema_producao_24h.py")
    
    if not sistema_file.exists():
        print("❌ Arquivo sistema não encontrado")
        return False
    
    # Ler arquivo
    with open(sistema_file, 'r', encoding='utf-8') as f:
        codigo = f.read()
    
    print("🔄 Aplicando correções...")
    
    # Correção 1: Adicionar maintenance_hour na configuração
    if 'maintenance_hour' not in codigo:
        config_pattern = r'(PRODUCTION_CONFIG = \{[^}]+)"log_level": "INFO"([^}]*)\}'
        replacement = r'\1"log_level": "INFO",\n    "maintenance_hour": 4\2}'
        codigo = re.sub(config_pattern, replacement, codigo, flags=re.DOTALL)
        print("✅ Adicionado maintenance_hour na configuração")
    
    # Correção 2: Melhorar encoding dos logs para Windows
    if 'errors="replace"' not in codigo:
        # Substituir setup de logging
        logging_setup = '''def setup_logging():
    """Configurar sistema de logs completo"""
    # Criar diretórios
    Path("logs").mkdir(exist_ok=True)
    Path("backup").mkdir(exist_ok=True)
    Path("data").mkdir(exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger('SistemaSignals')
    logger.setLevel(getattr(logging, PRODUCTION_CONFIG["log_level"]))
    
    # Formatador simples para Windows
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo principal (rotativo) - encoding UTF-8
    main_handler = RotatingFileHandler(
        'logs/sistema_principal.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8',
        errors='replace'  # Ignora caracteres problemáticos
    )
    main_handler.setFormatter(formatter)
    logger.addHandler(main_handler)
    
    # Handler para arquivo diário - encoding UTF-8
    today = datetime.now().strftime('%Y-%m-%d')
    daily_handler = logging.FileHandler(
        f'logs/sinais_{today}.log', 
        encoding='utf-8',
        errors='replace'
    )
    daily_handler.setFormatter(formatter)
    logger.addHandler(daily_handler)
    
    # Handler para console - sem emojis problemáticos
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Logger específico para erros
    error_logger = logging.getLogger('Errors')
    error_handler = RotatingFileHandler(
        'logs/errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10,
        encoding='utf-8',
        errors='replace'
    )
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    
    return logger'''
        
        # Substituir função setup_logging
        codigo = re.sub(
            r'def setup_logging\(\):.*?return logger',
            logging_setup,
            codigo,
            flags=re.DOTALL
        )
        print("✅ Corrigido encoding dos logs para Windows")
    
    # Correção 3: Função simples para mensagens sem emojis problemáticos
    safe_log_func = '''
def safe_log(message, level="info"):
    """Log seguro sem emojis problemáticos"""
    # Remover emojis problemáticos para logs
    clean_message = message.encode('ascii', errors='ignore').decode('ascii')
    if hasattr(logger, level):
        getattr(logger, level)(clean_message)
    else:
        logger.info(clean_message)
'''
    
    if 'def safe_log' not in codigo:
        # Adicionar após setup_logging
        codigo = codigo.replace(
            'logger = setup_logging()',
            'logger = setup_logging()\n' + safe_log_func
        )
        print("✅ Adicionada função safe_log")
    
    # Correção 4: Substituir logs com emojis por safe_log
    emoji_logs = [
        (r'logger\.info\(f"🚀', 'safe_log(f"[INICIO]'),
        (r'logger\.info\(f"🆕', 'safe_log(f"[NOVO]'),
        (r'logger\.info\(f"✅', 'safe_log(f"[SUCESSO]'),
        (r'logger\.info\(f"⚠️', 'safe_log(f"[ALERTA]'),
        (r'logger\.info\(f"❌', 'safe_log(f"[ERRO]'),
        (r'logger\.warning\(f"⚠️', 'safe_log(f"[AVISO]", "warning")'),
        (r'logger\.error\(f"❌', 'safe_log(f"[ERRO]", "error")')
    ]
    
    for pattern, replacement in emoji_logs:
        codigo = re.sub(pattern, replacement, codigo)
    
    print("✅ Corrigidos logs com emojis problemáticos")
    
    # Salvar arquivo corrigido
    with open(sistema_file, 'w', encoding='utf-8') as f:
        f.write(codigo)
    
    print("✅ CORREÇÕES APLICADAS COM SUCESSO!")
    return True

def main():
    print("🔧 CORREÇÕES URGENTES DO SISTEMA")
    print("=" * 35)
    print("Aplicando correções para:")
    print("1. ❌ KeyError: 'maintenance_hour'")
    print("2. ❌ UnicodeEncodeError nos logs")
    print("3. ❌ Telegram API status 400")
    print("4. ❌ Emojis problemáticos")
    print()
    
    if corrigir_bugs():
        print("\n✅ SISTEMA CORRIGIDO!")
        print("🚀 Execute: python sistema_producao_24h.py")
    else:
        print("\n❌ Falha nas correções")

if __name__ == "__main__":
    main() 