---
title: "Slack App チュートリアル"
tags:
  - slack-app
  - tutorial
  - learning-material
type: tutorial
created: 2026-10-15
description: "uv と Bolt for Python で、メンション・コマンド・ボタン・モーダル・App Home・ストリーミングに対応した練習用 Slack ボットを手元で動かし、応用編でエージェント画面（進捗表示・停止ボタン）まで試すハンズオン教材"
related:
  - "[[Slack]]"
  - "[[Python]]"
  - "[[uv]]"
  - "[[Block Kit]]"
  - "[[WebSocket]]"
---

# Slack App チュートリアル

> Slack App（いわゆる Slack ボット）を初めて作る人向けのハンズオン教材です。uv と Bolt for Python を使い、手元の PC で動く練習用ボットを 1 つ育てながら、メンション・メッセージ・スラッシュコマンド・ボタン・モーダル・App Home・ストリーミング返信まで体験します。
> 各章のコードとマニフェストは、リポジトリの章ごとのディレクトリ（`01_preparing/` など）に用意してあります。コードを打ち込む時間を省き、「何が届いて、何を返すか」を読み解くことに時間を使います。
> 全体像を先に掴みたい方 → `slack-app-overview.md`
> 本番運用まで考えたくなったら → `slack-app-best-practices.md`
>
> 動作確認環境（2026-10-15 時点）: uv 0.9.26 / 最新 0.13.1、Python 3.14、slack-bolt 1.30.0、slack-sdk 3.45.0

---

## Chapter 0: Slack App 開発とは：このチュートリアルで作るもの

### 1. 完成形

章を追うごとに機能を足し、最後には次のことができる **Practice Bot** になります。

| 章 | 機能 | 使う仕組み | ディレクトリ |
|---|---|---|---|
| 1 | `@practice-bot` とメンションすると挨拶を返す | Events API（`app_mention`） | `01_preparing/` |
| 2 | 「hello」を含む発言や DM に、スレッドで反応する | メッセージイベント + 共通ヘルパー | `02_messages/` |
| 3 | `/practice-echo` で入力を返す | スラッシュコマンド | `03_slash_commands/` |
| 4 | 承認ボタン付きメッセージを送り、押されたら書き換える | Block Kit + アクション | `04_block_kit/` |
| 5 | `/practice-feedback` で入力フォームを開く | モーダル | `05_modals/` |
| 6 | アプリのホームタブに案内を表示する | App Home | `06_app_home/` |
| 7 | AI のように文字を少しずつ表示する | ストリーミング | `07_streaming/` |
| 8（応用編） | 調査の進捗を段階的に見せ、停止ボタンと 👍👎 に対応する | エージェント画面（`agent_view`） | `08_agents/` |

各ディレクトリには、その章を終えた時点の `main.py` と `manifest.yaml` が入っています。Chapter 1〜7 の中身は**それまでの章を全部含んだ状態**なので、途中の章から始めることもできます。応用編の Chapter 8 だけは、**専用の別 App** で動かす単独のプログラムです（理由は Chapter 8 で説明します）。

### 2. 手元の PC で動かす理由：Socket Mode

普通の Web サービス連携では、Slack から届く通知を受けるために **インターネットに公開された HTTPS の URL** が必要です。このチュートリアルでは **Socket Mode** を使います。手元のプログラムから Slack へ WebSocket（つなぎっぱなしの双方向通信）を張り、その上で通知を受け取る方式です。

```text
あなたの PC                          Slack
┌──────────────┐   WebSocket   ┌──────────────┐
│ main.py      │ ────────────▶ │              │
│ (Bolt)       │ ◀──────────── │ ワークスペース │
└──────────────┘  イベント通知   └──────────────┘
   公開 URL 不要・ファイアウォール内でも動く
```

公式も「開発やローカル環境では Socket Mode が手軽」としています。本番運用では HTTP 方式が推奨される点は、overview の Chapter 3 を参照してください。

### 3. 練習用ボットは「新人アシスタント」

Practice Bot は、**入館証（トークン）を渡された新人アシスタント**だと思って育ててください。最初は「呼ばれたら挨拶する」だけですが、章ごとに「できること（スコープ）」と「担当する窓口（イベント・コマンド）」を増やしていきます。新しい仕事を任せるたびに入館証を書き換える（再インストール）必要がある、という感覚を Chapter 2 で体験します。

---

## Chapter 1: 準備と 5 分ハロー

> `slack-app-prework.md`（準備）を済ませた方は、1〜2 は飛ばして「3. マニフェストからアプリを作る」から始めてください。準備の手順には、つまずいたときの対処も載っています。

### 1. 必要なもの

| もの | 確認方法・入手先 |
|---|---|
| uv | `uv --version` で表示されること |
| Git | `git --version` で表示されること |
| 練習用の Slack ワークスペース | 下記のどちらか |
| ブラウザ | Slack の App 設定画面（https://api.slack.com/apps）を使う |

```bash
uv --version   # 例: uv 0.13.1。表示されなければ uv をインストールしてください
git --version
```

⚠ **会社のワークスペースでは練習しないでください。** アプリの追加に管理者の承認が必要なことが多く、練習用のメッセージが同僚に見えてしまいます。練習用ワークスペースは次のどちらかで用意します。

- **Developer Program のサンドボックス（おすすめ）**: 無料で作れる練習用ワークスペースです。作り方と、期限切れ（基本サンドボックスは 1 か月でアーカイブ）になったときの作り直し方は、`slack-app-prework.md` の「3. Slack Developer Program に参加し、サンドボックスを作る」を参照してください
- **自分で作る無料ワークスペース**: Slack の通常の手順で新規作成します

### 2. リポジトリを取得する

ハンズオン用のリポジトリを取得し、依存関係（Bolt for Python など）をインストールします。

```bash
git clone https://github.com/mitonattou919/slack-app-tutorial.git
cd slack-app-tutorial
uv sync
```

`uv sync` を実行すると、`pyproject.toml` と `uv.lock`（バージョン固定ファイル）に従って `.venv/`（仮想環境）が作られ、依存関係がインストールされます。

```text
slack-app-tutorial/
├── 01_preparing/          ← Chapter 1 の main.py と manifest.yaml
│   ├── main.py
│   └── manifest.yaml
├── 02_messages/           ← Chapter 2（以下、章ごとに同じ構成）
├── 03_slash_commands/
├── 04_block_kit/
├── 05_modals/
├── 06_app_home/
├── 07_streaming/          ← Chapter 1〜7 の完成形
├── 08_agents/             ← 応用編 Chapter 8（別 App 用。単独で動く）
├── answers/               ← 練習課題の解答例（章ごと）
├── slack_helpers/         ← 各章で共通して使うヘルパー（Chapter 2 で扱う）
├── docs/                  ← この教材
├── .env.example           ← トークンのひな形
├── .gitignore             ← .env を除外済み
├── pyproject.toml
└── uv.lock
```

> ゼロから自分で作る場合は、`uv init --no-package slack-app-practice` → `cd slack-app-practice` → `uv add slack-bolt` で同じ準備ができます。その場合は各章の `main.py` の中身を自分のファイルに書き写し、Chapter 2 の `slack_helpers` も同じディレクトリに置いてください。

### 3. マニフェストからアプリを作る

Slack App の設定は **App Manifest**（設定一式を書いた YAML）で作るのが確実です。Chapter 1 のマニフェストは `01_preparing/manifest.yaml` に用意してあります。中身は次のとおりです。

