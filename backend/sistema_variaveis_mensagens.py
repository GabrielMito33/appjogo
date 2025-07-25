#!/usr/bin/env python3
"""
📝 SISTEMA DE VARIÁVEIS GLOBAIS PARA MENSAGENS
Processa todas as variáveis avançadas definidas pelo usuário
Compatível com templates personalizados dos bots
"""

import re
from datetime import datetime
from typing import Dict, Any

class ProcessadorVariaveisGlobais:
    def __init__(self):
        self.stats = {
            'wins_dia': 0,
            'losses_dia': 0,
            'ganhos_consecutivos': 0,
            'ganhos_consecutivos_gale': 0,
            'ganhos_consecutivos_semgale': 0,
            'wins_sem_gale': 0,
            'wins_por_gale': {f'G{i}': 0 for i in range(1, 21)},  # G1 até G20
            'gale_atual': 0,
            'max_gales': 2,
            'nome_estrategia': '',
            'ultimo_resultado': None
        }
    
    def atualizar_estatisticas(self, resultado: str, gale_usado: int = 0, estrategia: str = ''):
        """Atualiza estatísticas baseado no resultado"""
        self.stats['nome_estrategia'] = estrategia
        self.stats['gale_atual'] = gale_usado
        
        if resultado.upper() in ['WIN', 'GREEN', 'ACERTO']:
            self.stats['wins_dia'] += 1
            self.stats['ganhos_consecutivos'] += 1
            
            if gale_usado == 0:
                self.stats['wins_sem_gale'] += 1
                self.stats['ganhos_consecutivos_semgale'] += 1
                self.stats['ganhos_consecutivos_gale'] = 0
            else:
                self.stats['ganhos_consecutivos_gale'] += 1
                self.stats['ganhos_consecutivos_semgale'] = 0
                
                # Incrementar contador do gale específico
                gale_key = f'G{gale_usado}'
                if gale_key in self.stats['wins_por_gale']:
                    self.stats['wins_por_gale'][gale_key] += 1
        
        elif resultado.upper() in ['LOSS', 'RED', 'ERRO']:
            self.stats['losses_dia'] += 1
            self.stats['ganhos_consecutivos'] = 0
            self.stats['ganhos_consecutivos_gale'] = 0
            self.stats['ganhos_consecutivos_semgale'] = 0
        
        self.stats['ultimo_resultado'] = resultado
    
    def calcular_percentual_assertividade(self) -> float:
        """Calcula percentual de assertividade do dia"""
        total = self.stats['wins_dia'] + self.stats['losses_dia']
        if total == 0:
            return 0.0
        return (self.stats['wins_dia'] / total) * 100
    
    def obter_tipo_green_minusculo(self, gale_usado: int = None) -> str:
        """Retorna texto do tipo de green em minúsculo"""
        if gale_usado is None:
            gale_usado = self.stats['gale_atual']
        
        if gale_usado == 0:
            return "de primeira"
        else:
            return f"com {gale_usado} gale{'s' if gale_usado > 1 else ''}"
    
    def obter_tipo_green_maiusculo(self, gale_usado: int = None) -> str:
        """Retorna texto do tipo de green em maiúsculo"""
        return self.obter_tipo_green_minusculo(gale_usado).upper()
    
    def processar_formatacao_especial(self, texto: str) -> str:
        """Processa formatações especiais como [N]texto[/N] e [url=]"""
        
        # Processar negrito [N]texto[/N] -> **texto**
        texto = re.sub(r'\[N\](.*?)\[/N\]', r'**\1**', texto)
        
        # Processar links [url=https://example.com]Texto[/url] -> [Texto](https://example.com)
        texto = re.sub(r'\[url=(.*?)\](.*?)\[/url\]', r'[\2](\1)', texto)
        
        return texto
    
    def processar_todas_variaveis(self, template: str, **kwargs) -> str:
        """Processa todas as variáveis globais no template"""
        
        # Dados de data/hora
        agora = datetime.now()
        data_hoje = agora.strftime("%d/%m/%Y")
        hora_agora = agora.strftime("%H:%M:%S")
        
        # Estatísticas
        percentual = self.calcular_percentual_assertividade()
        
        # Mapeamento de todas as variáveis
        variaveis = {
            # Data e hora
            '[DATA_HOJE]': data_hoje,
            '[HORA_AGORA]': hora_agora,
            
            # Estatísticas básicas
            '[WINS]': str(self.stats['wins_dia']),
            '[LOSSES]': str(self.stats['losses_dia']),
            '[PERCENTUAL_ASSERTIVIDADE]': f"{percentual:.1f}",
            
            # Gales
            '[GALE_ATUAL]': str(self.stats['gale_atual']),
            '[MAX_GALES]': str(self.stats['max_gales']),
            
            # Ganhos consecutivos
            '[GANHOS_CONSECUTIVOS]': str(self.stats['ganhos_consecutivos']),
            '[GANHOS_CONSECUTIVOS_GALE]': str(self.stats['ganhos_consecutivos_gale']),
            '[GANHOS_CONSECUTIVOS_SEMGALE]': str(self.stats['ganhos_consecutivos_semgale']),
            
            # Wins específicos
            '[SG]': str(self.stats['wins_sem_gale']),
            
            # Tipos de green
            '[TIPO_GREEN_MINUSCULO]': self.obter_tipo_green_minusculo(),
            '[TIPO_GREEN_MAIUSCULO]': self.obter_tipo_green_maiusculo(),
            
            # Nome da estratégia
            '[NOME_ESTRATEGIA]': self.stats['nome_estrategia'],
        }
        
        # Adicionar G1 até G20
        for i in range(1, 21):
            gale_key = f'G{i}'
            variaveis[f'[{gale_key}]'] = str(self.stats['wins_por_gale'][gale_key])
        
        # Substituir todas as variáveis
        texto_processado = template
        for variavel, valor in variaveis.items():
            texto_processado = texto_processado.replace(variavel, valor)
        
        # Processar variáveis extras passadas como parâmetro
        for key, value in kwargs.items():
            placeholder = f'{{{key}}}'
            if placeholder in texto_processado:
                texto_processado = texto_processado.replace(placeholder, str(value))
        
        # Processar formatações especiais por último
        texto_processado = self.processar_formatacao_especial(texto_processado)
        
        return texto_processado
    
    def resetar_estatisticas_diarias(self):
        """Reseta estatísticas diárias (chamar a cada novo dia)"""
        self.stats.update({
            'wins_dia': 0,
            'losses_dia': 0,
            'ganhos_consecutivos': 0,
            'ganhos_consecutivos_gale': 0,
            'ganhos_consecutivos_semgale': 0,
            'wins_sem_gale': 0,
            'wins_por_gale': {f'G{i}': 0 for i in range(1, 21)},
            'gale_atual': 0
        })
    
    def obter_resumo_estatisticas(self) -> Dict[str, Any]:
        """Retorna resumo das estatísticas atuais"""
        return {
            'wins_dia': self.stats['wins_dia'],
            'losses_dia': self.stats['losses_dia'],
            'percentual_assertividade': self.calcular_percentual_assertividade(),
            'ganhos_consecutivos': self.stats['ganhos_consecutivos'],
            'wins_sem_gale': self.stats['wins_sem_gale'],
            'wins_com_gale': sum(self.stats['wins_por_gale'].values()),
            'gale_atual': self.stats['gale_atual'],
            'max_gales': self.stats['max_gales']
        }

