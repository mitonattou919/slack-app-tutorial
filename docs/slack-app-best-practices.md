---
title: "Slack App ベストプラクティス"
tags:
  - slack-app
  - best-practices
  - learning-material
type: best-practices
created: 2026-10-15
description: "Bolt for Python で作った Slack App を、コンテナや関数（FaaS）で本番運用するための設計原則・トレードオフ・失敗パターンをまとめた中級者向け教材"
related:
  - "[[Slack]]"
  - "[[コンテナ]]"
  - "[[FaaS]]"
  - "[[メッセージキュー]]"
  - "[[シークレット管理]]"
  - "[[OAuth 2.0]]"
  - "[[Redis]]"
---

# Slack App ベストプラクティス

> `slack-app-tutorial.md` を終え、Bolt for Python で一通り動くボットを作れる人向けの実務教材です。手元の Socket Mode で動いたボットを、チームの本番運用に耐える形へ持っていくための設計原則、トレードオフ、失敗パターンを扱います。ホスティング先は特定のクラウドに依存しないよう、**コンテナ**と**関数（FaaS）**の 2 種類に抽象化して説明します。
> 基本操作の復習 → `slack-app-tutorial.md` ／ 全体像 → `slack-app-overview.md`
>
> 確認日: 2026-10-15（slack-bolt 1.30.0、slack-sdk 3.45.0、uv 0.13.1）

---

## Chapter 0: Slack App の本番運用とは：中核となる 3 つの制約

### 1. ベストプラクティスの大半は 3 つの制約から導かれる

Slack App の本番運用は、**書留郵便の受付窓口**にたとえると分かりやすくなります。配達員（Slack）は 3 秒しか待ってくれず、その間に受領印を押さないと「不在」とみなして再配達してきます。窓口の合鍵（トークン）を落とせば、拾った人が窓口になりすませます。運用上の判断は、ほぼ次の 3 つの制約に帰着します。

| 制約 | 内容 | 破ったときの症状 |
|---|---|---|
| ⭐ **3 秒ルール** | イベント・コマンド・ボタン操作には 3 秒以内に受領を返す。`trigger_id` も 3 秒で失効する | ユーザーにエラー表示、イベントの再送、モーダルが開かない |
| **少なくとも 1 回の配信** | **イベント**は、受領が返らなければ最大 3 回再送される。同じイベントが複数回届く前提で作る（コマンドやボタン操作は再送されず、ユーザーにエラーが表示される） | 二重投稿、二重処理、外部システムへの二重登録 |
| **トークン ＝ 権限** | トークンを持つ者はスコープの範囲で何でもできる。漏洩はそのまま権限の漏洩になる | なりすまし投稿、過去ログの流出 |

本教材の各章は、この 3 つのどれかへの対策です。

### 2. 付きまとうトレードオフ

| トレードオフ | 典型的な判断 |
|---|---|
| **応答速度 ↔ コスト** | コンテナを常時 1 台以上起動しておけば 3 秒ルールは守りやすいが、待機中も課金される（Chapter 1） |
| **単純さ ↔ 信頼性** | リスナーの中で全部処理すれば単純だが、重い処理を混ぜると 3 秒を超える。キューを挟むと信頼性は上がるが部品が増える（Chapter 2） |
| **機能 ↔ 権限** | スコープを足すほど機能は増えるが、管理者承認が通りにくくなり、漏洩時の被害も広がる（Chapter 4） |
| **自律性 ↔ 安全性** | AI エージェントに任せるほど便利になるが、確認なしの実行はリスクになる（Chapter 7） |

### 3. 本教材の前提

- 言語は Python、フレームワークは Bolt for Python、パッケージ管理は uv
- ホスティングは**コンテナ**（常駐するプロセスを、インスタンス数を増減させて動かす）を主軸にし、**関数**（FaaS：リクエストごとに起動する）との比較も扱う。クラウドごとの具体的なサービスは Chapter 1 の対応表を参照
- 社内向けの単一ワークスペース運用を主軸にし、他社配布は Chapter 5 で扱う

---

## Chapter 1: 実行方式とホスティング

### 1. Socket Mode から HTTP へ

tutorial では Socket Mode を使いましたが、公式は**本番運用では HTTP 方式を推奨**しています。

| 観点 | Socket Mode | HTTP |
|---|---|---|
| スケール | ステートフル。同時接続はアプリあたり最大 10 | ステートレス。インスタンスを増やすだけで水平スケール |
| 信頼性 | 長時間接続のため、切断や再起動の影響を受ける | リクエストごとに完結 |
| 公開 URL | 不要 | 必要（HTTPS） |
| Marketplace | 掲載不可 | 掲載には必須 |

**判断基準**: 公開 HTTPS エンドポイントを用意できるなら HTTP。社内ネットワークの事情で外部から受けられない場合だけ、Socket Mode を本番で使う選択肢があります。

⚠ Bolt の `app.start()` は **開発用サーバー**（Python 標準の `http.server`）です。ソースのコメントにも「本番では本番向けのサーバーを使う」旨が書かれています。本番では FastAPI などのアダプター経由で、本番向けの ASGI/WSGI サーバーに載せます。

### 2. FastAPI アダプターで HTTP 化する

次は Bolt for Python 公式の FastAPI サンプルに沿った最小構成です。tutorial のリスナーは、ほぼそのまま移植できます。

```python
# app.py
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

# SLACK_BOT_TOKEN と SLACK_SIGNING_SECRET を環境変数から読む
app = App()
app_handler = SlackRequestHandler(app)


@app.event("app_mention")
def handle_mention(event, say):
    say(f"こんにちは、<@{event['user']}> さん！")


api = FastAPI()


@api.post("/slack/events")
async def endpoint(req: Request):
    return await app_handler.handle(req)
```

