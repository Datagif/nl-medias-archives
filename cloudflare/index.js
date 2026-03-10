/**
 * Cloudflare Worker — Relais webhook Mailchimp → GitHub
 *
 * Ce worker reçoit le webhook Mailchimp (campaign.sent)
 * et déclenche la GitHub Action via repository_dispatch.
 *
 * Variables d'environnement à configurer dans le Worker (Settings > Variables) :
 *   GITHUB_TOKEN   Personal Access Token GitHub (scope: repo)
 *   GITHUB_REPO    ex: datagif/nl-medias-archives
 *   SECRET_KEY     Clé secrète à mettre aussi dans Mailchimp webhook URL (?key=xxx)
 *                  pour vérifier que la requête vient bien de Mailchimp
 */

export default {
  async fetch(request, env) {
    // Vérification méthode
    if (request.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Vérification clé secrète via query param ?key=xxx
    const url = new URL(request.url);
    const key = url.searchParams.get("key");
    if (!key || key !== env.SECRET_KEY) {
      return new Response("Unauthorized", { status: 401 });
    }

    // Lecture du body Mailchimp (form-urlencoded ou JSON selon version)
    let body;
    const contentType = request.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      body = await request.json();
    } else {
      const text = await request.text();
      body = Object.fromEntries(new URLSearchParams(text));
    }

    // On ne traite que les événements campaign.sent
    const type = body.type || body["type[0]"];
    if (type !== "campaign" ) {
      return new Response("Ignored", { status: 200 });
    }

    // Déclenchement de la GitHub Action
    const ghResponse = await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "Content-Type": "application/json",
          "User-Agent": "Cloudflare-Worker-Mailchimp-Relay",
        },
        body: JSON.stringify({
          event_type: "mailchimp_campaign_sent",
          client_payload: {
            triggered_by: "mailchimp_webhook",
            campaign_type: type,
          },
        }),
      }
    );

    if (!ghResponse.ok) {
      const err = await ghResponse.text();
      console.error("GitHub API error:", ghResponse.status, err);
      return new Response("GitHub dispatch failed", { status: 502 });
    }

    return new Response("OK", { status: 200 });
  },
};