def criar_template_exemplo():
    """Cria exemplos de templates com as novas variáveis"""
    
    templates_exemplo = {
        'sinal_avancado': """🎯 [N]SINAL DETECTADO[/N] 🔥

📋 **Estratégia**: [NOME_ESTRATEGIA]
🎰 **Apostar**: {cor_emoji} **{cor_nome}**
🛡️ **Proteção**: ⚪ BRANCO
🔄 **Gales**: Até [MAX_GALES]x

📊 **Estatísticas de Hoje**:
• ✅ Wins: [WINS] | ❌ Losses: [LOSSES]
• 📈 Assertividade: [PERCENTUAL_ASSERTIVIDADE]%
• 🔥 Consecutivos: [GANHOS_CONSECUTIVOS]
• 🎯 Sem Gale: [SG] | 🎲 Com Gale: [G1]

📅 **[DATA_HOJE]** | ⏰ **[HORA_AGORA]**

[url=https://blaze.bet]🚀 ENTRAR NA BLAZE[/url]""",

        'resultado_win': """✅ [N]GREEN[/N] - [TIPO_GREEN_MAIUSCULO]! 🎉

🎯 **Estratégia**: [NOME_ESTRATEGIA]
🔥 **Resultado**: GREEN [TIPO_GREEN_MINUSCULO]
💰 **Sequência**: [GANHOS_CONSECUTIVOS] wins seguidos

📊 **Hoje**:
• Wins: [WINS] | Losses: [LOSSES]
• Assertividade: [PERCENTUAL_ASSERTIVIDADE]%
• Sem Gale: [SG] | G1: [G1] | G2: [G2]

⏰ [HORA_AGORA] | 💪 [N]VAMOS CONTINUAR![/N]""",

        'resultado_loss': """❌ [N]RED[/N] - Não foi dessa vez 😔

🎯 **Estratégia**: [NOME_ESTRATEGIA]
🔴 **Resultado**: LOSS após [GALE_ATUAL] gale(s)
📊 **Resetando sequência**...

📈 **Estatísticas do Dia**:
• Wins: [WINS] | Losses: [LOSSES]
• Assertividade: [PERCENTUAL_ASSERTIVIDADE]%
• Último Green: [TIPO_GREEN_MINUSCULO]

⏰ [HORA_AGORA] | 🚀 [N]PRÓXIMO SINAL EM BREVE![/N]""",

        'relatorio_diario': """📊 [N]RELATÓRIO DIÁRIO[/N] - [DATA_HOJE]

🎯 **Performance Geral**:
• ✅ Wins: [WINS]
• ❌ Losses: [LOSSES]  
• 📈 Assertividade: [PERCENTUAL_ASSERTIVIDADE]%

🎲 **Detalhamento de Gales**:
• 🎯 Sem Gale: [SG]
• 🎲 G1: [G1] | G2: [G2] | G3: [G3]
• 🔥 Melhor Sequência: [GANHOS_CONSECUTIVOS]

📅 [DATA_HOJE] | ⏰ [HORA_AGORA]

[url=https://t.me/seucanalvip]💎 CANAL VIP[/url]"""
    }
    
    return templates_exemplo