```bash
uv add slack-bolt fastapi uvicorn
uv run uvicorn app:api --host 0.0.0.0 --port 3000
```

Socket Mode との違いは 2 点です。

- **App-level token（`xapp-`）が不要になり、代わりに Signing Secret が必須になる**: HTTP では、届いたリクエストが Slack から来たものかを署名で検証します（Bolt が自動で行う）
- **マニフェストを HTTP 用に変える**: `socket_mode_enabled: false` にし、イベント・インタラクション・コマンドの Request URL に `https://<公開ホスト名>/slack/events` を設定します

### 3. コンテナと関数のどちらで動かすか

HTTP 化したアプリの動かし方は、大きく 2 種類です。

| 種類 | 動き方 | 例 |
|---|---|---|
| **コンテナ** | プロセスが常駐し、リクエストを受け続ける。負荷に応じてインスタンス数を増減する | Kubernetes、マネージドなコンテナ実行サービス |
| **関数（FaaS）** | リクエストが来るたびに関数が起動し、応答を返したら終わる | AWS Lambda、Google Cloud Functions など |

Bolt との相性で比べると、次のようになります。

| 観点 | コンテナ | 関数（FaaS） |
|---|---|---|
| Bolt との相性 | FastAPI アダプターなどをそのまま動かせる | 公式アダプターがあるのは AWS Lambda と Google Cloud Functions（現 Cloud Run functions）のみ（Bolt for Python 1.30.0）。それ以外は自前でつなぐ |
| ack 後の処理 | プロセスが生き続けるので、Bolt 既定の「ack を返してから処理」がそのまま動く | ⚠ 応答を返した後のバックグラウンド処理は、完了が保証されないのが普通（応答後に実行環境が凍結・停止されうる） |
| 3 秒ルール | 最小インスタンス数を 1 以上にすれば、コールドスタートを避けられる | プランや設定によってはコールドスタートがある |
| 長い処理 | 別のワーカー（キュー連携）に逃がす | HTTP で起動された関数には最大実行時間がある。キューで起動する関数に逃がす |

⭐ **迷ったらコンテナを選びます。** Bolt の既定の実行モデル（`process_before_response=False`: 先に受領を返し、リスナーは後で実行）が、そのまま安全に動くためです。関数を選ぶ場合は、Chapter 2 の lazy listeners かキュー構成が前提になります。

本教材で使う抽象的な部品と、主なクラウドでの具体例の対応は次のとおりです（どれを選んでも、設計原則は変わりません）。

| 本教材での呼び方 | AWS の例 | Google Cloud の例 | Azure の例 |
|---|---|---|---|
| コンテナ | ECS / App Runner | Cloud Run | Container Apps |
| 関数（FaaS） | Lambda | Cloud Run functions | Functions |
| メッセージキュー | SQS | Pub/Sub | Service Bus |
| 共有の KV ストア（Redis） | ElastiCache | Memorystore | Azure Managed Redis |
| シークレット管理サービス | Secrets Manager | Secret Manager | Key Vault |
| 実行環境の ID | IAM ロール | サービスアカウント | マネージド ID |

### 4. コンテナの設定で外せないこと

多くのコンテナ実行サービスは、アイドル時に**インスタンス数を 0 まで減らす**（scale to zero）設定にできます。最小 0 のままだと、アイドル後の最初のリクエストでコールドスタート（イメージの取得とアプリ起動）が発生し、Slack の 3 秒ルールに間に合わないことがあります。

| 設定 | 本番 | 開発・ステージング |
|---|---|---|
| 最小インスタンス数 | ⭐ **1 以上**。コールドスタートをなくす（その分、待機中も課金される） | 0 でもよい。コストを優先し、初回の失敗は許容する |
| 最大インスタンス数 | 想定する負荷に合わせて上限を決める | 小さめでよい |

- 設定名はサービスによって異なります（「最小インスタンス数」「最小レプリカ数」「min instances」など）
- uv を使ったコンテナイメージの作り方は、uv 公式の Docker ガイド（関連リソース）に従います

### 5. よくあるアンチパターン

- **本番で `app.start()` を使う**: 開発用サーバーのまま公開しています
- **コンテナを最小 0 インスタンスで本番運用**: 朝一番のコマンドだけ失敗する、という再現しにくい不具合になります

---

## Chapter 2: 3 秒ルールと非同期設計

### 1. 原則：先に受領、処理は後

| 入口 | 受領の返し方 | 期限 |
|---|---|---|
| イベント | Bolt が自動で返す（既定の `process_before_response=False` ではリスナー実行前、`True` ではリスナー完了後） | 3 秒 |
| コマンド・ボタン・モーダル送信・ショートカット | リスナーの先頭で `ack()` | 3 秒 |
| モーダルを開く | `trigger_id` を使って `views_open` | **3 秒・1 回限り** |
| 後からの返信 | `response_url` | **30 分以内に最大 5 回** |

`ack()` の前に、データベースの読み込みや外部 API の呼び出しを置かないことが基本です。モーダルは「先に読み込み中の画面を開き、`views_update` で中身を差し替える」順序にします。

### 2. 処理の重さで置き場所を変える

| 処理時間の目安 | 置き場所 | 例 |
|---|---|---|
| 1 秒未満 | リスナー内でそのまま | 定型文の返信 |
| 数秒〜数十秒 | Bolt の既定（ack 後にリスナー実行）。コンテナなら OK | LLM の短い応答、外部 API 1〜2 回 |
| 数十秒以上・失敗時に再試行したい | **メッセージキューに積み、別のワーカーで処理** | レポート生成、大量データの集計 |

