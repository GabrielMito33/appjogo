#!/usr/bin/env python3
"""
📊 PAINEL DE ANÁLISE DE ESTRATÉGIAS
Interface interativa para filtrar e analisar as melhores estratégias
Baseado em dados reais das APIs das plataformas
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from plataformas_api import GerenciadorPlataformas
from configurador_robos import ConfiguradorRobos
from analisador_estrategias import AnalisadorEstrategias

class PainelEstrategias:
    def __init__(self):
        self.analisador = AnalisadorEstrategias()
        self.gerenciador_plataformas = GerenciadorPlataformas()
        self.configurador_robos = ConfiguradorRobos()
        
    def mostrar_menu_principal(self):
        """Mostra menu principal do painel"""
        print("\n📊 PAINEL DE ANÁLISE DE ESTRATÉGIAS")
        print("=" * 45)
        print("1. 🎯 Filtrar melhores estratégias")
        print("2. 📈 Análise por plataforma")
        print("3. 🤖 Performance por robô")
        print("4. 💡 Sugestões de novas estratégias")
        print("5. 🔄 Atualizar dados das plataformas")
        print("6. 📋 Relatório completo")
        print("7. ⚙️ Configurar robôs")
        print("8. 🚪 Sair")
    
    def filtrar_melhores_estrategias(self):
        """Interface para filtrar estratégias"""
        print("\n🎯 FILTROS DE ESTRATÉGIAS")
        print("=" * 30)
        
        # Opções de filtro
        print("📋 Critérios disponíveis:")
        print("1. Taxa de sucesso (com empates)")
        print("2. Taxa de sucesso (sem empates)")
        print("3. Quantidade de sinais")
        print("4. Frequência de sinais")
        print("5. Ver todas")
        
        try:
            opcao = int(input("\nEscolha o critério (1-5): "))
            
            criterios = {
                1: "taxa_sucesso",
                2: "taxa_sucesso_sem_empate", 
                3: "total_sinais",
                4: "frequencia_sinais",
                5: "todas"
            }
            
            if opcao not in criterios:
                print("❌ Opção inválida")
                return
            
            # Filtros adicionais
            print(f"\n🔍 FILTROS ADICIONAIS:")
            
            min_sinais = input("Mínimo de sinais (padrão 10): ").strip()
            min_sinais = int(min_sinais) if min_sinais.isdigit() else 10
            
            min_taxa = input("Taxa mínima % (padrão 60): ").strip()
            min_taxa = float(min_taxa) if min_taxa.replace('.', '').isdigit() else 60.0
            
            plataforma_filtro = input("Plataforma específica (enter para todas): ").strip().lower()
            
            if opcao == 5:
                self.mostrar_todas_estrategias(min_sinais, min_taxa, plataforma_filtro)
            else:
                criterio = criterios[opcao]
                self.mostrar_estrategias_filtradas(criterio, min_sinais, min_taxa, plataforma_filtro)
                
        except ValueError:
            print("❌ Valor inválido")
    
    def mostrar_estrategias_filtradas(self, criterio: str, min_sinais: int, min_taxa: float, plataforma_filtro: str):
        """Mostra estratégias filtradas por critério"""
        ranking = self.analisador.gerar_ranking_estrategias(criterio)
        
        # Aplicar filtros
        estrategias_filtradas = []
        for est in ranking:
            if est['total_sinais'] < min_sinais:
                continue
            if est['taxa_sucesso'] < min_taxa:
                continue
            if plataforma_filtro and plataforma_filtro not in est['plataforma']['id']:
                continue
            
            estrategias_filtradas.append(est)
        
        print(f"\n📊 ESTRATÉGIAS FILTRADAS ({len(estrategias_filtradas)}):")
        print(f"Critério: {criterio} | Min sinais: {min_sinais} | Min taxa: {min_taxa}%")
        print("-" * 80)
        
        for i, est in enumerate(estrategias_filtradas[:20], 1):  # Top 20
            estrategia = est['estrategia']
            print(f"{i:2d}. {estrategia['name']}")
            print(f"    Padrão: {estrategia['pattern']} → {estrategia['bet']}")
            print(f"    Taxa: {est['taxa_sucesso']}% | Sinais: {est['total_sinais']}")
            print(f"    Freq: {est['frequencia_sinais']}/100 | W:{est['wins']} L:{est['losses']} E:{est['empates']}")
            print(f"    Robô: {est['robo_nome']} | Plataforma: {est['plataforma']['nome']}")
            
            if est['ultimo_sinal']:
                ultimo = est['ultimo_sinal']
                print(f"    Último sinal: {ultimo['resultado']} - {ultimo['cor_apostada']} vs {ultimo['cor_resultado']}")
            
            print()
        
        if not estrategias_filtradas:
            print("📭 Nenhuma estratégia encontrada com os filtros aplicados")
        
        input("\nPressione Enter para continuar...")
    
    def mostrar_todas_estrategias(self, min_sinais: int, min_taxa: float, plataforma_filtro: str):
        """Mostra todas as estratégias organizadas"""
        melhores = self.analisador.identificar_melhores_estrategias(top_n=15)
        
        categorias = {
            'maior_taxa_sucesso': '🏆 MAIOR TAXA DE SUCESSO',
            'maior_taxa_sem_empate': '🎯 MAIOR TAXA SEM EMPATE', 
            'mais_frequentes': '⚡ MAIS FREQUENTES',
            'mais_sinais': '📊 MAIS SINAIS'
        }
        
        for categoria_key, titulo in categorias.items():
            estrategias = melhores.get(categoria_key, [])
            
            # Aplicar filtros
            estrategias_filtradas = []
            for est in estrategias:
                if est['total_sinais'] < min_sinais:
                    continue
                if est['taxa_sucesso'] < min_taxa:
                    continue
                if plataforma_filtro and plataforma_filtro not in est['plataforma']['id']:
                    continue
                estrategias_filtradas.append(est)
            
            if estrategias_filtradas:
                print(f"\n{titulo} ({len(estrategias_filtradas)}):")
                print("-" * 50)
                
                for i, est in enumerate(estrategias_filtradas[:5], 1):
                    estrategia = est['estrategia']
                    print(f"  {i}. {estrategia['name']}: {estrategia['pattern']} → {estrategia['bet']}")
                    print(f"     {est['taxa_sucesso']}% | {est['total_sinais']} sinais | {est['robo_nome']}")
        
        input("\nPressione Enter para continuar...")
    
    def analise_por_plataforma(self):
        """Análise detalhada por plataforma"""
        print("\n📈 ANÁLISE POR PLATAFORMA")
        print("=" * 30)
        
        # Listar plataformas disponíveis
        robos = self.analisador.carregar_robos_configurados()
        plataformas_ativas = list(set(r['plataforma']['id'] for r in robos if r['status'] == 'ativo'))
        
        if not plataformas_ativas:
            print("❌ Nenhuma plataforma ativa encontrada")
            return
        
        print("🎰 Plataformas ativas:")
        for i, plataforma_id in enumerate(plataformas_ativas, 1):
            print(f"{i}. {plataforma_id.upper()}")
        
        try:
            escolha = int(input(f"\nEscolha a plataforma (1-{len(plataformas_ativas)}): ")) - 1
            if not 0 <= escolha < len(plataformas_ativas):
                print("❌ Plataforma inválida")
                return
            
            plataforma_id = plataformas_ativas[escolha]
            self.mostrar_analise_plataforma_detalhada(plataforma_id)
            
        except ValueError:
            print("❌ Número inválido")
    
    def mostrar_analise_plataforma_detalhada(self, plataforma_id: str):
        """Mostra análise detalhada de uma plataforma"""
        print(f"\n🎰 ANÁLISE DETALHADA - {plataforma_id.upper()}")
        print("=" * 50)
        
        # Padrões da plataforma
        padroes = self.analisador.analisar_padroes_plataforma(plataforma_id)
        
        if not padroes:
            print("❌ Sem dados históricos para esta plataforma")
            return
        
        print(f"📊 ESTATÍSTICAS GERAIS:")
        print(f"  Total de resultados analisados: {padroes['total_resultados']}")
        
        dist = padroes['distribuicao_cores']
        print(f"  Distribuição de cores:")
        print(f"    🔴 Vermelho: {dist['vermelho']}%")
        print(f"    ⚫ Preto: {dist['preto']}%")
        print(f"    ⚪ Branco: {dist['branco']}%")
        
        print(f"  Número mais frequente: {padroes['numero_mais_frequente'][0]} ({padroes['numero_mais_frequente'][1]} vezes)")
        
        seq_max = padroes['sequencias_maximas']
        seq_med = padroes['sequencias_medias']
        print(f"  Sequências máximas: V:{seq_max['vermelho']} | P:{seq_max['preto']} | B:{seq_max['branco']}")
        print(f"  Sequências médias: V:{seq_med['vermelho']} | P:{seq_med['preto']} | B:{seq_med['branco']}")
        
        # Estratégias para esta plataforma
        robos_plataforma = [r for r in self.analisador.carregar_robos_configurados() 
                           if r['plataforma']['id'] == plataforma_id and r['status'] == 'ativo']
        
        print(f"\n🤖 ROBÔS ATIVOS NESTA PLATAFORMA ({len(robos_plataforma)}):")
        total_estrategias = 0
        
        for robo in robos_plataforma:
            analises = self.analisador.analisar_todas_estrategias_robo(robo)
            print(f"  • {robo['nome']}: {len(analises)} estratégias")
            total_estrategias += len(analises)
            
            # Mostrar melhor estratégia do robô
            if analises:
                melhor = max(analises, key=lambda x: x['taxa_sucesso'])
                est = melhor['estrategia']
                print(f"    Melhor: {est['name']} ({melhor['taxa_sucesso']}%)")
        
        # Sugestões de estratégias
        sugestoes = self.analisador.sugerir_estrategias_otimizadas(plataforma_id)
        
        if sugestoes:
            print(f"\n💡 SUGESTÕES DE ESTRATÉGIAS ({len(sugestoes)}):")
            for i, sug in enumerate(sugestoes, 1):
                print(f"  {i}. {sug['name']}: {sug['pattern']} → {sug['bet']}")
                print(f"     {sug['justificativa']}")
        
        input("\nPressione Enter para continuar...")
    
    def performance_por_robo(self):
        """Análise de performance por robô"""
        print("\n🤖 PERFORMANCE POR ROBÔ")
        print("=" * 25)
        
        robos = self.analisador.carregar_robos_configurados()
        robos_ativos = [r for r in robos if r['status'] == 'ativo']
        
        if not robos_ativos:
            print("❌ Nenhum robô ativo encontrado")
            return
        
        print("🤖 Robôs ativos:")
        for i, robo in enumerate(robos_ativos, 1):
            print(f"{i}. {robo['nome']} - {robo['plataforma']['nome']}")
        
        try:
            escolha = int(input(f"\nEscolha o robô (1-{len(robos_ativos)}): ")) - 1
            if not 0 <= escolha < len(robos_ativos):
                print("❌ Robô inválido")
                return
            
            robo = robos_ativos[escolha]
            self.mostrar_performance_robo_detalhada(robo)
            
        except ValueError:
            print("❌ Número inválido")
    
    def mostrar_performance_robo_detalhada(self, robo: Dict):
        """Mostra performance detalhada de um robô"""
        print(f"\n🤖 PERFORMANCE DETALHADA - {robo['nome']}")
        print("=" * 50)
        
        print(f"📋 INFORMAÇÕES GERAIS:")
        print(f"  Plataforma: {robo['plataforma']['nome']} {robo['plataforma']['jogo']}")
        print(f"  Status: {robo['status'].upper()}")
        print(f"  Configurações: {robo['configuracoes']['max_gales']} gales, {robo['configuracoes']['intervalo_segundos']}s")
        
        # Analisar estratégias do robô
        analises = self.analisador.analisar_todas_estrategias_robo(robo)
        
        if not analises:
            print("❌ Sem dados de análise para este robô")
            return
        
        # Estatísticas agregadas
        total_sinais = sum(a['total_sinais'] for a in analises)
        total_wins = sum(a['wins'] for a in analises)
        total_losses = sum(a['losses'] for a in analises)
        total_empates = sum(a['empates'] for a in analises)
        
        taxa_geral = ((total_wins + total_empates) / total_sinais * 100) if total_sinais > 0 else 0
        
        print(f"\n📊 ESTATÍSTICAS AGREGADAS:")
        print(f"  Total de sinais: {total_sinais}")
        print(f"  Wins: {total_wins} | Losses: {total_losses} | Empates: {total_empates}")
        print(f"  Taxa de sucesso geral: {taxa_geral:.2f}%")
        
        print(f"\n🎯 ESTRATÉGIAS INDIVIDUAIS ({len(analises)}):")
        print("-" * 70)
        
        # Ordenar por taxa de sucesso
        analises.sort(key=lambda x: x['taxa_sucesso'], reverse=True)
        
        for i, analise in enumerate(analises, 1):
            est = analise['estrategia']
            print(f"{i:2d}. {est['name']}")
            print(f"    Padrão: {est['pattern']} → {est['bet']}")
            print(f"    Performance: {analise['taxa_sucesso']}% | {analise['total_sinais']} sinais")
            print(f"    Detalhes: {analise['wins']}W {analise['losses']}L {analise['empates']}E")
            print(f"    Frequência: {analise['frequencia_sinais']}/100 rodadas")
            
            if analise['ultimo_sinal']:
                ultimo = analise['ultimo_sinal']
                print(f"    Último: {ultimo['resultado']} ({ultimo['timestamp'][:10]})")
            
            print()
        
        input("\nPressione Enter para continuar...")
    
    def atualizar_dados_plataformas(self):
        """Atualiza dados das plataformas"""
        print("\n🔄 ATUALIZANDO DADOS DAS PLATAFORMAS")
        print("=" * 40)
        
        print("🔍 Testando conectividade...")
        conectividade = self.gerenciador_plataformas.testar_conectividade()
        
        plataformas_online = [nome for nome, online in conectividade.items() if online]
        
        if not plataformas_online:
            print("❌ Nenhuma plataforma online")
            return
        
        print(f"✅ {len(plataformas_online)} plataformas online")
        
        confirmar = input("Coletar dados de todas as plataformas? (S/n): ").strip().lower()
        
        if confirmar != 'n':
            print("📊 Coletando dados...")
            dados = self.gerenciador_plataformas.coletar_e_salvar_dados()
            
            print(f"\n📈 DADOS COLETADOS:")
            for plataforma, resultados in dados.items():
                if resultados:
                    print(f"  🎰 {plataforma.capitalize()}: {len(resultados)} resultados")
                    ultimo = resultados[-1]
                    print(f"      Último: {ultimo['numero']} ({ultimo['cor']}) - {ultimo['timestamp'][:19]}")
            
            print("✅ Dados atualizados com sucesso!")
        
        input("\nPressione Enter para continuar...")
    
    def gerar_relatorio_completo(self):
        """Gera e exibe relatório completo"""
        print("\n📋 GERANDO RELATÓRIO COMPLETO")
        print("=" * 35)
        
        print("🔄 Analisando dados...")
        relatorio = self.analisador.gerar_relatorio_completo()
        
        # Mostrar resumo
        resumo = relatorio['resumo_geral']
        print(f"\n📊 RESUMO EXECUTIVO:")
        print(f"  Total de robôs: {resumo['total_robos']}")
        print(f"  Robôs ativos: {resumo['robos_ativos']}")
        print(f"  Plataformas em uso: {len(resumo['plataformas_usadas'])}")
        
        # Top estratégias
        melhores = relatorio['melhores_estrategias']
        print(f"\n🏆 TOP 3 ESTRATÉGIAS:")
        
        for i, est in enumerate(melhores['maior_taxa_sucesso'][:3], 1):
            estrategia = est['estrategia']
            print(f"  {i}. {estrategia['name']}: {est['taxa_sucesso']}%")
            print(f"     {estrategia['pattern']} → {estrategia['bet']} | {est['total_sinais']} sinais")
        
        # Salvar relatório
        relatorio_file = Path(f"relatorio_estrategias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        try:
            with open(relatorio_file, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Relatório completo salvo em: {relatorio_file}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar relatório: {e}")
        
        input("\nPressione Enter para continuar...")
    
    def executar(self):
        """Loop principal do painel"""
        while True:
            try:
                self.mostrar_menu_principal()
                opcao = input("\nEscolha uma opção: ").strip()
                
                if opcao == "1":
                    self.filtrar_melhores_estrategias()
                elif opcao == "2":
                    self.analise_por_plataforma()
                elif opcao == "3":
                    self.performance_por_robo()
                elif opcao == "4":
                    print("\n💡 Use a opção 2 (Análise por plataforma) para ver sugestões")
                    input("Pressione Enter para continuar...")
                elif opcao == "5":
                    self.atualizar_dados_plataformas()
                elif opcao == "6":
                    self.gerar_relatorio_completo()
                elif opcao == "7":
                    print("\n⚙️ Iniciando configurador de robôs...")
                    self.configurador_robos.main()
                elif opcao == "8":
                    print("👋 Até logo!")
                    break
                else:
                    print("❌ Opção inválida")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Sistema interrompido pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                input("Pressione Enter para continuar...")

def main():
    """Ponto de entrada do painel"""
    print("🚀 INICIANDO PAINEL DE ESTRATÉGIAS")
    print("=" * 40)
    
    painel = PainelEstrategias()
    painel.executar()

if __name__ == "__main__":
    main() 