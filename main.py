import bottle, requests

with open("secret_token.txt") as f:
    TOKEN = f.read().strip()

def turi(endpoint):
    return f"https://api.telegram.org/bot{TOKEN}/{endpoint}"

@bottle.route("/")
def receive_webhook():
    print(bottle.request.json())
    return 200

if __name__ == "__main__":
    host, port = "localhost", 8090
    requests.get(turi("setWebhook"), params={
        "url": f"http://{host}:{port}/",
        "certificate": "https://core.telegram.org/bots/api#setwebhook",
        "allowed_updates": []
    })
    bottle.run(host=host, port=port)