```yaml
display_information:
  name: Practice Bot
features:
  bot_user:
    display_name: practice-bot
    always_online: true
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - chat:write
settings:
  event_subscriptions:
    bot_events:
      - app_mention
  socket_mode_enabled: true
```

| 部分 | 意味 |
|---|---|
| `bot_user` | チャンネルで発言する「顔」となるボットユーザー |
| `oauth_config.scopes.bot` | ボットに許可する操作。メンションを読む（`app_mentions:read`）と投稿する（`chat:write`） |
| `event_subscriptions.bot_events` | 通知してほしい出来事。ここではメンション（`app_mention`） |
| `socket_mode_enabled` | Socket Mode で受け取る |

続いてブラウザで操作します。

1. https://api.slack.com/apps を開き、**Create New App** → **From a manifest** を選ぶ
2. 練習用ワークスペースを選ぶ
3. YAML のタブに `01_preparing/manifest.yaml` の内容を貼り付け、作成する

> 画面の名称や配置は 2026-10 時点のものです。変わっている場合は、同じ意味のボタンを探してください。

### 4. 2 種類のトークンを取得する

Socket Mode のボットには、役割の違う 2 つのトークンが必要です。次の順に操作します。

1. **Basic Information** の **App-Level Tokens** で、トークンを作成する（名前は `practice-socket` など何でもよい）。スコープに `connections:write` を追加して作成し、表示された `xapp-` で始まる値を控える
2. **Install App**（または **OAuth & Permissions**）で **Install to Workspace** を押し、許可画面で許可する
3. インストール後に表示される **Bot User OAuth Token**（`xoxb-` で始まる値）を控える

| トークン | 形 | 役割 | 取得場所 |
|---|---|---|---|
| **App-level token** | `xapp-` で始まる | WebSocket をつなぐ | **Basic Information** → **App-Level Tokens** で作成。スコープに `connections:write` を付ける |
| **Bot token** | `xoxb-` で始まる | ボットとして投稿する | アプリをワークスペースに**インストール**すると発行される（**Install App** または **OAuth & Permissions** に表示） |

取得したら、リポジトリのルートでひな形 `.env.example` を `.env` にコピーし、`=` の右側を自分のトークンに置き換えます。

```bash
cp .env.example .env
```

```bash
# .env（Git には入れない。.gitignore で除外済み）
SLACK_BOT_TOKEN=xoxb-で始まる値をここに貼る
SLACK_APP_TOKEN=xapp-で始まる値をここに貼る
```

`.env` はルートに 1 つだけ置き、全章で共用します。

⚠ トークンはパスワードと同じです。チャットやスクリーンショットに載せないでください。

### 5. 最初のコードを読んで動かす

`01_preparing/main.py` を開きます。中身は次のとおりです。

```python
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
    say(f"こんにちは、<@{event['user']}> さん！")


if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

- `@app.event("app_mention")` は「メンションされたら、この関数を呼ぶ」という登録（リスナー）です
- `say()` は、イベントが起きたチャンネルへ投稿します
- `<@ユーザーID>` と書くと、Slack 上ではメンションとして表示されます
- `logging.basicConfig(...)` は、ログをターミナル（コンソール）に表示する設定です。各リスナーの先頭の `logger.info(...)` で「何が届いたか」を 1 行ずつ表示します。以降の章のリスナーも、すべて同じようにログを出します

リポジトリのルートで、`.env` を読み込んで起動します。

```bash
uv run --env-file .env 01_preparing/main.py
```

`Bolt app is running!` という起動ログが出たら起動は成功です。ただし、このログは Slack との接続が成功した保証ではありません（WebSocket の接続が拒否されていても出ます）。接続できているかは、次の節で実際にメンションして、**返事が来ること**で確かめます。以降の章も、**ルートで `uv run --env-file .env <章のディレクトリ>/main.py`** の形で起動します。

### 6. 5 分で成功体験

ワークスペースとトークンの準備ができていれば、ここからは 5 分で終わります。Slack で練習用チャンネル（例: `#bot-practice`）を作り、ボットを招待してからメンションします。

```text
/invite @practice-bot
@practice-bot やあ
```

`こんにちは、@あなた さん！` と返ってきたら成功です。**「Slack で起きた出来事 → 手元のプログラム → Slack へ投稿」** という、Slack App の基本の往復が完成しました。

ターミナルには、届いたメンションのログが表示されます（ID は環境によって変わります）。

```text
2026-10-15 10:00:00,123 INFO __main__ app_mention from U0123ABCD in C0456EFGH: <@U0789IJKL> やあ
```

| 部分 | 意味 |
|---|---|
| `INFO` | ログの重要度。`WARNING` や `ERROR` は問題が起きたときに出る |
| `__main__` | ログを出したモジュール。Bolt 自身のログは `slack_bolt...` のように表示される |
| `U...` / `C...` | 発言したユーザーの ID と、チャンネルの ID |

Slack から届いた中身をすべて見たいときは、`.env` に `LOG_LEVEL=DEBUG` を追加して起動し直します。Bolt が受け取ったリクエストの詳細まで表示されるので、「どんな JSON が届いているのか」を観察するのに便利です（量が多いので、見終わったら行を消して戻します）。

止めるときは、ターミナルで `Ctrl+C` を押します。

> **うまくいかない時**:
> - `KeyError: 'SLACK_BOT_TOKEN'` → `.env` が読めていません。リポジトリのルート（`.env` がある場所）で `--env-file .env` を付けて起動しているか確認します
> - `invalid_auth` → トークンのコピーミスです。前後の空白や、`xoxb-` と `xapp-` の取り違えを確認します
> - 起動はするが反応がない → ターミナルに `app_mention from ...` のログが出ているかを見ます。出ていなければイベントが届いていません（ボットをチャンネルに招待したか、プログラムが起動したままか確認します）。出ているのに返事がなければ、その後に表示される `ERROR` のログを確認します
> - `Bolt app is running!` は出るのに、ずっと反応がない、または同じ警告を繰り返す → 通信が拒否されている可能性があります。サンドボックス（sbx）で動かしている場合は、`slack-app-prework.md` の「sbx で動かす場合」を確認します
> - `WARNING Unhandled request ... 404` が出る → 正常です。ボットが購読しているイベントのうち、担当するリスナーがないものが届いたときに出ます。エラーではありません

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 1（動くコードは `answers/01_preparing/`）

練習課題では、その章のディレクトリの `main.py` を直接書き換えます。書き換えは次の章のディレクトリには引き継がれません。元に戻したいときは `git restore 01_preparing/main.py` のように実行します。

1. **基本**: 挨拶の文言を変え、プログラムを再起動して反映されることを確認する
2. **応用**: プログラムを止めた状態でメンションし、何も返ってこないことを確かめる。「自前ホストの App は、手元のプログラムが止まると止まる」ことを体験する（停止中の確認は **1 分以上**待ちます。また、起動し直す前に別のメンションを送らないでください。Slack の再送で、後から返事が届くことがあります）
3. **複合**: 返事に、メンションされた本文（`event['text']`）を含める。本文の先頭に `<@ボットのID>` が付いていることを観察する

---

## Chapter 2: メッセージとイベント

### 1. メンション以外の発言にも反応したい

