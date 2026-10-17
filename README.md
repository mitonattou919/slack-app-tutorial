# Slack App ハンズオン

uv と Bolt for Python で練習用の Slack ボット（Practice Bot）を育てるハンズオン用リポジトリです。章ごとのディレクトリに、その章を終えた時点の `main.py` と `manifest.yaml` が入っています。

## 教材

| 教材 | 内容 |
|---|---|
| [docs/slack-app-prework.md](docs/slack-app-prework.md) | **始める前の準備**（ツール、サンドボックス、リポジトリの取得。つまずいたときの対処付き） |
| [docs/slack-app-overview.md](docs/slack-app-overview.md) | Slack App の全体像（コードを書く前の地図） |
| [docs/slack-app-tutorial.md](docs/slack-app-tutorial.md) | ハンズオン本編。このリポジトリのコードを使う |
| [docs/slack-app-tutorial-answers.md](docs/slack-app-tutorial-answers.md) | 練習課題のヒントと解答例（動くコードは `answers/`） |
| [docs/slack-app-best-practices.md](docs/slack-app-best-practices.md) | 本番運用の設計原則と失敗パターン |

## ディレクトリ構成

```text
.
├── 01_preparing/       Chapter 1: メンションに返事をする
├── 02_messages/        Chapter 2: メッセージイベントとスレッド返信
├── 03_slash_commands/  Chapter 3: スラッシュコマンド
├── 04_block_kit/       Chapter 4: Block Kit とボタン
├── 05_modals/          Chapter 5: モーダル
├── 06_app_home/        Chapter 6: App Home
├── 07_streaming/       Chapter 7: ストリーミング返信（全章の完成形）
├── answers/            練習課題の解答例（章ごと。例: answers/02_messages/task1.py）
├── slack_helpers/      各章で共通して使うヘルパー（スレッド返信など）
├── docs/               教材
├── .env.example        トークンのひな形
└── pyproject.toml
```

各章のディレクトリは**それまでの章を全部含んだ状態**です。途中の章から始めても、そのディレクトリの `main.py` と `manifest.yaml` を使えば動きます。

## セットアップ

初めての方は、[準備の手順](docs/slack-app-prework.md)に沿って進めてください。ツールのインストールから練習用ワークスペースの作成まで、つまずいたときの対処も含めて載っています。

```bash
git clone https://github.com/mitonattou919/slack-app-tutorial.git
cd slack-app-tutorial
uv sync
cp .env.example .env   # 中身を自分のトークンに置き換える
```

Slack App の作成とトークンの取得は、tutorial の Chapter 1 を参照してください。

## 動かす

リポジトリのルートで、動かしたい章の `main.py` を指定します。

```bash
uv run --env-file .env 01_preparing/main.py
```

ターミナルには、届いたイベントや操作のログが表示されます。Slack から届いた中身まで見たいときは、`.env` に `LOG_LEVEL=DEBUG` を追加して起動し直します。

```text
2026-10-15 10:00:00,123 INFO __main__ app_mention from U0123ABCD in C0456EFGH: <@U0789IJKL> やあ
```

章を進めるときは、次の 2 つを行います。

1. App 設定画面の **App Manifest** に、その章の `manifest.yaml` を貼り替えて保存する（スコープが増えた章では再インストールも必要）
2. プログラムを `Ctrl+C` で止め、その章の `main.py` で起動し直す
