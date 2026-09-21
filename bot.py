import os
import time
import requests
from discord_webhook import DiscordEmbed, DiscordWebhook

# Holt die Webhook-URL aus Render
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK")

MIN_CPM = 2.0  # Mindestens $2.00 CPM
MIN_BUDGET = 500  # Mindestens $500 Restbudget
MAX_CREATORS = 200  # Maximal 200 Teilnehmer
CHECK_INTERVAL = 300  # Alle 5 Minuten prüfen (300 Sekunden)

seen_campaigns = set()


def check_whop_campaigns():
    url = "https://whop.com/api/v5/content_rewards/public/"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Fehler beim Abrufen: Status {response.status_code}")
            return

        data = response.json()
        campaigns = data.get("data", [])

        for campaign in campaigns:
            campaign_id = campaign.get("id")
            name = campaign.get("title", "Unbekannte Kampagne")
            cpm = campaign.get("reward_per_thousand", 0) / 100
            budget_left = campaign.get("budget_remaining", 0) / 100
            creators_count = campaign.get("creators_count", 0)
            campaign_url = f"https://whop.com/rewards/{campaign_id}"

            if (
                cpm >= MIN_CPM
                and budget_left >= MIN_BUDGET
                and creators_count <= MAX_CREATORS
            ):
                if campaign_id not in seen_campaigns:
                    seen_campaigns.add(campaign_id)
                    send_discord_alert(
                        name, cpm, budget_left, creators_count, campaign_url
                    )

    except Exception as e:
        print(f"Fehler: {e}")


def send_discord_alert(name, cpm, budget, creators, url):
    if not DISCORD_WEBHOOK_URL:
        print("Fehler: Kein Discord Webhook hinterlegt!")
        return

    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
    embed = DiscordEmbed(
        title=f"🚀 Gefundene Top-Kampagne: {name}", color="00FF00"
    )
    embed.add_embed_field(name="💰 CPM", value=f"${cpm:.2f}", inline=True)
    embed.add_embed_field(
        name="💵 Restbudget", value=f"${budget:.2f}", inline=True
    )
    embed.add_embed_field(
        name="👥 Creators", value=f"{creators}", inline=True
    )
    embed.add_embed_field(
        name="🔗 Link", value=f"[Zur Kampagne]({url})", inline=False
    )
    webhook.add_embed(embed)
    webhook.execute()
    print(f"Alert gesendet für: {name}")


if __name__ == "__main__":
    print("Whop Auto-Bot gestartet...")
    while True:
        check_whop_campaigns()
        time.sleep(CHECK_INTERVAL)
