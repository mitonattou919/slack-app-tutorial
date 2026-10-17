---
title: "Slack App チュートリアル 練習課題の解答例"
tags:
  - slack-app
  - tutorial
  - learning-material
type: answers
created: 2026-10-17
description: "slack-app-tutorial.md の各章の練習課題について、ヒント・解答例・確かめ方・つまずきやすい点をまとめた解説"
related:
  - "[[Slack]]"
  - "[[Python]]"
  - "[[Block Kit]]"
---

# Slack App チュートリアル 練習課題の解答例

> `slack-app-tutorial.md` の各章の練習課題について、ヒントと解答例をまとめています。
> まず自分で試し、手が止まったら **ヒント** → それでも分からなければ **解答例** の順に開いてください。

---

## 使い方

### 解答例のファイル

解答例は、そのまま動くファイルとして `answers/` に置いてあります。中身は**その章の `main.py` に、課題の変更を加えたもの**です。

```text
answers/
├── 01_preparing/
│   ├── task1.py      ← Chapter 1 の課題 1 の解答例
│   └── task3.py
├── 02_messages/
│   ├── task1.py
│   ├── task2.py
│   └── task3.py
└── …（07_streaming まで同じ構成）
```

リポジトリのルートで、章のファイルと同じように起動できます。

```bash
uv run --env-file .env answers/02_messages/task1.py
```

章の `main.py` との違いは `diff` で確かめられます。自分の書いたコードと見比べるときにも使えます。

```bash
diff 02_messages/main.py answers/02_messages/task1.py
```

### マニフェスト

解答例は、どれも**その章の `manifest.yaml` のまま**で動きます。新しいスコープやイベントは必要ありません。

### 解答例は「一例」

ここに載せたのは書き方の一例です。動いて、課題の意図を満たしていれば、違う書き方でも正解です。

---

## Chapter 1: 準備と 5 分ハロー

### 課題 1（基本）: 挨拶の文言を変えて、再起動で反映されることを確かめる

<details>
<summary>ヒント</summary>

`handle_mention` の中の `say(...)` に渡している文字列を書き換えます。書き換えた後は、`Ctrl+C` でプログラムを止めてから起動し直さないと反映されません。

</details>

<details>
<summary>解答例（<code>answers/01_preparing/task1.py</code>）</summary>

```python
    say(f"やあ、<@{event['user']}> さん！ Practice Bot です。")
```

**確かめ方**: 起動し直してから `@practice-bot やあ` とメンションし、新しい文言で返ってくることを確認します。

**ポイント**: Python のプログラムは、起動した時点のコードで動き続けます。ファイルを保存しただけでは、動いているボットは変わりません。

</details>

### 課題 2（応用）: プログラムを止めた状態でメンションし、何も返ってこないことを確かめる

<details>
<summary>解説（コードの変更はありません）</summary>

`Ctrl+C` でプログラムを止めてから、Slack でメンションします。返事は来ません。

Slack はイベントを送ろうとしますが、受け取るプログラムがいないため、何も起きません。Slack App の「中身」は Slack の中ではなく、**あなたの PC で動いているプログラム**です。プログラムが止まればボットも止まります。本番でサーバーを止めない工夫が必要になる理由は、`slack-app-best-practices.md` の Chapter 1 で扱います。

</details>

### 課題 3（複合）: 返事にメンションの本文を含め、先頭に何が付いているか観察する

<details>
<summary>ヒント</summary>

メンションの本文は `event['text']` に入っています。f 文字列の中に `{event['text']}` と書けば、返事に埋め込めます。

</details>

<details>
<summary>解答例（<code>answers/01_preparing/task3.py</code>）</summary>

```python
    # 本文の先頭には <@ボットのID> が付いている（例: "<@U0789IJKL> やあ"）
    say(f"こんにちは、<@{event['user']}> さん！ 受け取った本文: {event['text']}")
```

