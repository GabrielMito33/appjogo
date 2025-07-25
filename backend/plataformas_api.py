#!/usr/bin/env python3
"""
🎰 SISTEMA DE APIs PARA MÚLTIPLAS PLATAFORMAS
Suporte para Blaze, Jonbet e outras casas de apostas
Coleta dados via JSON das APIs oficiais
"""

import requests
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class PlataformaAPI(ABC):
    """Classe base para APIs de plataformas"""
    
    def __init__(self, nome: str):
        self.nome = nome
        self.ultima_atualizacao = None
        self.dados_cache = []
    
    @abstractmethod
    def buscar_resultados(self) -> List[Dict[str, Any]]:
        """Busca resultados da API da plataforma"""
        pass
    
    @abstractmethod
    def converter_para_padrao(self, dados_raw: List[Dict]) -> List[Dict]:
        """Converte dados da API para formato padrão do sistema"""
        pass
    
    def get_resultados_padronizados(self) -> List[Dict[str, Any]]:
        """Retorna resultados no formato padrão do sistema"""
        dados_raw = self.buscar_resultados()
        if dados_raw:
            self.dados_cache = self.converter_para_padrao(dados_raw)
            self.ultima_atualizacao = datetime.now()
        return self.dados_cache

class BlazeAPI(PlataformaAPI):
    """API da Blaze Double"""
    
    def __init__(self):
        super().__init__("Blaze")
        self.api_url = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"
        self.jogo = "Double"
    
    def buscar_resultados(self) -> List[Dict[str, Any]]:
        """Busca resultados da Blaze Double"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Erro ao buscar Blaze: {e}")
            return []
    
    def converter_para_padrao(self, dados_raw: List[Dict]) -> List[Dict]:
        """Converte dados da Blaze para formato padrão"""
        resultados = []
        
        for item in dados_raw:
            numero = item.get('roll', 0)
            cor = self.numero_para_cor(numero)
            
            resultado = {
                'plataforma': 'blaze',
                'jogo': 'double',
                'numero': numero,
                'cor': cor,
                'timestamp': item.get('created_at', ''),
                'id': item.get('id', ''),
                'dados_originais': item
            }
            resultados.append(resultado)
        
        return resultados
    
    def numero_para_cor(self, numero: int) -> str:
        """Converte número da Blaze para cor"""
        if numero == 0:
            return "B"  # Branco
        elif 1 <= numero <= 7:
            return "V"  # Vermelho
        elif 8 <= numero <= 14:
            return "P"  # Preto
        else:
            return "?"

class JonbetAPI(PlataformaAPI):
    """API da Jonbet Double"""
    
    def __init__(self):
        super().__init__("Jonbet")
        self.api_url = "https://api.jonbet.com/v1/games/double/recent"  # URL hipotética
        self.jogo = "Double"
    
    def buscar_resultados(self) -> List[Dict[str, Any]]:
        """Busca resultados da Jonbet Double"""
        try:
            # Headers podem ser necessários para algumas APIs
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(self.api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Jonbet pode ter estrutura diferente
                return data.get('results', [])
            return []
        except Exception as e:
            print(f"Erro ao buscar Jonbet: {e}")
            return []
    
    def converter_para_padrao(self, dados_raw: List[Dict]) -> List[Dict]:
        """Converte dados da Jonbet para formato padrão"""
        resultados = []
        
        for item in dados_raw:
            # Jonbet pode ter campo 'value' em vez de 'roll'
            numero = item.get('value', item.get('number', 0))
            cor = self.numero_para_cor(numero)
            
            resultado = {
                'plataforma': 'jonbet',
                'jogo': 'double',
                'numero': numero,
                'cor': cor,
                'timestamp': item.get('timestamp', item.get('created_at', '')),
                'id': item.get('game_id', item.get('id', '')),
                'dados_originais': item
            }
            resultados.append(resultado)
        
        return resultados
    
    def numero_para_cor(self, numero: int) -> str:
        """Converte número da Jonbet para cor (mesmo padrão Blaze)"""
        if numero == 0:
            return "B"
        elif 1 <= numero <= 7:
            return "V"
        elif 8 <= numero <= 14:
            return "P"
        else:
            return "?"

class BetfireAPI(PlataformaAPI):
    """API da Betfire Double (exemplo de extensão)"""
    
    def __init__(self):
        super().__init__("Betfire")
        self.api_url = "https://api.betfire.com/double/history"  # URL hipotética
        self.jogo = "Double"
    
    def buscar_resultados(self) -> List[Dict[str, Any]]:
        """Busca resultados da Betfire"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                return response.json().get('data', [])
            return []
        except Exception as e:
            print(f"Erro ao buscar Betfire: {e}")
            return []
    
    def converter_para_padrao(self, dados_raw: List[Dict]) -> List[Dict]:
        """Converte dados da Betfire para formato padrão"""
        resultados = []
        
        for item in dados_raw:
            numero = item.get('result', 0)
            cor = self.numero_para_cor(numero)
            
            resultado = {
                'plataforma': 'betfire',
                'jogo': 'double',
                'numero': numero,
                'cor': cor,
                'timestamp': item.get('time', ''),
                'id': item.get('round_id', ''),
                'dados_originais': item
            }
            resultados.append(resultado)
        
        return resultados
    
    def numero_para_cor(self, numero: int) -> str:
        """Converte número para cor"""
        if numero == 0:
            return "B"
        elif 1 <= numero <= 7:
            return "V"
        elif 8 <= numero <= 14:
            return "P"
        else:
            return "?"