### 3. キューに逃がす構成

重い処理や、失敗したら再試行したい処理は、受け取った内容をキューに積んで、すぐ終わらせます。

```text
Slack ──▶ Bolt（コンテナ: slack-bot）
            │ ① ack() / 受領
            │ ② メッセージキューへ投入（チャンネル ID、response_url など）
            ▼
      メッセージキュー ──▶ ワーカー（コンテナ、またはキューで起動する関数: slack-worker）
                              ③ 重い処理
                              ④ chat.postMessage または response_url で結果を返す
```

次はキューに積む側の例です。キューへの投入は使うキューサービスの SDK で実装するため、ここでは `enqueue_job` という関数に切り出しています。Bolt 側のコードは、どのキューサービスを使っても変わりません。

```python
import json


def enqueue_job(queue_name: str, job: dict) -> None:
    """ジョブをメッセージキューに積む。使うキューサービスの SDK で実装する。"""
    raise NotImplementedError


@app.command("/report")
def handle_report(ack, command):
    ack("レポートを作成しています。完了したらお知らせします。")
    job = {
        "channel_id": command["channel_id"],
        "user_id": command["user_id"],
        "response_url": command["response_url"],
        "text": command["text"],
    }
    enqueue_job("slack-jobs", job)
```

- キューへの認証には、接続文字列やアクセスキーではなく、**実行環境の ID**（Chapter 1 の対応表）に送信だけの権限を付けて使います。キーをどこにも置かずに済みます
- ワーカー側は、キューにたまったメッセージ数でインスタンス数を増減させる設定にできることが多いです（Kubernetes なら KEDA など）
- `response_url` は 30 分で失効します。それより長くかかる処理は、`chat.postMessage` で返します
- キューのメッセージも「少なくとも 1 回」届く前提で、ワーカー側を冪等にします（Chapter 3）

### 4. FaaS で動かす場合：lazy listeners

FaaS では、応答を返した後にスレッドを動かせません。Bolt for Python は、このために **lazy listeners** を用意しています（Bolt for Python だけの機能です）。

```python
from slack_bolt import App

# FaaS では process_before_response=True が必須
app = App(process_before_response=True)


def respond_within_3_seconds(body, ack):
    ack(f"受け付けました（{body['text']}）")


def run_long_process(respond, body):
    # 3 秒を超える処理
    respond(f"完了しました（{body['text']}）")


app.command("/start-process")(
    ack=respond_within_3_seconds,
    lazy=[run_long_process],
)
```

> lazy listeners を別の実行単位として起動する仕組みは、公式には AWS Lambda 向けにだけ実装されています（Lambda の関数呼び出し権限が必要）。Google Cloud Functions のアダプターは、lazy listeners を使うと「サポートしていない」というエラーを出します（slack-bolt 1.30.0 のソースで確認）。Lambda 以外の FaaS を選ぶ場合は、lazy listeners に頼らず、Section 3 のキュー構成にするのが安全です。

### 5. よくあるアンチパターン

- **`ack()` の前に DB 照会**: 平常時は間に合っても、DB が遅い日にだけ失敗します
- **`response_url` を 1 時間後に使う**: 30 分で失効しています

---

## Chapter 3: 冪等性と重複イベント

### 1. 重複は「たまに起きる例外」ではなく「仕様」

Events API は、3 秒以内に 2xx が返らない配信を失敗とみなし、**最大 3 回（ほぼ即時、1 分後、5 分後）再送**します。再送には次のヘッダーが付きます。

| ヘッダー | 意味 |
|---|---|
| `x-slack-retry-num` | 何回目の再送か |
| `x-slack-retry-reason` | 再送の理由（例: `http_timeout`） |

ネットワークの遅延やデプロイ中の再起動でも再送は起きます。**同じイベントが 2 回届いても、結果が 1 回分になる**（冪等である）ように作ります。

### 2. `event_id` で重複を捨てる

イベントのペイロードの外側には `event_id` があり、公式は「全ワークスペースを通じて一意」と説明しています。重複排除の方法そのものは公式に明記されていませんが、一意性が保証されている以上、**重複判定のキーとして使うのが自然な設計**です。

次は Bolt のグローバルミドルウェアで重複を捨てる例です。複数インスタンスで動かすため、判定には共有の KV ストア（ここでは Redis）を使います。

```python
import os

import redis
from slack_bolt import BoltResponse

# 依存: uv add redis
# 例: REDIS_URL=rediss://<ホスト名>:<ポート>（TLS で接続する）
store = redis.Redis.from_url(
    os.environ["REDIS_URL"],
    decode_responses=True,
    socket_timeout=1,
)


@app.use
def drop_duplicate_events(body, next, logger):
    event_id = body.get("event_id")
    if event_id:
        try:
            # 初めて見る event_id なら登録して True、既にあれば None
            first_time = store.set(f"slack:event:{event_id}", 1, nx=True, ex=3600)
        except redis.RedisError as e:
            # ストア障害時は重複排除をあきらめて処理を続ける（fail-open）
            logger.warning(f"重複判定をスキップしました: {e}")
            first_time = True
        if not first_time:
            logger.info(f"重複イベントを破棄しました: {event_id}")
            return BoltResponse(status=200, body="")
    next()
```

⚠ **重複を捨てるときは `BoltResponse(status=200)` を返してください。** `next()` を呼ばずにただ `return` すると、Bolt は 404（`no next() calls in middleware`）を返します。Slack はこれを配信失敗とみなし、**さらに再送してきます**。この挙動は、slack-bolt 1.30.0 で手元に模擬リクエストを流して確認しました。