**確かめ方**: `@practice-bot やあ` とメンションすると、返事の中の本文が `@practice-bot やあ` のように表示されます。ターミナルのログを見ると、実際に届いている本文は `<@U0789IJKL> やあ` のような形です。

**ポイント**: Slack 上では `@practice-bot` と見えていても、プログラムに届くのは `<@ユーザーID>` という形です。返事に `<@...>` を含めると、Slack がメンションとして表示し直します。本文から自分へのメンションを取り除きたいときは、`re.sub(r"<@[A-Z0-9]+>\s*", "", event["text"])` のように正規表現で消します。

</details>

---

## Chapter 2: メッセージとイベント

### 課題 1（基本）: 「bye」を含むメッセージに「またね！」とスレッドで返す

<details>
<summary>ヒント</summary>

`handle_hello` をまねて、`@app.message("bye")` のリスナーをもう 1 つ作ります。関数名は他と重ならない名前（例: `handle_bye`）にします。

</details>

<details>
<summary>解答例（<code>answers/02_messages/task1.py</code>）</summary>

```python
# 練習課題 1: 「bye」を含むメッセージにスレッドで返す
@app.message("bye")
def handle_bye(message, say):
    logger.info("bye from %s in %s", message["user"], message["channel"])
    reply_in_thread(say, message, "またね！")
```

**確かめ方**: チャンネルで `bye` と発言し、スレッドに「またね！」が付くことを確認します。

**つまずきやすい点**:
- 関数名を `handle_hello` のまま複製すると、Python の関数が上書きされて紛らわしくなります。リスナーごとに違う名前を付けます
- `hello bye` のように両方を含む発言には、**先に書いたリスナーだけ**が反応します。Bolt は、1 つのイベントに対して最初に一致したリスナーを実行します

</details>

### 課題 2（応用）: hello への返事を、発言した人への DM で送る

<details>
<summary>ヒント</summary>

`say` の代わりに `client.chat_postMessage(channel=..., text=...)` を使います。リスナーの引数に `client` を追加し、`channel` には発言した人のユーザー ID（`message["user"]`）を指定します。

</details>

<details>
<summary>解答例（<code>answers/02_messages/task2.py</code>）</summary>

```python
def handle_hello(message, client):
    logger.info("message from %s in %s: %s", message["user"], message["channel"], message["text"])
    # channel にユーザー ID を指定すると、そのユーザーへの DM になる
    client.chat_postMessage(channel=message["user"], text="hello を受け取りました（DM でお返事しています）")
```

**確かめ方**: チャンネルで `hello` と発言すると、チャンネルには何も返らず、サイドバーの Practice Bot との DM に返事が届きます。

**ポイント**: Bolt のリスナーは、引数の**名前**を見て必要なものを渡してくれます。`say` を使わなくなったら引数から外し、代わりに `client` を書きます。名前を間違える（例: `clinet`）と、エラーになります。

</details>

### 課題 3（複合）: チャンネル直下とスレッド内で返事の付き方を比べ、`reply_broadcast=True` を試す

<details>
<summary>ヒント</summary>

まずはコードを変えずに、チャンネル直下で `hello`、続いてボットの返事のスレッドの中で `hello` と発言して、返事の場所を比べます。次に、`reply_in_thread(...)` の最後の引数として `reply_broadcast=True` を足します。

</details>

<details>
<summary>解答例（<code>answers/02_messages/task3.py</code>）</summary>

```python
    # reply_broadcast=True は **kwargs を通って say に渡る。スレッドへの返事がチャンネルにも表示される
    reply_in_thread(say, message, f"hello を受け取りました、<@{message['user']}> さん", reply_broadcast=True)
```

**確かめ方**:
- 変更前: チャンネル直下の `hello` には新しいスレッドで、スレッド内の `hello` には同じスレッドで返事が付きます
- 変更後: スレッドへの返事が、「スレッドに返信しました」という形でチャンネルにも表示されます

**ポイント**: `reply_in_thread` は、知らない引数を `**kwargs` でまとめて `say` に渡します。ヘルパーを書き換えなくても、`say`（`chat.postMessage`）が受け付ける引数はそのまま使えます。

