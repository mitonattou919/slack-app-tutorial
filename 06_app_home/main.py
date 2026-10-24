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
    logger.info("message from %s in %s: %s", message.get("user"), message["channel"], message["text"])
    # ボットの発言（subtype: bot_message）には user がないので、何もしない
    if "user" not in message:
        return
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
    logger.info("approval request from %s in %s", message.get("user"), message["channel"])
    reply_in_thread(
        say,
        message,
        "承認依頼が届きました",
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*staging* へのデプロイを承認しますか？"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "承認"},
                    "style": "primary",
                    "action_id": "approve_button",
                },
            }
        ],
    )


@app.action("approve_button")
def handle_approve(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    logger.info("approve_button clicked by %s", user_id)
    respond(replace_original=True, text=f"<@{user_id}> さんが承認しました")


# Chapter 5: モーダル
@app.command("/practice-feedback")
def open_feedback(ack, body, client):
    ack()
    logger.info("/practice-feedback from %s", body["user_id"])
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "feedback_modal",
            "title": {"type": "plain_text", "text": "フィードバック"},
            "submit": {"type": "plain_text", "text": "送信"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "feedback_block",
                    "label": {"type": "plain_text", "text": "ご意見をどうぞ"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "feedback_input",
                        "multiline": True,
                    },
                }
            ],
        },
    )


@app.view("feedback_modal")
def handle_feedback(ack, body, client):
    value = body["view"]["state"]["values"]["feedback_block"]["feedback_input"]["value"]
    if len(value) < 5:
        logger.info("feedback from %s rejected: too short", body["user"]["id"])
        ack(response_action="errors", errors={"feedback_block": "5 文字以上で入力してください"})
        return
    ack()
    logger.info("feedback from %s: %s", body["user"]["id"], value)
    client.chat_postMessage(channel=body["user"]["id"], text=f"フィードバックを受け付けました: {value}")


# Chapter 6: App Home
@app.event("app_home_opened")
def update_home_tab(client, event):
    logger.info("app_home_opened by %s (tab=%s)", event["user"], event.get("tab"))
    if event.get("tab") != "home":
        return
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "Practice Bot へようこそ"},
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"<@{event['user']}> さん、使えるコマンドは `/practice-echo` と `/practice-feedback` です。",
                        },
                    },
                ],
            },
        )
    except Exception:
        logger.exception("failed to publish home tab")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
