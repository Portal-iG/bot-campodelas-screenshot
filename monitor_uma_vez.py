import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# --- CONFIGURAÇÕES ---
# O script agora lê estas informações das Variáveis de Ambiente do sistema
# Isso é mais seguro e necessário para a automação na nuvem.
URL_DO_SITE = "https://campodelas.ig.com.br/"
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")
# --- FIM DAS CONFIGURAÇÕES ---

def tirar_print(url, filename, is_mobile=False):
    """
    Abre o navegador, acessa a URL e salva um screenshot dos primeiros 500px de altura.
    """
    print(f"Configurando o driver para a captura {'Mobile (iPhone 14 Pro Max)' if is_mobile else 'Desktop'}...")
    chrome_options = Options()
    # Argumentos essenciais para rodar em servidores (Linux) sem interface gráfica
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") # Necessário para rodar como 'root' em containers
    chrome_options.add_argument("--disable-dev-shm-usage") # Evita problemas de memória compartilhada
    chrome_options.add_argument("--hide-scrollbars")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    if is_mobile:
        # Emulação de iPhone 14 Pro Max com 500px de altura
        mobile_emulation = {
            "deviceMetrics": { "width": 430, "height": 500, "pixelRatio": 3.0 },
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    else:
        # Tamanho da janela desktop fixo para 1920x500
        chrome_options.add_argument("--window-size=1920,500")

    # Silencia os logs do "Plausible"
    service = Service(log_output=subprocess.DEVNULL)
    
    # Tenta encontrar o chromedriver automaticamente (comum em GitHub Actions)
    # Se você estiver em um VPS, pode precisar especificar o caminho
    # service = Service(executable_path='/usr/bin/chromedriver', log_output=subprocess.DEVNULL)
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        # Espera inteligente para a página carregar
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2) # Pausa final para renderização de scripts

        driver.save_screenshot(filename)
        print(f"Screenshot de 500px de altura salvo como '{filename}'")
        return True
    except Exception as e:
        print(f"ERRO: Ocorreu um erro ao tirar o print: {e}")
        return False
    finally:
        driver.quit()

def enviar_multiplos_prints_slack(filenames, initial_comment):
    """
    Envia múltiplos arquivos de imagem para o Slack em uma única mensagem.
    """
    if not filenames:
        print("Nenhum print foi capturado com sucesso. Nenhum envio será feito.")
        return

    print(f"Preparando para enviar {len(filenames)} prints para o Slack...")
    client = WebClient(token=SLACK_BOT_TOKEN)
    
    try:
        file_uploads = [{"file": file, "title": file} for file in filenames]
        client.files_upload_v2(
            channel=SLACK_CHANNEL,
            file_uploads=file_uploads,
            initial_comment=initial_comment,
        )
        print("Prints enviados com sucesso para o Slack!")
        
    except SlackApiError as e:
        print(f"ERRO: Ocorreu um erro ao enviar para o Slack: {e.response['error']}")
    except FileNotFoundError as e:
        print(f"ERRO: Arquivo de screenshot não encontrado: {e.filename}")

def job():
    """
    Função principal que organiza a execução das tarefas.
    """
    print("\n--- INICIANDO NOVO CICLO DE VERIFICAÇÃO ---")
    
    # Verifica se as variáveis de ambiente foram carregadas
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL:
        print("ERRO CRÍTICO: As variáveis de ambiente SLACK_BOT_TOKEN ou SLACK_CHANNEL não foram definidas.")
        return

    desktop_filename = "screenshot_desktop.png"
    mobile_filename = "screenshot_mobile.png"
    
    desktop_success = tirar_print(URL_DO_SITE, desktop_filename, is_mobile=False)
    time.sleep(2)
    mobile_success = tirar_print(URL_DO_SITE, mobile_filename, is_mobile=True)
    
    files_to_send = []
    if desktop_success:
        files_to_send.append(desktop_filename)
    if mobile_success:
        files_to_send.append(mobile_filename)

    timestamp = time.ctime()
    comment = (
        f"🖥️📱 *Monitoramento do site (Primeira Dobra - 500px)*\n"
        f"Capturado em: {timestamp}"
    )
    enviar_multiplos_prints_slack(files_to_send, comment)
        
    print("\n--- CICLO DE VERIFICAÇÃO CONCLUÍDO ---")

# --- Execução Principal ---
# Quando o script for chamado (ex: python monitor_uma_vez.py),
# ele executará a função job() uma vez e depois sairá.
if __name__ == "__main__":
    job()