</details>

---

## Chapter 3: スラッシュコマンド

### 課題 1（基本）: `/practice-echo` の返事をチャンネル全員に見せる

<details>
<summary>ヒント</summary>

`respond(...)` に `response_type="in_channel"` を渡します。文字列を `text=` で渡す形に書き換えるのを忘れずに。

</details>

<details>
<summary>解答例（<code>answers/03_slash_commands/task1.py</code>）</summary>

```python
    respond(response_type="in_channel", text=f"あなたの入力: {command['text']}")
```

**確かめ方**: 返事の横に「あなただけに表示されています」が出なくなります。別のユーザー（サンドボックスのデモユーザーなど）でログインして見ると、確実に確かめられます。

**つまずきやすい点**: `respond("...", response_type="in_channel")` のように、文字列を先に書いて名前付きの引数を後ろに書くのは問題ありません。ただし、`respond(response_type="in_channel", "...")` のように名前付きの引数の後ろに文字列を書くと、Python の文法エラー（`SyntaxError`）になります。

</details>

### 課題 2（応用）: 入力が空のときに「何か入力してください」と返す

<details>
<summary>ヒント</summary>

`command['text']` が空文字かどうかを `if` で調べ、空なら別の返事をして `return` します。空白だけの入力も空とみなすなら、`.strip()` で前後の空白を取り除いてから調べます。

</details>

<details>
<summary>解答例（<code>answers/03_slash_commands/task2.py</code>）</summary>

```python
    if not command["text"].strip():
        respond("何か入力してください（例: /practice-echo こんにちは）")
        return
    respond(f"あなたの入力: {command['text']}")
```

**確かめ方**: `/practice-echo` だけを送ると案内が返り、`/practice-echo こんにちは` では今までどおりの返事が返ります。

**つまずきやすい点**: `ack()` は、入力のチェックより**前**に呼んだままにします。入力が空でも、Slack には 3 秒以内に「受け取った」と返す必要があるからです。

</details>

### 課題 3（複合）: 先頭が `public ` のときだけ全員に見せる

<details>
<summary>ヒント</summary>

`text.startswith("public ")` で先頭を調べます。返事から `public ` を取り除くには、`text.removeprefix("public ")` が使えます。

</details>

<details>
<summary>解答例（<code>answers/03_slash_commands/task3.py</code>）</summary>

```python
    text = command["text"]
    if text.startswith("public "):
        respond(response_type="in_channel", text=f"あなたの入力: {text.removeprefix('public ')}")
    else:
        respond(f"あなたの入力: {text}")
```

**確かめ方**: `/practice-echo public みなさんこんにちは` は全員に、`/practice-echo ひとりごと` は自分だけに表示されます。

**ポイント**: f 文字列の `{...}` の中でさらに文字列を書くときは、外側と違う種類の引用符（ここでは `'public '`）にしておくと読みやすくなります（Python 3.11 以前では、違う種類にしないとエラーになりました）。

</details>

---

## Chapter 4: Block Kit とボタン

### 課題 1（基本）: 承認メッセージの先頭に `header` ブロックを足す

<details>
<summary>ヒント</summary>

`blocks=[...]` のリストの**先頭**に、課題文の `header` ブロックを 1 つ足します。リストの要素の間のカンマを忘れずに。

</details>

<details>
<summary>解答例（<code>answers/04_block_kit/task1.py</code>）</summary>

```python
        blocks=[
            {"type": "header", "text": {"type": "plain_text", "text": "デプロイ承認"}},
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*staging* へのデプロイを承認しますか？"},
```

**確かめ方**: `approve` と発言すると、ボタン付きメッセージの上に大きな見出しが表示されます。

**つまずきやすい点**: `header` の `text` は `plain_text` しか使えません。`mrkdwn` にするとエラーになり、メッセージが送られません（ターミナルに `invalid_blocks` のエラーが出ます）。

</details>

