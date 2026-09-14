import os
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://diss.unibas.it/site/home/bacheca/articolo27012978.html"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
DATA_TARGET = "14/09/2026"

def invia_telegram(testo):
    endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": testo,
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(endpoint, data=payload, timeout=20)
        print(f"Risposta Telegram: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def pulisci_testo(t):
    return " ".join(t.split())

def scarica_pagina(url):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=2, status_forcelist=[500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retries))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9",
        "Connection": "close"
    }
    return session.get(url, headers=headers, timeout=35)

def main():
    try:
        res = scarica_pagina(URL)
        res.raise_for_status()
    except Exception as e:
        print(f"Errore connessione: {e}")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    corpo = soup.find("div", class_="testo") or soup.find("div", id="content") or soup

    blocchi = corpo.find_all(["p", "div", "li"])
    visti = set()

    for b in blocchi:
        testo = pulisci_testo(b.get_text())

        if DATA_TARGET in testo and len(testo) > 35 and testo not in visti:
            visti.add(testo)
            link_tag = b.find("a")
            link_info = ""
            if link_tag and link_tag.get("href"):
                href = link_tag.get("href")
                url_link = href if href.startswith("http") else f"https://diss.unibas.it{href}"
                link_info = f"\n\nLink: {url_link}"

            messaggio = f"📢 Avviso Bacheca ({DATA_TARGET}):\n\n{testo}{link_info}"
            invia_telegram(messaggio)
            time.sleep(1)

if __name__ == "__main__":
    main()