Chapter 1 のボットは、メンションされたときしか反応しません。チャンネルの普通の発言や DM に反応させるには、**新しいイベントの購読**と、**それを読むためのスコープ**が必要です。

| 反応したいもの | イベント | 必要なスコープ |
|---|---|---|
| 公開チャンネルの発言 | `message.channels` | `channels:history` |
| ボットとの DM | `message.im` | `im:history` |

### 2. マニフェストを更新して再インストールする

Chapter 2 のマニフェストは `02_messages/manifest.yaml` です。Chapter 1 から追加したのは、`app_home`、スコープ 2 つ、イベント 2 つです。

```yaml
features:
  app_home:                              # 追加
    messages_tab_enabled: true
    messages_tab_read_only_enabled: false
  # （bot_user は変更なし）
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history                 # 追加
      - chat:write
      - im:history                       # 追加
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.channels                 # 追加
      - message.im                       # 追加
```

`app_home` の 2 行は、ユーザーがボットに DM を送れるようにする設定です。

App 設定画面の **App Manifest** を開き、`02_messages/manifest.yaml` の内容に丸ごと貼り替えて保存します。⭐ **スコープを追加したら、アプリの再インストールが必要です。** 画面上部に再インストールの案内が出るので、それに従ってください。再インストール後に Bot token が変わっていたら、`.env` も更新します。

### 3. 「hello」に反応するコード

`02_messages/main.py` を開きます。Chapter 1 のリスナーに加えて、次のリスナーが入っています。

```python
# Chapter 2: 「hello」を含むメッセージに反応する
@app.message("hello")
def handle_hello(message, say):
    logger.info("message from %s in %s: %s", message.get("user"), message["channel"], message["text"])
    # ボットの発言（subtype: bot_message）には user がないので、何もしない
    if "user" not in message:
        return
    reply_in_thread(say, message, f"hello を受け取りました、<@{message['user']}> さん")
```

`@app.message("hello")` は、「hello」を含むメッセージが届いたときに呼ばれるリスナーです。`reply_in_thread` は、返事を**スレッドに**書くための共通ヘルパーです（次の節で説明します）。

`if "user" not in message: return` は、他のボットの発言を無視するためのガードです。ボットの発言（`subtype: bot_message`）には `user` がなく、そのまま `message["user"]` を読むと `KeyError` になります。

プログラムを Chapter 2 のもので起動し直します（`Ctrl+C` で止めてから）。

```bash
uv run --env-file .env 02_messages/main.py
```

チャンネルで `hello` と発言すると、その発言へのスレッド返信として返事が届きます。続いて、サイドバーの Practice Bot を開き、DM で `hello` と送ってみます。

> ボット自身の発言（「hello を受け取りました…」）にも「hello」が含まれますが、Bolt は既定でボット自身のイベントを無視するため、無限ループにはなりません。

> **うまくいかない時**:
> - `Hello` や `HELLO` に反応しない → 文字列での指定は大文字と小文字を区別します
> - `@practice-bot hello` と送ると 2 回返事が来る → メンションのリスナーと hello のリスナーの**両方**が反応しています。メンションも「hello を含むメッセージ」でもあるためで、不具合ではなく、イベントが 2 種類届いているだけです
> - DM で送れない → マニフェストの `app_home` の 2 行が保存されているか確認し、Slack を再読み込みします
> - `hello` や `bye` などの発言で `WARNING Unhandled request ... 404` が出る → 正常です。ボットは発言のイベントをすべて受け取りますが、一致するリスナーがないものは「担当なし」として警告されるだけで、エラーではありません
> - `ModuleNotFoundError: No module named 'slack_helpers'` → リポジトリのルートで `uv sync` を実行してから、`uv run` で起動します

### 4. スレッドに返す：共通ヘルパー `reply_in_thread`

ボットがチャンネル直下に返事を書き続けると、チャンネルがボットの発言で埋まってしまいます。返事は**元の発言のスレッドに**書くのが行儀のよい返し方です。この先の章でも何度も使うので、リポジトリの `slack_helpers/threads.py` に関数として切り出してあります。

```python
def reply_in_thread(say, message, text, **kwargs):
    thread_ts = message.get("thread_ts", message["ts"])
    return say(text=text, thread_ts=thread_ts, **kwargs)
```

| 部分 | 意味 |
|---|---|
| `message["ts"]` | 発言そのものの ID（タイムスタンプ）。これを `thread_ts` に指定すると、その発言を起点にスレッドができる |
| `message.get("thread_ts", ...)` | 発言がすでにスレッドの中にある場合は、親のスレッドの ID が入っている。そのスレッドに返す |
| `**kwargs` | `blocks` など、`say` に渡したい残りの引数をそのまま渡す（Chapter 4 で使う） |

```text
チャンネル直下の発言（ts=100）       → thread_ts=100 で返す（新しいスレッドができる）
スレッド内の発言（ts=150, thread_ts=120）→ thread_ts=120 で返す（同じスレッドに続ける）
```

使う側では、`from slack_helpers import reply_in_thread` で読み込みます。リポジトリのルートは `uv sync` でパッケージとしてインストールされているため、どの章のディレクトリの `main.py` からでも同じように import できます。

Chapter 2 からは、Chapter 1 のメンションへの返事も `reply_in_thread` に切り替えています（`02_messages/main.py` の先頭のリスナー）。メッセージイベント（`message`）でもメンションイベント（`event`）でも、`ts` と `thread_ts` を同じ形で持っているため、同じヘルパーが使えます。

### 5. `say` と `client.chat_postMessage` の違い

| 書き方 | 投稿先 | 使いどころ |
|---|---|---|
| `say("...")` | イベントが起きた会話 | 「その場で返事」 |
| `reply_in_thread(say, message, "...")` | イベントが起きた会話のスレッド | 「その場で、スレッドに返事」 |
| `client.chat_postMessage(channel=..., text=...)` | 指定した任意の会話 | 別のチャンネルへの通知、ユーザーへの DM |

`client` はリスナーの引数で受け取れる Web API クライアントです。`channel` にユーザー ID を指定すると、そのユーザーへの DM になります。`thread_ts` を指定すればスレッドにも書けます。

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 2（動くコードは `answers/02_messages/`）

1. **基本**: 「bye」を含むメッセージに「またね！」とスレッドで返すリスナーを、`reply_in_thread` を使って追加する
2. **応用**: hello に反応したとき、`reply_in_thread` ではなく `client.chat_postMessage` を使って、発言した人に DM で返事を送る（リスナーの引数に `client` を追加し、`channel=message["user"]` を指定）
3. **複合**: `hello` を、チャンネル直下とスレッドの中の両方で発言し、返事がどこに付くかを比べる。続いて `reply_in_thread(say, message, "...", reply_broadcast=True)` と書き換え、スレッドへの返事がチャンネルにも表示されることを確かめる（`**kwargs` で `say` に引数がそのまま渡ることを体験する）

---

## Chapter 3: スラッシュコマンド

### 1. 明示的に呼び出す入口

メッセージへの反応は便利ですが、「hello」という単語を偶然含む発言にも反応してしまいます。**スラッシュコマンド**は、`/practice-echo こんにちは` のように明示的に呼び出す入口です。

### 2. マニフェストにコマンドを追加する

Chapter 3 のマニフェストは `03_slash_commands/manifest.yaml` です。Chapter 2 から、`slash_commands`、スコープ `commands`、`interactivity` を追加しています。

