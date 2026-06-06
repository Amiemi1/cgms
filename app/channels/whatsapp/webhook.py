from flask import Flask, request
import requests


app = Flask(__name__)

API_URL = "http://localhost:8000/ingest/message"


@app.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    text = data["messages"][0]["text"]["body"]
    user = data["messages"][0]["from"]

    payload = {
        "channel": "whatsapp",
        "user_id": user,
        "text": text
    }

    requests.post(API_URL, json=payload)

    return "ok", 200