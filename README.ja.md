# saygoal

「やりたいことだけ伝えれば、あとは勝手に終わらせてくれる」——そんな AI ワークフローのための、小さなツールです。

Claude Code と Codex で使える `/dec` + `/goal` の組み合わせ。Andrej Karpathy の「指示するんじゃなくて、成功条件を渡して見ていろ」という考え方がベースになっています。

![/dec — 命令形から宣言形へ](./saygoal.TW.png)

[English](./README.md) | [繁體中文（台灣）](./README.zh-TW.md) | [简体中文](./README.zh-CN.md) | 日本語

> **本家リポジトリ**：[`aeopress/saygoal.TW`](https://github.com/aeopress/saygoal.TW)

## これは何をするもの？

ざっくり言うと、**あいまいなお願いを「検証できる契約」に書き換えて、達成するまで AI に回してもらう**ツールです。

- **`/dec <やりたいこと>`** — お願いを「成功条件 + 検証コマンド + 触っていい範囲」に整理して、そのまま貼れる **`/goal` の条件文**を出してくれます。
- それを Claude Code（や Codex）の **`/goal`** に貼ると、小さくて速いモデルが毎ターン結果をチェックして、条件を満たすまで AI を走らせ続けます。

### 30 秒でわかる例

```
/dec ログイン画面の初回読み込みのちらつきを直して

→ /goal "run npx playwright test login-flicker.spec.ts until it paste-shows 0 failures
         without changing the auth flow or any file outside the login component
         or stop after 20 turns"
```

`/dec` が契約を書いて、`/goal` が緑になるまで走らせる。やることはそれだけ。Claude Code（`/dec` コマンド）でも OpenAI Codex（`$dec` スキル）でも動きます。

## `/dec` と `/goal` の関係

Karpathy の「成功条件を渡して、あとは見ていろ」という言葉を、ちょうど 2 つのコマンドに分けたもの、と思ってもらえれば。

- **`/dec`** は**動き出す前**の担当。あいまいなお願いを契約に書き換えます。あなたが確認するまでは、まだ実装はしません。
- **`/goal`**（Claude Code v2.1.139+ に標準搭載）は**動いている間**の担当。毎ターンごとに「条件を満たしたか？」を小さいモデル（Haiku）が判定して、満たすまで自動で次のターンへ進みます。

### なんで宣言形のほうがいいの？

命令形（「〜して」）だと、AI は「やった気」になって止まりがちなんですよね。宣言形（「〜という状態になるまで」）にすると、達成したかどうかを自分で確かめながら進めます。

| 命令形（弱い） | 宣言形（強い） |
|---|---|
| 「入力バリデーションを追加して」 | 「この不正な入力に対する“失敗するテスト”を書いて、それを通して」 |
| 「このバグを直して」 | 「バグを再現するテストを書いて、それを通して。他のテストも通ったまま」 |
| 「もっと速くして」 | 「この負荷で p95 を X ms 以下に。`scripts/bench.sh` で計測」 |

ちなみに、UI の微調整や文章書き、「正解が人の好み次第」みたいなことには `/dec` は向きません。そういうときは普通にお願いしたほうが速いです（`/dec` 自身も「これは不要、そのままやって」と返してきます）。

### 地味だけど大事：Claude の評価役は「会話の中身しか見ない」

ちょっとだけ技術的な話を。Claude の `/goal` で毎ターン判定する小さいモデルは、**会話のログ（transcript）しか読みません**。自分でコマンドを実行したり、ファイルを直接覗いたりはしないんです。

だから `/dec` が出す検証条件は、「`npx playwright test` を**実行して、その出力を貼る**」という形になっています。「テストが通る」とだけ書くと、AI が「通ったはず」と言うだけで評価役には判断できない——ここ、地味ですが効いてきます。

### Codex でも同じように使えます

OpenAI の Codex CLI も自前の `/goal` を持っています（実は Claude Code より 11 日早かった）。Codex 公式の「良い goal の書き方」では、達成すべきこと・変えてはいけないこと・進捗の検証方法・止めどき、の 4 つを挙げています。`/dec` が書く契約は、まさにこれ。Codex 側では 7 項目のテンプレート形式で出力します。

細かい対応表や実験データは [英語版 README](./README.md) と [`EXPERIMENT.md`](./EXPERIMENT.md) に置いてあります。

## インストール

### Claude Code

```
/plugin marketplace add aeopress/saygoal.TW
/plugin install saygoal@saygoal
```

あとは `/saygoal:dec <やりたいこと>` で使えます。`/goal` は標準搭載なのでインストール不要です。

> **旧バージョンからの移行：** 本プロジェクトは以前 `andrej-karpathy-skills.TW`（marketplace 名 `karpathy-skills`、旧リポジトリはアーカイブ済み）でした。改名前にインストールした場合は、更新を受け取れるよう先に古い marketplace を削除してください。`marketplace remove` で古いプラグインも一緒にアンインストールされます：
>
> ```
> /plugin marketplace remove karpathy-skills
> /plugin marketplace add aeopress/saygoal.TW
> /plugin install saygoal@saygoal
> /reload-plugins
> ```

### Codex

clone したリポジトリの中で：

```
codex plugin marketplace add .
codex plugin add saygoal@saygoal
```

`$dec <やりたいこと>`（または `/skills` から選択）で使って、出てきた `/goal "..."` を Codex の `/goal` に貼ってください。

<details>
<summary><b>応用</b> — 短い <code>/dec</code>、おまけの <code>CLAUDE.md</code> ルール、自動更新、Cursor</summary>

**短い `/dec`（namespace なし）。** プラグイン経由だと `/saygoal:dec` になります。短い `/dec` がよければ、コマンドファイルをグローバルに置きます：

```bash
mkdir -p ~/.claude/commands
curl -o ~/.claude/commands/dec.md \
  https://raw.githubusercontent.com/aeopress/saygoal.TW/main/plugin/commands/dec.md
```

**3 行の `CLAUDE.md` ルール（おまけ）。** 正直なところ、[A/B 実験](./EXPERIMENT.md) では Opus 4.7/4.8 に対して測定できるほどの効果は出ませんでした。欲しい人だけどうぞ：

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/aeopress/saygoal.TW/main/CLAUDE.md
```

**自動更新する短い `/dec`。** 一度 clone して symlink しておけば、`git pull` で最新に保てます：

```bash
mkdir -p ~/.claude/external ~/.claude/commands
git clone https://github.com/aeopress/saygoal.TW ~/.claude/external/saygoal.TW
ln -sf ~/.claude/external/saygoal.TW/plugin/commands/dec.md ~/.claude/commands/dec.md
# あとで更新： cd ~/.claude/external/saygoal.TW && git pull
```

**Cursor。** [`.cursor/rules/karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc)（`alwaysApply: true`）が入っています。詳しくは [`CURSOR.md`](./CURSOR.md) を。

