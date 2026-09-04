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
        "disable_web_page_preview": False
    }
    try:
        requests.post(endpoint, data=payload, timeout=15)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    res = requests.get(URL, headers=headers, timeout=25)
    res.raise_for_status()
    
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Isola il corpo principale della pagina dell'Unibas
    corpo = soup.find("div", class_="testo") or soup.find("div", id="content") or soup
    links = corpo.find_all("a")

    visti_precedenti = set()
    if os.path.exists(FILE_MEMORIA):
        with open(FILE_MEMORIA, "r", encoding="utf-8") as f:
            visti_precedenti = set(line.strip() for line in f if line.strip())

    primo_avvio = not os.path.exists(FILE_MEMORIA)
    nuovi_avvisi = []

    for a in links:
        titolo = a.get_text(strip=True)
        href = a.get("href", "")

        # Salta voci di navigazione e link vuoti
        if not titolo or len(titolo) < 5 or href.startswith("#") or "javascript" in href:
            continue

        identificatore = f"{titolo}|{href}"

        if identificatore not in visti_precedenti:
            nuovi_avvisi.append(identificatore)
            
            # Invia messaggio solo se non è la prima scansione di inizializzazione
            if not primo_avvio:
                link_completo = href if href.startswith("http") else f"https://diss.unibas.it{href}"
                messaggio = (
                    f"📢 <b>Nuovo avviso Bacheca DiSS Unibas:</b>\n\n"
                    f"{titolo}\n\n"
                    f"🔗 <a href='{link_completo}'>Apri avviso / documento</a>"
                )
                invia_telegram(messaggio)

    # Salva la lista aggiornata
    if nuovi_avvisi:
        with open(FILE_MEMORIA, "a", encoding="utf-8") as f:
            for voce in nuovi_avvisi:
                f.write(voce + "\n")
        print(f"Salvati {len(nuovi_avvisi)} elementi.")
    else:
        print("Nessun nuovo avviso.")

if __name__ == "__main__":
    main()
