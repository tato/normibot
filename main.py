import bottle, dotenv, requests, os, sys, logging

handlers = [
    logging.StreamHandler(stream=sys.stdout),
    logging.FileHandler(filename=os.getenv("LOG_FILE"))
]
logging.basicConfig(handlers=handlers, style="{", level="DEBUG")
log = logging.getLogger("normibot")


def turi(endpoint):
    token = os.getenv("TELEGRAM_BOT_TOKEN") or "UNDEFINED_BOT_TOKEN"
    return f"https://api.telegram.org/bot{token}/{endpoint}"

@bottle.route("/")
def receive_webhook():
    log.info("received webhook, attempting to print json body:")
    try:
        log.info(bottle.request.json)
        update = bottle.request.json
        if update["message"] != None and update["message"]["text"] != None:
            text = update["message"]["text"]
            if text.strip().startswith("https://open.spotify.com/"):
                new_text = text.split("?")[0].strip()
                requests.get(turi("sendMessage"), params={
                    "chat_id": update["message"]["chat"]["id"],
                    "text": new_text,
                })
    except Exception as e:
        log.error("failed, printing exception")
        log.error(e)
    return 200

if __name__ == "__main__":
    dotenv.load_dotenv(verbose=True)
    host = os.getenv("HOST") or "localhost"
    port = os.getenv("PORT") or "8090"
    port = int(port)
    requests.get(turi("setWebhook"), params={
        "url": f"http://{host}:{port}/",
        "certificate": "https://core.telegram.org/bots/api#setwebhook",
        "allowed_updates": []
    })
    bottle.run(host=host, port=port)
