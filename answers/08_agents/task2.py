# 練習課題の解答例: Chapter 8 課題 2（応用）
# 起動: uv run --env-file .env.agent answers/08_agents/task2.py

import logging
import os
import threading
import time

import anthropic
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = App(token=os.environ["SLACK_BOT_TOKEN"])

# 応答の作り方。dummy（既定）は固定文、claude は Claude API を呼ぶ
AGENT_LLM = os.environ.get("AGENT_LLM", "dummy")
# ANTHROPIC_API_KEY は環境変数から読まれる（.env.agent に書く。コードには書かない）
llm = anthropic.Anthropic() if AGENT_LLM == "claude" else None
MODEL = os.environ.get("AGENT_MODEL", "claude-haiku-4-5-20251001")
SYSTEM_PROMPT = "あなたはSlackハンズオン用の練習エージェントです。日本語で、200文字以内で簡潔に答えてください。"


# 停止ボタンが押されたスレッドの目印（thread_ts ごと）。リスナーは別スレッドで動くので Event を使う
stop_flags = {}


def stream_dummy(text):
    """LLM を使わない練習用。固定の文を、少しずつ返す。"""
    for word in ["こんにちは！ ", "練習用の ", "エージェント ", "です。 ", f"「{text}」 ", "と言いましたね。"]:
        time.sleep(1.0)
        yield word


def llm_options():
    """モデルの世代で変わるオプション。effort は 4.5 世代の Haiku では 400 になるので、5 世代のときだけ付ける。"""
    return {"output_config": {"effort": "low"}} if MODEL.split("-")[2] == "5" else {}


def stream_llm(text):
    """Claude の応答を、テキストの断片として順に返す。

    別の LLM（Gemini など）を使うときは、この関数だけを差し替える。
    """
    with llm.messages.stream(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
        **llm_options(),
    ) as stream:
        yield from stream.text_stream
        final = stream.get_final_message()
    logger.info(
        "llm done: stop_reason=%s input_tokens=%d output_tokens=%d",
        final.stop_reason,
        final.usage.input_tokens,
        final.usage.output_tokens,
    )
    if final.stop_reason == "refusal":
        yield "\n\n（この内容にはお答えできません）"
    elif final.stop_reason == "max_tokens":
        yield "\n\n（長いので、ここで切れました）"


# 画面の確認用: リサーチタスクの進捗を、段階的に見せるモック（中身はダミー）
class StopRequested(Exception):
    """停止ボタンが押された。"""


def work(stop_flag, seconds):
    """処理に時間がかかるふりをする。LLM を呼ぶ処理に差し替えるのは、この関数の呼び出しの部分。"""
    for _ in range(int(seconds / 0.5)):
        time.sleep(0.5)
        if stop_flag.is_set():
            raise StopRequested()


def source(text, path):
    return {"type": "url", "text": text, "url": f"https://docs.slack.dev/{path}"}


# 各段階: (id, タイトル, 実行中の説明, 所要秒数, 完了時の output, 出典)
RESEARCH_STAGES = [
    (
        "research", "調査", "公開情報を検索しています", 2.0,
        "3 件の情報源から、4 件の主張を抽出しました",
        [
            source("Agent messaging experience", "changelog/2026/06/30/agent-messages-tab"),
            source("chat.startStream", "reference/methods/chat.startStream"),
            source("chat.appendStream", "reference/methods/chat.appendStream"),
        ],
    ),
    (
        "factcheck", "ファクトチェック", "主張を情報源と照合しています", 2.5,
        "✅ 一致: エージェント画面はメッセージタブで動く\n"
        "✅ 一致: 停止ボタンはイベントで受け取れる\n"
        "✅ 一致: 進捗はタスクとして見せられる\n"
        "⚠️ 要再確認: 使える機能がプランによって違う可能性",
        [source("app-manifest", "reference/app-manifest"), source("developing-agents", "ai/developing-agents")],
    ),
    (
        "summarize", "要約", "要点をまとめています", 2.0,
        "要点を 3 つに整理しました。要再確認の 1 件は、断定せずに注記にしました",
        [],
    ),
    (
        "verify", "ベリファイ", "要約が元の情報と食い違わないか確認しています", 2.0,
        "要約の各文を出典と突き合わせました。食い違いはありません（注記つきの 1 件を除く）",
        [source("developing-agents", "ai/developing-agents")],
    ),
    ("translate", "翻訳", "英語に訳しています", 2.0, "英語版の要点ができました", []),
    ("done", "完成", "レポートに仕上げています", 1.5, "レポートができました", []),
]