```yaml
features:
  # （app_home と bot_user は変更なし）
  slash_commands:                        # 追加
    - command: /practice-echo
      description: 入力した文字をそのまま返します
      usage_hint: "[返したい文字]"
      should_escape: false
oauth_config:
  scopes:
    bot:
      # （既存のスコープに加えて）
      - commands                         # 追加
settings:
  # （event_subscriptions は変更なし）
  interactivity:                         # 追加
    is_enabled: true
  socket_mode_enabled: true
```

| 項目 | 意味 |
|---|---|
| `command` | コマンド名。先頭に `/` を付け、最大 32 文字 |
| `usage_hint` | 入力欄に表示されるヒント |
| `interactivity.is_enabled` | ボタン・モーダルなどの操作を受け取る設定（Chapter 4 以降で使うため、ここで先に有効にしておく） |

Socket Mode を使っているので、コマンドの Request URL（`url`）は書きません。App Manifest を `03_slash_commands/manifest.yaml` の内容に貼り替えて保存したら、スコープが増えたので再インストールします。

### 3. コマンドを処理するコード

`03_slash_commands/main.py` には、次のリスナーが追加されています。

```python
# Chapter 3: スラッシュコマンド
@app.command("/practice-echo")
def handle_echo(ack, respond, command):
    ack()
    logger.info("/practice-echo from %s: %s", command["user_id"], command["text"])
    respond(f"あなたの入力: {command['text']}")
```

| 道具 | 役割 |
|---|---|
| `ack()` | ⭐ 「受け取りました」を Slack に返す。**3 秒以内に呼ばないとユーザーにエラーが表示される** |
| `respond()` | このコマンドへの返事を送る |
| `command['text']` | コマンド名の後ろに入力された文字 |

> スラッシュコマンドには「返事を付ける元の発言」（`ts`）がないため、`reply_in_thread` ではなく `respond()` で返します。

Chapter 3 のもので起動し直します。

```bash
uv run --env-file .env 03_slash_commands/main.py
```

チャンネルで `/practice-echo こんにちは` と入力します。返事の横に「あなただけに表示されています」という表示が出るはずです。スラッシュコマンドの返事は、既定では **ephemeral**（実行した本人だけに見える）になります。

### 4. チャンネル全員に見せる

全員に見せたいときは `response_type="in_channel"` を指定します。

```python
respond(response_type="in_channel", text=f"あなたの入力: {command['text']}")
```

> **うまくいかない時**:
> - コマンドが候補に出てこない → マニフェストの保存と再インストールを確認し、Slack を再読み込みします
> - コマンドを実行するとエラーが表示される → プログラムが起動していないか、`ack()` が呼ばれていません
> - スレッドの中で実行できない → 自作のスラッシュコマンドはスレッド内では使えない仕様です
> - リスナーのログ（`logger.info`）は出ているのに、返事が Slack に表示されない → `respond()` は、`response_url`（`hooks.slack.com`）への通信に失敗しても、例外にもエラーログにもなりません。サンドボックス（sbx）などで `hooks.slack.com` への通信が許可されていないと、この状態になります。`slack-app-prework.md` の「sbx で動かす場合」を確認します

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 3（動くコードは `answers/03_slash_commands/`）

1. **基本**: `/practice-echo` の返事を `in_channel` に変え、全員に見えることを確認する
2. **応用**: 入力が空のとき（`command['text']` が空文字）に「何か入力してください」と返す
3. **複合**: 入力の先頭が `public ` のときだけ `in_channel`、それ以外は ephemeral で返す（例: `/practice-echo public みなさんこんにちは`）

---

## Chapter 4: Block Kit とボタン

### 1. 文字だけでなく UI を送る

Slack のメッセージには、**Block Kit**（見出し・文・ボタンなどの部品を JSON で組み立てる仕組み）で UI を載せられます。この章では「承認」ボタン付きのメッセージを送り、押されたら内容を書き換えます。

マニフェストは Chapter 3 で `interactivity` を有効にしてあるので、変更不要です（`04_block_kit/manifest.yaml` は Chapter 3 と同じ内容です）。

### 2. ボタン付きメッセージを送る

「approve」を含むメッセージが届いたら、ボタン付きのメッセージをスレッドに返します。`04_block_kit/main.py` には、次のリスナーが追加されています。

```python
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
```

| 部分 | 意味 |
|---|---|
| `"承認依頼が届きました"` | `reply_in_thread` の `text`。通知やブロックを表示できない環境で使われる代替テキスト |
| `blocks` | 表示する UI の部品の並び |
| `section` + `accessory` | 文の右側にボタンを置くブロック |
| `action_id` | ⭐ ボタンの識別子。押されたときにどのリスナーを呼ぶかの目印になる |

`blocks` は `reply_in_thread` の `**kwargs` を通って、そのまま `say` に渡されます。

### 3. ボタンが押されたときの処理

```python
@app.action("approve_button")
def handle_approve(ack, body, respond):
    ack()
    user_id = body["user"]["id"]
    logger.info("approve_button clicked by %s", user_id)
    respond(replace_original=True, text=f"<@{user_id}> さんが承認しました")
```

- `@app.action("approve_button")` で、`action_id` が一致するボタンの操作を受け取ります
- ボタン操作も `ack()` が必須です
- `respond(replace_original=True, ...)` で、ボタンの付いた元のメッセージを書き換えます。ボタンが消えるので、二重に押される心配がなくなります

Chapter 4 のもので起動し直し、チャンネルで `approve` と発言して、スレッドに表示されたボタンを押してみてください。

```bash
uv run --env-file .env 04_block_kit/main.py
```

> **うまくいかない時**: ボタンを押すと警告マークが出る → `action_id` の綴りがメッセージ側とリスナー側で一致しているか確認します。プログラムの停止中に押した場合も同じ表示になります。

> JSON を手書きする前に、ブラウザで部品を組んでプレビューできる **Block Kit Builder** を使うと効率的です。

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 4（動くコードは `answers/04_block_kit/`）

1. **基本**: 承認メッセージの先頭に `header` ブロック（`{"type": "header", "text": {"type": "plain_text", "text": "デプロイ承認"}}`）を追加する
2. **応用**: 「却下」ボタン（`action_id` は `reject_button`、`style` は `danger`）を追加し、押されたら「却下しました」に書き換える。ボタンを 2 つ並べるには、`section` の代わりに `actions` ブロック（`{"type": "actions", "elements": [ボタン1, ボタン2]}`）を使う
3. **複合**: 書き換え後のメッセージに、承認した人と時刻（Python の `datetime` で取得）を表示する

---

## Chapter 5: モーダル

### 1. 入力フォームを開く

複数の項目を入力してもらうときは、**モーダル**（画面中央に開くダイアログ）を使います。流れは 3 段階です。

```text
① /practice-feedback を実行
      │  trigger_id（モーダルを開くための引換券）が届く
      ▼
② views_open でモーダルを開く        ← ⚠ 引換券は 3 秒で失効・1 回限り
      │
      ▼
③ ユーザーが「送信」を押す → app.view で入力値を受け取る
```

### 2. マニフェストにコマンドを追加する

Chapter 5 のマニフェストは `05_modals/manifest.yaml` です。`slash_commands` に 2 つ目のコマンドを追加しています。

```yaml
features:
  slash_commands:
    - command: /practice-echo
      description: 入力した文字をそのまま返します
      usage_hint: "[返したい文字]"
      should_escape: false
    - command: /practice-feedback        # 追加
      description: フィードバック用のフォームを開きます
      should_escape: false
```

