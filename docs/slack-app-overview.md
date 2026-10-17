---
title: "Slack App 概要"
tags:
  - slack-app
  - overview
  - learning-material
type: overview
created: 2026-10-15
description: "いわゆる Slack ボットを支える Slack App の構成要素・権限・イベント受信・UI・配布・AI エージェント機能を俯瞰する入門教材"
related:
  - "[[Slack]]"
  - "[[OAuth 2.0]]"
  - "[[Webhook]]"
  - "[[WebSocket]]"
  - "[[MCP]]"
  - "[[Claude Tag]]"
---

# Slack App 概要

> Web API や Webhook の基本は分かるが、Slack App（いわゆる Slack ボット）はまだ作ったことがない開発者向けの俯瞰教材です。コードを書く前に「何がどうつながって動いているのか」の地図を手に入れることがゴールです。
> 実際に手を動かして作りたい方 → `slack-app-tutorial.md`
> 本番運用の設計を深めたい方 → `slack-app-best-practices.md`
>
> 本文の仕様は 2026-10-15 時点の公式ドキュメント（docs.slack.dev）で確認しています。

---

## Chapter 0: Slack App とは

### 1. 「ボット」は Slack App の一機能

日常会話で「Slack ボット」と呼ばれているものの正体は、**Slack App** です。Slack App は、Slack のワークスペースに**インストール**して使う外部アプリケーションの総称で、その中の一機能として「ボットユーザー」を持てます。

```text
Slack App（アプリ全体：権限・設定・トークンの単位）
 ├─ ボットユーザー   … チャンネルに参加し、発言する「顔」
 ├─ スラッシュコマンド … /deploy などの入口
 ├─ ショートカット・ボタン・モーダル … 対話 UI
 ├─ App Home        … アプリ専用のタブ
 └─ イベント購読     … Slack で起きたことの通知を受け取る
```

つまり「ボットを作る」とは、正確には「ボットユーザーを持つ Slack App を作る」ことです。

### 2. メタファー：社内に席をもらった外部スタッフ

Slack App は **「ワークスペースという会社に、入館証付きで席をもらった外部スタッフ」** と考えると理解しやすくなります。

| 外部スタッフ | Slack App |
|---|---|
| 入館証（何ができるかが書いてある） | トークンとスコープ |
| 総務からの館内放送・内線 | イベント通知（Events API / Socket Mode） |
| 受付窓口・申込用紙 | スラッシュコマンド、ショートカット、モーダル |
| 社内で発言・掲示する | Web API（`chat.postMessage` など） |
| 入社手続き | インストール（OAuth：利用者の同意を得てトークンを発行する標準手順） |

スタッフ本人（アプリのプログラム）は **Slack の外**、つまり自分のサーバーやクラウドで動きます。Slack はそのスタッフへ連絡し、スタッフは入館証の範囲内で Slack を操作します。

### 3. なぜ Slack App を作るのか

- **人が集まる場所で仕事を完結させる**: 通知・承認・問い合わせ対応を、別ツールへ移動せずに Slack 内で済ませられる
- **双方向にできる**: 単に投稿するだけの Webhook 連携と違い、ボタン操作やメンションに反応できる
- **権限を細かく絞れる**: 個人のアカウントを使い回さず、アプリ専用の権限で動かせる
- **AI エージェントの入口にできる**: Slack はエージェント向けの専用画面や API を提供している（Chapter 7 で扱います）

### 4. 位置づけ：3 つの「Slack を自動化する手段」

| 手段 | コード | ホスティング | 向いている用途 |
|---|---|---|---|
| **Workflow Builder** | 不要 | Slack | 定型の申請・通知フローを非エンジニアが組む |
| **Slack App（Bolt など）** | 必要 | 自前 | 外部システム連携、複雑なロジック、ボット |
| **Deno Slack SDK のアプリ** | 必要 | Slack | Slack 上で完結するワークフローとカスタムステップ |

公式ドキュメントは「ワークフローは、独自の能力と制約を持つ Slack App の一種」と位置づけています。本教材は主に 2 行目、自前ホストの Slack App を扱います。

---

