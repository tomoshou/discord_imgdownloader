# Discord 画像一括ダウンローダー

Discord サーバー「**ともしょうAquarium Group**」にアップロードされた画像を、
Bot アカウントを使って **全チャンネル・全スレッドからまとめてダウンロード** するツールです。

- 追加のライブラリは不要です（Python 本体だけで動きます）
- 画像はチャンネルごとのフォルダに分けて保存します
- 途中で止めても、もう一度実行すると **続きから再開** します（保存済みの画像は飛ばします）

---

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
