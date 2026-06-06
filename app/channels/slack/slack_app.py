from flask import Flask, request
import requests


app = Flask(__name__)

API_URL = "http://localhost:8000/ingest/message"


@app.route("/slack/events", methods=["POST"])
def slack_events():

    data = request.json

    user = data["event"]["user"]
    text = data["event"]["text"]

    payload = {
        "channel": "slack",
        "user_id": user,
        "text": text
    }

    requests.post(API_URL, json=payload)

    return "", 200