⚠ **このミドルウェア自体が 3 秒ルールの内側にあります。** グローバルミドルウェアは、イベントの自動受領より**前**に動きます。Redis の応答が遅いと、その分だけ受領が遅れます。Chapter 2 の「受領の前に外部照会をしない」原則の例外なので、次の点を設計に入れます。

| 論点 | この例での選択 | トレードオフ |
|---|---|---|
| ストアが遅い・落ちた | 短いタイムアウト（`socket_timeout=1`）で fail-open（処理を続ける） | 障害中は重複排除が効かない。代わりに受領が止まらない |
| 登録のタイミング | 処理の前に登録する | 登録後、受領が Slack に届く前にプロセスが落ちると、再送が「重複」として捨てられ、そのイベントは失われる |
| TTL | 1 時間（`ex=3600`） | 再送は最大 5 分後までなので十分。長くするとストアの容量を使う |

> Redis への認証は、マネージドなサービスごとに方法が異なります。パスワード（アクセスキー）を使う場合は、URL ごとシークレット管理サービス（Chapter 4）に置きます。実行環境の ID による認証に対応したサービスなら、そのサービスが提供する認証プロバイダーを redis-py の `credential_provider` に渡す形にすると、キーをどこにも置かずに済みます。クラスターモードを有効にした Redis では、クラスター対応のクライアント（`redis.cluster.RedisCluster`）が必要です。

### 3. 重複に強い設計の選択肢

| 方法 | 向いている場面 | 注意点 |
|---|---|---|
| `event_id` で重複排除（上記） | イベント全般 | 共有ストアが必要。メモリ上の `set()` はインスタンス間で共有されない |
| 処理自体を冪等にする | 外部システムへの登録 | 「同じキーなら上書き」「既にあれば何もしない」形にする |
| 再送を止める（`x-slack-no-retry: 1`） | 再送されても意味がない処理 | 失敗したイベントは失われる。Bolt の既定の応答では付かないため、使うなら独自に返す必要がある |

⭐ 最も確実なのは **「受領は即座に返して再送を起こさない」＋「念のため `event_id` で重複を捨てる」＋「副作用のある処理は冪等に」** の 3 段構えです。

### 4. 再送が続くとどうなるか

60 分間の配信の 95% 超が失敗すると、**イベント購読が一時的に無効化**され、アプリ作成者にメールが届きます（1 時間あたり 1,000 件未満のアプリは自動無効化の対象外）。デプロイ失敗で全リクエストが 500 を返し続ける、といった事態はこれに直結します。

### 5. よくあるアンチパターン

- **重複排除をプロセス内の変数で行う**: インスタンスが 2 台になった瞬間に効かなくなります
- **ミドルウェアで `next()` を呼ばずに return**: 404 が返り、再送を自分で増やしています

---

## Chapter 4: トークン・秘密情報・スコープ

### 1. 秘密情報はシークレット管理サービスに置き、実行環境の ID で読む

公式のセキュリティガイドは、開発時は `.env`（`.gitignore` で除外）、本番では専用の秘密管理ツールを使うよう求めています。クラウドを問わず、次の構成が基本です。

```text
シークレット管理サービス（SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET を保管）
   ▲ 読み取りだけの権限
   │
実行環境の ID（コンテナや関数そのものに割り当てる ID）
   │ シークレットへの参照として定義
   ▼
環境変数 SLACK_BOT_TOKEN（アプリからは普通の環境変数として見える）
```

| ポイント | 内容 |
|---|---|
| 実行環境の ID | コンテナや関数自身の ID でシークレット管理サービスに認証する。接続用の資格情報をどこにも置かない |
| 参照で渡す | 実行環境の設定に値を直接書かず、シークレット管理サービスの値への**参照**として環境変数を定義する |
| 最新版を参照する | 特定のバージョンを固定せず「最新版」を参照する設定にしておくと、値の差し替えだけでローテーションできる |
| 反映タイミング | ⚠ 多くの実行環境は、シークレットを**起動時に**環境変数として読み込む。値を更新しても、実行中のインスタンスには再起動や再デプロイまで反映されないのが普通。自動で取り直す機能の有無と間隔はサービスごとに確認する |

⚠ 実行環境の管理用ロールの中には、設定されたシークレットの値を平文で読めてしまう権限を含むものがあります。運用者に付けるロールは中身を確認してから割り当てます。

### 2. トークンのローテーション

Slack は、アクセストークンに有効期限を付ける **トークンローテーション** を提供しています。

| 項目 | 内容 |
|---|---|
| 有効化 | マニフェストの `settings.token_rotation_enabled: true`、または設定画面 |
| ⚠ 不可逆 | **一度有効にすると無効化できない**。公式も本番前に開発環境で試すよう勧めている |
| 有効期限 | アクセストークンは 12 時間で失効。`xoxe.` で始まる形式になる |
| 更新 | リフレッシュトークン（1 回限り有効）で `oauth.v2.access` を呼び、新しいトークンとリフレッシュトークンを受け取る |
| Bolt の対応 | Bolt for Python 1.7 以上は自動で処理する（OAuth のインストール情報ストアを使う構成の場合） |

**判断基準**: 単一ワークスペースの社内ボットで、Bot token をシークレット管理サービスに固定で置く運用なら、ローテーションの導入は「OAuth 構成（Chapter 5）に移るとき」に合わせて検討するのが現実的です。漏洩時の被害時間を短くできる一方、トークン更新の仕組みと保存先が必要になるためです。

### 3. 署名検証と IP 許可リスト