class GerenciadorPlataformas:
    """Gerencia múltiplas plataformas de apostas"""
    
    def __init__(self):
        self.plataformas = {
            'blaze': BlazeAPI(),
            'jonbet': JonbetAPI(),
            'betfire': BetfireAPI()
        }
        self.dados_historicos = {}
        self.arquivo_dados = Path("dados_plataformas.json")
    
    def listar_plataformas_disponiveis(self) -> Dict[str, Dict[str, str]]:
        """Lista plataformas disponíveis"""
        return {
            'blaze': {
                'nome': 'Blaze',
                'jogo': 'Double',
                'url': 'blaze.bet.br',
                'status': 'ativo'
            },
            'jonbet': {
                'nome': 'Jonbet',
                'jogo': 'Double', 
                'url': 'jonbet.com',
                'status': 'ativo'
            },
            'betfire': {
                'nome': 'Betfire',
                'jogo': 'Double',
                'url': 'betfire.com',
                'status': 'beta'
            }
        }
    
    def buscar_dados_plataforma(self, plataforma: str) -> List[Dict[str, Any]]:
        """Busca dados de uma plataforma específica"""
        if plataforma not in self.plataformas:
            raise ValueError(f"Plataforma '{plataforma}' não suportada")
        
        api = self.plataformas[plataforma]
        return api.get_resultados_padronizados()
    
    def buscar_todas_plataformas(self) -> Dict[str, List[Dict[str, Any]]]:
        """Busca dados de todas as plataformas"""
        dados = {}
        
        for nome, api in self.plataformas.items():
            try:
                dados[nome] = api.get_resultados_padronizados()
                print(f"✅ {nome}: {len(dados[nome])} resultados")
            except Exception as e:
                print(f"❌ Erro em {nome}: {e}")
                dados[nome] = []
        
        return dados
    
    def salvar_dados_historicos(self, dados: Dict[str, List[Dict[str, Any]]]):
        """Salva dados históricos em arquivo JSON"""
        dados_para_salvar = {
            'timestamp': datetime.now().isoformat(),
            'plataformas': dados
        }
        
        try:
            with open(self.arquivo_dados, 'w', encoding='utf-8') as f:
                json.dump(dados_para_salvar, f, indent=2, ensure_ascii=False)
            print(f"💾 Dados salvos em {self.arquivo_dados}")
        except Exception as e:
            print(f"❌ Erro ao salvar dados: {e}")
    
    def carregar_dados_historicos(self) -> Dict[str, List[Dict[str, Any]]]:
        """Carrega dados históricos do arquivo"""
        if not self.arquivo_dados.exists():
            return {}
        
        try:
            with open(self.arquivo_dados, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            return dados.get('plataformas', {})
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return {}
    
    def coletar_e_salvar_dados(self):
        """Coleta dados de todas as plataformas e salva"""
        print("🔄 Coletando dados de todas as plataformas...")
        dados_atuais = self.buscar_todas_plataformas()
        
        # Mesclar com dados históricos
        dados_historicos = self.carregar_dados_historicos()
        
        for plataforma, novos_dados in dados_atuais.items():
            if plataforma not in dados_historicos:
                dados_historicos[plataforma] = []
            
            # Adicionar novos dados (evitar duplicatas por ID)
            ids_existentes = {item.get('id') for item in dados_historicos[plataforma]}
            
            for novo in novos_dados:
                if novo.get('id') not in ids_existentes:
                    dados_historicos[plataforma].append(novo)
            
            # Manter apenas os últimos 1000 resultados por plataforma
            dados_historicos[plataforma] = dados_historicos[plataforma][-1000:]
        
        self.salvar_dados_historicos(dados_historicos)
        return dados_historicos
    
    def testar_conectividade(self) -> Dict[str, bool]:
        """Testa conectividade com todas as APIs"""
        resultados = {}
        
        print("\n🔍 TESTANDO CONECTIVIDADE DAS APIS:")
        print("-" * 40)
        
        for nome, api in self.plataformas.items():
            try:
                dados = api.buscar_resultados()
                sucesso = len(dados) > 0
                resultados[nome] = sucesso
                
                status = "✅ Online" if sucesso else "❌ Offline"
                print(f"{nome.capitalize()}: {status}")
                
                if sucesso:
                    print(f"  └─ {len(dados)} resultados obtidos")
                
            except Exception as e:
                resultados[nome] = False
                print(f"{nome.capitalize()}: ❌ Erro - {e}")
        
        return resultados

def main():
    """Demonstração do sistema de múltiplas plataformas"""
    print("🎰 SISTEMA DE MÚLTIPLAS PLATAFORMAS DE APOSTAS")
    print("=" * 55)
    
    gerenciador = GerenciadorPlataformas()
    
    # Listar plataformas
    print("\n📋 PLATAFORMAS DISPONÍVEIS:")
    plataformas = gerenciador.listar_plataformas_disponiveis()
    
    for key, info in plataformas.items():
        status_emoji = "✅" if info['status'] == 'ativo' else "🚧"
        print(f"  {status_emoji} {info['nome']} {info['jogo']} - {info['url']}")
    
    # Testar conectividade
    conectividade = gerenciador.testar_conectividade()
    
    # Coletar dados apenas das plataformas online
    plataformas_online = [nome for nome, online in conectividade.items() if online]
    
    if plataformas_online:
        print(f"\n🔄 Coletando dados das plataformas online...")
        dados = gerenciador.coletar_e_salvar_dados()
        
        print(f"\n📊 RESUMO DOS DADOS COLETADOS:")
        for plataforma, resultados in dados.items():
            if resultados:
                ultimo = resultados[-1]
                print(f"  🎰 {plataforma.capitalize()}: {len(resultados)} resultados")
                print(f"      Último: {ultimo['numero']} ({ultimo['cor']}) - {ultimo['timestamp']}")
    else:
        print("\n❌ Nenhuma plataforma online no momento")
    
    print(f"\n💾 Dados salvos em: {gerenciador.arquivo_dados}")

if __name__ == "__main__":
    main() 