## Chapter 1: 構成要素の全体マップ

### 1. 主要構成要素

| 構成要素 | 一言で | 詳しくは |
|---|---|---|
| **App 設定（api.slack.com/apps）** | アプリの登録情報・権限・URL を管理する画面 | Ch5 |
| **App Manifest** | 上記の設定を JSON / YAML で表したもの | Ch5 |
| **トークン** | Slack API を呼ぶときの身分証（`xoxb-` など） | Ch2 |
| **スコープ** | トークンで何ができるかの許可リスト | Ch2 |
| **Web API** | アプリ → Slack の操作（投稿、取得、モーダル表示） | Ch2 |
| **Events API** | Slack → アプリの通知（メンション、メッセージ等） | Ch3 |
| **Socket Mode** | イベントを HTTP ではなく WebSocket で受け取る方式 | Ch3 |
| **インタラクティビティ** | コマンド・ボタン・モーダル送信などのユーザー操作 | Ch4 |
| **Block Kit** | メッセージやモーダルの UI を組む部品体系 | Ch4 |
| **Bolt / SDK / Slack CLI** | 上記をまとめて扱う公式フレームワークと道具 | Ch5 |
| **OAuth・配布** | 他のワークスペースへインストールさせる仕組み | Ch6 |
| **エージェント機能** | AI アプリ向けの専用画面・ストリーミング API | Ch7 |

### 2. データの流れ

Slack App の通信は、**向きが逆の 2 本の流れ**でできています。

```text
            ① Slack → アプリ（受け取る）
   ┌──────── Events API / インタラクション ────────┐
   │      （HTTP POST または Socket Mode）          ▼
┌───────┐                                     ┌──────────┐
│ Slack │                                     │ あなたの  │
│       │ ◀──────── Web API 呼び出し ──────── │ アプリ    │
└───────┘      ② アプリ → Slack（操作する）     └──────────┘
                 Authorization: Bearer xoxb-...
```

- ① は「何かが起きた」「ボタンが押された」という**通知**です。アプリは素早く受領を返す必要があります（Chapter 3・4）
- ② は「投稿する」「モーダルを開く」という**操作**です。トークンとスコープで権限が決まります（Chapter 2）

ボットの基本動作は「① でメンションを受け取り、② で返信する」の組み合わせです。

### 3. よくあるアンチパターン

- **Slack の中でコードが動くと思い込む**: 自前ホストの App は、あなたのサーバーが止まれば止まります
- **ボット = App と混同して設定を探す**: コマンドやモーダルは「ボット」ではなく App の設定にあります

---

## Chapter 2: 権限モデル：トークンとスコープ

### 1. トークンは「誰として」動くかを決める

Slack App は複数種類のトークンを使い分けます。プレフィックスで見分けられます。

| トークン | プレフィックス | 誰として動くか | 主な用途 |
|---|---|---|---|
| ⭐ **Bot token** | `xoxb-` | アプリのボットユーザー | ほとんどのボット操作。インストールしたユーザーに依存しない |
| **User token** | `xoxp-` | インストール・認可したユーザー本人 | ユーザーの代わりに操作する必要がある場合 |
| **App-level token** | `xapp-` | アプリ全体（複数組織をまたぐ） | Socket Mode の接続など |

このほか、ワークフロー実行時に一時発行される **Workflow token**（`xwfp-`）、App Manifest API 用の **Configuration token**、Deno Slack SDK アプリ用の **Service token** があります。いずれも Chapter 5 で扱う道具に付随するもので、最初は意識しなくて構いません。

→ 迷ったら **Bot token** を使います。User token は「その人として」動くため、権限が強く、退職などで無効になる点に注意します。

### 2. スコープは「入館証に書かれた許可」

スコープは、トークンで呼べる操作の許可リストです。Bot token は **粒度の細かい権限（granular bot permissions）** を採用しており、必要なスコープだけを個別に要求します。

```text
例: メンションに返信するボット
  app_mentions:read   … メンションイベントを受け取る
  chat:write          … メッセージを投稿する
```

> 以前は包括的な `bot` スコープを使う「レガシー bot」がありましたが、現在は非推奨で、新しいプラットフォーム機能はサポートされません。古い記事のサンプルに注意してください。