App Manifest を `05_modals/manifest.yaml` の内容に貼り替えて保存します。スコープは変わっていないので、通常は再インストール不要です。画面に再インストールの案内が出た場合だけ従ってください。

### 3. モーダルを開くコード

`05_modals/main.py` には、次のリスナーが追加されています。

```python
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
```

- `callback_id` は、このモーダルの識別子です。送信されたときの受け取り先を決めます
- `input` ブロックの `block_id` と、その中の `action_id` は、入力値を取り出すときの住所になります

### 4. 送信を受け取るコード

```python
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
```

| 部分 | 意味 |
|---|---|
| `body["view"]["state"]["values"][block_id][action_id]["value"]` | 入力された値 |
| `ack(response_action="errors", errors={...})` | モーダルを閉じずに、指定したブロックの下にエラーを表示する |
| `ack()` | 送信を確定してモーダルを閉じる |
| `body["user"]["id"]` | 送信したユーザー。ここでは DM でお礼を送るために使う |

Chapter 5 のもので起動し直し（`uv run --env-file .env 05_modals/main.py`）、`/practice-feedback` を実行して、3 文字だけ入れて送信（エラーが出る）→ 5 文字以上入れて送信（DM が届く）を試してください。

> **うまくいかない時**: モーダルが開かない → `views_open` の前に時間のかかる処理を入れていないか確認します。`trigger_id` は 3 秒で失効するため、**先にモーダルを開き、重い処理は後で行う**のが鉄則です。

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 5（動くコードは `answers/05_modals/`）

1. **基本**: モーダルのタイトルと送信ボタンの文言を変える
2. **応用**: 「お名前」の 1 行入力欄（`multiline` なし、`block_id` は `name_block`、`action_id` は `name_input`）を追加し、DM のお礼に名前を含める
3. **複合**: Chapter 4 の承認ボタンを押したら、承認理由を入力するモーダルを開くようにする（アクションの `body["trigger_id"]` も使える）

---

## Chapter 6: App Home

### 1. アプリ専用のホーム画面

サイドバーでアプリを開くと表示される画面を **App Home** と呼びます。ここに **Home タブ**を作ると、使い方の案内やダッシュボードを置けます。必要なのは 3 つです。

1. Home タブを有効にする
2. `app_home_opened`（ユーザーがホームを開いた）イベントを購読する
3. 開かれたら、`views_publish` でそのユーザー向けの画面を公開する

### 2. マニフェストを更新する

Chapter 6 のマニフェストは `06_app_home/manifest.yaml` です。`app_home` に `home_tab_enabled` を、イベントに `app_home_opened` を追加しています。

```yaml
features:
  app_home:
    home_tab_enabled: true               # 追加
    messages_tab_enabled: true
    messages_tab_read_only_enabled: false
settings:
  event_subscriptions:
    bot_events:
      - app_home_opened                  # 追加
      - app_mention
      - message.channels
      - message.im
```

App Manifest を `06_app_home/manifest.yaml` の内容に貼り替えて保存します。Chapter 5 と同じく、再インストールの案内が出た場合だけ従ってください。

### 3. ホームを公開するコード

`06_app_home/main.py` には、次のリスナーが追加されています。

```python
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
```

- `app_home_opened` は、DM 用の **メッセージ** タブを開いたときにも届きます。先頭の `if` で、ホームタブ（`tab` が `"home"`）のときだけ処理しています
- `views_publish` は**ユーザーごと**に画面を公開します。`user_id` を変えれば、人によって違う内容を見せられます
- 画面を更新したいときも、同じ `views_publish` をもう一度呼びます

Chapter 6 のもので起動し直し（`uv run --env-file .env 06_app_home/main.py`）、サイドバーの Practice Bot を開いて、**ホーム**タブを確認してください。

> **うまくいかない時**: 「このアプリのホームはまだありません」のような表示のまま → マニフェストの `home_tab_enabled` と `app_home_opened` の両方が保存されているか確認し、ホームタブを開き直します。

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 6（動くコードは `answers/06_app_home/`）

1. **基本**: ホームに `divider` ブロック（`{"type": "divider"}`）と、使い方の説明文をもう 1 つ追加する
2. **応用**: ホームに Chapter 4 と同じ形式のボタン（`action_id` は `home_refresh`）を置き、押されたら `views_publish` で現在時刻を表示し直す（アクションでは `body["user"]["id"]` でユーザーを取得）
3. **複合**: `/practice-feedback` で送られた件数を Python の変数で数え、ホームに「これまでのフィードバック: N 件」と表示する（関数の外の変数を書き換えるには、関数内で `global` 宣言が必要。プログラムを再起動すると 0 に戻ることも確認する）

---

## Chapter 7: ストリーミング返信

### 1. AI のように少しずつ表示する

生成 AI のボットは、回答を一度に出すのではなく、文字が少しずつ流れるように表示されます。Slack はこのための **ストリーミング API** を用意しており、Bolt for Python では `say_stream` で簡単に使えます。この章では LLM の代わりに、決まった文章を少しずつ送ります。

> ⚠ ストリーミングは AI アプリ向けの新しい機能です。無料プランのワークスペースで利用できるかは、公式ドキュメントで確認できませんでした（2026-10-15 時点）。Developer Program の基本サンドボックスでは、`say_stream` によるストリーミングが動作することを確認しています（2026-10 時点）。動かない場合は Developer Program のサンドボックスで試すか、この章を飛ばして Chapter 9 へ進んでください（応用編の Chapter 8 も、ストリーミングが動くことが前提です）。

マニフェストの変更は不要です（必要なスコープ `chat:write` は Chapter 1 から付いています。`07_streaming/manifest.yaml` は Chapter 6 と同じ内容です）。

### 2. ストリーミングのコード

`07_streaming/main.py` では、先頭の import に `import time`（待ち時間を入れる `time.sleep` を使うため）と、次のリスナーが追加されています。

```python
# Chapter 7: ストリーミング返信
@app.message("stream")
def handle_stream(message, say_stream):
    logger.info("stream request from %s in %s", message.get("user"), message["channel"])
    # 既定では 256 文字たまるまで送信されないため、append するたびに送るよう buffer_size を小さくする
    stream = say_stream(buffer_size=1)
    for word in ["Slack App ", "の ", "ストリーミング ", "返信 ", "です。"]:
        stream.append(markdown_text=word)
        time.sleep(0.5)
    stream.stop()
```

| 部分 | 意味 |
|---|---|
| `say_stream(buffer_size=1)` | ストリームを開始する。投稿先のチャンネル・スレッド・受信者は、届いたイベントから自動で決まる |
| `buffer_size` | ⭐ 何文字たまったら Slack へ送るか（既定 256）。既定のままだと、この例の短い文章は `stop()` のときにまとめて送られ、少しずつ表示されない |
| `stream.append(markdown_text=...)` | 文章を追記する |
| `stream.stop()` | ストリームを終える |

Chapter 7 のもので起動し直し（`uv run --env-file .env 07_streaming/main.py`）、チャンネルで `stream` と発言してください。発言へのスレッド返信として、文章が少しずつ表示されます（スレッド指定がないイベントでは、元の発言の `ts` がスレッドの起点として使われるためです。`say_stream` は、Chapter 2 の `reply_in_thread` と同じ返し方を自動で行います）。