- **署名検証**: HTTP で受けるなら必須です。Bolt は `SLACK_SIGNING_SECRET` があれば自動で検証し、5 分以上古いリクエストは拒否します。古い verification token 方式は使いません
- **IP 許可リスト（Allowed IP Address Ranges）**: 設定画面の **OAuth & Permissions** → **Restrict API Token Usage** で、Web API を呼べる送信元 IP を最大 20 件まで制限できます。リスト外からの呼び出しは `invalid_auth` で拒否されます。IPv6 とローカル IP は登録できません

コンテナや関数から Slack API を呼ぶ送信元 IP を固定するには、ネットワーク構成（NAT ゲートウェイなどによる送信の固定 IP）の設計が別途必要です。固定できない構成では IP 許可リストは使えません。

### 4. スコープの方針を 3 段階で決める

公式のセキュリティガイドは、スコープを次の 3 区分でポリシー化し、文書にすることを勧めています。

| 区分 | 例 | 運用 |
|---|---|---|
| 常時許可（低リスク） | `commands`、`chat:write` | レビューなしで追加してよい |
| 承認必要（高リスク） | `channels:history`、`users:read` | 追加時にセキュリティレビュー |
| 制限（原則禁止） | `admin` 系 | 例外申請のみ |

- スコープを変えたら**再インストールが必要**です。本番で無計画にスコープを足すと、再インストールまで機能が止まります
- User token（`xoxp-`）は「その人として」動きます。退職や権限変更で止まるうえ、権限が強いため、Bot token で済むなら Bot token を使います

### 5. ログとエラーメッセージ

- トークンを**ログに出さない**、エラーメッセージや UI に出さない
- 秘密情報を GET のクエリ文字列で渡さない
- ただし、イベント・ユーザー操作・エラーを追跡できる**詳細なログ自体は必要**です（トークンを除いて記録する）

### 6. よくあるアンチパターン

- **実行環境の設定画面に Bot token を直接入力**: 誰がいつ変えたか追えず、ローテーションも手作業になります
- **トークンローテーションを本番でいきなり有効化**: 戻せないため、更新処理の不備がそのまま障害になります

---

## Chapter 5: マニフェスト・環境分離・配布

### 1. 環境ごとに別の Slack App を作る

1 つの Slack App を開発と本番で共用すると、開発中の変更（スコープ追加、Request URL の変更）が本番に直撃します。**環境ごとに別の App** を作るのが基本です。

| 環境 | App 名の例 | ワークスペース | Request URL |
|---|---|---|---|
| 開発 | `Practice Bot (dev)` | サンドボックス | Socket Mode またはトンネル |
| ステージング | `Practice Bot (stg)` | サンドボックス | stg のコンテナ |
| 本番 | `Practice Bot` | 本番ワークスペース | 本番のコンテナ |

マニフェストは共通部分をテンプレートにし、名前と Request URL だけを環境ごとに差し替えます。

### 2. Manifest API で設定をコード化する

App Manifest API を使うと、設定画面を触らずにアプリの設定を管理できます。

| メソッド | 用途 |
|---|---|
| `apps.manifest.validate` | マニフェストがスキーマに合っているか検証する（CI 向き） |
| `apps.manifest.update` | 既存アプリの設定を更新する |
| `apps.manifest.export` | 現在の設定を書き出す（画面で直接変えられた差分の検出に使う） |
| `apps.manifest.create` / `delete` | アプリの作成・削除 |

次は CI でマニフェストを検証する例です。`manifest.json` は YAML から変換したものを想定しています。

```bash
# SLACK_CONFIG_TOKEN は CI のシークレットに登録した Configuration token
curl -s -X POST https://slack.com/api/apps.manifest.validate \
  --data-urlencode "token=${SLACK_CONFIG_TOKEN}" \
  --data-urlencode "manifest=$(cat manifest.json)"
# 成功: {"ok": true, "errors": []}
# 失敗: {"ok": false, "error": "invalid_manifest", "errors": [{"message": ..., "pointer": ...}]}
```

⚠ **Configuration token は発行から 12 時間で失効します。** 発行時に受け取るリフレッシュトークンで `tooling.tokens.rotate` を呼び、新しいトークンとリフレッシュトークンに入れ替え続ける必要があります。CI に長期間置いておく値ではない点に注意します。

> `apps.manifest.update` の応答に含まれる `permissions_updated` が真なら、スコープが変わったため再インストールが必要です。自動更新のパイプラインでは、この値を見て処理を止めるか通知します。

### 3. 他のワークスペースに配る：OAuth

複数のワークスペースにインストールさせるには、OAuth 2.0 フローが必要です。Bolt for Python は `OAuthSettings` を渡すと、インストール用のパスとリダイレクト用のパスを自動で用意します。

| 要素 | 内容 |
|---|---|
| `/slack/install` | 「Add to Slack」ボタンのあるインストール開始ページ |
| `/slack/oauth_redirect` | OAuth のリダイレクト先。設定画面の OAuth & Permissions に登録する |
| `installation_store` | ワークスペースごとのトークンを保存する場所 |
| `state_store` | OAuth の state（CSRF 対策の値）を保存する場所 |

⚠ 公式サンプルは `FileInstallationStore`（ローカルファイル）を使っています。**複数インスタンスで動くコンテナや関数では、各インスタンスのファイルは共有されません**（関数ではインスタンスの終了とともに消えることもあります）。本番では、全インスタンスから読める永続ストア（データベースなど）に保存する独自の installation store を用意します。トークンが入るため、保存先の暗号化とアクセス制御も必要です。

### 4. 配布の段階と 2025 年の制限変更