スコープを追加・変更した場合、既存のインストールは**再インストール（再認可）**が必要です。

### 3. Web API のレート制限

Web API はメソッドごとに Tier が決まっており、**ワークスペース × アプリ × メソッド**単位で制限されます。

| Tier | 目安（1 分あたり） | 傾向 |
|---|---|---|
| Tier 1 | 1 回以上 | まれにしか呼ばないメソッド |
| Tier 2 | 20 回以上 | 多くのメソッドが該当 |
| Tier 3 | 50 回以上 | 一覧取得・ページネーション系に多い |
| Tier 4 | 100 回以上 | 大きめの枠、バーストに寛容 |
| Special | メソッドごと | 各リファレンスで確認 |

- `chat.postMessage` は特別扱いで、**1 チャンネルあたり毎秒 1 件程度**が目安です
- 超過すると HTTP `429` と `Retry-After`（待つべき秒数）が返ります
- 各メソッドの Tier は、リファレンスの「Facts」欄に書かれています

### 4. よくあるアンチパターン

- **「とりあえず全部」のスコープ要求**: 管理者の承認が通りにくくなり、漏洩時の被害も広がります
- **User token で何でもやる**: 作った人が抜けた瞬間にボットが止まります

---

## Chapter 3: イベントを受け取る：Events API と Socket Mode

### 1. Events API：Slack からの「館内放送」

Events API は、Slack で起きた出来事（メンションされた、DM が来た、リアクションが付いた等）をアプリへ通知する仕組みです。アプリは受け取りたいイベントを**購読**し、対応するスコープを持っている必要があります。

配信方法は 2 通りあります。

| 方式 | 仕組み | アプリ側に必要なもの |
|---|---|---|
| **HTTP（Request URL）** | Slack がイベントごとに JSON を HTTP POST する（1 リクエスト 1 イベント） | インターネットから届く公開 HTTPS エンドポイント |
| **Socket Mode** | アプリから Slack へ WebSocket をつなぎ、その上でイベントを受け取る | App-level token（`connections:write`） |

### 2. 共通ルール：3 秒以内に受領を返す

どちらの方式でも、アプリは**受け取ったことを素早く返す**必要があります。

| 項目 | HTTP の場合 |
|---|---|
| 応答期限 | ⭐ **3 秒以内**に HTTP 2xx。超えると配信失敗扱い |
| リトライ | 失敗すると最大 3 回再送される（ほぼ即時 → 1 分後 → 5 分後） |
| 失敗が続くと | 失敗率が極端に高いと、イベント購読が一時的に無効化される |

公式の推奨は **「すぐ 200 を返し、重い処理はキューで非同期に行う」** です。Socket Mode でも、各イベントに付いている `envelope_id`（配信ごとの識別子）を返して受領を伝える必要があります。配信上限やリトライ制御用ヘッダーなどの運用上の詳細は best-practices で扱います。

> **うまくいかない時**: 同じメッセージに 2 回、3 回と返信してしまう場合、処理が 3 秒を超えてリトライが来ている可能性が高いです。`x-slack-retry-num` ヘッダーの有無で見分けられます。

なお HTTP では、Request URL を設定するときに `url_verification` リクエストが届くことがあり、これに正しく応答できないと URL を登録できません。Bolt を使えば自動で処理されます。

### 3. HTTP と Socket Mode の比較

| 観点 | HTTP | Socket Mode |
|---|---|---|
| 公開エンドポイント | 必要（HTTPS） | **不要**。社内ネットワークやローカル PC から使える |
| 公式の位置づけ | **本番運用で推奨** | 開発・ローカル、外部から HTTP を受けられない環境向け |
| スケール | ステートレス（接続状態を持たない）で水平スケールしやすい | ステートフル（接続状態を持つ）。同時接続は**アプリあたり最大 10** |
| 信頼性 | リクエストごとに完結 | 長時間接続のため、切断や再起動の影響を受ける |
| Slack Marketplace | 掲載するなら**必須** | **掲載不可**（Marketplace 外での配布は可能） |
| 検証 | 署名検証が必要（Chapter 6） | WebSocket 上のイベントは署名検証不要 |
| 排他性 | — | Socket Mode を有効にしている間は Request URL を設定できない |

