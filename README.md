## 使い方

* 予めAWSのクレデンシャルを取得しておく。必要なPolicyは、AmazonPollyFullAccess, AmazonS3FullAccess

1. `./projects` にディレクトリを作る(例: `mkdir ./projects/gongitsune`)。以下プロジェクトと呼ぶ。
2. プロジェクトに青空文庫テキストをSJISのまま `novel.txt` として置く。
3. `./batch.sh {プロジェクト名} {AWS_ACCESS_KEY_ID} {AWS_SECRET_ACCESS_KEY}`を実行
4. プロジェクトの`output_{git_commit_id}`以下に一部の中間ファイル、出力ファイルが出力される

## メモ

* az2tex.py
    - 青空文庫形式を網羅しているわけではないので、うまく変換できないケースが出たら随時修正する。
    - 重いファイルだと一行ごと逐次にする必要あるかも。

