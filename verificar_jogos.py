import os
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- CONFIGURAÇÕES ---
URL_API = "https://service.ig.com.br/football_ig/ao-vivo"

# Lista de campeonatos para monitorar
CAMPEONATOS_FEMININOS = [
    "Campeonato Paulista Feminino",
    "Copa Libertadores da América Feminina",
    "Copa do Brasil Feminina",
    "Campeonato Brasileiro Feminino"
]

# Lendo as credenciais dos Secrets do GitHub
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")
# --- FIM DAS CONFIGURAÇÕES ---

def enviar_notificacao_slack(mensagem):
    """
    Envia uma mensagem de texto simples para o canal do Slack.
    """
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print("ERRO: Variáveis de ambiente SLACK_BOT_TOKEN ou SLACK_CHANNEL não definidas.")
        return

    client = WebClient(token=SLACK_BOT_TOKEN)
    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=mensagem)
        print("Notificação de jogos enviada ao Slack!")
    except SlackApiError as e:
        print(f"ERRO: Ocorreu um erro ao enviar para o Slack: {e.response['error']}")

def verificar_jogos_ao_vivo():
    """
    Função principal: chama a API, filtra os jogos e monta a mensagem.
    """
    print("Iniciando verificação de jogos ao vivo...")
    try:
        response = requests.get(URL_API, timeout=10)
        response.raise_for_status() # Lança um erro se a requisição falhar (ex: 404, 500)
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao acessar a API: {e}")
        return # Aborta a execução se não conseguir pegar os dados

    # Dicionário para agrupar os jogos por campeonato
    jogos_encontrados = {}

    # 1. Filtra os campeonatos
    for campeonato_data in data:
        nome_campeonato = campeonato_data.get("campeonato")
        
        if nome_campeonato in CAMPEONATOS_FEMININOS:
            # 2. Filtra os jogos "em andamento"
            for partida in campeonato_data.get("object", []):
                if partida.get("status") == "andamento":
                    if nome_campeonato not in jogos_encontrados:
                        jogos_encontrados[nome_campeonato] = []
                    
                    # Monta a string do jogo (ex: Ferroviária x São Paulo (1 x 0))
                    placar_str = partida.get('placar', 'Placar não disponível')
                    mandante_placar = partida.get('placar_mandante', 0)
                    visitante_placar = partida.get('placar_visitante', 0)
                    
                    jogo_info = f"{placar_str} ({mandante_placar} x {visitante_placar})"
                    jogos_encontrados[nome_campeonato].append(jogo_info)

    # 3. Monta e envia a notificação (se houver jogos)
    if not jogos_encontrados:
        print("Nenhum jogo feminino ao vivo encontrado.")
        return

    # Se encontrou jogos, cria a mensagem
    mensagem_partes = ["⚽ *ALERTA DE JOGO FEMININO AO VIVO!* ⚽\n"]
    
    for campeonato, jogos in jogos_encontrados.items():
        mensagem_partes.append(f"\n🏆 *{campeonato}*")
        for jogo in jogos:
            mensagem_partes.append(f"  • {jogo}")
            
    mensagem_final = "\n".join(mensagem_partes)
    
    # Envia para o Slack
    enviar_notificacao_slack(mensagem_final)
    print("Verificação concluída.")

# --- Execução Principal ---
if __name__ == "__main__":
    verificar_jogos_ao_vivo()