```text
開発中（手元の PC）        本番（チームで公開運用）
  Socket Mode       ──▶      HTTP Request URL
  URL 公開不要                 スケール・Marketplace 対応
```

Socket Mode の WebSocket URL は、App-level token で `apps.connections.open` を呼ぶと払い出され、定期的に更新（再接続）されます。この再接続処理は Bolt などの SDK が引き受けます。

### 4. よくあるアンチパターン

- **イベント受信の中で LLM や外部 API を同期的に待つ**: 3 秒を超えてリトライが重なり、重複投稿になります
- **本番を Socket Mode 1 プロセスで運用**: 再起動中のイベントや接続上限の考慮が抜けがちです

---

## Chapter 4: ユーザーとの接点：入口とサーフェス

### 1. ユーザーがアプリを呼び出す「入口」

| 入口 | 起動のしかた | 典型的な用途 |
|---|---|---|
| **メンション / DM** | `@アプリ名` で話しかける、DM を送る（Events API で受信） | 会話型ボット、質問応答 |
| **スラッシュコマンド** | メッセージ入力欄に `/deploy staging` のように打つ | 明示的なコマンド操作 |
| **ショートカット** | UI のメニューやメッセージのメニューから起動 | フォームを開く、メッセージを起点に処理 |
| **インタラクティブ部品** | メッセージやモーダル内のボタン・メニューを操作 | 承認ボタン、選択肢 |
| **自動起動** | スケジュール、外部 Webhook、イベント | 定期レポート、外部通知 |

スラッシュコマンド・ショートカット・ボタンなどの操作は、App 設定の **Interactivity & Shortcuts** で指定した Request URL（または Socket Mode）に届きます。

### 2. 操作に応答するときの制約

| 項目 | 制約 |
|---|---|
| 受領（ack） | ペイロード（Slack から届く操作内容の JSON）受信から **3 秒以内**に HTTP 200。超えるとユーザーにエラー表示 |
| `trigger_id`（モーダルを開くための引換券） | **3 秒で失効**、**1 回限り**（`trigger_expired` / `trigger_exchanged`） |
| `response_url`（その操作への返信用 URL） | 受信から **30 分以内に最大 5 回**まで使用可能 |
| Request URL（配布する場合） | HTTPS 必須、自己署名証明書は不可 |

⚠ 特に `trigger_id` の 3 秒は厳しく、「処理してからモーダルを開く」順番だと失効します。**先にモーダルを開き、後から内容を更新する**のが定石です。

### 3. サーフェスと Block Kit

アプリが UI を表示できる場所を **サーフェス** と呼びます。

| サーフェス | 特徴 | ブロック上限 |
|---|---|---|
| **メッセージ** | チャンネル・スレッド・DM への投稿 | 1 メッセージ 50 ブロック |
| **モーダル** | 入力フォームなどのダイアログ | 100 ブロック |
| **App Home** | アプリ専用タブ。ダッシュボードや設定画面に使う | 100 ブロック |

どのサーフェスも **Block Kit** という共通の部品体系で、`blocks` 配列（JSON）として組み立てます。

| 階層 | 役割 | 例 |
|---|---|---|
| **Blocks** | レイアウトの単位 | `section`、`header` |
| **Block elements** | 主にインタラクティブな部品。ブロックの中に置く | `button`、メニュー |
| **Composition objects** | テキストや選択肢を定義する小さな部品 | テキストオブジェクト |

次の例は、見出しとボタン付きの文を組んだ `blocks` 配列です。構造の階層関係を見るための例です。

```json
[
  { "type": "header", "text": { "type": "plain_text", "text": "デプロイ承認" } },
  {
    "type": "section",
    "text": { "type": "mrkdwn", "text": "*staging* へのデプロイを承認しますか？" },
    "accessory": {
      "type": "button",
      "text": { "type": "plain_text", "text": "承認" },
      "action_id": "approve_deploy"
    }
  }
]
```

