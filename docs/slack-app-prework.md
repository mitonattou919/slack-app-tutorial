---
title: "Slack App チュートリアルの準備"
tags:
  - slack-app
  - tutorial
  - learning-material
type: prework
created: 2026-10-17
description: "Slack App チュートリアルを始める前の準備（ツールのインストール、Developer Program のサンドボックス作成、リポジトリの取得）を、つまずいたときの対処まで含めて自分で完結できるようにまとめた手順"
related:
  - "[[Slack]]"
  - "[[uv]]"
  - "[[Git]]"
---

# Slack App チュートリアルの準備

> `slack-app-tutorial.md` を始める前に済ませておく準備です。この手順を終えたら、チュートリアルの Chapter 1「3. マニフェストからアプリを作る」から始められます。
> 各手順に「うまくいかない時」の対処を付けてあります。上から順に進めれば、自分だけで準備を終えられます。
>
> 所要時間の目安: 30 分程度（サンドボックスの有効化メールを待つ時間を除く）

---

## 準備することの一覧

| # | やること | 確認のしかた |
|---|---|---|
| 1 | uv と Git をインストールする | `uv --version` と `git --version` でバージョンが表示される |
| 2 | リポジトリを取得し、依存関係を入れる | 動作確認のコマンドで `OK` と表示される |
| 3 | Slack Developer Program に参加し、サンドボックスを作る | サンドボックスのワークスペースにログインできる |
| 4 | サンドボックスに練習用チャンネルを作る | `#bot-practice` が見える |

手順 1〜2 は手元の PC だけで終わります。手順 3 はメールの受け取りが必要です。

---

## 1. uv と Git をインストールする

### uv

uv は Python のパッケージとプロジェクトを管理するツールです。Python 本体も uv が自動で用意するので、Python を別にインストールする必要はありません。

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```powershell
# Windows（PowerShell）
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Homebrew を使っている場合は `brew install uv` でも構いません。インストール後、**ターミナルを開き直して**から確認します。

```bash
uv --version   # 例: uv 0.13.1
```

### Git

```bash
git --version
```

表示されなければインストールします。macOS は `xcode-select --install`（または `brew install git`）、Windows は Git for Windows（https://git-scm.com/）を使います。

> **うまくいかない時**:
> - `uv: command not found`（Windows では「認識されません」）→ ターミナルを開き直します。それでも駄目なら、インストール時に表示された「PATH に追加する」旨の案内に従うか、PC を再起動します
> - インストールのコマンドが通信エラーになる → 社内ネットワークのプロキシが原因の可能性があります。手順 2 の「プロキシがある環境」を参照してください

---

## 2. リポジトリを取得し、依存関係を入れる

作業用のディレクトリで、次を実行します。

```bash
git clone https://github.com/mitonattou919/slack-app-tutorial.git
cd slack-app-tutorial
uv sync
```

`uv sync` は、必要なバージョンの Python と依存関係（Bolt for Python など）を `.venv/` にインストールします。初回は数十秒かかることがあります。

続いて、トークンを書くファイルのひな形をコピーしておきます（中身はチュートリアルの Chapter 1 で書き込みます）。

```bash
cp .env.example .env
```

最後に、動作確認をします。

```bash
uv run python -c "import slack_bolt, slack_helpers; print('OK', slack_bolt.version.__version__)"
```

`OK 1.30.0` のように表示されれば完了です（バージョンの数字は違っていても構いません）。

### うまくいかない時

| 症状 | 対処 |
|---|---|
| `git clone` や `uv sync` が通信エラー・タイムアウトになる | 下の「プロキシがある環境」を参照 |
| `SSL` や `certificate` を含むエラーが出る | 社内ネットワークが通信を検査している可能性があります。`uv sync --system-certs` で、OS に登録された証明書を使って実行し直します（古い uv で `unexpected argument` と出る場合は `uv sync --native-tls`） |
| `git clone` がどうしても通らない | GitHub のリポジトリのページ（https://github.com/mitonattou919/slack-app-tutorial）で **Code** → **Download ZIP** を選び、展開したディレクトリで `uv sync` 以降を実行します（この場合、チュートリアルの `git restore` は使えません） |
| `ModuleNotFoundError` が出る | `slack-app-tutorial` ディレクトリの中で実行しているか、`uv sync` が最後まで成功したかを確認します |
| 何をしても直らない | `.venv` ディレクトリを削除してから、もう一度 `uv sync` を実行します |

### プロキシがある環境

会社のネットワークでは、外部への通信にプロキシ（中継サーバー）を通す必要があることがあります。プロキシのアドレスは、OS のネットワーク設定や、ブラウザのプロキシ設定で確認できます（例: `http://proxy.example.com:8080`）。

アドレスが分かったら、環境変数 `HTTPS_PROXY` に設定してから、失敗したコマンドを実行し直します。Git と uv はどちらもこの環境変数を読みます。

```bash
# macOS / Linux（このターミナルを閉じるまで有効）
export HTTPS_PROXY=http://proxy.example.com:8080
```

```powershell
# Windows（PowerShell。このウィンドウを閉じるまで有効）
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
```

---

## 3. Slack Developer Program に参加し、サンドボックスを作る

チュートリアルでは、**自分専用の練習用ワークスペース**（Developer Program のサンドボックス）を使います。会社の Slack ワークスペースは使いません。アプリの追加に管理者の承認が要らず、練習用のメッセージが同僚に見えることもありません。

### 登録に使うメールアドレス

サンドボックスへのログインは、登録したメールアドレスに届く使い捨てのコードで行います。**チュートリアル中にすぐ受信できるアドレス**を使ってください。会社のメールアドレスを使う場合は、社外サービスへの登録について社内のルールを確認しておきます。

