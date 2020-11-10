import bottle, dotenv, requests, os, sys, logging

# handlers = [
#     logging.StreamHandler(stream=sys.stdout),
#     logging.FileHandler(filename=os.getenv("LOG_FILE") or "/etc/normibot_logs.txt")
# ]
# logging.basicConfig(handlers=handlers, level="DEBUG")
logging.basicConfig(filename=os.getenv("LOG_FILE") or "/etc/normibot_logs.txt", level=logging.DEBUG)

def turi(endpoint):
    token = os.getenv("TELEGRAM_BOT_TOKEN") or "UNDEFINED_BOT_TOKEN"
    return f"https://api.telegram.org/bot{token}/{endpoint}"

@bottle.post("/")
def receive_webhook():
    logging.info("received webhook, attempting to print json body:")
    try:
        logging.info(bottle.request.json)
        update = bottle.request.json
        if update["message"] != None and update["message"]["text"] != None:
            logging.info("apparently there is a message in the update")
            logging.info("i'm sending something anyway")
            requests.get(turi("sendMessage"), params={
                "chat_id": update["message"]["chat"]["id"],
                "text": "something",
            })
            text = update["message"]["text"]
            if text.strip().startswith("https://open.spotify.com/"):
                logging.info("apparently the message is a spotify link")
                new_text = text.split("?")[0].strip()
                logging.info(f"sending '{new_text}'")
                requests.get(turi("sendMessage"), params={
                    "chat_id": update["message"]["chat"]["id"],
                    "text": new_text,
                })
    except Exception as e:
        logging.error("failed, printing exception")
        logging.error(e)
    return 200

if __name__ == "__main__":
    dotenv.load_dotenv(verbose=True)
    host = os.getenv("HOST") or "localhost"
    port = os.getenv("PORT") or "8090"
    port = int(port)
    logging.info(f"started server on {host}:{port}")
    requests.get(turi("deleteWebhook"))
    r = requests.get(turi("setWebhook"), params={
        "url": os.getenv("WEBHOOK_URI") or f"http://{host}:{port}/",
    })
    r.raise_for_status()
    logging.info(f"telegram setWebhook: {r.status_code}")
    logging.info(r.text)
    bottle.run(host=host, port=port)
