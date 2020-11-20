import bottle, dotenv, requests, os, sys, logging

logging.basicConfig(filename=os.getenv("LOG_FILE") or "/etc/normibot_logs.txt", level=logging.DEBUG)
log = logging.getLogger("normibot")
log.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.getenv("LOG_FILE") or "/etc/normibot_logs.txt")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
log.addHandler(fh)
log.addHandler(ch)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "UNDEFINED_BOT_TOKEN"
def turi(endpoint):
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{endpoint}"

def strip_spotify_url(update):
    log.info("ENTER strip_spotify_url")
    new_text = update.get("message", {}).get("text", "").split("?")[0].strip()
    log.info(f"sending '{new_text}'")
    requests.get(turi("sendMessage"), params={
        "chat_id": update["message"]["chat"]["id"],
        "text": new_text,
    })

@bottle.post("/")
def receive_webhook():
    log.info("received webhook, attempting to print json body:")
    try:
        log.info(bottle.request.json)
        update = bottle.request.json
        if update.get("message", {}).get("text", "").startswith("https://open.spotify.com/"):
            strip_spotify_url(update)

    except Exception as e:
        log.error("failed, printing exception")
        log.error(e)
    bottle.response.status = 200

if __name__ == "__main__":
    dotenv.load_dotenv(verbose=True)
    host = os.getenv("HOST") or "localhost"
    port = os.getenv("PORT") or "8090"
    port = int(port)
    log.info(f"started server on {host}:{port}")
    requests.get(turi("deleteWebhook"))
    r = requests.get(turi("setWebhook"), params={
        "url": os.getenv("WEBHOOK_URI") or f"http://{host}:{port}/",
        "drop_pending_updates": True,
    })
    r.raise_for_status()
    log.info(f"telegram setWebhook: {r.status_code}")
    log.info(r.text)
    bottle.run(host=host, port=port)