### 課題 2（応用）: 「却下」ボタンを足し、押されたら「却下しました」に書き換える

<details>
<summary>ヒント</summary>

- `section` の `accessory` にはボタンを 1 つしか置けません。`accessory` を外して、`section` の後ろに `actions` ブロックを足し、その `elements` にボタンを 2 つ並べます
- 却下ボタンの `action_id` は `reject_button` にし、`@app.action("reject_button")` のリスナーを新しく作ります。中身は承認ボタンのリスナーとほぼ同じです

</details>

<details>
<summary>解答例（<code>answers/04_block_kit/task2.py</code>）</summary>

```python
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
```

```python
# 練習課題 2: 却下ボタン
@app.action("reject_button")
def handle_reject(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    logger.info("reject_button clicked by %s", user_id)
    respond(replace_original=True, text=f"<@{user_id}> さんが却下しました")
```

**確かめ方**: `approve` と発言し、緑の「承認」と赤の「却下」が並ぶことを確認します。それぞれ押して、メッセージが書き換わることを確かめます（2 回目は、もう一度 `approve` と発言してボタンを出し直します）。

**つまずきやすい点**:
- 却下ボタンを押すと警告マークが出る → `reject_button` のリスナーを作り忘れているか、`action_id` の綴りが違います
- 同じブロックの中に、`action_id` が同じボタンを 2 つ置くことはできません。ボタンごとに違う `action_id` を付けます

</details>

### 課題 3（複合）: 書き換え後のメッセージに、承認した人と時刻を表示する

<details>
<summary>ヒント</summary>

ファイルの先頭で `from datetime import datetime` を読み込み、`datetime.now().strftime("%Y-%m-%d %H:%M")` で「2026-10-15 10:00」のような文字列を作ります。承認した人は、すでに `user_id` に入っています。

</details>

<details>
<summary>解答例（<code>answers/04_block_kit/task3.py</code>）</summary>

```python
from datetime import datetime
```

```python
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    respond(replace_original=True, text=f"<@{user_id}> さんが {now} に承認しました")
```

**確かめ方**: 承認ボタンを押すと、「@あなた さんが 2026-10-15 10:00 に承認しました」のように書き換わります。

**ポイント**: `datetime.now()` は、**プログラムが動いている PC の時刻**です。本番のサーバーでは時刻のタイムゾーンが日本時間と違うことがあります。

</details>

---

## Chapter 5: モーダル

### 課題 1（基本）: モーダルのタイトルと送信ボタンの文言を変える

<details>
<summary>ヒント</summary>

`views_open` に渡している `view` の `title` と `submit` の `text` を書き換えます。

</details>

<details>
<summary>解答例（<code>answers/05_modals/task1.py</code>）</summary>

```python
            # title は 24 文字まで
            "title": {"type": "plain_text", "text": "ご意見箱"},
            "submit": {"type": "plain_text", "text": "投函する"},
```

**確かめ方**: `/practice-feedback` を実行し、新しいタイトルと送信ボタンが表示されることを確認します。

**つまずきやすい点**: モーダルの `title` と `submit` は **24 文字まで**です。長くするとモーダルが開かず、ターミナルに `invalid_arguments` などのエラーが出ます。

</details>

### 課題 2（応用）: 「お名前」の入力欄を足し、DM のお礼に名前を含める

<details>
<summary>ヒント</summary>

- `blocks` に、もう 1 つ `input` ブロックを足します。`block_id` は `name_block`、中の `action_id` は `name_input`、`multiline` は書きません
- 送信を受け取る側では、`body["view"]["state"]["values"]["name_block"]["name_input"]["value"]` で名前を取り出せます

</details>

<details>
<summary>解答例（<code>answers/05_modals/task2.py</code>）</summary>

```python
            "blocks": [
                {
                    "type": "input",
                    "block_id": "name_block",
                    "label": {"type": "plain_text", "text": "お名前"},
                    "element": {"type": "plain_text_input", "action_id": "name_input"},
                },
                {
                    "type": "input",
                    "block_id": "feedback_block",
```