FEEDBACK_BLOCKS = [
    {
        "type": "context_actions",
        "elements": [
            {
                "type": "feedback_buttons",
                "action_id": "feedback",
                "positive_button": {
                    "text": {"type": "plain_text", "text": "👍"},
                    "accessibility_label": "この回答は役に立った",
                    "value": "good-feedback",
                },
                "negative_button": {
                    "text": {"type": "plain_text", "text": "👎"},
                    "accessibility_label": "この回答は役に立たなかった",
                    "value": "bad-feedback",
                },
            }
        ],
    }
]


def run_research(stream, topic, stop_flag):
    """リサーチの進捗を task_update チャンクで見せる。完走したら True、止められたら False を返す。"""
    title = f"「{topic}」のリサーチ"
    # 最初に、全タスクを pending で並べる（plan 表示のとき、一覧として見える）
    stream.append(
        chunks=[{"type": "plan_update", "title": f"{title}（準備中）"}]
        + [{"type": "task_update", "id": sid, "title": name, "status": "pending"} for sid, name, *_ in RESEARCH_STAGES]
    )
    for sid, name, doing, seconds, output, sources in RESEARCH_STAGES:
        stream.append(
            chunks=[
                {"type": "plan_update", "title": f"{title}（{name}）"},
                {"type": "task_update", "id": sid, "title": name, "status": "in_progress", "details": doing},
            ]
        )
        try:
            work(stop_flag, seconds)
        except StopRequested:
            logger.info("research stopped by user at %s", sid)
            stream.append(
                chunks=[{"type": "task_update", "id": sid, "title": name, "status": "error", "details": "ユーザーが停止しました"}]
            )
            return False
        update = {"type": "task_update", "id": sid, "title": name, "status": "complete", "details": doing, "output": output}
        if sources:
            update["sources"] = sources
        stream.append(chunks=[update])
    stream.append(
        chunks=[
            {"type": "plan_update", "title": f"{title}（完了）"},
            {
                "type": "markdown_text",
                "text": f"## 「{topic}」のリサーチ結果\n\n"
                "- エージェント画面は、メッセージタブで普通の DM のように動きます\n"
                "- 処理の進み具合は、タスクとして段階的に見せられます\n"
                "- 停止ボタンで、実行中の処理を止められます\n\n"
                "> 注記: 使える機能がプランによって違う可能性があります（要再確認）\n\n"
                "_これは画面の確認用のダミーです_\n",
            },
        ]
    )
    return True


RESEARCH_SYSTEM_PROMPT = "あなたはリサーチ担当です。日本語で、簡潔な箇条書きで答えてください。見出し（#）は付けないでください。"

# 段階ごとの指示と、Web 検索の最大回数。{prev} には前の段階の結果が入る
RESEARCH_PROMPTS = {
    "research": ("「{topic}」について Web で調べ、重要な事実を 4 件以内の箇条書きで答えてください。", 3),
    "factcheck": (
        "次の主張を Web 検索で確かめてください。各行の先頭に「✅ 一致:」か「⚠️ 要再確認:」を付けて、1 行ずつ答えてください。\n\n{research}",
        2,
    ),
    "summarize": ("次の確認結果から、⚠️ の項目は断定せず注記にして、要点を 3 つにまとめてください。\n\n{factcheck}", 0),
    "verify": (
        "次の要約が確認結果と食い違っていないか確認し、結論を 2 文以内で答えてください。\n\n要約:\n{summarize}\n\n確認結果:\n{factcheck}",
        0,
    ),
}


