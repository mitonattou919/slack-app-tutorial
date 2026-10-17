# 練習課題の解答例: Chapter 3 課題 3（複合）
# 起動: uv run --env-file .env answers/03_slash_commands/task3.py

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


# Chapter 3: スラッシュコマンド
@app.command("/practice-echo")
def handle_echo(ack, respond, command):
    ack()
    logger.info("/practice-echo from %s: %s", command["user_id"], command["text"])
    text = command["text"]
    if text.startswith("public "):
        respond(response_type="in_channel", text=f"あなたの入力: {text.removeprefix('public ')}")
    else:
        respond(f"あなたの入力: {text}")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
