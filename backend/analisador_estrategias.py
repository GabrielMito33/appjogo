#!/usr/bin/env python3
"""
📊 ANALISADOR DE ESTRATÉGIAS AVANÇADO
Analisa performance de estratégias usando dados históricos das plataformas
Calcula parciais, eficiência e sugere melhores estratégias
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class AnalisadorEstrategias:
    def __init__(self):
        self.dados_file = Path("dados_plataformas.json")
        self.robos_file = Path("robos_configurados.json")
        self.resultados_cache = {}
    
    def carregar_dados_historicos(self) -> Dict[str, List[Dict]]:
        """Carrega dados históricos das plataformas"""
        if not self.dados_file.exists():
            return {}
        
        try:
            with open(self.dados_file, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            return dados.get('plataformas', {})
        except Exception as e:
            print(f"❌ Erro ao carregar dados: {e}")
            return {}
    
    def carregar_robos_configurados(self) -> List[Dict]:
        """Carrega robôs configurados"""
        if not self.robos_file.exists():
            return []
        
        try:
            with open(self.robos_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config.get('robos', [])
        except Exception as e:
            print(f"❌ Erro ao carregar robôs: {e}")
            return []
    
    def converter_pattern_para_condicoes(self, pattern: str) -> List[str]:
        """Converte pattern de estratégia para lista de condições"""
        return pattern.split('-')
    
    def verificar_match_estrategia(self, condicoes: List[str], resultados: List[Dict]) -> bool:
        """Verifica se uma estratégia faz match com os resultados"""
        if len(condicoes) > len(resultados):
            return False
        
        for i, condicao in enumerate(condicoes):
            # A primeira condição corresponde ao resultado mais antigo
            posicao = len(condicoes) - 1 - i
            resultado = resultados[posicao]
            
            numero = resultado['numero']
            cor = resultado['cor']
            
            # Verificar match
            if condicao == "X":  # Wildcard
                continue
            elif condicao == str(numero):  # Match por número
                continue
            elif condicao == cor:  # Match por cor
                continue
            else:
                return False
        
        return True
    
    def analisar_estrategia_historica(self, estrategia: Dict, dados_plataforma: List[Dict], 
                                    janela_analise: int = 500) -> Dict[str, Any]:
        """Analisa performance histórica de uma estratégia"""
        pattern = estrategia['pattern']
        bet_direction = estrategia['bet']
        condicoes = self.converter_pattern_para_condicoes(pattern)
        
        # Usar apenas os últimos N resultados
        dados_recentes = dados_plataforma[-janela_analise:]
        
        sinais_encontrados = []
        resultados_sinais = []
        
        # Procurar por matches da estratégia
        for i in range(len(condicoes), len(dados_recentes)):
            segmento = dados_recentes[i-len(condicoes):i]
            
            if self.verificar_match_estrategia(condicoes, segmento):
                # Estratégia detectada, verificar resultado da aposta
                proximo_resultado = dados_recentes[i] if i < len(dados_recentes) else None
                
                if proximo_resultado:
                    cor_apostada = bet_direction
                    cor_resultado = proximo_resultado['cor']
                    
                    # Determinar resultado
                    if cor_resultado == cor_apostada:
                        resultado = "WIN"
                    elif cor_resultado == "B":  # Branco é proteção
                        resultado = "EMPATE"
                    else:
                        resultado = "LOSS"
                    
                    sinais_encontrados.append({
                        'timestamp': proximo_resultado['timestamp'],
                        'numero_resultado': proximo_resultado['numero'],
                        'cor_resultado': cor_resultado,
                        'cor_apostada': cor_apostada,
                        'resultado': resultado,
                        'posicao': i
                    })
                    
                    resultados_sinais.append(resultado)
        
        # Calcular estatísticas
        total_sinais = len(resultados_sinais)
        
        if total_sinais == 0:
            return {
                'estrategia': estrategia,
                'total_sinais': 0,
                'wins': 0,
                'losses': 0,
                'empates': 0,
                'taxa_sucesso': 0,
                'taxa_sucesso_sem_empate': 0,
                'frequencia_sinais': 0,
                'ultimo_sinal': None,
                'sinais_detalhados': []
            }
        
        wins = resultados_sinais.count("WIN")
        losses = resultados_sinais.count("LOSS")
        empates = resultados_sinais.count("EMPATE")
        
        # Taxa de sucesso (considerando empate como não-loss)
        taxa_sucesso = ((wins + empates) / total_sinais) * 100
        
        # Taxa de sucesso sem empates
        total_sem_empate = wins + losses
        taxa_sucesso_sem_empate = (wins / total_sem_empate * 100) if total_sem_empate > 0 else 0
        
        # Frequência de sinais (sinais por 100 rodadas)
        frequencia_sinais = (total_sinais / janela_analise) * 100
        
        return {
            'estrategia': estrategia,
            'total_sinais': total_sinais,
            'wins': wins,
            'losses': losses,
            'empates': empates,
            'taxa_sucesso': round(taxa_sucesso, 2),
            'taxa_sucesso_sem_empate': round(taxa_sucesso_sem_empate, 2),
            'frequencia_sinais': round(frequencia_sinais, 2),
            'ultimo_sinal': sinais_encontrados[-1] if sinais_encontrados else None,
            'sinais_detalhados': sinais_encontrados[-10:],  # Últimos 10 sinais
            'janela_analise': janela_analise
        }
    
    def analisar_todas_estrategias_robo(self, robo: Dict, janela_analise: int = 500) -> List[Dict]:
        """Analisa todas as estratégias de um robô"""
        plataforma_id = robo['plataforma']['id']
        dados_historicos = self.carregar_dados_historicos()
        
        if plataforma_id not in dados_historicos:
            return []
        
        dados_plataforma = dados_historicos[plataforma_id]
        resultados = []
        
        for estrategia in robo.get('estrategias', []):
            analise = self.analisar_estrategia_historica(estrategia, dados_plataforma, janela_analise)
            analise['robo_nome'] = robo['nome']
            analise['plataforma'] = robo['plataforma']
            resultados.append(analise)
        
        return resultados
    
    def gerar_ranking_estrategias(self, criterio: str = "taxa_sucesso") -> List[Dict]:
        """Gera ranking de estratégias baseado em critério"""
        robos = self.carregar_robos_configurados()
        todas_analises = []
        
        for robo in robos:
            if robo['status'] == 'ativo':
                analises_robo = self.analisar_todas_estrategias_robo(robo)
                todas_analises.extend(analises_robo)
        
        # Filtrar estratégias com sinais suficientes
        estrategias_validas = [a for a in todas_analises if a['total_sinais'] >= 10]
        
        # Ordenar por critério
        if criterio == "taxa_sucesso":
            estrategias_validas.sort(key=lambda x: x['taxa_sucesso'], reverse=True)
        elif criterio == "taxa_sucesso_sem_empate":
            estrategias_validas.sort(key=lambda x: x['taxa_sucesso_sem_empate'], reverse=True)
        elif criterio == "total_sinais":
            estrategias_validas.sort(key=lambda x: x['total_sinais'], reverse=True)
        elif criterio == "frequencia":
            estrategias_validas.sort(key=lambda x: x['frequencia_sinais'], reverse=True)
        
        return estrategias_validas
    
    def identificar_melhores_estrategias(self, top_n: int = 10) -> Dict[str, List[Dict]]:
        """Identifica as melhores estratégias por diferentes critérios"""
        return {
            'maior_taxa_sucesso': self.gerar_ranking_estrategias("taxa_sucesso")[:top_n],
            'maior_taxa_sem_empate': self.gerar_ranking_estrategias("taxa_sucesso_sem_empate")[:top_n],
            'mais_frequentes': self.gerar_ranking_estrategias("frequencia")[:top_n],
            'mais_sinais': self.gerar_ranking_estrategias("total_sinais")[:top_n]
        }
    
    def analisar_padroes_plataforma(self, plataforma_id: str, ultimos_n: int = 1000) -> Dict[str, Any]:
        """Analisa padrões gerais de uma plataforma"""
        dados_historicos = self.carregar_dados_historicos()
        
        if plataforma_id not in dados_historicos:
            return {}
        
        dados = dados_historicos[plataforma_id][-ultimos_n:]
        
        # Distribuição de cores
        cores_count = defaultdict(int)
        numeros_count = defaultdict(int)
        
        for resultado in dados:
            cores_count[resultado['cor']] += 1
            numeros_count[resultado['numero']] += 1
        
        total_resultados = len(dados)
        
        # Sequências
        sequencias_v = self.contar_sequencias_cor(dados, 'V')
        sequencias_p = self.contar_sequencias_cor(dados, 'P')
        sequencias_b = self.contar_sequencias_cor(dados, 'B')
        
        return {
            'plataforma': plataforma_id,
            'total_resultados': total_resultados,
            'distribuicao_cores': {
                'vermelho': round((cores_count['V'] / total_resultados) * 100, 2),
                'preto': round((cores_count['P'] / total_resultados) * 100, 2),
                'branco': round((cores_count['B'] / total_resultados) * 100, 2)
            },
            'numero_mais_frequente': max(numeros_count.items(), key=lambda x: x[1]),
            'sequencias_maximas': {
                'vermelho': max(sequencias_v) if sequencias_v else 0,
                'preto': max(sequencias_p) if sequencias_p else 0,
                'branco': max(sequencias_b) if sequencias_b else 0
            },
            'sequencias_medias': {
                'vermelho': round(statistics.mean(sequencias_v), 2) if sequencias_v else 0,
                'preto': round(statistics.mean(sequencias_p), 2) if sequencias_p else 0,
                'branco': round(statistics.mean(sequencias_b), 2) if sequencias_b else 0
            }
        }
    
    def contar_sequencias_cor(self, dados: List[Dict], cor: str) -> List[int]:
        """Conta sequências consecutivas de uma cor"""
        sequencias = []
        sequencia_atual = 0
        
        for resultado in dados:
            if resultado['cor'] == cor:
                sequencia_atual += 1
            else:
                if sequencia_atual > 0:
                    sequencias.append(sequencia_atual)
                    sequencia_atual = 0
        
        # Adicionar última sequência se terminar com a cor
        if sequencia_atual > 0:
            sequencias.append(sequencia_atual)
        
        return sequencias
    
    def sugerir_estrategias_otimizadas(self, plataforma_id: str) -> List[Dict]:
        """Sugere estratégias otimizadas baseadas nos padrões da plataforma"""
        padroes = self.analisar_padroes_plataforma(plataforma_id)
        
        if not padroes:
            return []
        
        sugestoes = []
        
        # Baseado na distribuição de cores
        dist_cores = padroes['distribuicao_cores']
        
        # Se vermelho é mais frequente, sugerir apostar contra
        if dist_cores['vermelho'] > 40:
            sugestoes.append({
                'pattern': 'V-V',
                'bet': 'P',
                'name': 'Anti-Vermelho Duplo',
                'justificativa': f"Vermelho aparece {dist_cores['vermelho']}% das vezes"
            })
        
        # Se preto é mais frequente
        if dist_cores['preto'] > 40:
            sugestoes.append({
                'pattern': 'P-P',
                'bet': 'V',
                'name': 'Anti-Preto Duplo',
                'justificativa': f"Preto aparece {dist_cores['preto']}% das vezes"
            })
        
        # Baseado em sequências máximas
        seq_max = padroes['sequencias_maximas']
        
        if seq_max['vermelho'] >= 4:
            sugestoes.append({
                'pattern': 'V-V-V',
                'bet': 'P',
                'name': 'Break Sequência Vermelha',
                'justificativa': f"Sequência máxima de vermelhos: {seq_max['vermelho']}"
            })
        
        if seq_max['preto'] >= 4:
            sugestoes.append({
                'pattern': 'P-P-P',
                'bet': 'V',
                'name': 'Break Sequência Preta',
                'justificativa': f"Sequência máxima de pretos: {seq_max['preto']}"
            })
        
        # Estratégias com branco se for frequente
        if dist_cores['branco'] < 5:  # Se branco é raro
            sugestoes.append({
                'pattern': 'V-P',
                'bet': 'V',
                'name': 'Alternância Simples',
                'justificativa': f"Branco raro ({dist_cores['branco']}%), focar em V/P"
            })
        
        return sugestoes
    
    def gerar_relatorio_completo(self) -> Dict[str, Any]:
        """Gera relatório completo de análise"""
        robos = self.carregar_robos_configurados()
        robos_ativos = [r for r in robos if r['status'] == 'ativo']
        
        relatorio = {
            'timestamp': datetime.now().isoformat(),
            'resumo_geral': {
                'total_robos': len(robos),
                'robos_ativos': len(robos_ativos),
                'plataformas_usadas': list(set(r['plataforma']['id'] for r in robos_ativos))
            },
            'melhores_estrategias': self.identificar_melhores_estrategias(),
            'analise_por_plataforma': {},
            'sugestoes_por_plataforma': {}
        }
        
        # Analisar cada plataforma
        for plataforma_id in relatorio['resumo_geral']['plataformas_usadas']:
            relatorio['analise_por_plataforma'][plataforma_id] = self.analisar_padroes_plataforma(plataforma_id)
            relatorio['sugestoes_por_plataforma'][plataforma_id] = self.sugerir_estrategias_otimizadas(plataforma_id)
        
        return relatorio

def main():
    """Demonstração do analisador de estratégias"""
    print("📊 ANALISADOR DE ESTRATÉGIAS AVANÇADO")
    print("=" * 45)
    
    analisador = AnalisadorEstrategias()
    
    print("\n🔄 Gerando relatório completo...")
    relatorio = analisador.gerar_relatorio_completo()
    
    print(f"\n📋 RESUMO GERAL:")
    resumo = relatorio['resumo_geral']
    print(f"  🤖 Robôs: {resumo['total_robos']} total, {resumo['robos_ativos']} ativos")
    print(f"  🎰 Plataformas: {len(resumo['plataformas_usadas'])}")
    
    # Mostrar melhores estratégias
    melhores = relatorio['melhores_estrategias']
    
    print(f"\n🏆 TOP 5 ESTRATÉGIAS POR TAXA DE SUCESSO:")
    for i, estrategia in enumerate(melhores['maior_taxa_sucesso'][:5], 1):
        est = estrategia['estrategia']
        print(f"  {i}. {est['name']}: {est['pattern']} → {est['bet']}")
        print(f"     Taxa: {estrategia['taxa_sucesso']}% | Sinais: {estrategia['total_sinais']}")
        print(f"     Robô: {estrategia['robo_nome']} ({estrategia['plataforma']['nome']})")
    
    # Análise por plataforma
    print(f"\n🎰 ANÁLISE POR PLATAFORMA:")
    for plataforma_id, analise in relatorio['analise_por_plataforma'].items():
        print(f"\n  📊 {plataforma_id.upper()}:")
        dist = analise['distribuicao_cores']
        print(f"    Distribuição: 🔴{dist['vermelho']}% | ⚫{dist['preto']}% | ⚪{dist['branco']}%")
        
        seq = analise['sequencias_maximas']
        print(f"    Seq. Máximas: V:{seq['vermelho']} | P:{seq['preto']} | B:{seq['branco']}")
    
    # Sugestões
    print(f"\n💡 SUGESTÕES DE ESTRATÉGIAS:")
    for plataforma_id, sugestoes in relatorio['sugestoes_por_plataforma'].items():
        if sugestoes:
            print(f"\n  🎯 Para {plataforma_id.upper()}:")
            for sug in sugestoes[:3]:
                print(f"    • {sug['name']}: {sug['pattern']} → {sug['bet']}")
                print(f"      {sug['justificativa']}")
    
    # Salvar relatório
    relatorio_file = Path("relatorio_estrategias.json")
    with open(relatorio_file, 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório completo salvo em: {relatorio_file}")

if __name__ == "__main__":
    main() 