> 本物の LLM の出力を流すときは、`buffer_size` を既定のままにして、ある程度まとめて送る方が API の呼び出し回数を抑えられます。1 文字ずつ送るのは、この練習で動きを見やすくするためです。

> **うまくいかない時**:
> - 文章が少しずつではなく、最後にまとめて表示される → `say_stream()` に `buffer_size` を指定しているか確認します
> - 起動時に `say_stream` 関連のエラーが出る → slack-bolt が古い可能性があります。`uv add slack-bolt --upgrade` で更新し、`uv pip list` で 1.30.0 以降か確認します
> - 何も表示されず、ターミナルにエラーが出る → ワークスペースでストリーミング機能が使えない可能性があります。冒頭の注意書きを参照してください

### 3. 3 秒ルールとの関係

Chapter 3〜5 では「3 秒以内に `ack()`」が必須でした。イベントのリスナーでは、`ack` を呼ぶ必要がありません。**イベントの受領は Bolt が自動で返す**ため、この例のように 2.5 秒かかる処理でも、Slack に再送されることはありません。本物の LLM を呼ぶときも、メッセージイベントで受けて `say_stream` で返す形が基本になります。

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 7（動くコードは `answers/07_streaming/`）

1. **基本**: 流れる文章と待ち時間を変えて、表示の変化を観察する
2. **応用**: 届いたメッセージの本文（リスナーの引数に `message` を追加し、`message["text"]`）を 1 文字ずつ流して返す
3. **複合**: Chapter 1 のメンションのリスナーをストリーミング版に書き換える（`app_mention` のリスナーでも `say_stream` を受け取れる）。手元で LLM の API を使える人は、`stream.append` に LLM の出力を流し込んでみる

---

## Chapter 8: エージェント画面（応用編）

### 1. エージェント画面とは

Slack には、AI エージェント向けの専用画面があります。アプリのメッセージタブを開くと DM のように話しかけられ、返事の途中経過（「考え中」の表示、作業の進み具合、停止ボタン）を Slack が標準の部品で見せてくれます。この章では、**調査を頼むと、調査 → ファクトチェック → 要約 → ベリファイ → 完成の 5 段階が順に表示されるエージェント**を作ります。

| 見える部分 | 正体 |
|---|---|
| 「<アプリ名> is working」と回るマーク | `agents.sessions.setStatus`（`processing` → `active`） |
| 5 段階の一覧・カード | ストリーミングの `task_update` チャンク |
| 全体タイトルの更新 | `plan_update` チャンク |
| 出典リンク | `task_update` の `sources` |
| 停止ボタン | `agent_session_stopped` を購読すると Slack が出す |
| 返事の下の 👍👎 | Block Kit の `feedback_buttons` |
| 話しかける候補 | マニフェストの `agent_view.suggested_prompts` |

自分で書くのは「どのタイミングで、どのチャンクを送るか」と、停止されたときに処理を抜ける部分だけです。画面そのものは作りません。

> ⚠ **応用編の注意**
> - `agent_view` は AI アプリ向けの新しい機能で、細かい仕様は変わる可能性があります。Developer Program のサンドボックスで動作を確認しています（2026-10 時点）。無料プランのワークスペースで使えるかは確認できていません。動かない場合は、この章を飛ばして Chapter 9 へ進んでください
> - **`agent_view` への切り替えは元に戻せません。** Chapter 1〜7 の Practice Bot では試さず、この章では**専用の新しい App** を作ります（そのため、`08_agents/` は Chapter 7 までのリスナーを含まない、単独のプログラムです）
> - LLM（Claude）とつなぐ部分は**任意**です。API キーがなくても、最後まで動かせます

### 2. 新しい App を作る

`08_agents/manifest.yaml` から、Chapter 1 の「3. マニフェストからアプリを作る」「4. 2 種類のトークンを取得する」と同じ手順で、新しい App（名前は `Practice Agent`）を作り、インストールします。トークンは Chapter 1〜7 の `.env` とは別に、`.env.agent` に書きます。

```bash
cp .env.example .env.agent
```

`.env.agent` の `SLACK_BOT_TOKEN` と `SLACK_APP_TOKEN` を、新しい App の値に置き換えます（`.env.agent` も `.gitignore` で除外済みです）。

マニフェストの追加項目は、次のとおりです。

| 部分 | 意味 |
|---|---|
| `features.agent_view` | エージェント画面を有効にする。`agent_description`（説明）と、`suggested_prompts`（話しかける候補）を書く |
| `features.app_home.messages_tab_enabled` | メッセージタブを出す。エージェント画面はここで動く |
| スコープ `assistant:write` | 「考え中」の表示などエージェント向けの API を使う |
| スコープ `im:history` | メッセージタブに届いた発言を読む |
| イベント `message.im` | メッセージタブへの発言を受け取る |
| イベント `agent_session_stopped` | **停止ボタンが押された**ことを受け取る。これを購読すると、実行中に停止ボタンが出る |
| イベント `app_home_opened` / `app_context_changed` | 画面を開いた・開いている場所が変わった通知。この章ではログに出すだけ |
| `settings.interactivity.is_enabled` | 👍👎 のボタン操作を受け取る |

> 候補のプロンプトは、マニフェストに書いたものが固定で表示されます。マニフェストに候補があると、`assistant.threads.setSuggestedPrompts` で動的に変える API は `static_prompts_configured` で拒否されます。

### 3. 最初の返事：考え中の表示とストリーミング

起動します。

```bash
uv run --env-file .env.agent 08_agents/main.py
```

Slack で `practice-agent` のメッセージタブを開くと、候補が 2 つ表示されます。「自己紹介して」を押すか、何か話しかけてください。固定の文章が少しずつ返ってきます。

```python
# Chapter 8: DM に届いたメッセージを受けて、応答をストリーミングで返す
@app.event("message")
def handle_message(client, event, say_stream):
    # 編集や削除、ボット自身の発言は無視する
    if event.get("subtype") or event.get("bot_id"):
        return
    channel_id = event["channel"]
    thread_ts = event.get("thread_ts") or event["ts"]
    client.agents_sessions_setStatus(channel_id=channel_id, thread_ts=thread_ts, status="processing")
    stream = say_stream(buffer_size=20)
    try:
        for chunk in stream_dummy(event["text"]):
            stream.append(markdown_text=chunk)
    finally:
        stream.stop()
        client.agents_sessions_setStatus(channel_id=channel_id, thread_ts=thread_ts, status="active")
```

> 実際の `08_agents/main.py` は、この骨組みに、次の節からの機能（調査・停止・👍👎・エラー処理）を足したものです。

| 部分 | 意味 |
|---|---|
| `event["thread_ts"] or event["ts"]` | 返事を付けるスレッドの目印。エージェント画面の会話は、スレッドごとに独立している |
| `agents_sessions_setStatus(... "processing")` | 「practice-agent is working」と回るマークを出す。返事の処理に入る合図 |
| `"active"` | 処理が終わったので、表示を消す。`finally` に置くと、失敗しても必ず消える |
| `say_stream(buffer_size=20)` | Chapter 7 と同じ。`stream.append` で追記、`stream.stop()` で終了 |

Chapter 7 との違いは、`@app.message("stream")` ではなく `@app.event("message")` で受けている点と、`setStatus` で処理中を知らせる点です。

### 4. 進捗をタスクで見せる

