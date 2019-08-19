import os
import glob
import hashlib
import json
import os.path
import shutil
import sys
import time

import boto3

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

    tasks = []
    for ssml in sorted(glob.glob('ssml/*.xml')):
        with open(ssml, 'r') as f:
            text = f.read()
            md5 = hashlib.md5(text.encode()).hexdigest()
            cache_path = f'cache/{consts["voice_id"]}/{md5}'
            if not os.path.isdir(cache_path):
                os.makedirs(cache_path, exist_ok=True)
                shutil.copy(ssml, f'{cache_path}/voice.xml')
                tasks.append(start_task(ssml, f'{cache_path}/voice.mp3', polly, text, 'mp3'))
                tasks.append(start_task(ssml, f'{cache_path}/voice.json', polly, text, 'json'))
            else:
                shutil.copy(f'{cache_path}/voice.mp3', f'voices/{basename(ssml)}.mp3')
                shutil.copy(f'{cache_path}/voice.json', f'marks/{basename(ssml)}.json')

    print(f'polly: {len(tasks) // 2} * 2 tasks')
    for task in tasks:
        while True:
            response = polly.get_speech_synthesis_task(TaskId=task['task_id'])
            st = response['SynthesisTask']['TaskStatus']
            if st == 'completed':
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
                break
            elif st == 'failed':
                print(f'polly: failed!!! ({task["format"]}, {task["name"]})')
                break
            else:
                print(f'polly: wait... ({task["format"]}, {task["name"]})')
                time.sleep(10)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
