# -*- coding: utf-8 -*-
"""
Discord サーバー画像一括ダウンローダー

Bot アカウントを使って、指定したサーバーの全チャンネル（スレッド・フォーラム含む）に
アップロードされた画像を、チャンネルごとのフォルダに保存します。

追加ライブラリ不要（Python 3.8 以上の標準機能だけで動きます）。
設定は同じフォルダの config.ini に書きます。
"""

import configparser
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://github.com/tomoshou/discord_imgdownloader, 1.0)"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.ini")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"}

# チャンネルの種類（Discord の内部番号）
CH_TEXT = 0
CH_CATEGORY = 4
CH_ANNOUNCEMENT = 5
CH_ANNOUNCEMENT_THREAD = 10
CH_PUBLIC_THREAD = 11
CH_PRIVATE_THREAD = 12
CH_FORUM = 15
CH_MEDIA = 16
CH_VOICE = 2
CH_STAGE = 13

# メッセージを読めるチャンネル（ボイスチャンネルにも付属のテキストチャットがある）
MESSAGE_CHANNEL_TYPES = {CH_TEXT, CH_ANNOUNCEMENT, CH_VOICE, CH_STAGE}
# スレッドを持てるチャンネル
THREAD_PARENT_TYPES = {CH_TEXT, CH_ANNOUNCEMENT, CH_FORUM, CH_MEDIA}


class ApiError(Exception):
    def __init__(self, status, body):
        super().__init__("HTTP {}: {}".format(status, body))
        self.status = status
        self.body = body


def log(msg=""):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Discord API 呼び出し
# ---------------------------------------------------------------------------
class DiscordClient:
    def __init__(self, token):
        token = token.strip()
        if token.lower().startswith("bot "):
            token = token[4:].strip()
        self.token = token

    def get(self, path, params=None):
        url = API_BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        for attempt in range(8):
            req = urllib.request.Request(url, headers={
                "Authorization": "Bot " + self.token,
                "User-Agent": USER_AGENT,
            })
            try:
                with urllib.request.urlopen(req, timeout=60) as res:
                    data = json.loads(res.read().decode("utf-8"))
                    # 制限に近づいたら少し待つ（Discord の利用制限対策）
                    remaining = res.headers.get("X-RateLimit-Remaining")
                    reset_after = res.headers.get("X-RateLimit-Reset-After")
                    if remaining == "0" and reset_after:
                        time.sleep(float(reset_after) + 0.1)
                    return data
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                if e.code == 429:
                    try:
                        wait = float(json.loads(body).get("retry_after", 5))
                    except Exception:
                        wait = 5.0
                    log("  （Discord から「少し待って」と言われたので {:.1f} 秒待ちます）".format(wait))
                    time.sleep(wait + 0.5)
                    continue
                if e.code >= 500:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise ApiError(e.code, body)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                log("  （通信エラー: {}。再試行します）".format(e))
                time.sleep(2 * (attempt + 1))
        raise ApiError(0, "再試行の上限に達しました: " + url)


def download_file(url, dest_path):
    tmp_path = dest_path + ".part"
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as res, open(tmp_path, "wb") as f:
                while True:
                    chunk = res.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
            os.replace(tmp_path, dest_path)
            return True
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                break
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    if os.path.exists(tmp_path):
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    return False


# ---------------------------------------------------------------------------
# 補助関数
# ---------------------------------------------------------------------------
INVALID_CHARS = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def safe_name(name, max_len=80):
    """Windows で使えない文字を置き換え、長すぎる名前を短くする"""
    name = INVALID_CHARS.sub("_", name or "").strip().rstrip(".")
    if not name:
        name = "_"
    if len(name) > max_len:
        root, ext = os.path.splitext(name)
        name = root[: max_len - len(ext)] + ext
    return name


def parse_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on", "はい")


def is_target_attachment(att, include_videos):
    content_type = (att.get("content_type") or "").lower()
    ext = os.path.splitext(att.get("filename", ""))[1].lower()
    if content_type.startswith("image/") or ext in IMAGE_EXTENSIONS:
        return True
    if include_videos and (content_type.startswith("video/") or ext in VIDEO_EXTENSIONS):
        return True
    return False