`調査 ○○` と送ると、5 段階の進捗が表示されます（例: `調査 Slack の chat.startStream`）。中身はダミーの待ち時間で、各段階が終わるたびに結果と出典リンクが付きます。

```python
# 最初に、全タスクを pending で並べる
stream.append(
    chunks=[{"type": "plan_update", "title": "「…」のリサーチ（準備中）"}]
    + [{"type": "task_update", "id": sid, "title": name, "status": "pending"} for sid, name, *_ in RESEARCH_STAGES]
)
for sid, name, doing, seconds, output, sources in RESEARCH_STAGES:
    # 実行中にする
    stream.append(chunks=[{"type": "task_update", "id": sid, "title": name, "status": "in_progress", "details": doing}])
    work(stop_flag, seconds)  # 処理に時間がかかるふり
    # 完了にして、結果と出典を付ける
    stream.append(chunks=[{"type": "task_update", "id": sid, "title": name, "status": "complete", "output": output, "sources": sources}])
```

| 部分 | 意味 |
|---|---|
| `chunks=[...]` | `markdown_text` の代わりに、構造のあるデータを送る。**同じストリームで `markdown_text` と混ぜられない**（`streaming_mode_mismatch`）ので、文章も `{"type": "markdown_text", "text": ...}` のチャンクで送る |
| `task_update` | 1 つの作業の状態。`id` が同じなら、同じカードが更新される。`status` は `pending` / `in_progress` / `complete` / `error` |
| `plan_update` | 全体のタイトルを更新する |
| `sources` | 出典リンク（`type: url`、`text`、`url`） |
| `buffer_size=1` | `chunks` は即座に送られる。進捗表示では `say_stream(buffer_size=1)` にしておく |

**表示モード**: `say_stream(task_display_mode=...)` で、見え方が変わります。

| `task_display_mode` | 見え方 |
|---|---|
| `plan`（既定） | 5 段階が 1 つのまとまり（プラン）として表示される。`pending` も一覧に出る |
| `timeline` | 進んだ段階が、それぞれカードとして順に積み上がる。`pending` は出ない |

`調査 Slack の chat.startStream timeline` のように `timeline` を含めると、`timeline` 表示になります。2 つを見比べてください。

### 5. 停止ボタンと 👍👎

**停止ボタン**: 処理中（`processing`）の間、「is working」の表示のところに停止ボタンが出ます。押されると `agent_session_stopped` イベントが届くので、処理を途中で抜けます。

```python
# 停止ボタンが押されたスレッドの目印（thread_ts ごと）。リスナーは別スレッドで動くので Event を使う
stop_flags = {}

@app.event("agent_session_stopped")
def handle_session_stopped(event):
    flag = stop_flags.get(event["thread_ts"])
    if flag is not None:
        flag.set()  # 処理の側が、このフラグを見て抜ける
```

| 部分 | 意味 |
|---|---|
| `threading.Event` | 停止の合図を、別のスレッド（処理中のリスナー）へ伝える。`work()` が 0.5 秒ごとに `is_set()` を見る |
| 毎回 `Event()` を作り直す | 前の処理が終わったあとに届いた停止イベントが、次の処理を止めないようにする |
| 止められたタスク | `status: "error"` と「ユーザーが停止しました」にして、`return False` で抜ける |

停止すると、返事に **`(stopped)`** が付くことがあります。これは「停止ボタンが押された時点で、ストリームがまだ開いていた」という Slack 側の記録です。返事が途中で切れたことを表すわけではありません（処理が終わる直前に押すと、最後まで出ていても付きます）。

**👍👎**: 最後まで終わったときだけ、`stream.stop(blocks=...)` で付けます。

```python
FEEDBACK_BLOCKS = [
    {
        "type": "context_actions",
        "elements": [
            {
                "type": "feedback_buttons",
                "action_id": "feedback",
                "positive_button": {"text": {"type": "plain_text", "text": "👍"}, "value": "good-feedback", "accessibility_label": "この回答は役に立った"},
                "negative_button": {"text": {"type": "plain_text", "text": "👎"}, "value": "bad-feedback", "accessibility_label": "この回答は役に立たなかった"},
            }
        ],
    }
]

@app.action("feedback")
def handle_feedback(ack, body, respond):
    ack()
    value = body["actions"][0]["value"]  # good-feedback か bad-feedback
    logger.info("feedback %s by %s", value, body["user"]["id"])
    respond(text="フィードバックありがとうございます！", response_type="ephemeral", replace_original=False)
```

Chapter 4 のボタンと同じく、`action_id` で受けて `ack()` を呼びます。マニフェストの `interactivity` が有効でないと、押しても届きません。

起動し直して（`Ctrl+C` → もう一度 `uv run ...`）、次を試してください。

| 操作 | 期待する結果 |
|---|---|
| `調査 Slack の chat.startStream` | 5 段階が 1 つのプランとして進み、出典リンクが付く。最後にレポートと 👍👎 が出る |
| `調査 Slack の chat.startStream timeline` | 5 段階が、カードとして順に積み上がる |
| 調査の途中で停止ボタンを押す | 実行中の段階が「ユーザーが停止しました」（エラー表示）になり、👍👎 は付かない |
| 👍 か 👎 を押す | 自分にだけ「フィードバックありがとうございます！」が出る。ターミナルに `feedback good-feedback by U…` |

> **うまくいかない時**:
> - 候補が出ない、メッセージタブが見つからない → マニフェストの `agent_view` と `messages_tab_enabled` を確認し、貼り替えたあとに再インストールします
> - 停止ボタンが出ない → `agent_session_stopped` を購読しているか、`setStatus` で `processing` にしているかを確認します
> - 👍👎 を押しても何も起きない → マニフェストの `interactivity.is_enabled: true` を確認します
> - `streaming_mode_mismatch` が出る → 同じストリームに `markdown_text=` と `chunks=` を混ぜていないか確認します
> - `static_prompts_configured` が出る → マニフェストに候補があるので、`setSuggestedPrompts` は呼ばないでください

### 6. （任意）Claude とつなぐ

ここまでの応答は、すべて固定の文章でした。Anthropic の API キーを持っている人は、**`AGENT_LLM=claude`** を付けて起動すると、次の 2 か所が本物になります。

| 場所 | 本物になること |
|---|---|
| 普通の発言 | `stream_llm()` が Claude の応答を少しずつ流す |
| `調査 ○○` | 5 段階それぞれで `ask()` が Claude を呼ぶ。調査とファクトチェックは **Web 検索つき**で、検索した語は `details` に、見つかった URL は `sources` に入る |

```bash
# .env.agent に ANTHROPIC_API_KEY=sk-ant-… を足してから
AGENT_LLM=claude uv run --env-file .env.agent 08_agents/main.py
```

ダミーの `work()` を `ask()`（Claude を呼ぶ関数）に差し替えただけで、タスクを出すコードは同じです。LLM を使わない人にも、**画面の仕組みを理解するにはダミーで十分**です。

