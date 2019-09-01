import os
import glob
import hashlib
import json
import os.path
import re
import shutil
import sys
import time

import boto3

PATTERNS = {
    'tag': re.compile(r'''<("[^"]*"|'[^']*'|[^'">])*>'''),
}

with open('consts.json', 'r') as f:
    consts = json.load(f)


def basename(path):
    return os.path.splitext(os.path.basename(path))[0]


def start_task(ssml_path, cache_path, polly, text, output_format):
    smt = []
    if output_format == 'json':
        smt = ['sentence', 'ssml', 'word']
    response = polly.start_speech_synthesis_task(
        OutputFormat=output_format,
        VoiceId=consts['voice_id'],
        OutputS3BucketName=consts['s3_bucket_name'], OutputS3KeyPrefix=consts['s3_obj_prefix'],
        SpeechMarkTypes=smt,
        TextType='ssml',
        Text=text,
    )
    rs = response['SynthesisTask']
    return {
        'task_id': rs['TaskId'],
        'cache_path': cache_path,
        'ssml_path': ssml_path,
        'name': basename(ssml_path),
        's3_basename': basename(rs['OutputUri']),
        'format': rs['OutputFormat'],
    }


def main(aws_access_key_id, aws_secret_access_key):
    os.makedirs('voices', exist_ok=True)
    os.makedirs('marks_tmp', exist_ok=True)
    os.makedirs('marks', exist_ok=True)

    session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='ap-northeast-1')
    polly = session.client('polly')
    bucket = session.resource('s3').Bucket(consts['s3_bucket_name'])

    pending_tasks = []
    for ssml in sorted(glob.glob('ssml/*.xml')):
        with open(ssml, 'r') as f:
            text = f.read()
            md5 = hashlib.md5(text.encode()).hexdigest()
            cache_path = f'cache/{consts["voice_id"]}/{md5}'
            if not os.path.isfile(f'{cache_path}/voice.mp3') or not os.path.isfile(f'{cache_path}/voice.json'):
                os.makedirs(cache_path, exist_ok=True)
                shutil.copy(ssml, f'{cache_path}/voice.xml')
                pending_tasks.append({'ssml': ssml, 'cache': f'{cache_path}/voice.mp3', 'text': text, 'format': 'mp3'})
                pending_tasks.append({'ssml': ssml, 'cache': f'{cache_path}/voice.json', 'text': text, 'format': 'json'})
            else:
                shutil.copy(f'{cache_path}/voice.mp3', f'voices/{basename(ssml)}.mp3')
                shutil.copy(f'{cache_path}/voice.json', f'marks/{basename(ssml)}.json')

    if len(pending_tasks) > 10:
        print({basename(task['ssml']) for task in pending_tasks})

        print('\n自動実行の場合はエラーが発生します。エラーが発生した場合は手動で実行してください。手動実行方法↓')
        print('\n---------------------------')
        print(f'docker run --rm -it -v $PWD/work:/work lp-python /bin/sh -c "python ssml2voice.py {aws_access_key_id} {aws_secret_access_key}"')
        print('cp -r ./work/cache/* ./cache')
        print('---------------------------\n')
        chars_len = 0
        for pending_task in pending_tasks:
            with open(pending_task['ssml'], 'r') as f:
                ssml = f.read()
                chars_len += len(PATTERNS['tag'].sub('', ssml))
        usd = chars_len * 4e-6
        jpy = usd * 106
        print(f'{chars_len:,} chars -> {usd:.2f} USD ≒ {jpy:.1f} JPY')

        input_text = input(f'polly変換数が10を超えました({len(pending_tasks)})。そのまま続ける場合はyを入力してください\n input: ')
        if input_text != 'y':
            print('終了します')
            return

    tasks = [start_task(t['ssml'], t['cache'] ,polly, t['text'], t['format']) for t in pending_tasks]
    with open('polly_tasks.json', 'w') as f:  # 落ちた時のために！
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    print(f'polly: {len(tasks) // 2} * 2 tasks')
    for task in tasks:
        while True:
            response = polly.get_speech_synthesis_task(TaskId=task['task_id'])
            st = response['SynthesisTask']['TaskStatus']
            if st == 'completed':
                try:
                    print(f'polly: success ({task["format"]}, {task["name"]})')
                    if task['format'] == 'mp3':
                        p = f'voices/{task["name"]}.mp3'
                        bucket.download_file(f'{task["s3_basename"]}.mp3', p)
                        shutil.copy(p, task['cache_path'])
                    if task['format'] == 'json':
                        p1 = f'marks_tmp/{task["name"]}.marks'
                        p2 = f'marks/{task["name"]}.json'
                        bucket.download_file(f'{task["s3_basename"]}.marks', p1)
                        with open(p1, 'r', encoding='utf-8') as fr, open(p2, 'w', encoding='utf-8') as fw:
                            json.dump([json.loads(line) for line in fr.readlines()], fw, ensure_ascii=False, indent=2)
                        shutil.copy(p2, task['cache_path'])
                except Exception:
                    pass
                break
            elif st == 'failed':
                print(f'polly: failed!!! ({task["format"]}, {task["name"]})')
                break
            else:
                print(f'polly: wait... ({task["format"]}, {task["name"]})')
                time.sleep(10)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