ボタンが押されると、`action_id` 付きのインタラクションがアプリに届きます。ブロックはサーフェスによって使えないものもあるため、リファレンスで互換性を確認します。JSON を手書きする前に **Block Kit Builder**（ブラウザで組んでプレビューできるツール）で試すと効率的です。

### 4. よくあるアンチパターン

- **重い処理の後に `trigger_id` を使う**: モーダルが開かずに失敗します
- **50 ブロックを超える長大な一覧を 1 メッセージに詰める**: 分割するか App Home やモーダルへ逃がします

---

## Chapter 5: 開発手段：Bolt・SDK・CLI・マニフェスト

### 1. 道具の全体像

| 道具 | 役割 |
|---|---|
| ⭐ **Bolt**（Python / JavaScript / Java） | Slack App 用の公式フレームワーク。署名検証、ack、Socket Mode、OAuth などの定型処理を引き受ける |
| **Slack SDK**（Python / Node / Java） | Web API クライアントなど、より低レベルな部品 |
| **Slack CLI** | アプリの作成（`slack create`）、ローカル実行（`slack run`）、設定画面を開く等 |
| **App Manifest** | アプリ設定を JSON / YAML で表したもの。Git 管理やコピーに使う |
| **Deno Slack SDK** | Slack がホストするワークフローアプリ用の SDK |

ゼロから HTTP サーバーと署名検証を書くことも可能ですが、通常は **Bolt を選ぶのが近道**です。

### 2. Bolt のリスナーと ack

Bolt では、「何が届いたら何をするか」をリスナーとして書きます。次は Bolt for Python の README の例をもとに、同じメンション応答リスナーを HTTP と Socket Mode の両方で受ける形にしたものです。受け口の違いを見るための例で、実行手順は tutorial で扱います。

```python
# HTTP で受ける場合（環境変数 SLACK_SIGNING_SECRET と SLACK_BOT_TOKEN を読む）
# Slack から届く公開 HTTPS の URL（ngrok などのトンネル）が別途必要
from slack_bolt import App

app = App()

@app.event("app_mention")
def handle_mention(say):
    say("呼びましたか？")

if __name__ == "__main__":
    app.start(3000)  # POST http://localhost:3000/slack/events
```

```python
# Socket Mode で受ける場合（公開 URL 不要）
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.event("app_mention")
def handle_mention(say):
    say("呼びましたか？")

if __name__ == "__main__":
    # connections:write スコープを持つ App-level token（xapp-）を使う
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
```

リスナーは同じで、**受け口だけを差し替えられる**ことが分かります。Chapter 3 の「開発は Socket Mode、本番は HTTP」という移行がしやすいのはこのためです。

リスナーには `ack`、`say`、`respond` といった道具が渡されます。

| 道具 | 役割 |
|---|---|
| `ack()` | 受領を Slack に返す。actions・commands・shortcuts・options・view submissions では**必須** |
| `say()` | イベントが起きたチャンネルへ投稿する |
| `respond()` | `response_url` を使って、その操作に返信する |

> FaaS（サーバーレス）環境では、ack を返した時点で処理が打ち切られることがあるため、Bolt for Python は **lazy listeners** という仕組みを用意しています。詳細は tutorial / best-practices で扱います。

### 3. App Manifest：設定のコード化

App 設定画面で行う設定（名前、スコープ、イベント購読、コマンド、Socket Mode の有無など）は、**App Manifest** として JSON / YAML で表せます。

- 設定画面の **Features > App Manifest** で確認・編集できる
- **Create New App** でマニフェストから新規作成できる（開発用・本番用の複製に便利）
- App Manifest API と Configuration token で、プログラムから作成・更新もできる
- マニフェストには v1 と v2 があり、Deno Slack SDK のアプリは v2 を使う

### 4. ワークフローとの関係

Chapter 0 で見た 3 つの手段は、**カスタムワークフローステップ**でつながります。カスタムステップは Bolt（自前ホスト）でも Deno Slack SDK（Slack ホスト）でも作れ、どちらも Slack CLI で開発します。Bolt で作った App は、Workflow Builder から呼べる**カスタムステップ**を提供することもできます。「非エンジニアが組むフローの一部だけをコードで書く」という分担が可能です。

