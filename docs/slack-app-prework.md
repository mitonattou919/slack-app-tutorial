---
title: "Slack App ハンズオン 事前準備"
tags:
  - slack-app
  - tutorial
  - learning-material
type: prework
created: 2026-10-17
description: "Slack App ハンズオンの当日までに、参加者が済ませておく準備（ツールのインストール、Developer Program のサンドボックス作成、リポジトリの取得）"
related:
  - "[[Slack]]"
  - "[[uv]]"
  - "[[Git]]"
---

# Slack App ハンズオン 事前準備

> ハンズオンの当日までに済ませておいてほしい準備です。当日は `slack-app-tutorial.md` の Chapter 1「3. マニフェストからアプリを作る」から始めます。
> 準備に詰まったら、当日を待たずに主催者へ連絡してください。
>
> 所要時間の目安: 30 分程度（サンドボックスの有効化メールを待つ時間を除く）

---

## 準備することの一覧

| # | やること | 確認のしかた |
|---|---|---|
| 1 | uv と Git をインストールする | `uv --version` と `git --version` でバージョンが表示される |
| 2 | Slack Developer Program に参加し、サンドボックスを作る | サンドボックスのワークスペースにログインできる |
| 3 | ハンズオン用リポジトリを取得し、依存関係を入れる | 動作確認のコマンドで `OK` と表示される |
| 4 | サンドボックスに練習用チャンネルを作る | `#bot-practice` が見える |

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

---

## 2. Slack Developer Program に参加し、サンドボックスを作る

ハンズオンでは、**参加者それぞれが自分専用の練習用ワークスペース**（Developer Program のサンドボックス）を使います。会社の Slack ワークスペースは使いません。1 人 1 ワークスペースなので、他の参加者のボットと反応がぶつかることもありません。

### 手順

1. https://api.slack.com/developer-program を開き、「Join the Program」を押す。登録フォームに記入して **Submit** する
2. 届いたメールの **Activate Developer Account** を押して有効化する（ダッシュボードが開く）
3. ダッシュボードの **Sandboxes** を開き、**Provision Sandbox** を押す
4. サンドボックスの内容を選ぶ画面では、**空のサンドボックス**（ワークスペース 1 つとデモユーザー 1 人）を選ぶ。テンプレート（架空のユーザーやチャンネル入り）でも動きますが、練習には不要です
5. もう一度 **Provision Sandbox** を押し、**Manage Sandboxes** を押す。作ったサンドボックスが Sandboxes ページに表示される
6. サンドボックスの名前を押し、メールアドレスでログインする。確認が終わると、サンドボックスと同じ名前のワークスペースが表示される

> 画面の名称や配置は 2026-10 時点のものです。変わっている場合は、同じ意味のボタンを探してください。

### ⚠ 作る時期に注意

誰でも作れる**基本サンドボックス**は、**1 か月で期限切れ（アーカイブ）**になります。アーカイブされると、作った本人もログインできなくなります。早く作りすぎると当日までに使えなくなるため、**ハンズオンの 1〜2 週間前**を目安に作ってください（アーカイブ前にはメールで通知が届きます）。

| 項目 | 内容 |
|---|---|
| 同時に持てる数 | 1 人あたり、有効なサンドボックスは **2 つまで**。以前作ったものが 2 つ残っていると新しく作れないので、不要なものは Sandboxes ページで削除する |
| 作れる回数 | 30 日間で 10 個まで |
| 基本サンドボックスの制限 | ゲストや Slack Connect が使えないなど一部の機能が制限されるが、このハンズオンの内容には影響しない |

> 有料プランのワークスペースのメンバーであるか、支払い方法を登録すると（課金はされません）、制限の少ないサンドボックスになり、有効期間も 6 か月になります。ハンズオンには基本サンドボックスで十分です。

### 詰まりやすいところ

- **有効化メールが届かない** → 迷惑メールフォルダや、社内のメールフィルタで止まっていないか確認します。見つからなければ主催者へ連絡してください
- **どのメールアドレスで登録するか** → 主催者の案内に従ってください。サンドボックスへのログインは、登録したメールアドレスに届く使い捨てのコードで行います
- **「Provision Sandbox」が押せない・エラーになる** → 有効なサンドボックスがすでに 2 つないか確認します

---

## 3. ハンズオン用リポジトリを取得し、依存関係を入れる

作業用のディレクトリで、次を実行します。

```bash
git clone https://github.com/mitonattou919/slack-app-tutorial.git
cd slack-app-tutorial
uv sync
```

`uv sync` は、必要なバージョンの Python と依存関係（Bolt for Python など）を `.venv/` にインストールします。初回は数十秒かかることがあります。

続いて、トークンを書くファイルのひな形をコピーしておきます（中身は当日に書き込みます）。

```bash
cp .env.example .env
```

最後に、動作確認をします。

```bash
uv run python -c "import slack_bolt, slack_helpers; print('OK', slack_bolt.version.__version__)"
```

`OK 1.30.0` のように表示されれば準備完了です（バージョンの数字は違っていても構いません）。

> **うまくいかない時**:
> - `uv sync` が通信エラーで失敗する → 社内ネットワークのプロキシが原因の可能性があります。環境変数 `HTTPS_PROXY` にプロキシのアドレスを設定してから実行し直します。分からなければ主催者へ連絡してください
> - `ModuleNotFoundError` が出る → `slack-app-tutorial` ディレクトリの中で実行しているか、`uv sync` が最後まで成功したかを確認します

---

## 4. サンドボックスに練習用チャンネルを作る

サンドボックスのワークスペースで、練習用のチャンネル `#bot-practice` を作っておきます。当日は、このチャンネルにボットを招待して動かします。

---

## 当日までのチェックリスト

- [ ] `uv --version` と `git --version` が表示される
- [ ] サンドボックスのワークスペースにログインできる（アーカイブされていない）
- [ ] `slack-app-tutorial` を clone し、`uv sync` が成功した
- [ ] 動作確認のコマンドで `OK` と表示された
- [ ] `.env` を作った（中身はまだひな形のままでよい）
- [ ] サンドボックスに `#bot-practice` チャンネルがある

当日は、`slack-app-tutorial.md` の Chapter 1「3. マニフェストからアプリを作る」から始めます。余裕があれば、`slack-app-overview.md` に目を通しておくと、当日の話が分かりやすくなります。

---

## 関連リソース

- **Developer Program**: https://api.slack.com/developer-program
- **Developer Program サンドボックス**: https://docs.slack.dev/tools/developer-sandboxes
- **uv のインストール**: https://docs.astral.sh/uv/getting-started/installation/
- **Git**: https://git-scm.com/

### 関連教材

- `slack-app-tutorial.md` — ハンズオン本編
- `slack-app-overview.md` — Slack App の全体像