| 段階 | ポイント |
|---|---|
| 単一ワークスペース | OAuth 不要。社内ボットの大半はここ |
| 公開配布（unlisted） | OAuth 必須。2025-05-29 以降に作成された unlisted アプリと、既存 unlisted アプリの新規インストールでは、`conversations.history` / `conversations.replies` が **1 分 1 回・1 回 15 件**に制限される（既存のインストールは対象外） |
| Marketplace | レビュー通過が必要。HTTP 方式が必須。上記の制限変更の対象外 |

社内向けの自作アプリは、この制限変更の対象外です。他社に配る予定があり、過去ログを読む機能を持つなら、**最初から Marketplace 承認を前提に計画**します。

### 5. デプロイの流れとチーム運用

マニフェストとコードの変更を、次の順でパイプラインに載せると事故が減ります。

```text
① apps.manifest.validate でマニフェストを検証
② stg の App に apps.manifest.update → permissions_updated が真なら停止して通知（再インストール待ち）
③ stg のコンテナに新バージョンをデプロイし、動作確認
④ 本番の App とコンテナに同じ手順を適用
⑤ 問題があれば、直前のバージョンへトラフィックを戻す
```

新旧のバージョンを並べてトラフィックを切り替えられる実行環境（リビジョン、ブルーグリーンデプロイなど）なら、⑤の切り戻しが速くできます。ただし、**Slack 側の設定（マニフェスト）はコードのバージョンと一緒には戻らない**点に注意します。スコープ削除のような後戻りしにくい変更は、コードのリリースと分けて行います。

チームで運用するなら、最低限次を決めておきます。

| 項目 | 決めること |
|---|---|
| 所有者 | Slack App の Collaborator（設定画面を触れる人）と、クラウドリソースの所有者。退職で誰も触れなくなる事態を避ける |
| 監視 | 受領までの時間、5xx の割合、429 の件数、重複破棄の件数、`app_rate_limited` イベント |
| 障害対応 | トークン漏洩時の手順（シークレット管理サービスの値の差し替え → インスタンスの再起動 → 旧トークンの失効）、イベント購読が無効化されたときの連絡先 |

### 6. よくあるアンチパターン

- **dev と本番で 1 つの App を共用**: 開発中のスコープ追加で本番が再インストール待ちになります
- **画面で直接設定を変え、マニフェストに戻さない**: 次のデプロイで変更が消えます。`apps.manifest.export` で定期的に差分を確認します

---

## Chapter 6: レート制限とスケール

### 1. 制限の種類を区別する

| 制限 | 単位 | 目安 |
|---|---|---|
| Web API の Tier | ワークスペース × アプリ × メソッド、1 分あたり | Tier 1: 1 回以上、Tier 2: 20 回以上、Tier 3: 50 回以上、Tier 4: 100 回以上 |
| `chat.postMessage` | チャンネルごと | 毎秒 1 件程度（短いバーストは許容） |
| Events API の配信 | ワークスペース × アプリ、60 分あたり | 30,000 件。超過分は `app_rate_limited` イベントで通知 |

各メソッドの Tier は、リファレンスの「Facts」欄で確認します。上限を超えると HTTP 429 と `Retry-After`（待つべき秒数）が返ります。

### 2. 429 に自動で再試行させる

slack-sdk の `WebClient` は、既定では接続エラーの再試行（`ConnectionErrorRetryHandler`）しか有効になっていません。**429 の再試行は自分で追加します。**

```python
import os

from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=2))

# Bolt に自前の WebClient を渡すと、リスナーの client / say もこれを使う
app = App(client=client, signing_secret=os.environ["SLACK_SIGNING_SECRET"])
```

- `RateLimitErrorRetryHandler` は `Retry-After` に従って待ってから再試行します
- ⚠ リスナーの中で長く待つと、ack 後とはいえインスタンスのスレッドを占有します。大量送信はキュー（Chapter 2）側で行います

### 3. 大量送信の設計

| やりたいこと | 設計 |
|---|---|
| 1 チャンネルへの連続通知 | まとめて 1 メッセージにする。毎秒 1 件を超えない |
| 多数のユーザーへの DM | キューに積み、ワーカーで送信間隔を制御する |
| 過去ログの一括取得 | ページネーション（`cursor`）で少しずつ。unlisted アプリは特に厳しい（Chapter 5） |

### 4. スケールと状態

コンテナや関数のインスタンスが増えると、**プロセス内の状態は共有されません**。

| 状態 | 置き場所 |
|---|---|
| 重複判定（`event_id`） | Redis などの共有ストア（Chapter 3） |
| OAuth のインストール情報 | 永続ストア（Chapter 5） |
| 会話の文脈（AI エージェント） | 必要最小限のメタデータだけを共有ストアへ。Slack のデータ自体は保存しない（Chapter 7） |

共有ストアに置く状態には、必ず **TTL（有効期限）** と **ストア障害時の方針**（処理を止めるか、続けるか）を決めておきます。重複判定のように「失っても致命的でない」状態は fail-open、OAuth のトークンのように「なければ動けない」状態は fail-closed（エラーとして扱う）が基本です。

### 5. よくあるアンチパターン

- **429 を握りつぶす**: 通知が黙って欠落します。再試行を入れ、それでも失敗したらログに残します
- **ループで `chat.postMessage` を連打**: チャンネルごとの制限にすぐ当たります

---

## Chapter 7: AI エージェントの運用

### 1. 公式の設計原則

Slack は、エージェント型アプリの設計指針を公開しています。運用で特に効くものを抜き出します。