### 5. よくあるアンチパターン

- **設定画面だけで管理し、本番と開発の差分が分からなくなる**: マニフェストを Git に置きます
- **Bolt を使わず署名検証や ack を自作して抜け漏れる**: 特別な理由がなければ Bolt を使います

---

## Chapter 6: 配布とセキュリティ

### 1. 配布の 3 段階

| 段階 | 対象 | 必要なこと | 向いている用途 |
|---|---|---|---|
| **単一ワークスペース** | 作成したワークスペースだけ | 設定画面の「Install App to Workspace」 | 社内ボット |
| **公開配布（Unlisted）** | 他のワークスペースも | OAuth 2.0 フローの実装、全 URL の SSL 化、「Activate Public Distribution」 | 早期顧客とのパイロット |
| **Slack Marketplace（Listed）** | 誰でも検索・導入 | 上記 + Marketplace のレビュー通過（HTTP 方式が必須） | 商用プロダクト |

- 他のワークスペースへ配るには、ワークスペースごとにトークンを発行する **OAuth 2.0 フロー**が必要です。公開配布を有効にすると「Add to Slack」ボタンと共有用 URL が使えます
- Enterprise 組織全体へデプロイ可能にするには、マニフェストの `settings.org_deploy_enabled` を使います
- ⚠ Marketplace 掲載後は、公開配布の無効化ボタンでは止められず、掲載の終了手続きが必要です

### 2. 2025 年のレート制限変更に注意

**商用配布されていて Marketplace 未承認のアプリ（unlisted アプリ）**では、`conversations.history` と `conversations.replies`（過去メッセージの取得）のレート制限が大きく引き下げられました。

| 項目 | unlisted アプリ（変更後） | 社内向けの自作アプリ |
|---|---|---|
| Tier | Tier 1（**1 分あたり 1 リクエスト**） | 従来どおり（50 回以上/分） |
| `limit` の上限・既定値 | **15 件** | 1,000 件 |

- 適用対象: 2025 年 5 月 29 日以降に作成された unlisted アプリと、既存 unlisted アプリの新規インストール
- 対象外: 既存のインストール、Marketplace 承認済みアプリ、社内の顧客が自作したアプリ

社内ボットは影響を受けませんが、**他社へ配る予定のアプリで過去ログを大量に読む設計**（要約ボットや RAG（検索で集めた文書を LLM に渡す手法）の取り込みなど）は、Marketplace 承認を前提に計画する必要があります。

### 3. リクエストの署名検証

HTTP で受けるアプリは、届いたリクエストが**本当に Slack から来たか**を確かめる必要があります。仕組みは、リクエストのタイムスタンプとボディから、App 設定にある **Signing Secret** を鍵に HMAC-SHA256 で署名を計算し、ヘッダー `X-Slack-Signature` と照合するというものです。

- タイムスタンプが 5 分以上古いリクエストは破棄します（リプレイ攻撃＝盗んだ正規リクエストの再送への対策）
- 古い **verification token** 方式は非推奨で、Signing Secret だけを使うよう公式が強く勧めています
- Bolt は `SLACK_SIGNING_SECRET` を渡すだけで自動検証します。自作する場合の手順は公式の「Verifying requests from Slack」を参照してください

### 4. セキュリティの基本チェック

| 観点 | 押さえること |
|---|---|
| 秘密情報 | Bot token、App-level token、Signing Secret をコードに直書きしない |
| 権限 | 必要最小限のスコープだけを要求する（承認も通りやすい） |
| 検証 | HTTP なら署名検証を必ず行う |
| 経路 | 配布する場合、すべての URL を HTTPS（自己署名不可）にする |

### 5. よくあるアンチパターン

- **署名検証を省略した公開エンドポイント**: 誰でも偽のコマンドを送れてしまいます
- **トークンを Slack のチャンネルに貼って共有**: 漏洩したらすぐ再発行します

---

## Chapter 7: AI エージェントとしての Slack App

### 1. Slack が用意するエージェント向け機能

