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
- **`/saygoal:retro`** — `/goal` のループが行き詰まったら、transcript を探索の記録として読み直して原因を診断し、契約そのものを書き直します（修正版 condition + 元に戻すための rollback 行つき）。

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

それと、お願いがあいまいで契約の穴（達成ラインや検証先）が埋まらないときは、`/dec` がいきなり推測で埋めずに、**一度に一問ずつ**おすすめの答え付きで聞いてくれます。逆に十分はっきりしている依頼には何も聞かず、そのまま契約を書く——必要なときだけ確認する、という塩梅です（この挙動は Codex CLI で実機確認済み）。Claude Code チームの Thariq さんが語る Fable 5 の使い方——「最終的な spec を書く前に、実装について Claude に自分をインタビューさせる」（[元動画](https://x.com/trq212/status/2073100352921215386)）——とちょうど同じ流れです。

**制約じゃなくて文脈を渡す**：同じ動画で一番効くコツがこれ。「シンプルにして、作り込みすぎないで」と言う代わりに、「この機能は実験で、1 か月後に消すかもしれない。捨てるのが惜しくなるものは作らないで」と言う。制約は「やってはいけないこと」しか列挙できませんが、文脈があれば、制約が想定していなかった場面でも AI が自分で正しく判断できます。なので `/dec` は、こういう好みベースの制約をそのまま契約に写さず、裏にある理由（実験？寿命？締め切り？）を聞き出して、契約のオプション項目「Context」に書き込みます。

**仕様が複数項目あるときは、項目ごとの差分レポート**：仕様にいくつも項目が並んでいる場合、契約の検証に「各項目を implemented / deviated で示し、違いを説明したレポートを貼ること」が追加されます。ループは収束したのに、頼んだものと違うものができていた——という一番気づきにくい失敗を塞ぐ仕掛けです。レポートは既定では実装役の自己申告ですが、Claude 版では質問がひとつ増えて、**workflow による独立検証**（項目ごとに独立の検証エージェントを 1 つ、実装過程を見ずに仕様と成果だけを突き合わせる）に格上げできます。信頼度は上がるぶんトークンを使うので、オプション扱い・既定は自己申告です。

**探索型のタスクには「収束ガードレール」**：性能チューニングや flaky テストの調査、ベンチマーク数値の追い込みみたいに「試す→検証→また試す」を繰り返してやっと収束するタスクで一番よくある死に方が、同じ変更を延々と提案し続けてターン上限に達するパターンです（同じ状態を渡されると、LLM は自分の priors に戻ってしまう——[Bilevel Autoresearch](https://arxiv.org/abs/2603.23420) が Karpathy 自身のベンチマークで記録したのがまさにこれ）。そこで `/dec` は、こういうタスクの condition に 2 つのガードレールを足します：until 側に **trace 条項**（5 ターンごとに「試したこと→結果→除外したこと」を 1 行で貼る）、without 側に **anti-fixation 条項**（検証に 2 回落ちたアプローチは繰り返さない）。探索型じゃないタスクにはどちらも付けません——ただのノイズになるので。

**ループが行き詰まったら `/saygoal:retro`（外側のループ）**：`/goal` がターン上限まで同じ修正の言い換えを繰り返して終わってしまうことがあります。そこで同じ condition をもう一度貼るのは、一番効かない手です——先ほどの論文の実験でも、パラメータ調整には効果がなく、探索の仕組みそのものを書き換えることが 5 倍の改善のすべてでした。`/saygoal:retro` は transcript を読んで行き詰まりの原因（検証が壊れている／しきい値が高すぎる／制約が正解の方向を塞いでいる／同じ手への固着／タスクの誤解）を診断し、契約を構造から書き直します。修正版 condition と、元の condition をそのまま残した rollback 行がセットなので、書き直しが外れても貼り直し 1 回で戻せます。診断結果は `.claude/saygoal.history.jsonl` に 1 行ずつ残り、次の `/dec` が最初に読みます。

ちなみに、この契約はそのまま**委任プロンプト**にもなります。[openai/codex-plugin-cc](https://github.com/openai/codex-plugin-cc) の `/codex:rescue`、[codex-orchestrator](https://github.com/yelban/codex-orchestrator) の `codex-agent start`、あるいは素の `codex exec`（プラグイン不要で一番汎用的なチャネル。バックグラウンド task として投げれば、task id・`--json` イベントストリーム・完了通知・TaskStop がそのまま実行ステータスの追跡になります）に契約の全文を渡せば、検証条件と完了判定つきのタスクとして別モデルに外注できます。`/goal` に貼れば自分でループ、委任ツールに渡せば外注——合格ラインはどちらでも同じです。Claude 版の `/dec` はここまで自動でやってくれます：契約を出したあとにツールの有無を検出し、見つかれば「自分で `/goal` するか、委任するか」を選択肢で確認。選んだ答えはプロジェクトの `.claude/saygoal.local.json` に覚えて次回は先頭候補にしますが、確認自体は毎回入ります（外注のたびにクォータを使うので、拒否権はあなたの手元に）。

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

GitHub から直接インストール（Claude Code の marketplace コマンドと対称）：

```
codex plugin marketplace add aeopress/saygoal.TW
codex plugin add saygoal@saygoal
```

または clone したリポジトリの root で、1 行目を `codex plugin marketplace add .` に置き換えても構いません。

`$dec <やりたいこと>`（または `/skills` から選択）で使って、出てきた `/goal "..."` を Codex の `/goal` に貼ってください。

固定モデルで実行を委任したい場合は、契約を明示的に確認してから `$execute-goal` を呼び出します。初回は同梱の `saygoal_writer` custom-agent テンプレートが入っているかを確認し、プロジェクト単位（`.codex/agents/`）または個人単位（`~/.codex/agents/`）のセットアップを案内します。セットアップ後に新しい thread を開いてもう一度実行すると、親 thread の `/goal` を有効にし、`gpt-5.6-sol`／`high` の writer を 1 つだけ起動し、最後に親が検証を独立して再実行します。

`$execute-goal` は未固定のモデルへ黙って切り替えません。対象モデルや custom agent を選べない環境では、ファイルを変更する前に停止します。これは Codex 専用で、Claude Code の `/saygoal:dec` は変わりません。

- **更新**：`codex plugin marketplace upgrade saygoal` のあと `codex plugin add saygoal@saygoal` を再実行。
- **削除**：`codex plugin remove saygoal@saygoal` のあと `codex plugin marketplace remove saygoal`。

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

## Bilevel アップグレード —— arXiv 2603.23420 がここを変えました

[Bilevel Autoresearch: Meta-Autoresearching Itself](https://arxiv.org/abs/2603.23420) は、Karpathy のループの上にもう 1 つループを重ねた論文です：内側のループの記録を読み、探索がどこで行き詰まっているかを見つけ、探索の仕組みそのものを書き換え、検証し、ダメなら元に戻す。論文自身が言うように（§5.3）、Python コードは「仕組み」の入れ物のひとつにすぎず、skill・prompt・workflow も同等の入れ物です。この見立てはこのパイプラインにそのまま重なります：**`/goal` が内側のループ、契約がその探索の仕組み、`/dec` はもともと人間がゲートする仕組みの設計係**。v4.6.0–v4.8.0 の 3 リリースで、対応表の空欄を埋めました：

| 論文の仕組み | saygoal に元からあったもの | 今回追加（v4.6.0–v4.8.0） |
|---|---|---|
| 内側のループ：提案 → 評価 → 採否 | `/goal`（Claude Code / Codex 標準搭載） | — |
| 実行前に設計する「仕組みの入れ物」 | 契約（`/dec` がコンパイル） | — |
| ごまかせない評価役 | 「CMD を実行して**出力を貼る**」という書き方；検証コマンドの事前確認 | — |
| 構造化された探索の記録 | — | **trace 条項**（v4.6.0）：探索型タスクで 5 ターンごとに 1 行のログ |
| Tabu Search——論文が生成した最有力の仕組み | — | **anti-fixation 条項**（v4.6.0）：検証に 2 回落ちた手は繰り返さない |
| 外側のループ：記録を読む → 診断 → 仕組みを書き換える | — | **`/saygoal:retro`**（v4.7.0）：5 種類の行き詰まり診断 → 契約の構造的書き直し |
| 書き換えのたびに validate-and-revert | — | **`rollback:` 行**（v4.7.0）：書き直しには必ず元の condition を添付 |
| 実行をまたぐ永続メモリ | — | **`.claude/saygoal.history.jsonl`**（v4.7.0）：retro が書き、次の `/dec` が最初に読む |
| パラメータ調整だけでは効果なし（論文の負の結果） | — | retro のルール（v4.7.0）：構造を変えない書き直し（ターン上限を増やすだけ等）は禁止 |
| 制約の凍結が正解を塞いだ（Group B の教訓） | 制約の自動追加テーブル | 行き詰まり診断では自動追加の制約を**第一容疑者**に（v4.7.0） |
| ループのコスト（論文ではなく解説記事から） | ターン上限 | **検証コストを織り込んだ上限**（v4.8.0）：検証が重いなら上限を下げる、または毎ターンは軽い検証・最後にフルスイート |

> **正直な注記**：論文の「5 倍」という数字は各グループ n = 3、標準偏差は平均の 67%、ベンチマークも 1 つだけで、再現に失敗したという報告もあります。このリポジトリ自身の [`EXPERIMENT.md`](./EXPERIMENT.md) の基準（N = 3 の結論は N ≥ 10 まで保留）に照らして、数字そのものは未検証扱いです。採用したのは**アーキテクチャのパターン**——trace、tabu、外側ループでの書き直し、validate-and-revert——で、どれも安価でフェイルセーフ：探索型でないタスクには何も足されず、書き直しには必ず rollback が付きます。

## ちなみに：ルールファイルは主役じゃありません

saygoal には 3 行の `CLAUDE.md`（Karpathy の観察がベース）もおまけで入っているんですが、実験してみたら**ルールファイル自体はモデルの挙動をほとんど動かさない**、という結果でした。効くのは `/dec` + `/goal` のほう。

Opus 4.8 で A/B を回したら、バグ発見率は 33% → 90% に跳ね上がったのに、`CLAUDE.md` の中身（v1 / v2 / なし）では差が出なかったんです。ちなみに v1 のルールの大半は、もともと Claude Code のシステムプロンプトにほぼそのまま入っていて、v2 が残したのは「変更した行はすべて依頼に紐づく」という新しい一行だけ。要するにモデルがもう規律を内面化していて、残っている伸びしろは**使う側の工夫**——それが `/dec` というわけです。

データの全部は [`EXPERIMENT.md`](./EXPERIMENT.md)（英語）に置いてあります。

## このリポジトリについて

[`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) の繁体字（台湾）ローカライズ fork を、Claude Code Opus 4.7 → 4.8 時代向けに手を入れたものです。プラグイン名・マーケットプレイス名は `saygoal`。

## ライセンス

[MIT](./LICENSE) — Copyright © 2026 yelban