| 原則 | 具体策 |
|---|---|
| **AI であることを明示する** | 名前・アイコン・説明で AI だと分かるようにする。応答のフッター（`context` ブロック）に LLM 生成である旨を表示する |
| **データ境界を守る** | 起動したユーザー本人がアクセスできない情報を、読んだり生成に使ったりしない |
| **Slack のデータを保存しない** | 必要なときにリアルタイムで取得する。保存してよいのはメタデータ |
| **境界付きの自律性** | 確認なしでできることとできないことの境界を決め、最初は制限を強くして、信頼に応じて広げる |
| **実世界に影響する操作は確認必須** | 作成・送信・削除の前にプレビューを見せ、承認・修正・却下を選ばせる。ただし確認疲れを避けるため、本当に必要な場面に限る |
| **失敗時は次の手を示す** | 「問題が発生しました」で終わらせず、再試行・依頼の変更・エスカレーションなど 2〜3 の選択肢を出す |

### 2. プロンプトインジェクション対策

公式のセキュリティガイドは、AI 機能を持つアプリに次の対策を求めています。

- LLM の出力に含まれるリンクの**アンファール（プレビュー展開）を無効化**し、外部ドメインは許可リストで管理する（悪意あるリンク経由の情報送出を防ぐ）
- **他の Bot のメッセージに LLM が反応しない**ようにする（Bot 同士の連鎖や、Bot 経由の指示注入を防ぐ）

Bolt は既定でアプリ自身のイベントを無視しますが、**他の Bot のメッセージは無視しません**。エージェントのリスナーでは、イベントの `bot_id` の有無などで Bot からのメッセージを除外する処理を入れます。

### 3. 状態表示を必ず戻す

エージェントの「処理中」表示（`agents.sessions.setStatus` の `processing`）は、`active` に戻さないと**最大 1 時間残ります**。例外が起きても戻るよう、`try` / `finally` で囲みます。

```python
def answer_with_status(client, channel_id, thread_ts, run_agent):
    # スレッド型セッションでは channel_id と thread_ts を指定する（必要スコープ: chat:write）
    client.api_call(
        "agents.sessions.setStatus",
        json={"channel_id": channel_id, "thread_ts": thread_ts, "status": "processing"},
    )
    try:
        return run_agent()
    finally:
        client.api_call(
            "agents.sessions.setStatus",
            json={"channel_id": channel_id, "thread_ts": thread_ts, "status": "active"},
        )
```

`status` には `active`（次の依頼を受け付けられる）、`processing`（処理中）、`suspended`（ユーザーの確認や承認待ち）、`closed`（セッション終了）があります。Section 1 の「実世界に影響する操作は確認必須」を実装するときは、確認待ちの間を `suspended` にすると、ユーザーに状況が伝わります。

> エージェント関連の API は、名称変更や旧メソッド（`assistant.threads.setStatus` など）との互換ブリッジが続いている領域です。実装時は最新のメソッドリファレンスを確認してください。

### 4. LLM 呼び出しと 3 秒ルール

LLM の応答は 3 秒を超えるのが普通です。Chapter 2 の原則どおり、**イベントで受けて（受領は Bolt が自動で返す）、ストリーミングで少しずつ返す**か、時間がかかる処理はキューに逃がします。ストリーミングは `chat.startStream` → `chat.appendStream` → `chat.stopStream` の 3 つのメソッドで行い、Bolt for Python ではリスナー引数の `say_stream` がこれらをまとめて扱います（使い方は tutorial の Chapter 7）。リトライによる二重回答を防ぐため、Chapter 3 の重複排除はエージェントでこそ必須です。

### 5. よくあるアンチパターン

- **すべての操作に確認ボタン**: 確認疲れで、ユーザーが中身を読まずに承認するようになります
- **エージェントが他の Bot の投稿に返信**: Bot 同士で無限に会話を続けます

---

## Chapter 8: よくある失敗パターン

運用で実際に起きやすい失敗を、症状から引けるようにまとめます。

| 症状 | 主な原因 | 対策 | 詳しくは |
|---|---|---|---|
| 同じ返信が 2〜4 回投稿される | 処理が 3 秒を超えて再送されている | 先に受領、`event_id` で重複排除 | Ch2, Ch3 |
| 朝一番のコマンドだけ失敗する | 最小 0 インスタンスからのコールドスタート | 最小インスタンス数を 1 以上にする | Ch1 |
| モーダルが開かない（`trigger_expired`） | `views_open` の前に重い処理 | 先に開いて `views_update` | Ch2 |
| 重複排除を入れたら再送が増えた | ミドルウェアで `next()` を呼ばずに return → 404 | `BoltResponse(status=200)` を返す | Ch3 |
| インスタンスを増やしたら重複排除が効かない | プロセス内の変数で判定している | 共有ストアで判定 | Ch3, Ch6 |
| イベントが突然届かなくなった | 配信の 95% 超が失敗し、購読が一時無効化 | デプロイ失敗の監視、受領を最優先 | Ch3 |
| スコープ追加後に機能が止まった | 再インストールしていない | スコープ変更をリリース手順に組み込む | Ch4, Ch5 |
| シークレットの値を変えたのに反映されない | 実行環境が起動時にしか読み込まない、または特定のバージョンを固定で参照している | 再起動か再デプロイ。最新版を参照する設定にする | Ch4 |
| Redis が遅い日だけ再送が増える | 重複判定のミドルウェアが受領を遅らせている | 短いタイムアウトと fail-open | Ch3 |
| 12 時間後に Manifest API が失敗する | Configuration token の失効 | `tooling.tokens.rotate` で更新 | Ch5 |
| 開発中の変更で本番が壊れた | dev と本番で 1 つの App を共用 | 環境ごとに App を分ける | Ch5 |
| OAuth インストール後、一部のリクエストで認証エラー | `FileInstallationStore` がインスタンス間で共有されない | 共有の永続ストアに保存 | Ch5 |
| 過去ログ取得が極端に遅い | unlisted アプリの新レート制限（1 分 1 回） | Marketplace 承認、または取得設計の見直し | Ch5, Ch6 |
| 通知がときどき欠落する | 429 を再試行せずに捨てている | `RateLimitErrorRetryHandler` | Ch6 |
| エージェントが「考え中」のまま止まる | 例外で状態表示を戻せていない | `finally` で `active` に戻す | Ch7 |
| Bot 同士が延々と会話する | 他の Bot のメッセージに反応している | Bot からのメッセージを除外 | Ch7 |