def snowflake_time(snowflake_id):
    """Discord の ID から投稿日時（日本時間）を計算する"""
    ms = (int(snowflake_id) >> 22) + 1420070400000
    return datetime.fromtimestamp(ms / 1000, JST)


# ---------------------------------------------------------------------------
# サーバー・チャンネルの取得
# ---------------------------------------------------------------------------
def find_guild(client, guild_id, guild_name):
    if guild_id:
        return client.get("/guilds/{}".format(guild_id))

    guilds = []
    after = None
    while True:
        params = {"limit": 200}
        if after:
            params["after"] = after
        page = client.get("/users/@me/guilds", params)
        guilds.extend(page)
        if len(page) < 200:
            break
        after = page[-1]["id"]

    if not guilds:
        log("【エラー】Bot がどのサーバーにも参加していません。先に Bot をサーバーに招待してください。")
        return None

    if guild_name:
        matched = [g for g in guilds if g["name"].strip() == guild_name.strip()]
        if not matched:
            matched = [g for g in guilds if guild_name.strip().lower() in g["name"].lower()]
        if len(matched) == 1:
            return matched[0]

    if len(guilds) == 1:
        return guilds[0]

    log("【エラー】対象のサーバーを特定できませんでした。Bot が参加しているサーバー：")
    for g in guilds:
        log("   - {}  (ID: {})".format(g["name"], g["id"]))
    log("config.ini の GUILD_NAME か GUILD_ID を正しく設定してください。")
    return None


def normalize_key(text):
    """名前・ID・リンクの書き方の違いをそろえる"""
    text = (text or "").strip()
    m = re.search(r"discord(?:app)?\.com/channels/\d+/(\d+)", text)
    if m:
        return m.group(1)  # チャンネルのリンクなら末尾の ID を使う
    m = re.fullmatch(r"<#(\d+)>", text)
    if m:
        return m.group(1)
    return text.lstrip("#").strip().lower()


def parse_channel_filter(value):
    """「水槽写真, 質問フォーラム」のようなカンマ区切りの指定を一覧にする"""
    items = re.split(r"[,、，\n]", value or "")
    return [normalize_key(i) for i in items if normalize_key(i)]


def filter_targets(targets, channels, wanted):
    """指定されたチャンネル（とその中のスレッド・投稿）だけに絞り込む"""
    selected = [t for t in targets if t["keys"] & set(wanted)]
    matched = set()
    for t in selected:
        matched |= t["keys"] & set(wanted)
    missing = [w for w in wanted if w not in matched]
    if missing:
        log("【注意】次のチャンネルが見つかりませんでした: " + ", ".join(missing))
        log("  このサーバーにあるチャンネル・フォーラム・カテゴリ：")
        for c in sorted(channels, key=lambda c: (c.get("type") != CH_CATEGORY, c.get("position", 0))):
            if c["type"] in MESSAGE_CHANNEL_TYPES | THREAD_PARENT_TYPES | {CH_CATEGORY}:
                kind = {CH_CATEGORY: "カテゴリ", CH_FORUM: "フォーラム", CH_MEDIA: "メディア"}.get(c["type"], "チャンネル")
                log("   - {}  [{}]  (ID: {})".format(c["name"], kind, c["id"]))
        log("")
    return selected


