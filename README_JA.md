# drawio-skill — テキストからプロフェッショナルな図へ

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/Agents365-ai/drawio-skill?style=flat&logo=github)](https://github.com/Agents365-ai/drawio-skill/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Agents365-ai/drawio-skill?style=flat&logo=github)](https://github.com/Agents365-ai/drawio-skill/network/members)
[![Latest Release](https://img.shields.io/github/v/release/Agents365-ai/drawio-skill?logo=github)](https://github.com/Agents365-ai/drawio-skill/releases/latest)
[![Last Commit](https://img.shields.io/github/last-commit/Agents365-ai/drawio-skill?logo=github)](https://github.com/Agents365-ai/drawio-skill/commits/main)

[![SkillsMP](https://img.shields.io/badge/SkillsMP-listed-1f6feb)](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-compatible-2ea44f)](https://agentskills.io)

[English](README.md) · [中文](README_CN.md) · **日本語** · [📖 オンラインドキュメント](https://agents365-ai.github.io/drawio-skill/)

自然言語と実際のシステムソースを、保守可能な `.drawio` アーキテクチャモデルに変換するスキルです。生成やエクスポートにとどまらず、手動で調整したレイアウトを破棄せずに差分同期し、1つのモデルから複数のビューを投影し、アーキテクチャ契約を強制し、依存関係を問い合わせ、障害の伝播をシミュレートし、依存関係のないインタラクティブなウォークスルーを公開します。**Claude Code、Cursor、Copilot、OpenClaw、Codex、Autohand Code、Hermes**、および [Agent Skills](https://agentskills.io) 形式に対応したあらゆるエージェントで動作します。

<p align="center">
  <img src="assets/hero-demo.gif" width="900" alt="ヒーローデモ：Terraform のソースが公式アイコン付きのアーキテクチャ図になり、v2 の変更が更新された図として描画される">
</p>

## ✨ ハイライト

**プロンプトから**

- **説明するだけで編集可能な `.drawio` を取得** — スキルがレイアウトを計画し、XML を書き、エクスポートした後、自身の PNG をセルフチェックして重なり・切れたラベル・積み重なったエッジを自動修正します（最大 2 ラウンド）。さらに最大 5 ラウンドのフィードバックに対応します
- **Mermaid → ネイティブ .drawio**（draw.io ≥ 30）— 28 種類の標準タイプ（**mindmap、gantt、timeline、journey、pie、sankey、kanban**…）を Mermaid テキストで記述すると、CLI がレイアウト済みで編集可能な `.drawio` に変換します。構造を入れるだけで、レイアウトは不要です
- **ホワイトボード写真 / スクリーンショット → 編集可能な図** — 古い PNG や実物のホワイトボードを撮影し、ビジョンでグラフを抽出させると、`raster2drawio.py` が元のレイアウトを尊重した本物の編集可能な `.drawio` として再構築します
- **11 種類の図タイププリセット** — ERD、UML クラス図、シーケンス図、C4、アーキテクチャ、ML/ディープラーニング、フローチャート、SysML、BPMN、ネットワークトポロジー、部門横断スイムレーン

**実際のソースから**

- **コードベースを可視化** — Python / JS-TS / Go / Rust のインポートグラフと Python のクラス階層を、Graphviz による配置、推移的縮約、ネストしたモジュールコンテナ付きで生成します
- **IaC とライブインフラ** — Terraform、Kubernetes、docker-compose の設定を、AWS / Azure / GCP / K8s の公式アイコン付きの図にします。`terraform show -json`、`docker inspect`、`kubectl get -o json` から*実際にデプロイされているもの*のスナップショットも取得できます
- **スキーマとパイプライン** — SQL DDL → ER 図、OpenAPI/Swagger → HTTP メソッドで色分けされた API 図、AsyncAPI → イベント駆動アーキテクチャ図、Protocol Buffers → メッセージ/サービス図、GraphQL SDL → エンティティタイプ図、GitHub Actions / GitLab CI → パイプライン DAG

- **決定論的エンジン** — ライフラインとアクティベーションバーを計算したシーケンス図、クリックでドリルダウンできる複数ページの C4 モデル

**時間が経っても正確に保つ**

- **アーキテクチャのデジタルツイン / Diagram IR** — 意味・来歴・ジオメトリを分離し、1つのモデルからエグゼクティブ、システム、デプロイ、データフロー、セキュリティの各ビューを投影します
- **手動レイアウトを失わない差分同期** — `diagramctl sync` は、調整済みの座標・スタイル・注釈を保持したまま、変更されたノード/関係を更新します。削除はデフォルトでレビュー可能なまま残ります
- **CI での Diagram-as-Test** — YAML/JSON のアーキテクチャルール（インターネットからデータベースへのアクセス、循環、孤立ノード、信頼境界、コントラスト…）に加え、それをすべての PR で強制する公式 GitHub Action と、視覚的な差分を描画する PR アクションを提供します
- **クエリ、レビュー、What-if** — コンポーネント/オーナー/パスを問い合わせ、関節点や高結合を発見し、障害の伝播をシミュレートし、アクセシブルな Story ウォークスルーを公開します
- **ドリフトと履歴** — 2 つの図または 2 つのライブスナップショット間の色分けされた差分、コードベースのアーキテクチャがどのように成長したかを示すタイムラプスプレーヤー

**共有とスタイル変更**

- **1 コマンドで再利用** — インタラクティブな HTML ビューア（パン/ズーム/検索）、PowerPoint デッキ、アニメーション付きデータフロー SVG、Mermaid または Markdown へのエクスポート、クリックで進むランブック、エグゼクティブサマリーへの圧縮
- **スタイル変更と情報の付加** — スタイルプリセット（独自のものまたは組み込みの `dark`/`corporate`/…）、レイアウトはそのままの二言語ラベル版、データ駆動のヒートマップ、白地からメトロ風への路線図モード
- **10,000 以上の公式シェイプ + 321 の AI/LLM ロゴ** — AWS / Cisco / K8s / UML のアイコンスタイルを推測せず正確に解決し、さらに draw.io 自体にないブランドロゴも利用できます
- **1 つの CLI と、オプションの MCP サーバー** — `diagramctl doctor/build/sync/views/query/test/review/whatif/story/publish/transform`。コアワークフローは標準ライブラリのみでオフライン動作します。MCP サーバーはこれらを Claude Desktop、Cursor、VS Code、Codex、およびあらゆる MCP ホストに公開します。Agent Skills 互換のどのエージェントにも移植可能で、デーモンは不要です

## 🗺️ 機能マップ

<div align="center">
  <img src="assets/mindmap.png" width="900" alt="drawio-skill の機能マップ — すべての機能を網羅した 1 枚のマインドマップ。このマップ自体もこのスキルで描画">
</div>

図のタイプ、インポート元、レイアウトエンジン、スタイル設定、エクスポート形式、再利用など、このスキルができることすべてを 1 枚のマップで俯瞰できます。ふさわしいことに、このマップ自体も drawio-skill で描かれています。

## 🚀 インストール

### 1. draw.io デスクトップ CLI をインストールする

| プラットフォーム | コマンド |
| ---------- | --------- |
| **macOS** | `brew install --cask drawio` |
| **Windows** | [インストーラーをダウンロード](https://github.com/jgraph/drawio-desktop/releases) |
| **Linux** | [releases](https://github.com/jgraph/drawio-desktop/releases) から `.deb`/`.rpm`。ヘッドレス環境では `sudo apt install xvfb` |

`drawio --version` で確認してください。**バージョン ≥ 30 を推奨**します — Mermaid → `.drawio` 変換と ELK の `--layout` パスが利用可能になります（どちらも ≤ 29 では利用できません）。**WSL2** では、CLI は `/mnt/c` 経由で呼び出す Windows デスクトップ版の exe です — スキルはこれを自動検出します（[トラブルシューティング](skills/drawio-skill/references/troubleshooting.md)を参照）。詳しい手順は [docs/INSTALL_CLI.md](docs/INSTALL_CLI.md) にあります。

### 2. スキルをインストールする

```bash
# Any agent (Claude Code, Cursor, Copilot, ...)
npx skills add Agents365-ai/drawio-skill -g
```

手動インストール：永続的なパスに一度クローンし、スキルのサブディレクトリをリンクします（Claude Code の例）。シンボリックリンクをたどらないホストでは、`ln -s` の代わりに `cp -R` を使用してください。リンク先はまだ存在していてはいけないため、既存の `drawio-skill` エントリがある場合は先に移動してください。

```bash
mkdir -p ~/src
git clone https://github.com/Agents365-ai/drawio-skill.git ~/src/drawio-skill
mkdir -p ~/.claude/skills
ln -s ~/src/drawio-skill/skills/drawio-skill ~/.claude/skills/drawio-skill

# Copy alternative, for hosts that do not follow symlinks
# mkdir -p ~/.claude/skills
# cp -R ~/src/drawio-skill/skills/drawio-skill ~/.claude/skills/drawio-skill
```

スキル本体は `skills/drawio-skill/` サブディレクトリなので、`SKILL.md` はホストのエントリ直下、つまり `<skills root>/drawio-skill/SKILL.md` に配置されている必要があります。リポジトリのルートをスキルディレクトリにクローンしないでください。その他のホストのルート（Opencode、OpenClaw、Codex、Autohand Code のグローバルおよびプロジェクト）：[docs/INSTALL_SKILL.md](docs/INSTALL_SKILL.md)。

Autohand Code はカタログ掲載済みのスキル向けに `autohand --skill-install` もサポートしており、ワークスペース単位のインストールには `--project` を使います。このスキルがそこに掲載されるまでは、Autohand Code のスキルルート `~/.autohand/skills/`（グローバル）または `<project>/.autohand/skills/`（プロジェクト）を指定して、上記の手動手順を使用してください。

[SkillsMP](https://skillsmp.com/skills/agents365-ai-drawio-skill-skills-drawio-skill-skill-md) にも掲載されています。

**アップデート：** インストーラーでインストールした場合は `npx skills update drawio-skill -g`（skills CLI）、リンクでインストールした場合は `git -C ~/src/drawio-skill pull` で更新でき、コピーでインストールした場合は手動での更新が必要です。[docs/INSTALL_SKILL.md#updates](docs/INSTALL_SKILL.md#updates) を参照してください。リリース履歴は [CHANGELOG.md](CHANGELOG.md) にあります。

## ⚡ クイックスタート

インストール後は、欲しいものを説明するだけです。たとえば ML モデルの場合：

```text
Draw a Transformer encoder-decoder for machine translation: 6-layer encoder
with self-attention, 6-layer decoder with cross-attention, input embeddings
(batch × 512 × 768), positional encoding, and a final output projection.
Annotate tensor shapes between layers and color-code by layer type.
```

スキルがレイアウトを計画し、`.drawio` XML を生成し、選択した形式でエクスポートし、結果をセルフチェックしたうえで、繰り返し改善できるようにします。

## 🖼️ 例

<p align="center">
  <img src="assets/microservices-example.png" width="900" alt="マイクロサービスアーキテクチャ：1 つの自然言語プロンプトから生成">
</p>

> [!TIP]
> **上の図は、次の 1 つのプロンプトから生成されました：**

```text
Create a microservices e-commerce architecture with Mobile/Web/Admin clients,
API Gateway (auth + rate limiting + routing), Auth/User/Order/Product/Payment
services, Kafka message queue, Notification service, and User DB / Order DB /
Product DB / Redis Cache / Stripe API
```

メンテナンスされている [Architecture Studio ショーケース](examples/architecture-studio/)では、
コード → IR → `.drawio`、手動で調整したレイアウトを保持する
競合を考慮した同期、そしてアーキテクチャ → ポリシー/ビュー/What-if/アクセシブルな Story を扱っています。
すべての成果物は 1 つのスクリプトで再生成され、テストスイートで検証されています。

このスキルは、さまざまなトポロジーでエッジをきれいにルーティングし、線がシェイプを横切らないように設計されています：

<table>
  <tr>
    <td align="center" width="33%">
      <img src="assets/demo-star.png" alt="スター型トポロジー" width="100%"><br>
      <b>スター型</b> · 7 ノード<br>
      <sub>中央のメッセージブローカーから 6 つのマイクロサービスが放射状に広がり、この例ではエッジの交差はありません。</sub>
    </td>
    <td align="center" width="33%">
      <img src="assets/demo-layered.png" alt="レイヤー型フロー" width="100%"><br>
      <b>レイヤー型</b> · 10 ノード / 4 層<br>
      <sub>水平方向と斜め方向の相互接続を通路経由でルーティングした E コマーススタック。</sub>
    </td>
    <td align="center" width="33%">
      <img src="assets/demo-ring.png" alt="リング型サイクル" width="100%"><br>
      <b>リング型</b> · 8 ノード<br>
      <sub>閉ループと 2 本の分岐が外周に沿って流れる CI/CD パイプライン。</sub>
    </td>
  </tr>
</table>

**Mermaid** にも対応しています — 標準タイプ（flowchart、mindmap、**kanban**、gitGraph、timeline…）はネイティブで編集可能な `.drawio` に直接変換されます。以下は、数行の Mermaid から生成したカンバンボード（このプロジェクト自身のロードマップ）です：

<div align="center">
  <img src="assets/kanban.png" width="620" alt="drawio-skill が Mermaid から生成したカンバンボード — Backlog / Todo / In Progress / Done にわたるこのプロジェクトのロードマップ">
</div>

**路線図モード**は、パイプラインやジャーニーをロンドン地下鉄風の路線図にスタイル変更します — 色分けされた路線、八方向（水平/垂直/45°）のルーティング、白い乗換駅の円。以下はスキル自身のフローです（このマップは `assets/tubemap.json`、約 20 行）：

<div align="center">
  <img src="assets/tubemap.png" width="720" alt="drawio-skill のパイプラインを路線図として描画 — Author / Import / Repurpose / Analyze の各路線が Auto-layout と .drawio の乗換駅で交わる">
</div>

詳しいウォークスルーは [docs/USAGE.md](docs/USAGE.md) にあります。

## 🗺️ 実際のソースから図へ

手作業で作成する図にとどまらず、このスキルは**既存のコード、インフラ、スキーマを図に変換**します — 手動での座標指定は不要です。次のように頼むだけです：

> *「この Python プロジェクトのモジュール構造を可視化して」* · *「`mypackage` のクラス階層を描いて」*

<p align="center">
  <img src="assets/code-structure-example.png" width="900" alt="Python の logging パッケージのクラス階層を自動生成 — モジュールは枠で囲まれ、継承の矢印は解決済み">
</p>

<sub>↑ Python の <code>logging</code> パッケージをクラス階層として表示 — 1 コマンドで、モジュールは自動的に枠で囲まれ、すべての継承エッジが解決されます。</sub>

内部では、同梱の抽出器 → 自動レイアウト → 検証のパイプラインが実行されます：

```bash
# source -> graph JSON -> placed, editable .drawio
python3 scripts/tfimports.py ./infra -o graph.json          # Terraform -> official AWS icons
python3 scripts/autolayout.py graph.json -o architecture.drawio

# drift between two states, then share as one interactive file
python3 scripts/drawiodiff.py v1.drawio v2.drawio -o drift.json
python3 scripts/drawiohtml.py architecture.drawio -o architecture.html
```

ステージ別にまとめたツールボックス全体：

| ステージ | ツール |
| --- | --- |
| **インポート** | 16 の抽出器：**Python · JS/TS · Go · Rust** のインポートグラフ、**Python のクラス継承**、公式クラウドアイコン付きの **Terraform / Kubernetes / docker-compose**、`terraform show -json` / `docker inspect` / `kubectl get -o json` からの**ライブ**インフラ、**SQL DDL → ERD**、**OpenAPI → API 図**（HTTP メソッドで色分け）、**AsyncAPI → イベント駆動アーキテクチャ図**、**Protobuf → メッセージ/サービス図**、**GraphQL SDL → エンティティタイプ図**、**GitHub Actions + GitLab CI → DAG** |
| **比較と進化** | `drawiodiff.py` は 2 つの図または 2 つのライブスナップショット間のドリフトを色分けします（追加=緑、削除=赤、変更=オレンジ）。`timelapse.py` は git 履歴を HTML プレーヤーで再生し、`prdiff.py` は CI で PR の差分を描画します |
| **再利用** | `explain.py` → Markdown、`drawiohtml.py` → パン/ズーム/検索可能な HTML ビューア、`drawio2pptx.py` → デッキ、`svgflow.py` → アニメーション SVG、`drawio2mermaid.py` → diagrams-as-code、`runbook.py` → クリック可能なトリアージアプリ、`compress.py` → ドリルダウン付きエグゼクティブサマリー、`buildup.py` → 自動描画プレーヤー、`tubemap.py` → 路線図 |
| **スタイル変更と情報の付加** | `restyle.py` は色相のリマップでプリセットを適用し、`relabel.py` はレイアウトをそのままに翻訳版を作成し、`heatmap.py` はメトリクスの CSV/JSON からノードに色を付け、`edgeports.py` はシェイプ境界で積み重なったエッジを解消します |
| **レイアウトとリント** | `autolayout.py`（Graphviz による配置、直交ルーティング、`--tune` による方向選択、`--group` コンテナ、推移的縮約：asyncio で 149 → 46 エッジ）、`seqlayout.py`、`c4.py`、そして決定論的な `validate.py` リンター（`--score` / `--strict`） |

レイアウトには Graphviz（`brew install graphviz` / `apt install graphviz`）が必要ですが、これはオプションで、それ以外はすべて Graphviz なしで動作します。形式とフラグの完全なリファレンスは [references/autolayout.md](skills/drawio-skill/references/autolayout.md)、すべてのツールは [references/toolbox.md](skills/drawio-skill/references/toolbox.md) にあります。CI での再生成、検証（`--strict` ゲート）、ヘッドレス描画：[docs/CI.md](docs/CI.md)。

## 🧩 対応している図のタイプ

| カテゴリ | 例 | 主な機能 |
| --- | --- | --- |
| アーキテクチャ | マイクロサービス、クラウド（AWS/GCP/Azure）、ネットワークトポロジー、デプロイ | 階層ベースのスイムレーン、ハブ中心の配置戦略 |
| C4 モデル | システムコンテキスト、コンテナ、コンポーネント | 複数ページの `.drawio`、クリックでドリルダウンできるリンク |
| ML / ディープラーニング | Transformer、CNN、LSTM、GRU | テンソル形状の注釈、レイヤータイプ別の色分け |
| フローチャート | 業務プロセス、ワークフロー、決定木、ステートマシン | 意味を持つシェイプ（平行四辺形の入出力、ひし形の分岐） |
| UML | クラス図、シーケンス図 | 継承 / コンポジション / 集約の矢印、ライフライン + アクティベーションボックス |
| SysML / MBSE | ブロック定義図（bdd）、内部ブロック図（ibd）、要求図（req）、パラメトリック図（par） | «block» / «requirement» のコンパートメント、satisfy/derive/verify エッジ、ネイティブな `mxgraph.sysml.*` のポートとフロー |
| BPMN | 業務プロセス、プールとレーン | ネイティブな `mxgraph.bpmn.*` のイベント/タスク/ゲートウェイ、シーケンスフローとメッセージフローの区別 |
| ネットワークトポロジー | LAN/WAN、サブネット、DMZ | `mxgraph.networks.*` のデバイスシェイプ、ゾーンコンテナ、リンクラベル。Cisco/ラックはシェイプ検索で対応 |
| 部門横断スイムレーン | 誰が何をするかのプロセス、引き継ぎ | プール + 役割レーン、フローチャートの語彙、直交する引き継ぎエッジ |
| データ | ER 図、データフロー図（DFD） | テーブルコンテナ、PK/FK 表記 |
| Mermaid で記述 | マインドマップ、ガント、タイムライン、ジャーニー、円グラフ、サンキー、カンバン + 他 20 種類 | ネイティブ CLI による変換（≥ v30）— 構造のみで、レイアウトは不要 |
| その他 | 組織図、ワイヤーフレーム | — |

## 🔍 シェイプ検索

本物の AWS / Azure / GCP / Cisco / Kubernetes / UML / BPMN アイコンが必要ですか？スキルは **10,000 以上の公式 draw.io シェイプ**から正確なスタイル文字列を検索します — そのため、推測した `shape=mxgraph.*` 名のせいで空のボックスになってしまうことなく、ベンダーアイコンが正しく描画されます。

> *「S3 バケットに接続された AWS Lambda を追加して」* · *「本物の Kubernetes の Pod アイコンを使って」*

```bash
python3 scripts/shapesearch.py "aws lambda" --limit 5
# → Lambda (77x93)
#   outlineConnect=0;...;shape=mxgraph.aws3.lambda;fillColor=#F58534;...
```

<p align="center">
  <img src="assets/shape-search-example.png" width="900" alt="shapesearch.py で解決した公式 draw.io アイコンで構築したサーバーレス AWS アーキテクチャ">
</p>

<sub>↑ サーバーレス AWS アーキテクチャ — すべてのアイコンは、手で推測した <code>shape=</code> 文字列ではなく、<code>shapesearch.py</code> で解決した本物の公式 draw.io シェイプです。</sub>

AWS / Azure / GCP / Cisco / Kubernetes / UML / BPMN / ER / 電気回路 / P&ID および一般的なシェイプセットをカバーしています。手書き可能なスタイルのチートシートと検索の使い方は [references/shapes.md](skills/drawio-skill/references/shapes.md) にあります。

## 🤖 AI / LLM ブランドロゴ

draw.io には最新の AI/LLM ロゴが**一切**含まれていないため、LLM アプリの図は汎用的なボックスとして描画されてしまいます。`aiicons.py` は、[lobe-icons](https://github.com/lobehub/lobe-icons)（MIT）の **321 のロゴ**（OpenAI、Claude、Gemini、Mistral、Llama、Cohere、DeepSeek、Qwen、Ollama、LangChain、HuggingFace…）に加え、RAG スタック向けに [simple-icons](https://simpleicons.org)（CC0）の **18 のデータストアブランド**（Redis、Postgres、MongoDB、Qdrant、Milvus、Supabase…）について、ブランド名を draw.io の画像スタイルに解決します。

```bash
python3 scripts/aiicons.py "claude" --json      # CDN-referenced (default)
python3 scripts/aiicons.py "openai" --embed     # self-contained data URI
```

<p align="center">
  <img src="assets/ai-logos-example.png" width="900" alt="aiicons.py で解決した本物の AI ブランドロゴを使ったマルチプロバイダー LLM アプリの図">
</p>

<sub>↑ マルチプロバイダー LLM アプリ — すべてのブランドロゴは <code>aiicons.py</code> で解決されています。アイコンはデフォルトで unpkg CDN から参照されます（描画時にネットワークが必要）。<code>--embed</code> を使うとオフライン用にインライン化されます。ロゴは各所有者の商標であり、識別目的でのみ使用しています。</sub>

## 🎨 スタイルプリセット

ビジュアルスタイルを一度取り込めば、どこでも再利用できます。5 つのプリセットが組み込まれています — `default`、`corporate`、`handdrawn`、`colorblind-safe`（Okabe-Ito パレット）、`dark` — また、`.drawio` ファイルや画像から独自のスタイルをスキルに学習させることもできます：

```text
Draw a microservices architecture using my "corporate" style
```

```text
Learn my style from ~/diagrams/brand.drawio as "mybrand"
```

スキルは色、シェイプ、フォント、エッジスタイルを抽出し、プレビューを描画し、承認された後にのみプリセットを保存します。プリセット管理コマンドの一覧は [docs/STYLE_PRESETS.md](docs/STYLE_PRESETS.md) にあります。

## 🔄 仕組み

<p align="center">
  <img src="assets/workflow.png" width="700" alt="内部ワークフロー">
</p>

裏側では次の流れで動いています：**依存関係のチェック → レイアウトの計画 → `.drawio` XML の生成 → ドラフト PNG のエクスポート → セルフチェック + 自動修正**（最大 2 ラウンド）→ **ユーザーへの提示 → 承認されるまで 5 ラウンドのフィードバックループ** → **最終エクスポート**。

## 🆚 比較

### 他の draw.io スキル・ツールとの比較

| 機能 | drawio-skill | [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp)（公式）<br>![stars](https://img.shields.io/github/stars/jgraph/drawio-mcp?style=flat-square&logo=github&v=2) | [bahayonghang/drawio-skills](https://github.com/bahayonghang/drawio-skills)<br>![stars](https://img.shields.io/github/stars/bahayonghang/drawio-skills?style=flat-square&logo=github) | [GBSOSS/ai-drawio](https://github.com/GBSOSS/ai-drawio)<br>![stars](https://img.shields.io/github/stars/GBSOSS/ai-drawio?style=flat-square&logo=github) |
| --- | --- | --- | --- | --- |
| **アプローチ** | 純粋な SKILL.md + オプションの MCP サーバー | MCP サーバー / Claude Code プラグイン / Project | YAML DSL + CLI（MCP はオプション） | Claude Code プラグイン |
| **依存関係** | draw.io デスクトップのみ | draw.io デスクトップ | draw.io デスクトップ（MCP はオプション） | draw.io プラグイン + ブラウザ |
| **マルチエージェント** | ✅ 6 プラットフォーム | ⚠️ MCP ホスト（Claude、Cursor、VS Code） | ✅ Claude / Gemini / Codex | ❌ Claude Code のみ |
| **セルフチェック + 自動修正** | ✅ 2 ラウンド（PNG を読み取り） | ❌ | ✅ 検証 + strict モード | ❌ スクリーンショットのみ |
| **反復レビュー** | ✅ 5 ラウンドのループ | ❌ 一度だけ生成 | ✅ 3 つのワークフロー | ❌ |
| **図のプリセット** | ✅ 7 タイプ | ❌ | ✅ 論文モード分類器 | ❌ |
| **Mermaid での記述** | ✅ 28 タイプ（CLI ≥ 30） | ✅ | ❌ | ❌ |
| **ML/DL の図** | ✅ テンソル形状、レイヤーの色分け | ❌ | ❌ | ❌ |
| **カラーシステム** | ✅ 7 色のセマンティックカラー | ❌ | ✅ 6 テーマ | ❌ |
| **公式シェイプ検索** | ✅ 10k 以上のシェイプ（ローカル） | ✅ 10k 以上のシェイプ（MCP） | ❌ | ❌ |
| **AI/LLM ブランドロゴ** | ✅ 321 + 18 データストア | ❌ | ❌ | ❌ |
| **ブラウザフォールバック** | ✅ diagrams.net URL（ビューア + 編集可能） | ✅ diagrams.net URL（プラグイン）+ インラインプレビュー | ✅ オプションの MCP 経由 | ✅ diagrams.net ビューア（メイン） |
| **設定不要** | ✅ `skills/drawio-skill/` をコピー | ✅ | ✅ デスクトップのみのモード | ❌ プラグインのインストールが必要 |

> **公式の jgraph プラグインを使っていますか？** [jgraph/drawio-mcp](https://github.com/jgraph/drawio-mcp) は現在、公式の Claude Code プラグイン（`/plugin install drawio@drawio`）を提供しており、これも `.drawio` を生成してデスクトップ CLI 経由でエクスポートします。drawio-skill はこれを補完するものです — コード / IaC / SQL / OpenAPI / AsyncAPI / Protobuf のインポーター、AI ブランドロゴ、決定論的なシーケンス図と C4 のジェネレーター、セルフチェック + レビューループ、インタラクティブな HTML ビューアを、MCP サーバーなしの単一の SKILL.md で使いたいときにご利用ください。

完全な比較と主な利点のまとめは [docs/COMPARISON.md](docs/COMPARISON.md) にあります（監査日時付き）。

## 🎯 使うべきとき（と使うべきでないとき）

**適している用途：**

- 洗練された正確な図 — ステークホルダー向けの資料、アーキテクチャ、ネットワークトポロジー、厳密な UML、ER 図
- 不透明な塗りつぶし、10,000 以上の公式シェイプ、ブランドアイコン（AWS / Azure / GCP / Cisco / Kubernetes + AI/LLM ロゴ）、スイムレーン、カスタムジオメトリ
- PNG / SVG / PDF にエクスポートしつつ、編集可能なまま残しておきたいもの

**次のものが必要な場合は、姉妹スキルを使ってください：**

- **カジュアルな手描き / ホワイトボード風の見た目** → [excalidraw-skill](https://github.com/Agents365-ai/excalidraw-skill) または [tldraw-skill](https://github.com/Agents365-ai/tldraw-skill)
- **git で管理でき Markdown で描画される diagrams-as-code** → [mermaid-skill](https://github.com/Agents365-ai/mermaid-skill)（汎用）または [plantuml-skill](https://github.com/Agents365-ai/plantuml-skill)（UML）
- **自由な無限キャンバスでのスケッチ / フリーハンドのストローク** → [tldraw-skill](https://github.com/Agents365-ai/tldraw-skill)

## 🔗 関連スキル

[Agents365-ai の図スキルファミリー](https://github.com/Agents365-ai)の一部です — 用途に合ったツールを選んでください：

| スキル | スタイル | 最適な用途 |
| --- | --- | --- |
| [excalidraw-skill](https://github.com/Agents365-ai/excalidraw-skill) | 手描き / スケッチ風 | ホワイトボードのモックアップ、くだけた図 |
| [mermaid-skill](https://github.com/Agents365-ai/mermaid-skill) | テキストベース、自動レイアウト | README への埋め込み、バージョン管理しやすい |
| [plantuml-skill](https://github.com/Agents365-ai/plantuml-skill) | UML 特化 | CI パイプラインでのクラス図 / シーケンス図 |
| [tldraw-skill](https://github.com/Agents365-ai/tldraw-skill) | ホワイトボードでの共同作業 | カジュアルなスケッチ、FigJam 風のボード |

## 👤 作者

**Agents365-ai**

- GitHub: <https://github.com/Agents365-ai>
- Bilibili: <https://space.bilibili.com/441831884>

## 📄 ライセンス

[MIT](LICENSE)
