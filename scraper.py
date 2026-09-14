import hashlib
import os
import time
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://diss.unibas.it/site/home/bacheca/articolo27012978.html"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
FILE_MEMORIA = "avvisi_visti.txt"

def invia_telegram(testo):
    endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": testo[:4000],
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(endpoint, data=payload, timeout=20)
        r.raise_for_status()
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

    # Carica gli hash degli avvisi già notificati
    visti_precedenti = set()
    if os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, "r", encoding="utf-8") as f:
            visti_precedenti = set(line.strip() for line in f if line.strip())

    primo_avvio = not os.path.exists(FILE_MEMORIA)
    nuovi_hash = []

    # Isola i singoli paragrafi escludendo i contenitori generici
    paragrafi = corpo.find_all("p")

    for p in paragrafi:
        testo = pulisci_testo(p.get_text())

        # Salta frammenti corti o il titolo statico della bacheca
        if len(testo) < 35 or "CdLM in Medicina e Chirurgia" in testo:
            continue

        # Genera l'impronta univoca del singolo blocco di testo
        hash_id = hashlib.md5(testo.encode("utf-8")).hexdigest()

        if hash_id not in visti_precedenti:
            nuovi_hash.append(hash_id)

            # Invia la notifica solo se non è la prima scansione di inizializzazione
            if not primo_avvio:
                link_tag = p.find("a")
                link_info = ""
                if link_tag and link_tag.get("href"):
                    href = link_tag.get("href")
                    url_link = href if href.startswith("http") else f"https://diss.unibas.it{href}"
                    link_info = f"\n\nLink: {url_link}"

                messaggio = f"📢 <b>Nuovo avviso Bacheca DiSS:</b>\n\n{testo}{link_info}"
                invia_telegram(messaggio)
                time.sleep(1.5)

    # Aggiorna la memoria con i nuovi avvisi registrati
    if nuovi_hash:
        with open(FILE_MEMORIA, "a", encoding="utf-8") as f:
            for h in nuovi_hash:
                f.write(h + "\n")
        print(f"Salvati {len(nuovi_hash)} elementi.")
    else:
        print("Nessun nuovo avviso.")

if __name__ == "__main__":
    main()