---

## Chapter 9: 直感を育てる

### 1. 設計レビューで問う 5 つの質問

1. **このリスナーは 3 秒以内に受領を返すか？** 返した後の処理は、プロセスが落ちても許容できるか
2. **同じイベントが 2 回届いたら何が起きるか？** 二重投稿、二重登録は起きないか
3. **このトークンが漏れたら何ができてしまうか？** スコープは最小か、保管場所はシークレット管理サービスか
4. **インスタンスが 2 台になったら壊れる状態はないか？** プロセス内の変数やローカルファイルに頼っていないか
5. **このエージェントは、確認なしにどこまでやってよいか？** 境界は文書になっているか

### 2. 判断の目安

| 迷ったとき | まず選ぶもの | 例外となる条件 |
|---|---|---|
| 実行方式 | HTTP + コンテナ（最小 1 インスタンス） | 外部から HTTPS を受けられない → Socket Mode。利用が少ない stg → 最小 0 インスタンス |
| 重い処理 | メッセージキュー + 別のワーカー | 数秒で終わり、失敗しても再実行不要 → ack 後にリスナー内で処理 |
| 秘密情報 | シークレット管理サービスへの参照 + 実行環境の ID | 開発環境 → `.env`（`.gitignore` で除外） |
| トークン | Bot token。User token は必要な機能だけ | ユーザー本人として操作する機能 → User token を最小スコープで |
| 設定管理 | マニフェストを正本にし、環境ごとに App を分ける | 個人の検証用 → 1 つの App でもよい |
| レート制限 | `RateLimitErrorRetryHandler` + 送信はキュー側で制御 | 送信が少なく遅延も許されない → 再試行回数を絞る |

### 3. 次の一歩

- **監視を整える**: 受領までの時間、429 の発生数、重複破棄の件数、`app_rate_limited` イベントをメトリクスにすると、障害の予兆が見えます
- **公式の更新を追う**: エージェント機能とレート制限は変化が速い領域です。docs.slack.dev の changelog を定期的に確認します
- **全体像を振り返る**: `slack-app-overview.md` の Chapter 8 の構成早見表と、本教材の判断の目安を突き合わせ、自分のボットの位置を確認します

---

## 関連リソース

### Slack

- **HTTP と Socket Mode の比較**: https://docs.slack.dev/apis/events-api/comparing-http-socket-mode
- **Events API（再送・`event_id`）**: https://docs.slack.dev/apis/events-api/
- **ユーザー操作の処理（3 秒、`trigger_id`、`response_url`）**: https://docs.slack.dev/interactivity/handling-user-interaction
- **lazy listeners**: https://docs.slack.dev/tools/bolt-python/concepts/lazy-listeners
- **グローバルミドルウェア**: https://docs.slack.dev/tools/bolt-python/concepts/global-middleware
- **Bolt for Python の OAuth**: https://docs.slack.dev/tools/bolt-python/concepts/authenticating-oauth
- **Bolt for Python リポジトリ（アダプター・FastAPI サンプル）**: https://github.com/slackapi/bolt-python
- **トークンローテーション**: https://docs.slack.dev/authentication/using-token-rotation
- **セキュリティのベストプラクティス**: https://docs.slack.dev/authentication/best-practices-for-security
- **リクエストの署名検証**: https://docs.slack.dev/authentication/verifying-requests-from-slack
- **App Manifest API**: https://docs.slack.dev/app-manifests/configuring-apps-with-app-manifests
- **apps.manifest.validate**: https://docs.slack.dev/reference/methods/apps.manifest.validate
- **アプリの配布**: https://docs.slack.dev/app-management/distribution/
- **Web API レート制限**: https://docs.slack.dev/apis/web-api/rate-limits
- **2025 年 unlisted アプリのレート制限変更**: https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps
- **Python Slack SDK（RetryHandler）**: https://docs.slack.dev/tools/python-slack-sdk/web/
- **エージェント設計**: https://docs.slack.dev/concepts/agent-design
- **エージェント開発**: https://docs.slack.dev/ai/developing-agents
- **agents.sessions.setStatus**: https://docs.slack.dev/reference/methods/agents.sessions.setStatus

### ホスティング・周辺部品

- **Bolt for Python のアダプター一覧（ソース）**: https://github.com/slackapi/bolt-python/tree/main/slack_bolt/adapter
- **Redis の SET コマンド（`NX`、`EX`）**: https://redis.io/docs/latest/commands/set/
- **redis-py**: https://redis.readthedocs.io/
- **KEDA（キューの長さなどによるスケール）**: https://keda.sh/

### uv

- **uv の Docker 統合ガイド**: https://docs.astral.sh/uv/guides/integration/docker/

### 関連教材

- `slack-app-overview.md` — Slack App の全体像
- `slack-app-tutorial.md` — uv と Bolt for Python で練習用ボットを作るハンズオン