def collect_targets(client, guild_id, wanted=None):
    """メッセージを読む対象（チャンネル＋スレッド）を一覧にする"""
    channels = client.get("/guilds/{}/channels".format(guild_id))
    by_id = {c["id"]: c for c in channels}
    categories = {c["id"]: c["name"] for c in channels if c["type"] == CH_CATEGORY}

    targets = []
    seen = set()

    def add(ch, parent=None):
        if ch["id"] in seen:
            return
        seen.add(ch["id"])
        if parent is not None:
            folder = os.path.join(safe_name(parent["name"]), safe_name(ch.get("name", ch["id"])))
            label = "#{} > {}".format(parent["name"], ch.get("name", ""))
        else:
            folder = safe_name(ch["name"])
            label = "#" + ch["name"]
        cat_id = ch.get("parent_id") if parent is None else parent.get("parent_id")
        cat = categories.get(cat_id)
        if cat:
            folder = os.path.join(safe_name(cat), folder)
        # 絞り込み用：自分・親チャンネル（フォーラム等）・カテゴリの名前と ID
        keys = {ch["id"], normalize_key(ch.get("name"))}
        if parent is not None:
            keys |= {parent.get("id"), normalize_key(parent.get("name"))}
        if cat:
            keys |= {cat_id, normalize_key(cat)}
        keys.discard(None)
        keys.discard("")
        targets.append({"id": ch["id"], "label": label, "folder": folder, "keys": keys})

    for ch in sorted(channels, key=lambda c: c.get("position", 0)):
        if ch["type"] in MESSAGE_CHANNEL_TYPES:
            add(ch)

    # 現在アクティブなスレッド
    try:
        active = client.get("/guilds/{}/threads/active".format(guild_id))
        for th in active.get("threads", []):
            add(th, by_id.get(th.get("parent_id"), {"name": "unknown", "parent_id": None}))
    except ApiError as e:
        log("  （アクティブなスレッド一覧を取得できませんでした: HTTP {}）".format(e.status))

    # アーカイブ済み（過去の）スレッド
    for ch in channels:
        if ch["type"] not in THREAD_PARENT_TYPES:
            continue
        kinds = ["public"] if ch["type"] in (CH_FORUM, CH_MEDIA) else ["public", "private"]
        for kind in kinds:
            before = None
            while True:
                params = {"limit": 100}
                if before:
                    params["before"] = before
                try:
                    data = client.get("/channels/{}/threads/archived/{}".format(ch["id"], kind), params)
                except ApiError:
                    break  # 権限がない場合などはスキップ
                threads = data.get("threads", [])
                for th in threads:
                    add(th, ch)
                if not data.get("has_more") or not threads:
                    break
                before = threads[-1].get("thread_metadata", {}).get("archive_timestamp")
                if not before:
                    break
    if wanted:
        targets = filter_targets(targets, channels, wanted)
    return targets


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------
def process_channel(client, target, out_root, include_videos, stats):
    folder = os.path.join(out_root, target["folder"])
    before = None
    found = 0
    saved = 0
    while True:
        params = {"limit": 100}
        if before:
            params["before"] = before
        try:
            messages = client.get("/channels/{}/messages".format(target["id"]), params)
        except ApiError as e:
            if e.status in (403, 404):
                log("  → 閲覧権限がないためスキップしました")
                stats["skipped_channels"] += 1
                return
            raise
        if not messages:
            break

        for msg in messages:
            for att in msg.get("attachments", []):
                if not is_target_attachment(att, include_videos):
                    continue
                found += 1
                posted = snowflake_time(msg["id"]).strftime("%Y%m%d_%H%M%S")
                filename = safe_name("{}_{}_{}".format(posted, att["id"], att.get("filename", "image")), 150)
                dest = os.path.join(folder, filename)
                if os.path.exists(dest):
                    stats["already"] += 1
                    continue
                os.makedirs(folder, exist_ok=True)
                url = att.get("url") or att.get("proxy_url")
                if download_file(url, dest):
                    saved += 1
                    stats["saved"] += 1
                    if saved % 20 == 0:
                        log("  ... {} 枚保存しました".format(saved))
                else:
                    stats["failed"] += 1
                    log("  × 保存失敗: {}".format(att.get("filename")))

        before = messages[-1]["id"]
        if len(messages) < 100:
            break

    log("  → 画像 {} 件（新しく保存 {} 件）".format(found, saved))