def ask(prompt, search_uses=0):
    """Claude を 1 回呼ぶ。(本文, 検索クエリの一覧, 出典) を返す。search_uses が 1 以上なら Web 検索を使わせる。"""
    kwargs = llm_options()
    if search_uses:
        # Web 検索は Anthropic 側で実行されるサーバーツール。sbx の許可は要らない
        kwargs["tools"] = [{"type": "web_search_20250305", "name": "web_search", "max_uses": search_uses}]
    messages = [{"role": "user", "content": prompt}]
    texts, queries, found = [], [], {}
    for _ in range(3):
        r = llm.messages.create(model=MODEL, max_tokens=1024, system=RESEARCH_SYSTEM_PROMPT, messages=messages, **kwargs)
        for b in r.content:
            if b.type == "text":
                texts.append(b.text)
            elif b.type == "server_tool_use":
                queries.append(b.input.get("query", ""))
            elif b.type == "web_search_tool_result" and isinstance(b.content, list):
                for item in b.content:
                    found.setdefault(item.url, item.title)
        # サーバーツールが長引くと pause_turn で返ってくるので、続きを呼ぶ
        if r.stop_reason != "pause_turn":
            break
        messages = messages + [{"role": "assistant", "content": r.content}]
    sources = [{"type": "url", "text": (title or url)[:60], "url": url} for url, title in list(found.items())[:5]]
    return "\n".join(t.strip() for t in texts).strip(), queries, sources


def run_research_llm(stream, topic, stop_flag):
    """run_research の本物版。各段階で Claude を呼ぶ（調査とファクトチェックは Web 検索つき）。
    停止ボタンは、Claude を呼ぶ前後で確認する（呼び出しの最中には止められない）。"""
    title = f"「{topic}」のリサーチ"
    stream.append(
        chunks=[{"type": "plan_update", "title": f"{title}（準備中）"}]
        + [{"type": "task_update", "id": sid, "title": name, "status": "pending"} for sid, name, *_ in RESEARCH_STAGES]
    )
    results = {"topic": topic}
    for sid, name, doing, *_ in RESEARCH_STAGES:
        stream.append(
            chunks=[
                {"type": "plan_update", "title": f"{title}（{name}）"},
                {"type": "task_update", "id": sid, "title": name, "status": "in_progress", "details": doing},
            ]
        )
        try:
            if stop_flag.is_set():
                raise StopRequested()
            update = {"type": "task_update", "id": sid, "title": name, "status": "complete", "details": doing}
            if sid in RESEARCH_PROMPTS:
                template, search_uses = RESEARCH_PROMPTS[sid]
                text, queries, sources = ask(template.format(**results), search_uses)
                if stop_flag.is_set():
                    raise StopRequested()
                results[sid] = text
                update["output"] = text
                if queries:
                    update["details"] = "検索: " + " / ".join(queries)
                if sources:
                    update["sources"] = sources
            else:
                update["output"] = "レポートができました"
        except StopRequested:
            logger.info("research stopped by user at %s", sid)
            error = "ユーザーが停止しました"
        except anthropic.APIError as e:
            # チャンク形式のストリームには markdown_text を足せないので、失敗はタスクの表示で伝える
            logger.error("research failed at %s: %s (request_id=%s)", sid, e, getattr(e, "request_id", None))
            error = "Claude API でエラーが出ました"
        else:
            stream.append(chunks=[update])
            continue
        stream.append(chunks=[{"type": "task_update", "id": sid, "title": name, "status": "error", "details": error}])
        return False
    stream.append(
        chunks=[
            {"type": "plan_update", "title": f"{title}（完了）"},
            {
                "type": "markdown_text",
                "text": f"## 「{topic}」のリサーチ結果\n\n{results['summarize']}\n\n> 検証: {results['verify']}\n",
            },
        ]
    )
    return True


# Chapter 8: メッセージタブを開いたとき。候補のプロンプトは manifest（agent_view.suggested_prompts）で固定している。
# manifest に静的な候補があると、assistant.threads.setSuggestedPrompts は static_prompts_configured で拒否される
@app.event("app_home_opened")
def handle_home_opened(event):
    logger.info("app_home_opened by %s (tab=%s)", event["user"], event.get("tab"))


