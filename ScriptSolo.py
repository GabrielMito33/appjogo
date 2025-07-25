import datetime
import requests
import telebot
import pwinput
import time
import json
import csv

class WebScraper:
    
    def __init__(self):
        self.game = "Blaze Double"
        self.token = "8106969377:AAHp4PRKZN-RHb1GxR3C3l7PzikFHEcRsck" # config
        self.chat_id = "-1002852101467" # config
        self.url_API = "https://blaze.bet.br/api/singleplayer-originals/originals/roulette_games/recent/1"
        self.link = "[Clique aqui!](blaze.com/r/0aJYR6)"
        self.protection = True
        self.gales = 1
        self.win_results = 0
        self.branco_results = 0
        self.loss_results = 0
        self.max_hate = 0
        self.win_hate = 0
        self.count = 0
        self.analisar = True
        self.direction_color = "None"
        self.message_delete = False
        self.bot = telebot.TeleBot(token=self.token, parse_mode="MARKDOWN", disable_web_page_preview=True)
        self.date_now = str(datetime.datetime.now().strftime("%d/%m/%Y"))
        self.check_date = self.date_now
  
    def restart(self):
        if self.date_now != self.check_date:
            print("Reiniciando bot!")
            self.check_date = self.date_now

            self.bot.send_sticker(
                self.chat_id,
                sticker="CAACAgEAAxkBAAEBbJJjXNcB92-_4vp2v0B3Plp9FONrDwACvgEAAsFWwUVjxQN4wmmSBCoE",
            )
            self.results()

            # ZERA OS RESULTADOS
            self.win_results = 0
            self.loss_results = 0
            self.branco_results = 0
            self.max_hate = 0
            self.win_hate = 0
            time.sleep(10)

            self.bot.send_sticker(
                self.chat_id,
                sticker="CAACAgEAAxkBAAEBPQZi-ziImRgbjqbDkPduogMKzv0zFgACbAQAAl4ByUUIjW-sdJsr6CkE",
            )
            self.results()
            return True
        else:
            return False

    def results(self):
        if self.win_results + self.branco_results + self.loss_results != 0:
            a = (
                100
                / (self.win_results + self.branco_results + self.loss_results)
                * (self.win_results + self.branco_results)
            )
        else:
            a = 0
        self.win_hate = f"{a:,.2f}%"

        self.bot.send_message(chat_id=self.chat_id,text=(f"""

► PLACAR = ✅{self.win_results} | ⚪️{self.branco_results} | 🚫{self.loss_results} 
► Consecutivas = {self.max_hate}
► Assertividade = {self.win_hate}
    
    """))
        return

    def alert_sinal(self):
        message_id = self.bot.send_message(
            self.chat_id,
            text="""
⚠️ ANALISANDO, FIQUE ATENTO!!!
""",
        ).message_id
        self.message_ids = message_id
        self.message_delete = True
        return

    def alert_gale(self):
        self.message_ids = self.bot.send_message(
            self.chat_id, text=f"""⚠️ Vamos para o {self.count}ª GALE""").message_id

        self.message_delete = True
        return

    def delete(self):
        if self.message_delete == True:
            self.bot.delete_message(chat_id=self.chat_id, message_id=self.message_ids)
            self.message_delete = False

    def send_sinal(self):
        self.analisar = False
        self.bot.send_message(chat_id=self.chat_id,text=(f"""
🎲 - Modo: Double Blaze
🎰 - Entrada será para: {self.direction_color}
💰 - Com proteção no: ⚪️
♻️ - Utilize até o Gale: {self.gales} 
"""))
        
        return

    def martingale(self, result):
        if result == "WIN":
            print(f"WIN")
            self.win_results += 1
            self.max_hate += 1
            self.bot.send_sticker(self.chat_id, sticker='CAACAgEAAxkBAAMPZrqPFR0VdwEGmMIhUvD-ftVCU9IAAm8CAAIhWPBGBpXDpqXsW8Q1BA')

        elif result == "LOSS":
            self.count += 1

            if self.count > self.gales:
                print(f"LOSS")
                self.loss_results += 1
                self.max_hate = 0
                self.bot.send_sticker(self.chat_id, sticker='CAACAgEAAxkBAAMTZrqPNtuE01MlUnK6yF68sSO6lc0AAsQCAAIEQehG-NlOMcjRGTM1BA')

            else:
                print(f"Vamos para o {self.count}ª gale!")
                self.alert_gale()
                return

        elif result == "BRANCO":
            print(f"BRANCO")
            self.branco_results += 1
            self.max_hate += 1
            self.bot.send_sticker(self.chat_id, sticker='CAACAgEAAxkBAAMRZrqPJkaflJxOqn_wTYTupKMtpDkAAjYCAAJMK-lGHp_XWq_MVE01BA')

        self.count = 0
        self.analisar = True
        self.results()
        self.restart()
        return

    def check_results(self, results):
        if results == "B" and self.protection == True:
            self.martingale("BRANCO")
            return
        elif results == "B" and self.protection == False:
            self.martingale("LOSS")
            return

        if results == "B" and self.direction_color == "⚪️":
            self.martingale("EMPATE")
            return

        elif results != "B" and self.direction_color == "⚪️":
            self.martingale("LOSS")
            return

        if results == "V" and self.direction_color == "🔴":
            self.martingale("WIN")
            return
        elif results == "V" and self.direction_color == "⚫️":
            self.martingale("LOSS")
            return

        if results == "P" and self.direction_color == "⚫️":
            self.martingale("WIN")
            return
        elif results == "P" and self.direction_color == "🔴":
            self.martingale("LOSS")
            return

    def start(self):
        check = []
        while True:
            try:
                self.date_now = str(datetime.datetime.now().strftime("%d/%m/%Y"))

                results = []
                time.sleep(1)

                response = requests.get(self.url_API)
                json_data = json.loads(response.text)

                for i in json_data:
                    results.append(i['roll'])

                if check != results:
                    check = results
                    self.delete()
                    self.estrategy(results)

            except Exception as e:
                print("ERROR - 404!", e)
                continue

    def estrategy(self, results):
        finalnum = results
        finalcor = []

        # Converter números em cores conforme regras da Blaze
        for i in results:
            if i >= 1 and i <= 7:
                finalcor.append("V")  # Vermelho
            elif i >= 8 and i <= 14:
                finalcor.append("P")  # Preto
            else:
                finalcor.append("B")  # Branco

        print(f"Números recentes: {finalnum[0:10]}")
        print(f"Cores recentes: {finalcor[0:10]}")

        if self.analisar == False:
            self.check_results(finalcor[0])
            return

        # ESTRATÉGIAS COM BASE NO CSV - LÓGICA CORRIGIDA
        elif self.analisar == True:
            with open("_blaze_estrategyG1VIP-Cpro.csv", newline="") as f:
                reader = csv.reader(f)

                for row in reader:
                    estrategia_completa = str(row[0]).strip()
                    
                    # Dividir estratégia em condições e aposta
                    if "=" not in estrategia_completa:
                        continue
                        
                    condicoes_str, aposta_str = estrategia_completa.split("=")
                    condicoes = condicoes_str.split("-")
                    
                    print(f"\n--- Analisando estratégia: {estrategia_completa} ---")
                    print(f"Condições: {condicoes} | Aposta: {aposta_str}")
                    
                    # Verificar se temos dados suficientes
                    if len(condicoes) > len(finalnum):
                        print(f"❌ Dados insuficientes: precisa de {len(condicoes)} resultados, temos {len(finalnum)}")
                        continue
                    
                    # LÓGICA CORRIGIDA FINAL: 
                    # "1-P=P" significa: primeiro sai 1, depois sai P, então aposta P
                    # Ordem temporal: condicoes[0] é mais antigo, condicoes[-1] é mais recente
                    match = True
                    
                    for i, condicao in enumerate(condicoes):
                        # A condição i corresponde à posição (len(condicoes)-1-i) no histórico
                        # Exemplo: condicoes = ["1", "P"] 
                        # condicoes[0]="1" verifica posicao_historico=1 (mais antigo)
                        # condicoes[1]="P" verifica posicao_historico=0 (mais recente)
                        posicao_historico = len(condicoes) - 1 - i
                        
                        numero_nesta_posicao = str(finalnum[posicao_historico])
                        cor_nesta_posicao = finalcor[posicao_historico]
                        
                        print(f"  Condição {i+1}: '{condicao}' | Posição {posicao_historico} | Número: {numero_nesta_posicao} | Cor: {cor_nesta_posicao}")
                        
                        # Verificar se a condição é atendida
                        if condicao == "X":  # X = qualquer valor (wildcard)
                            print(f"    ✓ Wildcard aceito")
                            continue
                        elif condicao == numero_nesta_posicao:  # Comparar com número
                            print(f"    ✓ Número match: {condicao} == {numero_nesta_posicao}")
                            continue
                        elif condicao == cor_nesta_posicao:  # Comparar com cor
                            print(f"    ✓ Cor match: {condicao} == {cor_nesta_posicao}")
                            continue
                        else:
                            print(f"    ❌ Sem match: {condicao} != {numero_nesta_posicao} e != {cor_nesta_posicao}")
                            match = False
                            break
                    
                    # Se todas as condições foram atendidas, enviar sinal
                    if match:
                        print(f"🎯 SINAL ENCONTRADO! Estratégia: {estrategia_completa}")
                        
                        # Definir cor da aposta
                        if aposta_str == "P":
                            self.direction_color = "⚫️"  # Preto
                        elif aposta_str == "V":
                            self.direction_color = "🔴"  # Vermelho
                        elif aposta_str == "B":
                            self.direction_color = "⚪️"  # Branco
                        
                        print(f"Direção da aposta: {self.direction_color}")
                        self.send_sinal()
                        return
                    
                    # Verificar alerta (condições parciais - remover última condição)
                    if len(condicoes) > 1:
                        condicoes_alerta = condicoes[:-1]  # Remove a última condição (mais recente)
                        alerta_match = True
                        
                        print(f"  Verificando alerta com: {condicoes_alerta}")
                        
                        for i, condicao in enumerate(condicoes_alerta):
                            posicao_historico = len(condicoes_alerta) - 1 - i
                            
                            numero_nesta_posicao = str(finalnum[posicao_historico])
                            cor_nesta_posicao = finalcor[posicao_historico]
                            
                            if condicao == "X":
                                continue
                            elif condicao == numero_nesta_posicao or condicao == cor_nesta_posicao:
                                continue
                            else:
                                alerta_match = False
                                break
                        
                        if alerta_match:
                            print(f"⚠️ ALERTA: Próximo resultado pode ativar estratégia {estrategia_completa}")
                            self.alert_sinal()
                            return



scraper = WebScraper()
scraper.start()