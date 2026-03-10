# nl-medias-archives

Archives de la newsletter **Médias** de [Datagif](https://datagif.fr), synchronisées automatiquement depuis Mailchimp.

## Structure

```
archives/
├── html/   # Version HTML brute de chaque campagne
└── txt/    # Version texte (markdown) générée depuis le HTML
```

### Convention de nommage

```
{numéro}_{date}.html   →   170_2026-03-05.html
{numéro}_{date}.txt    →   170_2026-03-05.txt
```

## Mise en place

### 1. Secrets GitHub à configurer

Dans **Settings > Secrets and variables > Actions** du repo, ajouter :

| Secret               | Valeur                                      |
|----------------------|---------------------------------------------|
| `MAILCHIMP_API_KEY`  | Clé API Mailchimp (se termine par `-us19`)  |
| `MAILCHIMP_LIST_ID`  | ID de l'audience "Médias" dans Mailchimp    |

### 2. Peuplement initial

Lancer la GitHub Action manuellement :  
**Actions > Sync Mailchimp Newsletter > Run workflow**

Cela va récupérer toutes les campagnes existantes (~170 numéros).

### 3. Sync automatique (webhook Mailchimp)

Configurer un webhook dans Mailchimp pour déclencher la Action à chaque envoi :

1. Créer un **Personal Access Token** GitHub avec le scope `repo`  
   → Stocker dans un secret `WEBHOOK_TOKEN`

2. Dans Mailchimp : **Audience > Manage contacts > Webhooks**  
   Ajouter un webhook de type `campaign` avec l'URL :
   ```
   https://api.github.com/repos/datagif/nl-medias-archives/dispatches
   ```
   Header HTTP à ajouter :
   ```
   Authorization: Bearer {WEBHOOK_TOKEN}
   Content-Type: application/json
   ```
   Body :
   ```json
   { "event_type": "mailchimp_campaign_sent" }
   ```

   > **Note :** Mailchimp ne supporte pas nativement les headers personnalisés sur les webhooks.  
   > Une alternative simple : utiliser un service intermédiaire comme **Make** ou une **Cloudflare Worker**  
   > pour recevoir le webhook Mailchimp et relayer vers l'API GitHub avec le bon header.

## Lancement local (optionnel)

```bash
pip install requests html2text
MAILCHIMP_API_KEY=xxx MAILCHIMP_LIST_ID=xxx python fetch_archives.py
```
