import gc
import json
import os
import sys

from moviepy.editor import AudioClip, CompositeVideoClip, CompositeAudioClip, ImageClip, AudioFileClip, VideoFileClip, concatenate_videoclips

with open('consts.json', 'r') as f:
    consts = json.load(f)
with open(f'timekeeper.json', 'r') as f:
    timekeeper = json.load(f)


def write_raw_video(path, video_clip):
    video_clip.write_videofile(path, fps=30, codec='utvideo', audio_codec='pcm_s32le')


def silence_clip(duration):
    return AudioClip(lambda t: 2 * [0], duration=duration)


def generate_voice_clip(voices, video_clip_duration):
    voice_clips = []
    for voice in voices.values():
        clip = AudioFileClip(voice['voice_path'])
        clip = clip.set_duration(clip.duration - 0.05)  # 後ろに雑音が入ることがあるのでちょっと削る
        clip = clip.set_start(voice['start'])
        voice_clips.append(clip)
    voice_clip = CompositeAudioClip(voice_clips)
    return voice_clip


def main(part_id):
    os.makedirs('chapter_movies', exist_ok=True)

    cft = consts['cross_fade_time']
    ci = consts['chapter_interval'] / 2
    chapters = timekeeper['parts'][part_id]['chapters']
    for chapter in chapters:
        first_page = chapter['pages'][0]
        last_page = chapter['pages'][-1]
        video_clips = [ImageClip(first_page['image_path']).set_duration(first_page['start'])]  # 最初一瞬真っ黒になるのを防ぐ
        for page in chapter['pages']:
            clip = VideoFileClip(page['movie_path']).set_start(page['start'])
            video_clips.append(clip)
            if page['page_id'] > 0:  # 1ページ目の入り以外はクロスフェードインする
                clip = ImageClip(page['image_path']).set_start(page['start'] - cft).set_duration(cft).crossfadein(cft)
                video_clips.append(clip)
        video_clip_tmp = CompositeVideoClip(video_clips)
        write_raw_video('tmp.avi', video_clip_tmp)  # メモリ不足回避のため一旦ファイル化する

        # おそうじ
        clip, video_clips, video_clip_tmp = None, None, None
        gc.collect()
        for page in chapter['pages']:
            os.remove(page['movie_path'])

        video_clip = VideoFileClip('tmp.avi')
        video_clip = video_clip.set_audio(generate_voice_clip(chapter['voices'], video_clip.duration))
        video_clip = concatenate_videoclips([  # 前後に chapter_interval 分の静止画を挟んでおく
            ImageClip(first_page['image_path']).set_duration(ci).set_audio(silence_clip(ci)),
            video_clip,
            ImageClip(last_page['words'][-1]['animation_image_path']).set_duration(ci).set_audio(silence_clip(ci)),  # 無音を入れないと雑音がはいる
        ])
        write_raw_video(chapter['movie_path'], video_clip)
        os.remove('tmp.avi')


if __name__ == '__main__':
    main(int(sys.argv[1]))
