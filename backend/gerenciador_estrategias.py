#!/usr/bin/env python3
"""
🎯 GERENCIADOR DE ESTRATÉGIAS PERSONALIZÁVEIS
Permite ao usuário definir e gerenciar suas próprias estratégias
Sistema compatível com ScriptSolo.py original
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

class GerenciadorEstrategias:
    def __init__(self):
        self.csv_file = Path("estrategias_usuario.csv")
        self.backup_dir = Path("backup_estrategias")
        self.backup_dir.mkdir(exist_ok=True)
        
    def carregar_estrategias_csv(self) -> List[Dict]:
        """Carrega estratégias do arquivo CSV do usuário (formato ScriptSolo.py)"""
        estrategias = []
        
        if not self.csv_file.exists():
            print(f"❌ Arquivo {self.csv_file} não encontrado")
            return []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                for i, row in enumerate(reader):
                    if not row or not row[0].strip():
                        continue
                    
                    estrategia_str = row[0].strip()
                    estrategia_dict = self.parser_estrategia(estrategia_str, i+1)
                    
                    if estrategia_dict:
                        estrategias.append(estrategia_dict)
            
            print(f"✅ Carregadas {len(estrategias)} estratégias do arquivo CSV")
            return estrategias
            
        except Exception as e:
            print(f"❌ Erro ao carregar estratégias: {e}")
            return []
    
    def parser_estrategia(self, estrategia_str: str, linha: int) -> Dict:
        """
        Converte string de estratégia CSV para formato do sistema
        Formato: "V-V=P" ou "1-2-P=V" etc.
        """
        try:
            if "=" not in estrategia_str:
                print(f"⚠️ Linha {linha}: Formato inválido '{estrategia_str}' (precisa ter '=')")
                return None
            
            # Dividir condições e aposta
            condicoes_str, aposta_str = estrategia_str.split("=", 1)
            condicoes = [c.strip() for c in condicoes_str.split("-")]
            aposta = aposta_str.strip()
            
            # Validar aposta
            if aposta not in ["V", "P", "B"]:
                print(f"⚠️ Linha {linha}: Aposta inválida '{aposta}' (deve ser V, P ou B)")
                return None
            
            # Validar condições
            for cond in condicoes:
                if not self.validar_condicao(cond):
                    print(f"⚠️ Linha {linha}: Condição inválida '{cond}'")
                    return None
            
            # Criar nome descritivo
            nome = self.gerar_nome_estrategia(condicoes, aposta)
            
            return {
                "id": linha,
                "name": nome,
                "conditions": condicoes,
                "bet_direction": aposta,
                "priority": 1,
                "active": True,
                "min_confidence": 75,
                "max_daily_signals": 10,
                "source": "csv_usuario",
                "original_string": estrategia_str
            }
            
        except Exception as e:
            print(f"❌ Erro ao processar linha {linha} '{estrategia_str}': {e}")
            return None
    
    def validar_condicao(self, condicao: str) -> bool:
        """Valida se uma condição é válida"""
        # X = wildcard
        if condicao == "X":
            return True
        
        # Cores: V, P, B
        if condicao in ["V", "P", "B"]:
            return True
        
        # Números: 0-14 (Blaze)
        if condicao.isdigit():
            num = int(condicao)
            if 0 <= num <= 14:
                return True
        
        return False
    
    def gerar_nome_estrategia(self, condicoes: List[str], aposta: str) -> str:
        """Gera nome descritivo para a estratégia"""
        cores_map = {"V": "Vermelho", "P": "Preto", "B": "Branco"}
        
        # Criar descrição das condições
        desc_condicoes = []
        for cond in condicoes:
            if cond == "X":
                desc_condicoes.append("Qualquer")
            elif cond in cores_map:
                desc_condicoes.append(cores_map[cond])
            else:
                desc_condicoes.append(f"Nº{cond}")
        
        condicoes_str = " → ".join(desc_condicoes)
        aposta_str = cores_map.get(aposta, aposta)
        
        return f"{condicoes_str} = {aposta_str}"
    
    def converter_para_sistema_atual(self, estrategias_csv: List[Dict]) -> str:
        """Converte estratégias CSV para formato do sistema atual"""
        codigo_estrategias = "# ESTRATÉGIAS CARREGADAS DO CSV DO USUÁRIO\n"
        codigo_estrategias += f"# Arquivo: {self.csv_file}\n"
        codigo_estrategias += f"# Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        
        codigo_estrategias += "ESTRATEGIAS_USUARIO = [\n"
        
        for estrategia in estrategias_csv:
            codigo_estrategias += f"""    {{
        "id": {estrategia["id"]},
        "name": "{estrategia["name"]}",
        "conditions": {estrategia["conditions"]},
        "bet_direction": "{estrategia["bet_direction"]}",
        "priority": {estrategia["priority"]},
        "active": {estrategia["active"]},
        "min_confidence": {estrategia["min_confidence"]},
        "max_daily_signals": {estrategia["max_daily_signals"]},
        "source": "{estrategia["source"]}",
        "original_string": "{estrategia["original_string"]}"
    }},\n"""
        
        codigo_estrategias += "]\n"
        
        return codigo_estrategias
    
    def salvar_backup(self, estrategias: List[Dict]):
        """Salva backup das estratégias atuais"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f"estrategias_{timestamp}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(estrategias, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Backup salvo: {backup_file}")
    
    def criar_exemplo_csv(self):
        """Cria arquivo de exemplo se não existir"""
        if self.csv_file.exists():
            return
        
        exemplos = [
            "V-V=P",           # Dois vermelhos → apostar preto
            "P-P=V",           # Dois pretos → apostar vermelho  
            "V-V-P=V",         # Vermelho-Vermelho-Preto → apostar vermelho
            "P-P-P=V",         # Três pretos → apostar vermelho
            "1-2=P",           # Números 1 e 2 → apostar preto
            "8-9=V",           # Números 8 e 9 → apostar vermelho
            "X-V-V=P",         # Qualquer-Vermelho-Vermelho → apostar preto
            "V-X-P=V",         # Vermelho-Qualquer-Preto → apostar vermelho
        ]
        
        with open(self.csv_file, 'w', encoding='utf-8') as f:
            for exemplo in exemplos:
                f.write(f"{exemplo}\n")
        
        print(f"✅ Arquivo de exemplo criado: {self.csv_file}")
    
    def validar_todas_estrategias(self, estrategias: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Valida todas as estratégias e retorna válidas e erros"""
        validas = []
        erros = []
        
        for estrategia in estrategias:
            try:
                # Verificar campos obrigatórios
                campos_obrigatorios = ["conditions", "bet_direction"]
                for campo in campos_obrigatorios:
                    if campo not in estrategia:
                        erros.append(f"Estratégia {estrategia.get('id', '?')}: Campo '{campo}' obrigatório")
                        continue
                
                # Validar condições
                for cond in estrategia["conditions"]:
                    if not self.validar_condicao(cond):
                        erros.append(f"Estratégia {estrategia['id']}: Condição inválida '{cond}'")
                        continue
                
                # Validar aposta
                if estrategia["bet_direction"] not in ["V", "P", "B"]:
                    erros.append(f"Estratégia {estrategia['id']}: Aposta inválida '{estrategia['bet_direction']}'")
                    continue
                
                validas.append(estrategia)
                
            except Exception as e:
                erros.append(f"Estratégia {estrategia.get('id', '?')}: Erro {e}")
        
        return validas, erros
    
    def listar_estrategias(self, estrategias: List[Dict]):
        """Lista estratégias de forma organizada"""
        print(f"\n📋 ESTRATÉGIAS CARREGADAS ({len(estrategias)}):")
        print("=" * 80)
        
        for i, estrategia in enumerate(estrategias, 1):
            status = "✅ ATIVA" if estrategia.get("active", True) else "❌ INATIVA"
            condicoes = " → ".join(estrategia["conditions"])
            
            print(f"{i:2d}. {estrategia['name']}")
            print(f"    Condições: {condicoes}")
            print(f"    Aposta: {estrategia['bet_direction']} | Status: {status}")
            print(f"    Confiança: {estrategia.get('min_confidence', 75)}% | Sinais/dia: {estrategia.get('max_daily_signals', 10)}")
            if "original_string" in estrategia:
                print(f"    CSV: {estrategia['original_string']}")
            print()

def main():
    print("🎯 GERENCIADOR DE ESTRATÉGIAS PERSONALIZÁVEIS")
    print("=" * 50)
    
    gerenciador = GerenciadorEstrategias()
    
    # Criar arquivo de exemplo se não existir
    gerenciador.criar_exemplo_csv()
    
    while True:
        print("\n📋 OPÇÕES:")
        print("1. 📁 Carregar estratégias do CSV")
        print("2. 📝 Listar estratégias atuais")
        print("3. ✅ Validar estratégias")
        print("4. 🔄 Converter para código Python")
        print("5. 💾 Fazer backup")
        print("6. 📖 Ajuda com formato CSV")
        print("7. 🚪 Sair")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "1":
            estrategias = gerenciador.carregar_estrategias_csv()
            if estrategias:
                gerenciador.listar_estrategias(estrategias)
        
        elif escolha == "2":
            estrategias = gerenciador.carregar_estrategias_csv()
            gerenciador.listar_estrategias(estrategias)
        
        elif escolha == "3":
            estrategias = gerenciador.carregar_estrategias_csv()
            validas, erros = gerenciador.validar_todas_estrategias(estrategias)
            
            print(f"\n✅ Estratégias válidas: {len(validas)}")
            if erros:
                print(f"❌ Erros encontrados: {len(erros)}")
                for erro in erros:
                    print(f"  • {erro}")
        
        elif escolha == "4":
            estrategias = gerenciador.carregar_estrategias_csv()
            if estrategias:
                codigo = gerenciador.converter_para_sistema_atual(estrategias)
                
                # Salvar código gerado
                with open("estrategias_convertidas.py", "w", encoding="utf-8") as f:
                    f.write(codigo)
                
                print(f"✅ Código Python gerado: estrategias_convertidas.py")
                print(f"📄 {len(estrategias)} estratégias convertidas")
        
        elif escolha == "5":
            estrategias = gerenciador.carregar_estrategias_csv()
            if estrategias:
                gerenciador.salvar_backup(estrategias)
        
        elif escolha == "6":
            print(f"""
📖 FORMATO DO ARQUIVO CSV ({gerenciador.csv_file}):

🎯 FORMATO BÁSICO:
condicao1-condicao2-...=aposta

🎯 EXEMPLOS:
V-V=P          → Dois vermelhos seguidos, apostar no preto
P-P=V          → Dois pretos seguidos, apostar no vermelho  
1-2=P          → Números 1 e 2, apostar no preto
8-9-10=V       → Números 8, 9 e 10, apostar no vermelho
V-V-P=V        → Vermelho, vermelho, preto, apostar no vermelho
X-V-V=P        → Qualquer, vermelho, vermelho, apostar no preto

🎯 CONDIÇÕES VÁLIDAS:
• V, P, B      → Cores (Vermelho, Preto, Branco)
• 0, 1, 2...14 → Números específicos da Blaze
• X            → Wildcard (qualquer valor)

🎯 APOSTAS VÁLIDAS:
• V → Vermelho
• P → Preto  
• B → Branco

🎯 ORDEM TEMPORAL:
A primeira condição é o resultado mais ANTIGO
A última condição é o resultado mais RECENTE
            """)
        
        elif escolha == "7":
            print("👋 Até logo!")
            break
        
        else:
            print("❌ Opção inválida")

if __name__ == "__main__":
    main() 