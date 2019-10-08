## 使い方

### プロジェクトの作成

* 準備
    - `pip install requests`
* 青空文庫でbook_idを調べる
* 実行
    - `python create_project.py {book_id}`
    - `./projects/{作者名}/{作品名}/` に `novel.txt` と `config.json` が生成される
* `config.json` は適宜調整する
    - `tex_replaces`
        - 表組みなど特殊すぎる表現をまるまる置換するために使用できる
        - `江戸川乱歩/二銭銅貨` 参照
    - `manual_chapters`
        - 一つの動画の時間が長過ぎるときなどに、chapterを指定箇所の前で切ることが可能
        - `太宰治/人間失格` 参照
        - コマンド等はエスケープが必要。(`\` => `\\\\`, '{' => '\{'}
    - `special_rubies`
        - 読み間違い等を調整できる。他の本にも通用する読み間違いは `./src/consts.json` に記述する。
        - 読み間違いは完成した動画や、`viseme.pdf` で確認できる
        - 入力形式は↓を実行すると対話で出力できる
            - `docker run --rm -it -v $PWD:/work lp-python-mecab /bin/sh -c "python -u ruby.py"`
* 画像がある場合は、`./projects/{作者名}/{作品名}/images` に画像をいれて、縦書きに対応するため↓のコマンドで90度回転させる
    - `docker run -v $PWD/projects/{作者名}/{作品名}/images:/images --rm -it rendertoolbox/imagemagick bash -c "mogrify -rotate -90 /images/*.png"`

### 動画作成

* ローカルPCにはdockerとjqをインストールしておく
* 予めAWSのクレデンシャルを取得しておく。必要なPolicyは、AmazonPollyFullAccess, AmazonS3FullAccess
    - `./certs/aws_credentials.json` に配置
        - 形式: `{"aws_access_key_id": "hoge", "aws_secret_access_key": "hoge"}`

1. `./batch.sh {作者名}/{作品名}`を実行
    - 1つのpartのみをbuildする場合
        - `./batch.sh {作者名}/{作品名} {part_id}`
    - 複数のpartをbuildする場合
        - `./batch.sh {作者名}/{作品名} {start_part_id} {end_part_id}`
    - 途中で止める場合
        - `./batch.sh {作者名}/{作品名} x x {止める箇所}`
            - tex, pdf, ssml, voice, timekeeper, before_movie, viseme が指定可能
            - 通常はvisemeは作成されない。visemeと入力した場合のみ作成される。
            - voice を入力した場合はキーボード入力(y)可能。ただしバックグラウンドでは動作できない。
2. プロジェクトの`./output/{git_commit_id}_{part_id_or_range}`以下に一部の中間ファイル、出力ファイルが出力される。
    - `./output/latest` には出力ファイルが上書きされる

* `./batch_first_pdf.sh {作者名}/{作品名}` を使うとpdfを生成し、ログを`./projects/{作者名}/{作品名}/tmp/batch_first_pdf.log` に保存できる。
    - 最初はこれかな。tex処理漏れ等を手軽に確認するために使う。
* `./batch_first_timekeeper.sh {作者名}/{作品名}` を使うと、pdf, 音声, timekeeperを生成し、ログを`./projects/{作者名}/{作品名}/tmp/batch_first_timekeeper.log` に保存できる。
    - 500万文字用の大量変換、timekeeperのエラーチェックに使う。

### youtube upload

* 予め、↓の方に書いてある準備をする
* start_part_id から end_part_id まで、start_publish_at(JST)から1日おきに公開されるよう設定される
* ただし、制限により1日6個までしかアップロードできないみたいなので間違えないように注意！
    - 特に、「第{part_id + 1}回」であることに注意！

1. `python upload.py {作者名}/{作品名} {version} {start_publish_at} {start_part_id} {end_part_id}`
    - 例: `python upload.py 新美南吉/ごん狐 latest 2019-08-25T18:00:00 0 0`
2. `python list.py` で現在のアップロード済み動画一覧、公開状態、公開日をリストアップできる。

## Youtube Upoload準備

* https://code.google.com/apis/console
    - プロジェクトを作成
        - プロジェクト名
            - listening-paperback
* https://console.developers.google.com/?hl=ja
    - プロジェクト listening-paperback を選択
    - ライブラリ -> YouTube Data API v3 を選択 -> 有効化
    - 認証情報 -> 認証情報を作成 -> OAuth2 -> JSONをダウンロード -> `./certs/youtube_client_secrets.json` に配置
    - OAuth同意画面を適当に作成する。スコープには `../auth/youtube` が必要

* youtube uploaderインストール

```
cd ~/Downloads
pip install --upgrade oauth2client google-api-python-client==1.7.4 progressbar2
wget https://github.com/tokland/youtube-upload/archive/master.zip
unzip master.zip
cd youtube-upload-master
python setup.py install
```

* credentialsを作成

```
youtube-upload --title="test" --client-secret='./certs/youtube_client_secrets.json'
# 表示されたURLにアクセスし、ログイン、verification code を入れる
# ~/.youtube-upload-credentials.json にファイルが生成され、以降それが使用される
```



## メモ

* az2tex.py
    - 青空文庫形式を網羅しているわけではないので、うまく変換できないケースが出たら随時修正する。
    - 重いファイルだと一行ごと逐次にする必要あるかも。

* チャンネルのアイコン
    - http://icooon-mono.com/11129-%e7%a9%8d%e3%81%bf%e9%87%8d%e3%81%ad%e3%81%9f%e6%9c%ac%e3%81%ae%e3%82%a2%e3%82%a4%e3%82%b3%e3%83%b3%e7%b4%a0%e6%9d%90/