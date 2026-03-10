#!/usr/bin/env python3
"""
fetch_archives.py
Récupère toutes les campagnes Newsletter Médias depuis Mailchimp
et les sauvegarde en HTML et TXT.

Usage :
    cp .env.example .env  # puis remplir les valeurs
    python fetch_archives.py

Variables d'environnement :
    MAILCHIMP_API_KEY   Clé API Mailchimp
    MAILCHIMP_LIST_ID   ID de l'audience "Médias"
    OUTPUT_DIR          Dossier de sortie (défaut: ./archives)
"""

import os
import re
import sys
import time
import html2text
from dotenv import load_dotenv

load_dotenv()
import requests
from datetime import datetime
from pathlib import Path

# --- Config ---
API_KEY   = os.environ["MAILCHIMP_API_KEY"]
LIST_ID   = os.environ["MAILCHIMP_LIST_ID"]
DC        = API_KEY.split("-")[-1]  # ex: us19
BASE_URL  = f"https://{DC}.api.mailchimp.com/3.0"
AUTH      = ("anystring", API_KEY)
OUT_DIR   = Path(os.environ.get("OUTPUT_DIR", "archives"))

HTML_DIR  = OUT_DIR / "html"
TXT_DIR   = OUT_DIR / "txt"
HTML_DIR.mkdir(parents=True, exist_ok=True)
TXT_DIR.mkdir(parents=True, exist_ok=True)

h2t = html2text.HTML2Text()
h2t.ignore_links = False
h2t.body_width   = 0  # pas de retour à la ligne forcé


def extract_number(title: str) -> str | None:
    """Extrait le numéro de campagne depuis le titre, ex: '#170 • 05.03.26' -> '170'"""
    m = re.match(r"#(\d+)\s*[•·]", title)
    return m.group(1) if m else None


def is_valid_campaign(campaign: dict) -> bool:
    """Filtre : envoyée + audience Médias + titre avec bullet."""
    status     = campaign.get("status") == "sent"
    list_id    = campaign.get("recipients", {}).get("list_id") == LIST_ID
    title      = campaign.get("settings", {}).get("title", "")
    has_bullet = "•" in title or "·" in title
    return status and list_id and has_bullet


def get_campaigns() -> list[dict]:
    """Récupère toutes les campagnes (pagination 100 par page)."""
    campaigns = []
    offset = 0
    while True:
        r = requests.get(
            f"{BASE_URL}/campaigns",
            auth=AUTH,
            params={
                "count":  100,
                "offset": offset,
                "status": "sent",
                "list_id": LIST_ID,
                "fields": "total_items,campaigns.id,campaigns.status,campaigns.settings.title,"
                          "campaigns.recipients.list_id,campaigns.send_time",
            },
        )
        r.raise_for_status()
        data = r.json()
        batch = data.get("campaigns", [])
        if not batch:
            break
        campaigns.extend(batch)
        offset += len(batch)
        total = data.get("total_items", 0)
        if total and offset >= total:
            break
    return campaigns


def get_content(campaign_id: str) -> str:
    """Récupère le HTML d'une campagne."""
    r = requests.get(
        f"{BASE_URL}/campaigns/{campaign_id}/content",
        auth=AUTH,
        params={"fields": "html"},
    )
    r.raise_for_status()
    return r.json().get("html", "")


def make_filename(number: str, send_time: str) -> str:
    """Construit le nom de fichier : 170_2026-03-05"""
    try:
        dt = datetime.fromisoformat(send_time.replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
    except Exception:
        date_str = "0000-00-00"
    return f"{number}_{date_str}"


def main():
    print("Récupération des campagnes…")
    campaigns = get_campaigns()
    valid = [c for c in campaigns if is_valid_campaign(c)]
    print(f"{len(campaigns)} campagnes trouvées, {len(valid)} retenues.")

    skipped = 0
    saved   = 0

    for c in valid:
        title     = c["settings"]["title"]
        number    = extract_number(title)
        send_time = c.get("send_time", "")

        if not number:
            print(f"  [SKIP] Numéro non trouvé dans : {title!r}")
            skipped += 1
            continue

        filename = make_filename(number, send_time)
        html_path = HTML_DIR / f"{filename}.html"
        txt_path  = TXT_DIR  / f"{filename}.txt"

        if html_path.exists() and txt_path.exists():
            print(f"  [OK]   {filename} — déjà présent")
            continue

        print(f"  [DL]   {filename} — {title}")
        try:
            html_content = get_content(c["id"])
        except requests.HTTPError as e:
            print(f"         Erreur contenu : {e}")
            skipped += 1
            continue

        html_path.write_text(html_content, encoding="utf-8")
        txt_path.write_text(h2t.handle(html_content), encoding="utf-8")
        saved += 1
        time.sleep(0.3)  # respect rate limit Mailchimp

    print(f"\nTerminé : {saved} sauvegardés, {skipped} ignorés.")
    print(f"Archives dans : {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