Slack は、推論・ツール利用・文脈保持を行う AI アプリ（エージェント）を Slack App として作るための専用機能を提供しています。

| 機能 | 内容 |
|---|---|
| **専用サーフェス** | 分割表示のコンテナ、トップナビからの入口、アプリとのスレッド |
| **テキストストリーミング** | `chat.startStream` → `chat.appendStream` → `chat.stopStream` で、生成中の文章を少しずつ表示 |
| **提案プロンプト** | `assistant.threads.setSuggestedPrompts` で、会話の最初に選択肢を提示 |
| **状態表示** | `agents.sessions.setStatus` で「処理中」を表示（応答後に `active` に戻さないと 1 時間残る） |
| **タスク表示** | ストリームの中で計画やタスクの進捗（`in_progress` / `completed` / `error`）を表示 |

主なスコープは `assistant:write`（状態・提案プロンプト・スレッドタイトルの設定）で、`message.im` や `app_context_changed` などのイベントを購読します。Bolt には、ストリーミングをまとめて扱う `say_stream` のような補助機能があります。

> 一部の AI 機能の開発・利用には**有料プラン**が必要です。有料プランがない場合は、Developer Program に参加すると開発用のサンドボックスを無料で用意できます。ただし、誰でも作れる基本サンドボックスは一部の機能が制限され、1 か月でアーカイブされます。すべての機能を使うには、有料プランのワークスペースのメンバーであるか、支払い方法を登録する必要があります（課金はされません）。
>
> エージェント関連の API は新しく、名称の変更や旧メソッドとの互換ブリッジ（`assistant.threads.setStatus` → `agents.sessions.setStatus` など）が見られます。実装前に必ず最新の公式ドキュメントを確認してください（本教材の確認日: 2026-10-15）。

### 2. 3 秒ルールとの付き合い方

LLM の応答は数秒〜数十秒かかるため、Chapter 3・4 の 3 秒ルールと正面からぶつかります。

```text
メンション受信
   │
   ├─ すぐ ack / 200 を返す             （3 秒以内）
   ├─ 状態を「処理中」にする
   ├─ 非同期で LLM を呼ぶ
   ├─ ストリーミングで少しずつ表示
   └─ 完了したら状態を戻す
```

「受領は即座に、処理は非同期に、経過はストリーミングで見せる」という形が、エージェント型 Slack App の基本形です。

### 3. MCP との関係

| 方向 | 仕組み | 例 |
|---|---|---|
| **外部 AI → Slack** | **Slack MCP Server**：MCP 対応クライアントから Slack を検索・投稿・キャンバス操作 | Claude や Cursor から Slack を操作 |
| **Slack → 外部ツール** | **Slackbot MCP Client**：リモート MCP サーバーを Slack に接続し、会話中に呼び出す | 社内ツールを Slackbot から使う |

MCP（Model Context Protocol）は、AI クライアントと外部ツールをつなぐ共通プロトコルです。

「自分で Slack App を作る」以外にも、既存の AI クライアントと Slack を MCP でつなぐ選択肢がある、という点を押さえておきます。Claude を Slack で使う具体例は `claude-tag-tutorial.md` を参照してください。

### 4. よくあるアンチパターン

- **LLM 呼び出しを ack の前に置く**: リトライで同じ質問に何度も回答します
- **状態表示を戻し忘れる**: 「処理中」が 1 時間残り、壊れているように見えます

---

## Chapter 8: 構成の選び方と次の一歩

### 1. 用途別の構成早見表

| やりたいこと | 受け口 | 主な部品 | 配布 |
|---|---|---|---|
| CI の結果を通知するだけ | （受信不要） | Bot token + `chat:write` | 単一ワークスペース |
| メンションに答える社内ボット | 開発: Socket Mode / 本番: HTTP | Events API（`app_mention`） | 単一ワークスペース |
| 承認フロー（ボタンで承認） | HTTP | Block Kit + インタラクティビティ | 単一ワークスペース |
| 申請フォーム | HTTP | ショートカット or コマンド + モーダル | 単一ワークスペース |
| 社内 AI アシスタント | HTTP（社外に公開できない場合は Socket Mode） | エージェント機能 + ストリーミング | 単一ワークスペース |
| 他社にも提供する SaaS 連携 | **HTTP 推奨**（Marketplace 掲載には必須） | OAuth 2.0 + 上記一式 | 公開配布 → Marketplace |
| 非エンジニアが定型フローを作る | — | Workflow Builder（必要ならカスタムステップ） | — |

