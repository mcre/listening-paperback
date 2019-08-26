## 使い方

### 動画作成

* ローカルPCにはdockerとjqをインストールしておく
* 予めAWSのクレデンシャルを取得しておく。必要なPolicyは、AmazonPollyFullAccess, AmazonS3FullAccess
    - `./certs/aws_credentials.json` に配置
        - 形式: `{"aws_access_key_id": "hoge", "aws_secret_access_key": "hoge"}`

1. `./projects` にディレクトリを作る(例: `mkdir ./projects/gongitsune`)。以下プロジェクトと呼ぶ。
2. プロジェクトに青空文庫テキストをSJISのまま `novel.txt` として置く。
3. 他プロジェクトを参考に、 `config.json` を作成。 
4. `./batch.sh {プロジェクト名}`を実行
    - 1つのpartのみをbuildする場合
        - `./batch.sh {プロジェクト名} {part_id}`
    - 複数のpartをbuildする場合
        - `./batch.sh {プロジェクト名} {start_part_id} {end_part_id}`
5. プロジェクトの`output_{git_commit_id}_{part_id_or_range}`以下に一部の中間ファイル、出力ファイルが出力される

### youtube upload

* 予め、↓の方に書いてある準備をする
* start_part_id から end_part_id まで、start_publish_at(JST)から1日おきに公開されるよう設定される
* ただし、制限により1日6個までしかアップロードできないみたいなので間違えないように注意！
    - 特に、「第{part_id + 1}回」であることに注意！

1. `python upload.py {project} {version} {start_publish_at} {start_part_id} {end_part_id}`
    - 例: `python upload.py gongitsune_short 20190824-3b79ff4_work 2019-08-25T18:00:00 0 0`

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