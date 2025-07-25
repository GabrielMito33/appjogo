#!/usr/bin/env python3
"""
💾 Sistema de Backup e Recovery
Gerencia backups automáticos e recovery do sistema
"""

import os
import shutil
import sqlite3
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

class BackupManager:
    def __init__(self):
        self.backup_dir = Path("backup")
        self.data_dir = Path("data") 
        self.logs_dir = Path("logs")
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_full_backup(self):
        """Cria backup completo do sistema"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_completo_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        print(f"💾 Criando backup completo: {backup_name}")
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Backup do banco de dados
                if (self.data_dir / "sistema_signals.db").exists():
                    zf.write(self.data_dir / "sistema_signals.db", "database/sistema_signals.db")
                    print("  ✅ Banco de dados incluído")
                
                # Backup dos logs (últimos 7 dias)
                log_files = list(self.logs_dir.glob("*.log"))
                for log_file in log_files[-7:]:  # Últimos 7 arquivos
                    zf.write(log_file, f"logs/{log_file.name}")
                print(f"  ✅ {len(log_files)} arquivos de log incluídos")
                
                # Backup das configurações
                config_data = {
                    "timestamp": timestamp,
                    "backup_type": "full",
                    "system_version": "3.0",
                    "files_included": [
                        "database/sistema_signals.db",
                        f"logs/* ({len(log_files)} files)"
                    ]
                }
                
                zf.writestr("config/backup_info.json", json.dumps(config_data, indent=2))
                print("  ✅ Configurações incluídas")
            
            print(f"✅ Backup completo criado: {backup_path}")
            print(f"📊 Tamanho: {backup_path.stat().st_size / 1024 / 1024:.2f} MB")
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return None
    
    def create_database_backup(self):
        """Cria backup apenas do banco de dados"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_source = self.data_dir / "sistema_signals.db"
        db_backup = self.backup_dir / f"database_{timestamp}.db"
        
        if not db_source.exists():
            print("❌ Banco de dados não encontrado")
            return None
        
        try:
            shutil.copy2(db_source, db_backup)
            print(f"✅ Backup do banco criado: {db_backup}")
            return db_backup
        except Exception as e:
            print(f"❌ Erro ao fazer backup do banco: {e}")
            return None
    
    def list_backups(self):
        """Lista todos os backups disponíveis"""
        backups = []
        
        # Backups completos (.zip)
        zip_backups = list(self.backup_dir.glob("backup_completo_*.zip"))
        for backup in zip_backups:
            stat = backup.stat()
            backups.append({
                "name": backup.name,
                "type": "Completo",
                "path": backup,
                "size": stat.st_size / 1024 / 1024,  # MB
                "date": datetime.fromtimestamp(stat.st_mtime)
            })
        
        # Backups de banco (.db)
        db_backups = list(self.backup_dir.glob("database_*.db"))
        for backup in db_backups:
            stat = backup.stat()
            backups.append({
                "name": backup.name,
                "type": "Banco",
                "path": backup,
                "size": stat.st_size / 1024 / 1024,  # MB
                "date": datetime.fromtimestamp(stat.st_mtime)
            })
        
        # Ordenar por data (mais recente primeiro)
        backups.sort(key=lambda x: x["date"], reverse=True)
        
        return backups
    
    def restore_database(self, backup_path):
        """Restaura banco de dados de um backup"""
        db_target = self.data_dir / "sistema_signals.db"
        
        print(f"🔄 Restaurando banco de dados de: {backup_path}")
        
        # Fazer backup do atual antes de restaurar
        if db_target.exists():
            current_backup = self.backup_dir / f"database_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_target, current_backup)
            print(f"💾 Backup atual salvo em: {current_backup}")
        
        try:
            if str(backup_path).endswith('.zip'):
                # Extrair banco do ZIP
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    zf.extract("database/sistema_signals.db", "temp_restore")
                    shutil.move("temp_restore/database/sistema_signals.db", db_target)
                    shutil.rmtree("temp_restore")
            else:
                # Copiar arquivo .db diretamente
                shutil.copy2(backup_path, db_target)
            
            print("✅ Banco de dados restaurado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao restaurar banco: {e}")
            return False
    
    def cleanup_old_backups(self, days_to_keep=30):
        """Remove backups antigos"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        print(f"🧹 Limpando backups anteriores a {cutoff_date.strftime('%d/%m/%Y')}")
        
        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file():
                file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_date < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    print(f"  🗑️ Removido: {backup_file.name}")
        
        print(f"✅ {removed_count} backups antigos removidos")
        return removed_count
    
    def get_database_stats(self):
        """Obtém estatísticas do banco de dados"""
        db_path = self.data_dir / "sistema_signals.db"
        
        if not db_path.exists():
            return {"error": "Banco de dados não encontrado"}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Contar registros por tabela
            tables_stats = {}
            
            # Signals
            cursor.execute("SELECT COUNT(*) FROM signals")
            tables_stats["signals"] = cursor.fetchone()[0]
            
            # Daily stats
            cursor.execute("SELECT COUNT(*) FROM daily_stats")
            tables_stats["daily_stats"] = cursor.fetchone()[0]
            
            # System logs
            cursor.execute("SELECT COUNT(*) FROM system_logs")
            tables_stats["system_logs"] = cursor.fetchone()[0]
            
            # Últimos sinais
            cursor.execute("SELECT strategy_name, result, timestamp FROM signals ORDER BY timestamp DESC LIMIT 5")
            recent_signals = cursor.fetchall()
            
            conn.close()
            
            return {
                "size_mb": db_path.stat().st_size / 1024 / 1024,
                "tables": tables_stats,
                "recent_signals": recent_signals,
                "last_modified": datetime.fromtimestamp(db_path.stat().st_mtime)
            }
            
        except Exception as e:
            return {"error": f"Erro ao analisar banco: {e}"}

def main():
    """Menu principal do backup manager"""
    backup_manager = BackupManager()
    
    while True:
        print("\n💾 SISTEMA DE BACKUP E RECOVERY")
        print("=" * 35)
        print("1. 📦 Criar backup completo")
        print("2. 🗄️ Backup apenas do banco")
        print("3. 📋 Listar backups")
        print("4. 🔄 Restaurar banco")
        print("5. 📊 Estatísticas do banco")
        print("6. 🧹 Limpar backups antigos")
        print("7. 🚪 Sair")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "1":
            backup_manager.create_full_backup()
            
        elif choice == "2":
            backup_manager.create_database_backup()
            
        elif choice == "3":
            backups = backup_manager.list_backups()
            if not backups:
                print("📭 Nenhum backup encontrado")
            else:
                print(f"\n📋 BACKUPS DISPONÍVEIS ({len(backups)}):")
                print("-" * 70)
                for i, backup in enumerate(backups, 1):
                    print(f"{i:2d}. {backup['name']}")
                    print(f"    Tipo: {backup['type']} | Tamanho: {backup['size']:.2f} MB")
                    print(f"    Data: {backup['date'].strftime('%d/%m/%Y %H:%M:%S')}")
                    print()
        
        elif choice == "4":
            backups = backup_manager.list_backups()
            if not backups:
                print("📭 Nenhum backup encontrado")
            else:
                print("\n📋 BACKUPS DISPONÍVEIS:")
                for i, backup in enumerate(backups, 1):
                    print(f"{i}. {backup['name']} ({backup['type']})")
                
                try:
                    choice = int(input("\nEscolha o backup para restaurar: ")) - 1
                    if 0 <= choice < len(backups):
                        backup_manager.restore_database(backups[choice]["path"])
                    else:
                        print("❌ Opção inválida")
                except ValueError:
                    print("❌ Número inválido")
        
        elif choice == "5":
            stats = backup_manager.get_database_stats()
            if "error" in stats:
                print(f"❌ {stats['error']}")
            else:
                print("\n📊 ESTATÍSTICAS DO BANCO:")
                print("-" * 30)
                print(f"Tamanho: {stats['size_mb']:.2f} MB")
                print(f"Última modificação: {stats['last_modified'].strftime('%d/%m/%Y %H:%M:%S')}")
                print("\nTabelas:")
                for table, count in stats['tables'].items():
                    print(f"  {table}: {count} registros")
                
                if stats['recent_signals']:
                    print("\nÚltimos sinais:")
                    for signal in stats['recent_signals']:
                        print(f"  {signal[0]} | {signal[1]} | {signal[2]}")
        
        elif choice == "6":
            days = input("Manter backups dos últimos quantos dias? (padrão: 30): ").strip()
            days = int(days) if days.isdigit() else 30
            backup_manager.cleanup_old_backups(days)
        
        elif choice == "7":
            print("👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main() 