```python
    values = body["view"]["state"]["values"]
    name = values["name_block"]["name_input"]["value"]
    value = values["feedback_block"]["feedback_input"]["value"]
```

```python
    client.chat_postMessage(channel=body["user"]["id"], text=f"{name} さん、フィードバックを受け付けました: {value}")
```

**確かめ方**: `/practice-feedback` で名前とご意見を入れて送信し、DM のお礼に名前が入っていることを確認します。

**ポイント**: `block_id` と `action_id` は、入力値を取り出すときの「住所」です。開く側と受け取る側で、綴りを一致させます。`input` ブロックは既定で入力必須なので、名前が空のまま送信しようとすると、Slack が自動で止めてくれます。

</details>

### 課題 3（複合）: 承認ボタンを押したら、承認理由を入力するモーダルを開く

<details>
<summary>ヒント 1: モーダルを開く</summary>

ボタン操作の `body` にも `trigger_id` が入っています。承認ボタンのリスナーで、`respond(...)` の代わりに `client.views_open(trigger_id=body["trigger_id"], view=...)` を呼びます。リスナーの引数は `respond` から `client` に変えます。

</details>

<details>
<summary>ヒント 2: 送信後に元のメッセージを書き換える</summary>

モーダルの送信を受け取るリスナーには、ボタンの付いていたメッセージの情報が届きません。モーダルを開くときに、`view` の `private_metadata`（モーダルに持たせておける文字列）へ、元のメッセージのチャンネル（`body["container"]["channel_id"]`）と ID（`body["container"]["message_ts"]`）を入れておきます。送信を受け取ったら、それを使って `client.chat_update(...)` でメッセージを書き換えます。

</details>

<details>
<summary>解答例（<code>answers/05_modals/task3.py</code>）</summary>

```python
import json
```

```python
@app.action("approve_button")
def handle_approve(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    logger.info("approve_button clicked by %s", user_id)
    # ボタン操作にも trigger_id が付いてくる。3 秒以内・1 回限りなので、先にモーダルを開く
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "approve_reason_modal",
            # モーダルの送信時に、書き換える元のメッセージが分かるように持たせておく
            "private_metadata": json.dumps(
                {"channel": body["container"]["channel_id"], "ts": body["container"]["message_ts"]}
            ),
            "title": {"type": "plain_text", "text": "承認理由"},
            "submit": {"type": "plain_text", "text": "承認する"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "reason_block",
                    "label": {"type": "plain_text", "text": "承認する理由"},
                    "element": {"type": "plain_text_input", "action_id": "reason_input"},
                }
            ],
        },
    )


@app.view("approve_reason_modal")
def handle_approve_reason(ack, body, view, client):
    ack()
    user_id = body["user"]["id"]
    reason = view["state"]["values"]["reason_block"]["reason_input"]["value"]
    logger.info("approval reason from %s: %s", user_id, reason)
    message = json.loads(view["private_metadata"])
    text = f"<@{user_id}> さんが承認しました（理由: {reason}）"
    # 元のメッセージをボタンなしの内容に書き換える
    client.chat_update(
        channel=message["channel"],
        ts=message["ts"],
        text=text,
        blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": text}}],
    )
```

**確かめ方**: `approve` と発言してボタンを押すと、理由の入力欄があるモーダルが開きます。理由を入れて「承認する」を押すと、元のメッセージが「@あなた さんが承認しました（理由: …）」に書き換わり、ボタンが消えます。

**つまずきやすい点**:
- モーダルが開かない → `views_open` の前に時間のかかる処理を入れていないか確認します（`trigger_id` は 3 秒で失効）
- モーダルの送信後に警告が出る → `@app.view` に指定した名前と、モーダルの `callback_id` が一致しているか確認します
- `private_metadata` には文字列しか入らないため、`json.dumps` で文字列にして入れ、`json.loads` で戻します

</details>

---

## Chapter 6: App Home

### 課題 1（基本）: ホームに `divider` ブロックと説明文を足す