def load_config():
    # 環境変数（GitHub Actions の Secrets など）があればそちらを優先する
    env_token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if not os.path.exists(CONFIG_PATH) and not env_token:
        log("【エラー】config.ini が見つかりません。")
        log("config.example.ini をコピーして config.ini という名前にし、トークンを書き込んでください。")
        return None
    s = {}
    if os.path.exists(CONFIG_PATH):
        cp = configparser.ConfigParser()
        # メモ帳で保存した UTF-8（BOM 付き）にも対応
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            cp.read_file(f)
        if cp.has_section("settings"):
            s = cp["settings"]

    def setting(key, default=""):
        value = os.environ.get(key, "").strip()
        return value if value else s.get(key, default).strip()

    cfg = {
        "token": env_token or s.get("BOT_TOKEN", "").strip(),
        "guild_id": setting("GUILD_ID"),
        "guild_name": setting("GUILD_NAME", "ともしょうAquarium Group"),
        "output_dir": setting("OUTPUT_DIR", "downloads") or "downloads",
        "include_videos": parse_bool(setting("INCLUDE_VIDEOS", "false")),
        "channels": parse_channel_filter(setting("CHANNELS")),
    }
    if not cfg["token"] or "ここに" in cfg["token"]:
        log("【エラー】config.ini の BOT_TOKEN にトークンが書かれていません。")
        return None
    return cfg


def main():
    log("=" * 60)
    log(" Discord 画像一括ダウンローダー")
    log("=" * 60)

    cfg = load_config()
    if not cfg:
        return 1

    client = DiscordClient(cfg["token"])

    try:
        me = client.get("/users/@me")
    except ApiError as e:
        if e.status == 401:
            log("【エラー】トークンが正しくありません。Developer Portal で Reset Token して貼り直してください。")
        else:
            log("【エラー】Discord に接続できませんでした: {}".format(e))
        return 1
    log("Bot としてログインしました: {}".format(me.get("username")))

    guild = find_guild(client, cfg["guild_id"], cfg["guild_name"])
    if not guild:
        return 1
    log("対象サーバー: {}".format(guild["name"]))

    out_root = cfg["output_dir"]
    if not os.path.isabs(out_root):
        out_root = os.path.join(SCRIPT_DIR, out_root)
    out_root = os.path.join(out_root, safe_name(guild["name"]))
    log("保存先: {}".format(out_root))
    log("")

    if cfg["channels"]:
        log("指定されたチャンネルだけを対象にします: " + ", ".join(cfg["channels"]))
    else:
        log("すべてのチャンネルを対象にします")
    log("チャンネルとスレッドの一覧を取得しています...")
    targets = collect_targets(client, guild["id"], cfg["channels"])
    if not targets:
        log("【エラー】対象のチャンネルがありません。指定した名前を確認してください。")
        return 1
    log("対象: {} 個のチャンネル／スレッド".format(len(targets)))
    log("")

    stats = {"saved": 0, "already": 0, "failed": 0, "skipped_channels": 0}
    start = time.time()
    for i, target in enumerate(targets, 1):
        log("[{}/{}] {}".format(i, len(targets), target["label"]))
        try:
            process_channel(client, target, out_root, cfg["include_videos"], stats)
        except ApiError as e:
            log("  → エラーのためスキップ: {}".format(e))
            stats["skipped_channels"] += 1

    elapsed = int(time.time() - start)
    log("")
    log("=" * 60)
    log(" 完了しました（{}分{}秒）".format(elapsed // 60, elapsed % 60))
    log("   新しく保存した画像 : {} 枚".format(stats["saved"]))
    log("   保存済みで飛ばした : {} 枚".format(stats["already"]))
    log("   保存に失敗         : {} 枚".format(stats["failed"]))
    log("   読めなかったチャンネル: {} 個".format(stats["skipped_channels"]))
    log("   保存先: {}".format(out_root))
    log("=" * 60)
    if stats["saved"] == 0 and stats["already"] == 0:
        log("")
        log("※ 画像が1枚も見つかりませんでした。Developer Portal の Bot 設定で")
        log("  「MESSAGE CONTENT INTENT」が ON になっているか確認してください。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\n中断しました。もう一度実行すると続きから再開します。")
        sys.exit(1)