### 2. 判断のための 4 つの問い

1. **公開 HTTPS エンドポイントを用意できるか？** できないなら Socket Mode（ただし Marketplace 不可）
2. **Slack の外のシステムと連携するか？** するなら自前ホストの Bolt アプリ。Slack 内で完結するなら Workflow Builder や Deno SDK も候補
3. **他のワークスペースに配るか？** 配るなら OAuth を最初から前提にし、Marketplace 掲載まで視野に入れるなら HTTP を選ぶ
4. **処理は 3 秒で終わるか？** 終わらないなら「即 ack + 非同期処理」を設計の起点にする

### 3. 次の一歩

- **手を動かす** → `slack-app-tutorial.md`: リポジトリの章ごとのコードを使い、uv と Bolt for Python でメンションに返信するボットを作り、コマンド・ボタン・モーダル・App Home・ストリーミングへ広げます
- **運用を設計する** → `slack-app-best-practices.md`: 重複処理対策、トークン管理、マニフェスト運用、レート制限との付き合い方
- **まず触ってみる** → ワークスペースがなければ Developer Program のサンドボックスを用意し、Slack CLI のクイックスタート（`slack login` → `slack create first-slack-app` → `slack run`）を試す

### 4. 直感を育てるコツ

- **「誰として」「どの向きに」を常に意識する**: トークン（誰として）と、イベント / Web API（どの向き）を切り分けると、ほとんどの設定画面の意味が分かります
- **3 秒を体で覚える**: Slack App の不具合の多くは「返事が遅い」ことから始まります
- **公式ドキュメントの日付を見る**: エージェント機能やレート制限は変化が速い領域です

---

## 関連リソース

- **Slack 開発者ドキュメント トップ**: https://docs.slack.dev/
- **クイックスタート（Slack CLI）**: https://docs.slack.dev/quickstart
- **トークンの種類**: https://docs.slack.dev/authentication/tokens
- **Events API**: https://docs.slack.dev/apis/events-api/
- **Socket Mode**: https://docs.slack.dev/apis/events-api/using-socket-mode
- **HTTP と Socket Mode の比較**: https://docs.slack.dev/apis/events-api/comparing-http-socket-mode
- **インタラクティビティ**: https://docs.slack.dev/interactivity/
- **ユーザー操作の処理（3 秒、trigger_id、response_url）**: https://docs.slack.dev/interactivity/handling-user-interaction
- **Block Kit**: https://docs.slack.dev/block-kit/
- **App Manifest**: https://docs.slack.dev/app-manifests/
- **ワークフロー**: https://docs.slack.dev/workflows/
- **Bolt for Python**: https://docs.slack.dev/tools/bolt-python/
- **Bolt for Python（ack）**: https://docs.slack.dev/tools/bolt-python/concepts/acknowledge
- **Bolt for Python リポジトリ**: https://github.com/slackapi/bolt-python
- **リクエストの署名検証**: https://docs.slack.dev/authentication/verifying-requests-from-slack
- **Web API レート制限**: https://docs.slack.dev/apis/web-api/rate-limits
- **2025 年 unlisted アプリのレート制限変更**: https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps
- **アプリの配布**: https://docs.slack.dev/app-management/distribution/
- **AI / エージェント**: https://docs.slack.dev/ai/
- **エージェント開発**: https://docs.slack.dev/ai/developing-agents
- **App 管理画面**: https://api.slack.com/apps

### 関連教材

- `claude-tag-tutorial.md` — Claude を Slack で使う（Claude Tag）
- `slack-app-tutorial.md` — uv と Bolt for Python で練習用ボットを作るハンズオン
- `slack-app-best-practices.md` — 本番運用（コンテナ / 関数でのホスティング）の設計原則と失敗パターン