| 注意 | 内容 |
|---|---|
| キーの扱い | `.env.agent` に書く。コードに直接書かない。チャットや画面に載せない |
| 料金 | 調査 1 回で Claude を 4 回呼び、Web 検索は最大 5 回です。目安は 1 回あたり 10 円前後（2026-10 時点。最新の料金は Anthropic の料金表で確認する）。長く試すときは、使用量の上限を設定しておく |
| モデル | 既定は `claude-haiku-4-5-20251001`。`AGENT_MODEL=…` で変えられる。モデルによっては、組織の設定で `429`（`rate_limit_error`）になることがある。その時は別のモデルを試す |
| ファイアウォール | サンドボックスで動かす場合、`api.anthropic.com` の許可が要る（Web 検索は Anthropic 側で実行されるので、検索先のサイトの許可は不要） |
| 停止ボタン | Claude を呼んでいる最中は止められない。呼び出しが終わった段階で止まる |
| エラー | API のエラーは、調査ではタスクの表示（「Claude API でエラーが出ました」）、普通の発言では返事の文章で伝える。詳しい原因は、ターミナルのログの `request_id` で追える |

別の LLM（Gemini など）を使う場合は、`stream_llm()` と `ask()` の中身を差し替えます。Slack に流す部分（`stream.append(...)`）は変わりません。

### 練習課題

> ヒントと解答例: `slack-app-tutorial-answers.md` の Chapter 8（動くコードは `answers/08_agents/`）

1. **基本**: `RESEARCH_STAGES` の所要秒数を変えて、`調査 ○○` と `調査 ○○ timeline` の見え方の違いを比べる
2. **応用**: 「ベリファイ」と「完成」の間に、「翻訳」の段階を足す。実行中に停止ボタンを押して、止まることを確かめる
3. **複合**: 👍👎 の件数を数え、押したときの返事に「これまでの合計: 👍 N 件 / 👎 M 件」を出す（プログラムを再起動すると 0 に戻ることも確認する）

---

## Chapter 9: 後片付けと次の一歩

### 1. ここまでの完成形

Chapter 1〜7 を終えた完成形は `07_streaming/` にあります（練習課題の内容は含みません）。応用編の Chapter 8 は別 App なので、`08_agents/` に単独で入っています。

| ファイル | 中身 |
|---|---|
| `07_streaming/main.py` | Chapter 1〜7 のすべてのリスナー |
| `07_streaming/manifest.yaml` | Chapter 6 と同じ、全機能を有効にしたマニフェスト |
| `08_agents/main.py` | Chapter 8 のエージェント（別 App 用。Chapter 1〜7 のリスナーは含まない） |
| `08_agents/manifest.yaml` | Chapter 8 のマニフェスト（`agent_view`） |
| `slack_helpers/threads.py` | スレッド返信の共通ヘルパー `reply_in_thread` |

章ごとの差分は、`diff` で確かめられます。

```bash
diff 03_slash_commands/main.py 04_block_kit/main.py
```

### 2. 後片付け

練習を終えたら、作ったものを片付けます。

| 対象 | 片付け方 |
|---|---|
| 動いているプログラム | ターミナルで `Ctrl+C` |
| Slack App | App 設定画面の **Basic Information** の最下部にある **Delete App** でアプリを削除する（Chapter 8 で作った `Practice Agent` も忘れずに） |
| トークン | リポジトリのルートの `.env` と `.env.agent` を削除する（下記）。アプリを残す場合は、App-Level Token を設定画面から無効化（Revoke）しておくと安心 |
| 練習用チャンネル | 不要ならアーカイブする |
| サンドボックス | 期限が来ると自動でアーカイブされる（基本サンドボックスは 1 か月） |
| 取得したリポジトリ | 下記のコマンドで削除（`.env` や `.env.agent` にトークンが残っているため） |

```bash
cd ..
rm -rf slack-app-tutorial   # リポジトリごと削除する。残したい場合は .env と .env.agent だけ削除する
```

⚠ 続けて best-practices に進む場合は、アプリとリポジトリを残しておいても構いません。ただし `.env` を Git に入れたり、誰かに送ったりしないでください（`.gitignore` で除外済みですが、`git add -f` などで無理に追加しないこと）。

### 3. このチュートリアルで身についたこと

| 章 | 身についたこと |
|---|---|
| 1 | マニフェストでアプリを作り、2 種類のトークンで Socket Mode につなぐ |
| 2 | イベントとスコープの対応、スコープ追加時の再インストール、共通ヘルパーによるスレッド返信 |
| 3 | スラッシュコマンドと `ack()` の 3 秒ルール |
| 4 | Block Kit の UI と、`action_id` によるボタン処理 |
| 5 | `trigger_id` を使ったモーダルと入力値の受け取り |
| 6 | ユーザーごとのホーム画面 |
| 7 | ストリーミング返信と、イベントの自動受領 |
| 8 | エージェント画面：タスクによる進捗表示、停止ボタン、👍👎 |

### 4. 次の一歩

- **本番運用を考える** → `slack-app-best-practices.md`: HTTP 方式への移行、重複イベント対策、トークン管理、マニフェストの運用、レート制限
- **全体像を振り返る** → `slack-app-overview.md`: 配布（OAuth）や Marketplace など、このチュートリアルで扱わなかった領域
- **公式のサンプルを読む** → Bolt for Python のリポジトリにある examples
- **ヘルパーを育てる** → `slack_helpers/` に、よく使う返し方（エラー時の定型文、ephemeral での返信など）を足していくと、章をまたいで使い回せます

### 5. 直感を育てるコツ

- **「何が届いて、何を返すか」を声に出す**: すべての機能は「イベントや操作が届く → `ack` → 何かを返す」の組み合わせです
- **エラーはまず 3 秒とスコープを疑う**: 反応しないときの原因の多くは、`ack` の遅れ・忘れ、またはスコープの不足と再インストール忘れです
- **マニフェストを正本にする**: 画面で設定を変えたら、`manifest.yaml` にも反映しておくと、作り直しが一瞬で済みます

---

## 関連リソース

- **Bolt for Python**: https://docs.slack.dev/tools/bolt-python/
- **Bolt for Python リポジトリ**: https://github.com/slackapi/bolt-python
- **Socket Mode（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/socket-mode
- **メッセージ送信とストリーミング（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/message-sending
- **スラッシュコマンド（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/commands
- **アクション（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/actions
- **モーダルを開く（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/opening-modals
- **モーダルの送信（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/view-submissions
- **App Home（Bolt for Python）**: https://docs.slack.dev/tools/bolt-python/concepts/app-home
- **App Manifest リファレンス**: https://docs.slack.dev/reference/app-manifest
- **Socket Mode**: https://docs.slack.dev/apis/events-api/using-socket-mode
- **スラッシュコマンドの実装**: https://docs.slack.dev/interactivity/implementing-slash-commands
- **chat.startStream**: https://docs.slack.dev/reference/methods/chat.startStream
- **Developer Program サンドボックス**: https://docs.slack.dev/tools/developer-sandboxes
- **App 管理画面**: https://api.slack.com/apps
- **chat.postMessage（`thread_ts`、`reply_broadcast`）**: https://docs.slack.dev/reference/methods/chat.postMessage
- **uv プロジェクトの作成**: https://docs.astral.sh/uv/concepts/projects/init/
- **uv プロジェクトの使い方**: https://docs.astral.sh/uv/guides/projects/

### 関連教材

- `slack-app-overview.md` — Slack App の全体像
- `slack-app-best-practices.md` — 本番運用（コンテナ / 関数でのホスティング）の設計原則と失敗パターン
- `slack-app-prework.md` — 始める前の準備（つまずいたときの対処付き）
- `slack-app-tutorial-answers.md` — 練習課題のヒントと解答例
- `claude-tag-tutorial.md` — Claude を Slack で使う（Claude Tag）
