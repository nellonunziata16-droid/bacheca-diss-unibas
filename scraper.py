import hashlib
import os
import requests
from bs4 import BeautifulSoup

URL = "https://diss.unibas.it/site/home/bacheca/articolo27012978.html"
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
FILE_MEMORIA = "avvisi_visti.txt"

def invia_telegram(testo):
    endpoint = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": testo,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(endpoint, data=payload, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def pulisci_testo(t):
    return " ".join(t.split())

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    res = requests.get(URL, headers=headers, timeout=25)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")

    # Isola l'area principale dei contenuti della bacheca Unibas
    corpo = soup.find("div", class_="testo") or soup.find("div", id="content") or soup

    visti_precedenti = set()
    if os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, "r", encoding="utf-8") as f:
            visti_precedenti = set(line.strip() for line in f if line.strip())

    primo_avvio = not os.path.exists(FILE_MEMORIA)
    nuovi_identificatori = []

    # Seleziona tutti i blocchi di testo rilevanti (paragrafi, punti elenco, link)
    elementi = corpo.find_all(["p", "li", "a"])

    for el in elementi:
        testo = pulisci_testo(el.get_text())

        # Salta stringhe troppo corte (date isolate, freccette, menu di navigazione)
        if len(testo) < 25:
            continue

        # Crea un identificatore univoco basato sul testo (evita problemi con caratteri speciali)
        hash_id = hashlib.md5(testo.encode("utf-8")).hexdigest()

        if hash_id not in visti_precedenti:
            nuovi_identificatori.append(hash_id)

            if not primo_avvio:
                # Controlla se l'elemento include anche un eventuale link da allegare
                link_tag = el if el.name == "a" else el.find("a")
                link_info = ""
                if link_tag and link_tag.get("href"):
                    href = link_tag.get("href")
                    link_completo = href if href.startswith("http") else f"https://diss.unibas.it{href}"
                    link_info = f"\n\n🔗 <a href='{link_completo}'>Apri allegato/link</a>"

                messaggio = (
                    f"📢 <b>Nuovo avviso Bacheca DiSS:</b>\n\n"
                    f"{testo}"
                    f"{link_info}"
                )
                invia_telegram(messaggio)

    # Salva i nuovi elementi per non ri-notificarli
    if nuovi_identificatori:
        with open(FILE_MEMORIA, "a", encoding="utf-8") as f:
            for hid in nuovi_identificatori:
                f.write(hid + "\n")
        print(f"Salvati {len(nuovi_identificatori)} nuovi blocchi.")
    else:
        print("Nessun nuovo blocco di testo trovato.")

if __name__ == "__main__":
    main()
