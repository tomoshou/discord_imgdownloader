# -*- coding: utf-8 -*-
"""discord_img_downloader.py から Google Colab 用ノートブックを作り直すスクリプト

使い方: python tools/build_colab_notebook.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "discord_img_downloader.py")
DEST = os.path.join(ROOT, "colab_downloader.ipynb")


def lines(text):
    parts = text.split("\n")
    return [p + "\n" for p in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": lines(text)}


def code(text, form=False):
    meta = {"cellView": "form"} if form else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [], "source": lines(text)}


with open(SRC, encoding="utf-8") as f:
    program = f.read()
# 末尾の「直接実行されたとき」の部分はノートブックでは使わない
program = program.split('\nif __name__ == "__main__":')[0].rstrip() + "\n"
program = "#@title ③ プログラム本体（中身は気にしなくてOK・そのまま ▶ を押してください）\n" \
          '__file__ = "/content/discord_img_downloader.py"\n' + program

cells = [
    md("# Discord 画像一括ダウンローダー（Google ドライブ保存版）\n"
       "\n"
       "Discord サーバーにアップロードされた画像を、**Google ドライブに直接保存** します。\n"
       "\n"
       "## はじめての方へ（初回だけ）\n"
       "1. 左側の **🔑（鍵）アイコン「シークレット」** を開く\n"
       "2. 「新しいシークレットを追加」→ 名前に `DISCORD_BOT_TOKEN`、値に Bot のトークンを貼り付け\n"
       "3. 「ノートブックからのアクセス」を **ON** にする\n"
       "\n"
       "## 実行方法\n"
       "上から順に、各ブロックの左上の **▶（再生ボタン）** を押してください。\n"
       "（メニューの「ランタイム」→「すべてのセルを実行」でもOK）\n"
       "\n"
       "- 途中で止まっても、もう一度実行すると **保存済みの画像は飛ばして続きから** 再開します。\n"
       "- 実行中はこのブラウザのタブを **閉じないで** ください（閉じると止まることがあります）。"),
    code("#@title ① Google ドライブに接続（許可画面が出たら「許可」を押してください）\n"
         "from google.colab import drive\n"
         "drive.mount('/content/drive')", form=True),
    code("#@title ② 設定（必要なら書き換えてから ▶ を押してください）\n"
         'サーバー名 = "ともしょうAquarium Group"  #@param {type:"string"}\n'
         'サーバーID = ""  #@param {type:"string"}\n'
         '#@markdown 対象チャンネル：空欄なら全部。名前・ID・リンクをカンマ（,）区切りで。フォーラムを指定すると中の投稿も全部対象\n'
         '対象チャンネル = ""  #@param {type:"string"}\n'
         'ドライブの保存先フォルダ = "Discord画像"  #@param {type:"string"}\n'
         "動画も保存する = False  #@param {type:\"boolean\"}\n"
         'print("設定しました。")', form=True),
    code(program, form=True),
    code("#@title ④ ダウンロード開始\n"
         "import os\n"
         "from google.colab import drive\n"
         "drive.mount('/content/drive')  # 接続が切れていたら再接続する\n"
         "if not os.path.isdir('/content/drive/MyDrive'):\n"
         "    raise SystemExit('Google ドライブに接続できていません。① をもう一度実行してください。')\n"
         "token = ''\n"
         "try:\n"
         "    from google.colab import userdata\n"
         "    token = userdata.get('DISCORD_BOT_TOKEN')\n"
         "except Exception:\n"
         "    pass\n"
         "if not token:\n"
         "    from getpass import getpass\n"
         "    token = getpass('シークレットにトークンが見つかりません。ここに貼り付けて Enter: ')\n"
         "\n"
         "os.environ['DISCORD_BOT_TOKEN'] = token\n"
         "os.environ['GUILD_NAME'] = サーバー名\n"
         "os.environ['GUILD_ID'] = サーバーID\n"
         "os.environ['CHANNELS'] = 対象チャンネル\n"
         "os.environ['INCLUDE_VIDEOS'] = 'true' if 動画も保存する else 'false'\n"
         "os.environ['OUTPUT_DIR'] = os.path.join('/content/drive/MyDrive', ドライブの保存先フォルダ)\n"
         "\n"
         "try:\n"
         "    main()\n"
         "finally:\n"
         "    # Google ドライブへの書き込みを確実に反映させる\n"
         "    drive.flush_and_unmount()\n"
         "    print('Google ドライブへの保存を確定しました。ドライブの「' + ドライブの保存先フォルダ + '」フォルダを見てください。')",
         form=True),
]

nb = {
    "nbformat": 4,
    "nbformat_minor": 0,
    "metadata": {
        "colab": {"provenance": [], "name": "colab_downloader.ipynb"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
        "language_info": {"name": "python"},
    },
    "cells": cells,
}

with open(DEST, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")
print("作成しました:", DEST)
