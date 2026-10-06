# Discord 画像一括ダウンローダー

Discord サーバー「**ともしょうAquarium Group**」にアップロードされた画像を、
Bot アカウントを使って **全チャンネル・全スレッドからまとめてダウンロード** するツールです。

- 追加のライブラリは不要です（Python 本体だけで動きます）
- 画像はチャンネルごとのフォルダに分けて保存します
- 途中で止めても、もう一度実行すると **続きから再開** します（保存済みの画像は飛ばします）

---

## 🟢 Google ドライブに保存する（おすすめ・PC に何も入れない）

Google の無料サービス「Colab」を使って、画像を **Google ドライブに直接保存** します。
ブラウザだけで完結し、容量も Google ドライブの空き（無料で 15GB）まで使えます。

> 「準備」の ②〜④（Bot の作成・設定・招待）は必要です。① Python は不要です。

### 開き方
1. 次のリンクを開く：
   **[Colab でノートブックを開く](https://colab.research.google.com/github/tomoshou/discord_imgdownloader/blob/claude/sweet-johnson-49keqi/colab_downloader.ipynb)**
2. このリポジトリは非公開なので、初回は GitHub との連携を求められます。画面の案内に従って許可してください。
   （うまく開けない場合：GitHub で `colab_downloader.ipynb` をダウンロード →
   https://colab.research.google.com/ の「ノートブックをアップロード」から開く）
3. 上部の「ドライブにコピー」を押しておくと、次回から自分のドライブから開けて便利です。

### 初回だけ：トークンを Colab の金庫（シークレット）に登録
1. 画面左側の **🔑（鍵）アイコン** を押す
2. 「新しいシークレットを追加」→ 名前に `DISCORD_BOT_TOKEN`、値にトークンを貼り付け
3. 「ノートブックからのアクセス」を **ON**

### 実行
- メニュー「ランタイム」→「**すべてのセルを実行**」
- 途中で Google ドライブへのアクセス許可を求められたら「許可」
- 完了すると、Google ドライブの **「Discord画像」フォルダ** に画像が入っています

### 注意
- 実行中はブラウザのタブを閉じないでください。止まってしまっても、もう一度実行すれば続きから再開します。
- 無料版の Colab は1回あたり最長12時間程度まで動かせます。

---

## ☁ GitHub 上で動かす（結果を ZIP で受け取る）

GitHub の「Actions」という機能を使い、GitHub のクラウド上のパソコンでダウンロードを実行します。
PC に Python を入れる必要はありません。ブラウザだけで完結します。

> 準備の「② Bot を作る」「③ Bot の設定」「④ Bot をサーバーに招待」は必要です（① Python は不要）。

### 初回だけ：トークンを GitHub の金庫（Secrets）に登録
1. GitHub でこのリポジトリを開く
2. 上のタブ **「Settings」** → 左メニュー **「Secrets and variables」→「Actions」**
3. **「New repository secret」** を押す
4. Name に `DISCORD_BOT_TOKEN`、Secret に Bot のトークンを貼り付けて **「Add secret」**

（Secrets に入れたトークンは、登録した本人でも二度と表示できない安全な場所に保管されます）

### 実行する
1. 上のタブ **「Actions」** → 左の **「Discord画像ダウンロード」** を選ぶ
2. 右側の **「Run workflow」** → 緑の **「Run workflow」** ボタン
3. 数分〜数十分待つ（画像の量によります）。緑のチェックが付けば完了
4. 完了した実行をクリック → 下の **「Artifacts」** にある **`discord-images`** をクリックすると ZIP でダウンロードされます

### クラウド版の注意
- 結果の ZIP は初期設定で **7日間** GitHub に置かれ、その後自動で消えます（実行時に日数を変えられます）。
- 無料プランの非公開リポジトリでは、GitHub に置いておけるファイルの合計が **約500MB** までです。
  画像が多くてアップロードで失敗した場合は、古い実行結果を削除するか、PC 版（下記）を使ってください。
- 1回の実行は最長約6時間です。

---

## 💻 PC で動かす（Windows）

## 準備（初回だけ）

### ① Python をインストール
1. https://www.python.org/downloads/ を開き、「Download Python」ボタンからダウンロード
2. インストーラーの最初の画面で **「Add python.exe to PATH」にチェック** を入れてから「Install Now」

### ② Bot を作る（すでにある場合は ③ へ）
1. https://discord.com/developers/applications を開いてログイン
2. 右上の「New Application」→ 好きな名前を入れて作成
3. 左メニュー「Bot」を開く

### ③ Bot の設定（重要）
左メニュー「Bot」の画面で：
1. 下のほうにある **「MESSAGE CONTENT INTENT」を ON** にして「Save Changes」
   （これが OFF だと、Bot は画像を見ることができません）
2. 「Reset Token」を押して表示された **トークン（長い文字列）をコピー**
   ※トークンは Bot のパスワードです。**絶対に他人に見せたり、ネットに貼ったりしないでください。**

### ④ Bot をサーバーに招待
1. 左メニュー「OAuth2」→「URL Generator」
2. 「SCOPES」で **bot** にチェック
3. 「BOT PERMISSIONS」で **View Channels** と **Read Message History** にチェック
4. 一番下にできた URL をブラウザで開き、「ともしょうAquarium Group」を選んで認証

> 鍵付き（非公開）チャンネルの画像も取りたい場合は、そのチャンネルの設定で
> Bot（または Bot のロール）に「チャンネルを見る」「メッセージ履歴を読む」を許可してください。

---

## 使い方

1. このフォルダを PC の好きな場所に置く（GitHub の「Code」→「Download ZIP」で取得して展開）
2. **`run.bat` をダブルクリック**
3. 初回はメモ帳で `config.ini` が開くので、`BOT_TOKEN =` の後ろにトークンを貼り付けて上書き保存
4. もう一度 **`run.bat` をダブルクリック** → ダウンロードが始まります
5. 終わると、`downloads\ともしょうAquarium Group\` の中にチャンネルごとのフォルダで画像が入っています

ファイル名は `投稿日時_番号_元のファイル名` になっているので、名前順に並べると投稿順になります。

## 設定（config.ini）

| 項目 | 説明 |
|---|---|
| `BOT_TOKEN` | Bot のトークン（必須） |
| `GUILD_NAME` | 対象サーバーの名前。初期値は「ともしょうAquarium Group」 |
| `GUILD_ID` | サーバーID。分かる場合はこちらが確実 |
| `OUTPUT_DIR` | 保存先フォルダ（初期値 `downloads`） |
| `INCLUDE_VIDEOS` | `true` にすると動画も保存 |

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| 「トークンが正しくありません」 | Developer Portal で Reset Token し、貼り直す（前後に空白が入っていないか確認） |
| 画像が1枚も見つからない | 「MESSAGE CONTENT INTENT」が ON になっているか確認 |
| 一部のチャンネルが「閲覧権限がない」 | そのチャンネルで Bot に閲覧権限を与える（ボイスチャンネルなどは問題ありません） |
| 「Python が見つかりません」 | Python を「Add python.exe to PATH」にチェックして再インストール |

## 補足
- 取得対象は「メッセージに添付（アップロード）された画像」です。URL を貼っただけの外部画像は対象外です。
- 画像が多いサーバーでは時間がかかります。途中で閉じても、再実行すれば続きからになります。