</details>

## おまけコマンド：`/saygoal:repo-audit`

プラグインには `/saygoal:repo-audit` も同梱されています — principal レベルの読み取り専用リポジトリ監査（[OmerFarukOruc 氏の `/repo-audit` gist](https://gist.github.com/OmerFarukOruc/753f95b1ac278b683be83ed26b3bcc1f) を saygoal ワークフロー向けに調整）。リポジトリマップを作成し、監査ディメンションごとにサブエージェントを並列展開、git 履歴から churn × 複雑度のホットスポットを発掘し、Critical/High の指摘は敵対的検証を通過したものだけを報告。成果物は単一の `AUDIT.md` で、タスク計画の**各タスク末尾にはそのまま貼れる `/goal` condition** が付きます。つまり監査結果がそのまま宣言型ループ（監査 → タスク → `/goal`）に流れ込みます。

`/dec` とは重複せず補完関係にあります — 同じパイプラインで、トリガーと粒度が違うだけです：

| | `/repo-audit` | `/dec` | `/goal` |
|---|---|---|---|
| 役割 | バッチ**発見器** | 単一タスクの**契約器** | **実行器** |
| トリガー | コードベースの現状（問題がどこにあるかまだ知らない） | 頭の中にすでにあるニーズ | condition を手にしたとき |
| 成果物 | `AUDIT.md` — タスクキューまるごと | 契約ひとつ + condition 一行 | 達成までループ |

監査タスクには `/dec` の evaluator ルールが組み込み済みなので、`/dec` を通さずそのまま `/goal` に貼れます。日常の単発タスクは引き続き `/dec` の担当です。

```
/saygoal:repo-audit                  # フル監査 → AUDIT.md
/saygoal:repo-audit security         # 任意のフォーカス：ディメンションやパス
/saygoal:repo-audit use a workflow   # 大規模リポジトリ向けマルチエージェント編成のオプトイン
```

通常モードで実行してください（plan mode は不要）。読み取り専用なので最後まで放置して大丈夫です — 作成されるファイルは `AUDIT.md` だけです。

## ちなみに：ルールファイルは主役じゃありません

saygoal には 3 行の `CLAUDE.md`（Karpathy の観察がベース）もおまけで入っているんですが、実験してみたら**ルールファイル自体はモデルの挙動をほとんど動かさない**、という結果でした。効くのは `/dec` + `/goal` のほう。

Opus 4.8 で A/B を回したら、バグ発見率は 33% → 90% に跳ね上がったのに、`CLAUDE.md` の中身（v1 / v2 / なし）では差が出なかったんです。ちなみに v1 のルールの大半は、もともと Claude Code のシステムプロンプトにほぼそのまま入っていて、v2 が残したのは「変更した行はすべて依頼に紐づく」という新しい一行だけ。要するにモデルがもう規律を内面化していて、残っている伸びしろは**使う側の工夫**——それが `/dec` というわけです。

データの全部は [`EXPERIMENT.md`](./EXPERIMENT.md)（英語）に置いてあります。

## このリポジトリについて

[`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) の繁体字（台湾）ローカライズ fork を、Claude Code Opus 4.7 → 4.8 時代向けに手を入れたものです。プラグイン名・マーケットプレイス名は `saygoal`。

## ライセンス

[MIT](./LICENSE) — Copyright © 2026 yelban