# Chapter 8: DM に届いたメッセージを Claude に渡し、応答をストリーミングで返す
@app.event("message")
def handle_message(client, event, say_stream):
    # 編集や削除、ボット自身の発言は無視する
    if event.get("subtype") or event.get("bot_id"):
        return
    logger.info("message from %s in %s (%d chars)", event["user"], event["channel"], len(event["text"]))
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]
    client.agents_sessions_setStatus(channel_id=channel_id, thread_ts=thread_ts, status="processing")
    # 前の処理が終わった後に届いた停止イベントのフラグが残っていることがあるので、毎回作り直す
    stop_flag = stop_flags[thread_ts] = threading.Event()
    # 「調査 ○○」で、リサーチの進捗を見せるモックになる（timeline を含めると、カードを順に出す表示）
    is_research = event["text"].startswith("調査")
    if is_research:
        mode = "timeline" if "timeline" in event["text"].lower() else "plan"
        stream = say_stream(buffer_size=1, task_display_mode=mode)
    else:
        stream = say_stream(buffer_size=20)
    final_blocks = None  # 最後まで終わったときだけ、フィードバックボタンを付ける
    try:
        if is_research:
            topic = event["text"].removeprefix("調査").replace("timeline", "").strip() or "テーマ未指定"
            if (run_research_llm if AGENT_LLM == "claude" else run_research)(stream, topic, stop_flag):
                final_blocks = FEEDBACK_BLOCKS
        else:
            for chunk in (stream_llm if AGENT_LLM == "claude" else stream_dummy)(event["text"]):
                if stop_flag.is_set():
                    logger.info("stopped by user at thread %s", thread_ts)
                    break
                if chunk:
                    stream.append(markdown_text=chunk)
            else:
                final_blocks = FEEDBACK_BLOCKS
    except anthropic.AuthenticationError:
        logger.error("Anthropic API の認証に失敗しました（キーを確認）")
        stream.append(markdown_text="API キーが無効です。管理者に伝えてください。")
    except anthropic.BadRequestError as e:
        # 不正なパラメーターのほか、クレジット不足も 400 で返ってくる
        logger.error("Anthropic API が 400 を返しました: %s (request_id=%s)", e.message, e.request_id)
        stream.append(markdown_text="Claude API が受け付けませんでした。ログを確認してください（クレジット不足の可能性もあります）。")
    except anthropic.RateLimitError as e:
        logger.error("Anthropic API のレート制限 (request_id=%s)", e.request_id)
        stream.append(markdown_text="混み合っています。少し待ってからもう一度どうぞ。")
    except (anthropic.APIConnectionError, anthropic.APIStatusError) as e:
        logger.error("Anthropic API でエラー: %s (request_id=%s)", e, getattr(e, "request_id", None))
        stream.append(markdown_text="Claude API に接続できませんでした。")
    except SlackApiError as e:
        # 停止ボタンで Slack 側が先にストリームを閉じていると、append が失敗する
        logger.warning("Slack API エラー（停止済みの可能性）: %s", e.response["error"])
    finally:
        try:
            stream.stop(blocks=final_blocks)
        except SlackApiError as e:
            logger.warning("stream.stop が失敗（Slack 側が閉じ済みの可能性）: %s", e.response["error"])
        stop_flags.pop(thread_ts, None)
        client.agents_sessions_setStatus(channel_id=channel_id, thread_ts=thread_ts, status="active")


# Chapter 8: processing 中に出る停止ボタンが押されたときのイベント
@app.event("agent_session_stopped")
def handle_session_stopped(event):
    logger.info("agent_session_stopped: %s", event)
    flag = stop_flags.get(event["thread_ts"])
    if flag is not None:
        flag.set()


# Chapter 8: 返事の下の 👍👎 が押されたとき
@app.action("feedback")
def handle_feedback(ack, body, respond):
    ack()
    value = body["actions"][0]["value"]
    logger.info("feedback %s by %s", value, body["user"]["id"])
    respond(text="フィードバックありがとうございます！", response_type="ephemeral", replace_original=False)


@app.event("app_context_changed")
def handle_context_changed(event):
    logger.info("app_context_changed: %s", event)


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