<details>
<summary>ヒント</summary>

`views_publish` に渡している `blocks` のリストの最後に、`{"type": "divider"}` と、もう 1 つの `section` ブロックを足します。

</details>

<details>
<summary>解答例（<code>answers/06_app_home/task1.py</code>）</summary>

```python
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "チャンネルで `hello` や `approve` と発言しても反応します。",
                        },
                    },
```

**確かめ方**: 起動し直してから、ホームタブを**開き直します**（別のタブに切り替えてから戻る）。区切り線と説明文が増えていれば成功です。

**ポイント**: ホームの画面は、`app_home_opened` が届いて `views_publish` を呼んだときにだけ更新されます。プログラムを変えても、ホームタブを開き直すまで見た目は変わりません。

</details>

### 課題 2（応用）: ホームに更新ボタンを置き、押されたら現在時刻を表示し直す

<details>
<summary>ヒント</summary>

- ホームを組み立てて `views_publish` する処理を、`publish_home(client, user_id)` のような関数に切り出すと、イベントとボタンの両方から呼べて楽になります
- ボタンは `actions` ブロックに置き、`action_id` を `home_refresh` にします。押されたら `@app.action("home_refresh")` のリスナーで `ack()` してから、`body["user"]["id"]` のユーザーに対して `publish_home` を呼びます

</details>

<details>
<summary>解答例（<code>answers/06_app_home/task2.py</code>）</summary>

```python
from datetime import datetime
```

```python
# Chapter 6: App Home
# ホームを組み立てて公開する処理を関数にまとめ、イベントとボタンの両方から呼ぶ
def publish_home(client, user_id):
    now = datetime.now().strftime("%H:%M:%S")
    client.views_publish(
        user_id=user_id,
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
                        "text": f"<@{user_id}> さん、使えるコマンドは `/practice-echo` と `/practice-feedback` です。",
                    },
                },
                {"type": "section", "text": {"type": "mrkdwn", "text": f"最終更新: {now}"}},
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "更新"},
                            "action_id": "home_refresh",
                        }
                    ],
                },
            ],
        },
    )


@app.event("app_home_opened")
def update_home_tab(client, event):
    logger.info("app_home_opened by %s (tab=%s)", event["user"], event.get("tab"))
    if event.get("tab") != "home":
        return
    try:
        publish_home(client, event["user"])
    except Exception:
        logger.exception("failed to publish home tab")


# 練習課題 2: ホームの更新ボタン
@app.action("home_refresh")
def handle_home_refresh(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    logger.info("home_refresh clicked by %s", user_id)
    publish_home(client, user_id)
```

**確かめ方**: ホームタブの「更新」ボタンを押すたびに、「最終更新」の時刻が新しくなります。

**つまずきやすい点**: ホームのボタンには `response_url` がありません。メッセージのボタン（Chapter 4）のように `respond(replace_original=True, ...)` では書き換えられないので、`views_publish` でホーム全体を出し直します。

</details>

### 課題 3（複合）: フィードバックの件数を数えて、ホームに表示する

<details>
<summary>ヒント</summary>

- 関数の外（`app = App(...)` の下など）に `feedback_count = 0` を用意し、`handle_feedback` で受け付けたときに 1 増やします
- 関数の中で外の変数を**書き換える**ときは、関数の中で `global feedback_count` と宣言します（読むだけなら不要です）

</details>

<details>
<summary>解答例（<code>answers/06_app_home/task3.py</code>）</summary>

```python
# 練習課題 3: フィードバックの件数（プロセスのメモリ上にあるので、再起動すると 0 に戻る）
feedback_count = 0
```

```python
    ack()
    global feedback_count
    feedback_count += 1
    logger.info("feedback from %s: %s (total %d)", body["user"]["id"], value, feedback_count)
```

```python
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"これまでのフィードバック: {feedback_count} 件"},
                    },
```

