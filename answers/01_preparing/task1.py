# 練習課題の解答例: Chapter 1 課題 1（基本）
# 起動: uv run --env-file .env answers/01_preparing/task1.py

import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = App(token=os.environ["SLACK_BOT_TOKEN"])


# Chapter 1: メンションに返事をする
@app.event("app_mention")
def handle_mention(event, say):
    logger.info("app_mention from %s in %s: %s", event["user"], event["channel"], event["text"])
    say(f"やあ、<@{event['user']}> さん！ Practice Bot です。")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