### 手順

1. https://api.slack.com/developer-program を開き、「Join the Program」を押す。登録フォームに記入して **Submit** する
2. 届いたメールの **Activate Developer Account** を押して有効化する（ダッシュボードが開く）
3. ダッシュボードの **Sandboxes** を開き、**Provision Sandbox** を押す
4. サンドボックスの内容を選ぶ画面では、**空のサンドボックス**（ワークスペース 1 つとデモユーザー 1 人）を選ぶ。テンプレート（架空のユーザーやチャンネル入り）でも動きますが、練習には不要です
5. もう一度 **Provision Sandbox** を押し、**Manage Sandboxes** を押す。作ったサンドボックスが Sandboxes ページに表示される
6. サンドボックスの名前を押し、メールアドレスでログインする。確認が終わると、サンドボックスと同じ名前のワークスペースが表示される

> 画面の名称や配置は 2026-10 時点のものです。変わっている場合は、同じ意味のボタンを探してください。

### ⚠ 期限と作り直し

誰でも作れる**基本サンドボックス**は、**1 か月で期限切れ（アーカイブ）**になります。アーカイブされると、作った本人もログインできなくなります（アーカイブ前にはメールで通知が届きます）。**チュートリアルを始める日に近いタイミング**で作るのがおすすめです。

期限が切れても、新しいサンドボックスを作り直せば続きから進められます。コードとマニフェストは手元のリポジトリにあるので、失われるのは Slack 側のアプリとトークンだけです（チュートリアルの Chapter 1「3. マニフェストからアプリを作る」からやり直します）。

| 項目 | 内容 |
|---|---|
| 同時に持てる数 | 1 人あたり、有効なサンドボックスは **2 つまで**。不要なものは Sandboxes ページの右端のメニューから削除する |
| 作れる回数 | 30 日間で 10 個まで |
| 基本サンドボックスの制限 | ゲストや Slack Connect が使えないなど一部の機能が制限されるが、チュートリアルの Chapter 1〜6 には影響しない |

> 有料プランのワークスペースのメンバーであるか、支払い方法を登録すると（課金はされません）、制限の少ないサンドボックスになり、有効期間も 6 か月になります。

### うまくいかない時

| 症状 | 対処 |
|---|---|
| 有効化メールが届かない | 数分待ってから、迷惑メールフォルダを確認します。会社のメールで届かない場合は、社内のメールフィルタで止まっている可能性があるので、別のメールアドレスで登録し直します |
| **Provision Sandbox** が押せない・エラーになる | 有効なサンドボックスがすでに 2 つないか、Sandboxes ページで確認します。不要なものを削除してから作り直します |
| ログインのコードが届かない | 登録したメールアドレスを入力しているか確認し、迷惑メールフォルダを見ます |
| ログインしたらワークスペースが見つからない | Sandboxes ページでサンドボックスの名前を押し、そこからログインし直します |

---

## 4. サンドボックスに練習用チャンネルを作る

サンドボックスのワークスペースで、練習用のチャンネル `#bot-practice` を作っておきます。チュートリアルでは、このチャンネルにボットを招待して動かします。

### サンドボックス（sbx）で動かす場合

自分の PC で直接動かす場合は、この節は不要です。Docker のサンドボックス（`sbx`）の中で動かす場合は、外部への通信がすべて許可制になっています。次のホストを許可しないと、ボットは動きません。ホスト側のターミナルで実行します。

```bash
sbx policy allow network "slack.com,*.slack.com,wss-*.slack.com,hooks.slack.com"
```

| ホスト | 用途 |
|---|---|
| `slack.com` / `*.slack.com` | Slack の Web API |
| `wss-*.slack.com` | Socket Mode の WebSocket 接続 |
| `hooks.slack.com` | `respond()` の返信先（`response_url`）。Chapter 3 以降で使う |

許可が足りないときの症状です。

| 症状 | 原因 |
|---|---|
| 起動時に `token is invalid` と出る | `slack.com` が許可されていません（トークンが間違っているわけではありません） |
| `Bolt app is running!` は出るが、403 で再接続を繰り返す | `wss-*.slack.com` が許可されていません |
| Chapter 3 以降で、ログは出るのに返事が表示されない | `hooks.slack.com` が許可されていません（`respond()` は失敗しても何も表示しません） |

---

## 準備完了のチェックリスト

- [ ] `uv --version` と `git --version` が表示される
- [ ] `slack-app-tutorial` を取得し、`uv sync` が成功した
- [ ] 動作確認のコマンドで `OK` と表示された
- [ ] `.env` を作った（中身はまだひな形のままでよい）
- [ ] サンドボックスのワークスペースにログインできる（アーカイブされていない）
- [ ] サンドボックスに `#bot-practice` チャンネルがある

すべて済んだら、`slack-app-tutorial.md` の Chapter 1「3. マニフェストからアプリを作る」へ進んでください。先に全体像を掴みたい場合は、`slack-app-overview.md` から読むのもおすすめです。

---

## 関連リソース

- **Developer Program**: https://api.slack.com/developer-program
- **Developer Program サンドボックス**: https://docs.slack.dev/tools/developer-sandboxes
- **uv のインストール**: https://docs.astral.sh/uv/getting-started/installation/
- **uv の TLS 証明書の設定**: https://docs.astral.sh/uv/concepts/authentication/certificates/
- **Git**: https://git-scm.com/

### 関連教材

- `slack-app-tutorial.md` — チュートリアル本編
- `slack-app-overview.md` — Slack App の全体像