**確かめ方**: `/practice-feedback` で 2 回送信してから、ホームタブを開き直すと「これまでのフィードバック: 2 件」と表示されます。プログラムを再起動すると 0 件に戻ります。

**ポイント**: 変数に入れた値は、プログラムのメモリの中にしかありません。再起動で消えるうえ、本番でサーバーを 2 台にすると台ごとに別々の値になります。消えては困る値をどこに置くかは、`slack-app-best-practices.md` の Chapter 6「スケールと状態」で扱います。

</details>

---

## Chapter 7: ストリーミング返信

### 課題 1（基本）: 流れる文章と待ち時間を変えて、表示の変化を観察する

<details>
<summary>ヒント</summary>

`for` で回しているリストの中身と、`time.sleep(...)` の秒数を変えます。

</details>

<details>
<summary>解答例（<code>answers/07_streaming/task1.py</code>）</summary>

```python
    for word in ["ゆっくり", "と、", "少し", "ずつ", "表示", "して", "います。"]:
        stream.append(markdown_text=word)
        time.sleep(1.0)
```

**確かめ方**: `stream` と発言し、1 秒ごとに文章が伸びていくことを確認します。

**ポイント**: 待ち時間を極端に短くする（例: `0.01`）と、Slack の API を短時間に何度も呼ぶことになり、レート制限（呼び出し回数の上限）に当たることがあります。

</details>

### 課題 2（応用）: 届いたメッセージの本文を 1 文字ずつ流して返す

<details>
<summary>ヒント</summary>

Python の文字列は、`for char in "文字列":` で 1 文字ずつ取り出せます。本文は `message["text"]` にあるので、リスナーの引数に `message` があることを確認します（Chapter 7 の `main.py` には、ログのためにすでに入っています）。

</details>

<details>
<summary>解答例（<code>answers/07_streaming/task2.py</code>）</summary>

```python
    for char in message["text"]:
        stream.append(markdown_text=char)
        time.sleep(0.1)
```

**確かめ方**: `stream テストです` と発言すると、同じ文章が 1 文字ずつ流れて返ってきます。

**つまずきやすい点**: 文字が 1 文字ずつではなく、最後にまとめて表示される → `say_stream()` に `buffer_size=1` を渡しているか確認します。既定では 256 文字たまるまで送られません。

</details>

### 課題 3（複合）: メンションへの返事をストリーミングにする

<details>
<summary>ヒント</summary>

`handle_mention` の引数を `say` から `say_stream` に変え、`handle_stream` と同じ形（`say_stream(buffer_size=1)` → `append` を繰り返す → `stop`）で返事を流します。

</details>

<details>
<summary>解答例（<code>answers/07_streaming/task3.py</code>）</summary>

```python
def handle_mention(event, say_stream):
    logger.info("app_mention from %s in %s: %s", event["user"], event["channel"], event["text"])
    # メンションのリスナーでも say_stream を受け取れる。スレッドの決め方も自動
    stream = say_stream(buffer_size=1)
    # LLM を使う場合は、このリストの代わりに、LLM のストリーミング応答の断片を 1 つずつ append する
    for word in ["こんにちは！ ", "メンション ", "にも ", "ストリーミング ", "で ", "返事 ", "しています。"]:
        stream.append(markdown_text=word)
        time.sleep(0.5)
    stream.stop()
```

**確かめ方**: `@practice-bot やあ` とメンションすると、スレッドに返事が少しずつ流れてきます。

**LLM を使う場合**: 多くの LLM の API は、応答を少しずつ受け取る「ストリーミング」の機能を持っています。上の `for` の代わりに、LLM から断片が届くたびに `stream.append(markdown_text=断片)` を呼べば、生成 AI のボットになります。このとき `time.sleep` は不要で、`buffer_size` は既定のまま（ある程度まとめて送る）にすると、Slack の API の呼び出し回数を抑えられます。

**つまずきやすい点**: `stream.stop()` を呼び忘れると、ストリームが終わらないままになります。途中で例外が起きても止められるよう、本番では `try` / `finally` で囲みます。

</details>