def main():
    """Demonstração do sistema de variáveis"""
    print("📝 SISTEMA DE VARIÁVEIS GLOBAIS PARA MENSAGENS")
    print("=" * 55)
    
    # Criar processador
    processador = ProcessadorVariaveisGlobais()
    
    # Simular algumas estatísticas
    processador.stats['max_gales'] = 2
    processador.atualizar_estatisticas('WIN', 0, 'V-V=P')  # Win sem gale
    processador.atualizar_estatisticas('WIN', 1, 'P-P=V')  # Win com 1 gale
    processador.atualizar_estatisticas('LOSS', 2, 'V-V-P=V')  # Loss após 2 gales
    processador.atualizar_estatisticas('WIN', 0, 'X-V-V=P')  # Win sem gale
    
    # Criar templates de exemplo
    templates = criar_template_exemplo()
    
    print("\n🎯 VARIÁVEIS DISPONÍVEIS:")
    print("-" * 30)
    variaveis_disponiveis = [
        "[DATA_HOJE] - Data atual",
        "[HORA_AGORA] - Horário atual", 
        "[WINS] - Wins do dia",
        "[LOSSES] - Losses do dia",
        "[PERCENTUAL_ASSERTIVIDADE] - % de acerto",
        "[GALE_ATUAL] - Gale atual",
        "[MAX_GALES] - Máximo de gales",
        "[GANHOS_CONSECUTIVOS] - Wins seguidos",
        "[SG] - Wins sem gale",
        "[G1] até [G20] - Wins por gale específico",
        "[TIPO_GREEN_MINUSCULO] - Tipo do green",
        "[NOME_ESTRATEGIA] - Nome da estratégia",
        "[N]texto[/N] - Negrito",
        "[url=link]texto[/url] - Link"
    ]
    
    for var in variaveis_disponiveis:
        print(f"  • {var}")
    
    print(f"\n📊 ESTATÍSTICAS ATUAIS:")
    stats = processador.obter_resumo_estatisticas()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    print(f"\n🎯 EXEMPLO DE TEMPLATE PROCESSADO:")
    print("-" * 40)
    
    template_exemplo = templates['sinal_avancado']
    resultado = processador.processar_todas_variaveis(
        template_exemplo,
        cor_emoji="🔴",
        cor_nome="VERMELHO"
    )
    
    print(resultado)
    
    print(f"\n📝 TEMPLATES DISPONÍVEIS:")
    for nome, template in templates.items():
        print(f"  • {nome}")

if __name__ == "__main__":
    main() 