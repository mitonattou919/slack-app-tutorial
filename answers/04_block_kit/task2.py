# 練習課題の解答例: Chapter 4 課題 2（応用）
# 起動: uv run --env-file .env answers/04_block_kit/task2.py

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
    respond(f"あなたの入力: {command['text']}")


# Chapter 4: ボタン付きメッセージ
@app.message("approve")
def send_approval(message, say):
    logger.info("approval request from %s in %s", message["user"], message["channel"])
    reply_in_thread(
        say,
        message,
        "承認依頼が届きました",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*staging* へのデプロイを承認しますか？"},
            },
            # ボタンを横に並べるときは actions ブロックを使う
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "承認"},
                        "style": "primary",
                        "action_id": "approve_button",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "却下"},
                        "style": "danger",
                        "action_id": "reject_button",
                    },
                ],
            },
        ],
    )


@app.action("approve_button")
def handle_approve(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    logger.info("approve_button clicked by %s", user_id)
    respond(replace_original=True, text=f"<@{user_id}> さんが承認しました")


# 練習課題 2: 却下ボタン
@app.action("reject_button")
def handle_reject(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    logger.info("reject_button clicked by %s", user_id)
    respond(replace_original=True, text=f"<@{user_id}> さんが却下しました")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
