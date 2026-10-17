# 練習課題の解答例: Chapter 2 課題 1（基本）
# 起動: uv run --env-file .env answers/02_messages/task1.py

import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_helpers import reply_in_thread

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = App(token=os.environ["SLACK_BOT_TOKEN"])


# Chapter 1: メンションに返事をする（Chapter 2 からスレッド返信に変更）
@app.event("app_mention")
def handle_mention(event, say):
    logger.info("app_mention from %s in %s: %s", event["user"], event["channel"], event["text"])
    reply_in_thread(say, event, f"こんにちは、<@{event['user']}> さん！")


# Chapter 2: 「hello」を含むメッセージに反応する
@app.message("hello")
def handle_hello(message, say):
    logger.info("message from %s in %s: %s", message["user"], message["channel"], message["text"])
    reply_in_thread(say, message, f"hello を受け取りました、<@{message['user']}> さん")


# 練習課題 1: 「bye」を含むメッセージにスレッドで返す
@app.message("bye")
def handle_bye(message, say):
    logger.info("bye from %s in %s", message["user"], message["channel"])
    reply_in_thread(say, message, "またね！")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
