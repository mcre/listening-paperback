import os
import glob
import json
import os.path
import sys
import time

import boto3

BUCKET_NAME = 'jp.mcreplannnig.polly'
S3_OBJ_PREFIX = 'lp'

def basename(path):
    return os.path.splitext(os.path.basename(path))[0]

def start_task(ssml_path, polly, text, output_format):
    smt = []
    if output_format == 'json':
        smt = ['sentence', 'ssml', 'word']
    response = polly.start_speech_synthesis_task(
        OutputFormat=output_format,
        VoiceId='Mizuki',
        OutputS3BucketName=BUCKET_NAME, OutputS3KeyPrefix=S3_OBJ_PREFIX,
        SpeechMarkTypes=smt,
        TextType='ssml',
        Text=text,
    )
    rs = response['SynthesisTask']
    return {
        'task_id': rs['TaskId'],
        'id': int(basename(ssml_path)),
        's3_basename': basename(rs['OutputUri']),
        'format': rs['OutputFormat'],
    }

def main(aws_access_key_id, aws_secret_access_key):
    os.makedirs('voices', exist_ok=True)
    os.makedirs('marks_tmp', exist_ok=True)
    os.makedirs('marks', exist_ok=True)
    
    session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name='ap-northeast-1')
    polly = session.client('polly')
    bucket = session.resource('s3').Bucket(BUCKET_NAME)
    ssml_list = sorted(glob.glob('ssml/*.xml'))

    tasks = []
    for ssml in ssml_list:
        with open(ssml, 'r') as f:
            text = f.read()
            tasks.append(start_task(ssml, polly, text, 'mp3'))
            tasks.append(start_task(ssml, polly, text, 'json'))
    print(f'polly: {len(tasks) // 2} * 2 tasks')
    for task in tasks:
        while True:
            response = polly.get_speech_synthesis_task(TaskId=task['task_id'])
            st = response['SynthesisTask']['TaskStatus']
            if st == 'completed':
                print(f'polly: success ({task["format"]}, {task["id"]})')
                if task['format'] == 'mp3':
                    bucket.download_file(f'{task["s3_basename"]}.mp3', f'voices/{task["id"]:0>5}.mp3')
                if task['format'] == 'json':
                    bucket.download_file(f'{task["s3_basename"]}.marks', f'marks_tmp/{task["id"]:0>5}.marks')
                break
            elif st == 'failed':
                print(f'polly: failed!!! ({task["format"]}, {task["id"]})')
                break
            else:
                print(f'polly: wait... ({task["format"]}, {task["id"]})')
                time.sleep(10)

    for marks in glob.glob('marks_tmp/*.marks'):
        with open(marks, 'r', encoding='utf-8') as fr, open(f'marks/{basename(marks)}.json', 'w', encoding='utf-8') as fw:
            json.dump([json.loads(line) for line in fr.readlines()], fw, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
